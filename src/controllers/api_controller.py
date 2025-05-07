"""API controller for the company bot application."""
from typing import List, Dict, Any, Optional
import logging
import traceback
import io
import os
import tempfile
from fastapi import APIRouter, HTTPException, Depends, Body, UploadFile, File, Form, Request

from src.models.class_models import QueryInput, MessageType
from src.agents.agent_nodes import AgentNodes
from src.services.vector_store_service import VectorStoreService
from src.utils.tools import SearchTool, DocumentTool, AddDocumentInput


# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api", tags=["Company Bot API"])

# Initialize services
agent_nodes = AgentNodes()
vector_store = VectorStoreService()
search_tool = SearchTool(vector_store)
document_tool = DocumentTool(vector_store)


@router.post("/query", response_model=Dict[str, Any])
async def process_query(query_input: QueryInput):
    """Process a user query through the agent system.
    
    Args:
        query_input: User query input
        
    Returns:
        Processing result with agent responses
    """
    try:
        logger.info(f"Received query: {query_input.query}")
        # Convert context to expected format
        context_dict = []
        for msg in query_input.context:
            context_dict.append({
                "content": msg.content,
                "type": msg.type,
                "sender": msg.sender
            })
        
        # Process the query through the agent workflow
        logger.info("Processing query through agent workflow")
        result = agent_nodes.process_user_query(
            query=query_input.query,
            conversation_history=context_dict
        )
        
        logger.info("Query processed, preparing response")
        
        # Ensure we have a valid result object
        if not result or not isinstance(result, dict):
            logger.error(f"Invalid result type: {type(result)}")
            return {
                "query": query_input.query,
                "response": "Lo siento, ocurrió un error al procesar tu consulta. Por favor intenta nuevamente.",
                "agent_responses": {},
                "context_documents": []
            }
        
        # Format response - result is now a dictionary
        logger.info("Formatting response")
        response = {
            "query": query_input.query,
            "response": result.get("final_response", "Lo siento, no pude generar una respuesta."),
            "agent_responses": {},
            "context_documents": []
        }
        
        # Add agent responses
        agent_responses = result.get("agent_responses", {})
        for role, agent_response in agent_responses.items():
            if not isinstance(agent_response, dict) and hasattr(agent_response, '__dict__'):
                # Convert object to dict if needed
                agent_response_dict = {
                    "content": getattr(agent_response, "content", ""),
                    "agent_id": getattr(agent_response, "agent_id", ""),
                    "agent_role": getattr(agent_response, "agent_role", role),
                    "sources": getattr(agent_response, "sources", [])
                }
                response["agent_responses"][role] = agent_response_dict
            else:
                # Already a dict or other structure
                response["agent_responses"][role] = agent_response
            
        # Add context documents
        context = result.get("context", [])
        for doc in context:
            if not isinstance(doc, dict) and hasattr(doc, '__dict__'):
                # Extract attributes if object
                doc_dict = {
                    "id": getattr(doc, "id", ""),
                    "title": getattr(doc, "title", "Unknown Document"),
                    "snippet": getattr(doc, "content", "")[:200] + "..." if len(getattr(doc, "content", "")) > 200 else getattr(doc, "content", ""),
                    "document_type": getattr(doc, "document_type", "unknown"),
                    "source": getattr(doc, "source", "")
                }
                response["context_documents"].append(doc_dict)
            else:
                # Already a dict or other structure
                response["context_documents"].append(doc)
            
        logger.info("Query processed successfully")
        return response
        
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Return a friendly error response instead of raising an exception
        return {
            "query": query_input.query,
            "response": f"Lo siento, ocurrió un error al procesar tu consulta: {str(e)}. Por favor intenta nuevamente.",
            "agent_responses": {},
            "context_documents": [],
            "error": str(e)  # Include error for frontend debugging
        }


@router.post("/documents/search")
async def search_documents(search_input: Dict[str, Any] = Body(...)):
    """Search for documents in the vector store.
    
    Args:
        search_input: Search query parameters
        
    Returns:
        Search results
    """
    try:
        result = search_tool.search_documents(search_input)
        
        if result.status == "error":
            raise HTTPException(status_code=400, detail=result.error_message)
            
        return {
            "status": "success",
            "results": result.result,
            "metadata": result.metadata
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching documents: {str(e)}")


@router.post("/documents")
async def add_document(document_input: AddDocumentInput):
    """Add a document to the vector store.
    
    Args:
        document_input: Document data
        
    Returns:
        Result of the operation
    """
    try:
        result = document_tool.add_document(document_input.dict())
        
        if result.status == "error":
            raise HTTPException(status_code=400, detail=result.error_message)
            
        return {
            "status": "success",
            "document": result.result,
            "metadata": result.metadata
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding document: {str(e)}")


@router.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    """Delete a document from the vector store.
    
    Args:
        document_id: ID of the document to delete
        
    Returns:
        Result of the operation
    """
    try:
        result = document_tool.delete_document(document_id)
        
        if result.status == "error":
            raise HTTPException(status_code=400, detail=result.error_message)
            
        return {
            "status": "success",
            "result": result.result,
            "metadata": result.metadata
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting document: {str(e)}")


@router.post("/documents/upload-file")
async def upload_file(
    file: UploadFile = File(...),
    title: str = Form(...),
    document_type: str = Form(...),
    source: str = Form("user_upload")
):
    """Upload and process a file, extracting its content before adding it to the vector store.
    
    Args:
        file: The uploaded file (PDF, CSV, etc.)
        title: Document title
        document_type: Type of document
        source: Source of the document
        
    Returns:
        Result of the operation
    """
    try:
        logger.info(f"Processing file upload: {file.filename}, type: {file.content_type}")
        
        # Leer el contenido del archivo
        file_content = await file.read()
        
        # Extraer el contenido según el tipo de archivo
        content = ""
        
        if file.content_type == "application/pdf" or file.filename.lower().endswith(".pdf"):
            # Procesar PDF - requeriría PyPDF2 o similar
            content = extract_pdf_content(file_content)
            
        elif file.content_type == "text/csv" or file.filename.lower().endswith(".csv"):
            # Procesar CSV como texto simple por ahora
            content = file_content.decode("utf-8")
            
        elif file.content_type in ["text/plain", "text/markdown"] or file.filename.lower().endswith((".txt", ".md")):
            # Procesar archivos de texto
            content = file_content.decode("utf-8")
            
        else:
            raise HTTPException(status_code=400, detail="Tipo de archivo no soportado")
        
        # Preparar el documento para añadirlo al vector store
        document_data = {
            "title": title,
            "content": content,
            "document_type": document_type,
            "source": source,
            "metadata": {
                "original_filename": file.filename,
                "content_type": file.content_type,
                "upload_method": "file"
            }
        }
        
        # Añadir el documento al vector store
        result = document_tool.add_document(document_data)
        
        if result.status == "error":
            raise HTTPException(status_code=400, detail=result.error_message)
            
        return {
            "status": "success",
            "document": result.result,
            "metadata": result.metadata
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")


def extract_pdf_content(pdf_binary):
    """Extract text content from a PDF file.
    
    Args:
        pdf_binary: Binary content of the PDF file
        
    Returns:
        Extracted text from the PDF
    """
    try:
        # Necesario instalar PyPDF2: pip install PyPDF2
        try:
            from PyPDF2 import PdfReader
        except ImportError:
            return "Error: PyPDF2 no está instalado. Por favor, instala PyPDF2 para procesar archivos PDF."
            
        # Crear un archivo temporal para el PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file.write(pdf_binary)
            temp_path = temp_file.name
        
        try:
            # Extraer texto del PDF
            reader = PdfReader(temp_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            
            # Limpiar un poco el texto extraído
            text = text.strip()
            return text
        finally:
            # Eliminar el archivo temporal
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    except Exception as e:
        logger.error(f"Error extracting PDF content: {str(e)}")
        return f"Error extracting content: {str(e)}" 