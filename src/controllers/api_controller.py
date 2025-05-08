"""API controller for the company bot application."""
from typing import List, Dict, Any, Optional
import logging
import traceback
import io
import os
import tempfile
from fastapi import APIRouter, HTTPException, Depends, Body, UploadFile, File, Form, Request
from fastapi.responses import StreamingResponse, JSONResponse
import asyncio

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
        
        # Check if streaming is requested in metadata
        enable_streaming = query_input.metadata.get("streaming", False)
        
        # Process the query through the agent workflow
        logger.info("Processing query through agent workflow")
        result = agent_nodes.process_user_query(
            query=query_input.query,
            conversation_history=context_dict,
            streaming=enable_streaming
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
            "context_documents": [],
            "streaming": result.get("is_streaming", False)
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
            
        # Add partial responses if streaming was enabled
        if result.get("is_streaming", False):
            partial_responses = result.get("partial_responses", {})
            response["partial_responses"] = {}
            
            for role, partial_response in partial_responses.items():
                if not isinstance(partial_response, dict) and hasattr(partial_response, '__dict__'):
                    # Convert object to dict if needed
                    partial_response_dict = {
                        "content": getattr(partial_response, "content", ""),
                        "agent_id": getattr(partial_response, "agent_id", ""),
                        "agent_role": getattr(partial_response, "agent_role", role),
                        "sources": getattr(partial_response, "sources", []),
                        "is_partial": True
                    }
                    response["partial_responses"][role] = partial_response_dict
                else:
                    # Already a dict or other structure
                    response["partial_responses"][role] = partial_response
        
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


@router.post("/query/stream")
async def stream_query(query_input: QueryInput):
    """Process a query and stream the response as it's generated.
    
    Args:
        query_input: User query input
        
    Returns:
        Streaming response with response chunks
    """
    async def generate():
        try:
            # Add streaming flag to metadata
            if not query_input.metadata:
                query_input.metadata = {}
            query_input.metadata["streaming"] = True
            
            # Convert context to expected format
            context_dict = []
            for msg in query_input.context:
                context_dict.append({
                    "content": msg.content,
                    "type": msg.type,
                    "sender": msg.sender
                })
            
            # Start processing in a separate thread to not block
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: agent_nodes.process_user_query(
                    query=query_input.query,
                    conversation_history=context_dict,
                    streaming=True
                )
            )
            
            # Initial response
            yield "data: " + '{"type": "start", "content": ""}\n\n'
            
            # Stream partial responses
            partial_responses = result.get("partial_responses", {})
            if partial_responses:
                for role, response in partial_responses.items():
                    if hasattr(response, "content"):
                        content = response.content
                    else:
                        content = str(response)
                    
                    # Send each partial result
                    yield f"data: {{\n"
                    yield f'"type": "partial",\n'
                    yield f'"role": "{role}",\n'
                    yield f'"content": "{content.replace(chr(34), chr(92)+chr(34)).replace(chr(10), chr(92)+"n")}"\n'
                    yield f"}}\n\n"
                    
                    # Small delay to control rate
                    await asyncio.sleep(0.01)
            
            # Final response
            final_content = result.get("final_response", "")
            yield f"data: {{\n"
            yield f'"type": "final",\n'
            yield f'"content": "{final_content.replace(chr(34), chr(92)+chr(34)).replace(chr(10), chr(92)+"n")}"\n'
            yield f"}}\n\n"
            
            # End of stream
            yield "data: " + '{"type": "end"}\n\n'
            
        except Exception as e:
            logger.error(f"Error in stream_query: {str(e)}")
            logger.error(traceback.format_exc())
            
            # Send error in the stream
            yield f"data: {{\n"
            yield f'"type": "error",\n'
            yield f'"content": "Error: {str(e).replace(chr(34), chr(92)+chr(34))}"\n'
            yield f"}}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


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
        metadata = {
            "original_filename": file.filename,
            "content_type": file.content_type,
            "upload_method": "file"
        }
        
        if file.content_type == "application/pdf" or file.filename.lower().endswith(".pdf"):
            # Procesar PDF usando PyPDF2
            content = extract_pdf_content(file_content)
            metadata["file_type"] = "pdf"
            
        elif file.content_type == "text/csv" or file.filename.lower().endswith(".csv"):
            # Procesar CSV como texto con formato
            content = extract_csv_content(file_content)
            metadata["file_type"] = "csv"
            
        elif file.content_type in ["text/plain", "text/markdown"] or file.filename.lower().endswith((".txt", ".md")):
            # Procesar archivos de texto
            content = file_content.decode("utf-8")
            metadata["file_type"] = "text"
            
        else:
            raise HTTPException(status_code=400, detail="Tipo de archivo no soportado")
        
        # Preparar el documento para añadirlo al vector store
        document_data = {
            "title": title,
            "content": content,
            "document_type": document_type,
            "source": source,
            "metadata": metadata
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
            
            # Extraer página por página para preservar estructura
            for i, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text:
                    # Agregar separador de página para mejor organización
                    if i > 0:
                        text += "\n\n--- Página " + str(i+1) + " ---\n\n"
                    else:
                        text += "--- Página 1 ---\n\n"
                    text += page_text.strip() + "\n"
            
            # Limpiar texto extraído
            text = text.strip()
            
            # Si no se extrajo texto, podría ser un PDF escaneado
            if not text:
                text = "Este documento parece ser un PDF escaneado o no contiene texto extraíble."
                
            return text
        finally:
            # Eliminar el archivo temporal
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    except Exception as e:
        logger.error(f"Error extracting PDF content: {str(e)}")
        return f"Error extracting content: {str(e)}"


def extract_csv_content(csv_binary):
    """Extract and format content from a CSV file.
    
    Args:
        csv_binary: Binary content of the CSV file
        
    Returns:
        Formatted text representation of the CSV content
    """
    try:
        import csv
        from io import StringIO
        
        # Decodificar el contenido binario a texto
        # Intentar con utf-8 primero, pero probar otras codificaciones si falla
        try:
            csv_text = csv_binary.decode('utf-8')
        except UnicodeDecodeError:
            try:
                csv_text = csv_binary.decode('latin-1')
            except:
                csv_text = csv_binary.decode('cp1252', errors='replace')
        
        # Usar StringIO para leer el texto como archivo
        csv_file = StringIO(csv_text)
        
        # Leer CSV con el módulo csv
        reader = csv.reader(csv_file)
        rows = list(reader)
        
        if not rows:
            return "CSV vacío o sin datos"
        
        # Obtener encabezados (primera fila)
        headers = rows[0]
        
        # Formatear como texto estructurado
        result = "--- DATOS CSV ---\n\n"
        
        # Agregar descripción de estructura
        result += f"Columnas ({len(headers)}): {', '.join(headers)}\n"
        result += f"Filas: {len(rows) - 1}\n\n"
        
        # Limitar la cantidad de filas para prevenir documentos demasiado grandes
        max_rows = min(100, len(rows))
        
        # Crear una tabla de texto simple
        column_widths = [max(len(str(row[i])) if i < len(row) else 0 for row in rows[:max_rows]) 
                         for i in range(len(headers))]
        column_widths = [max(w, len(h)) for w, h in zip(column_widths, headers)]
        
        # Agregar encabezados
        header_row = " | ".join(h.ljust(w) for h, w in zip(headers, column_widths))
        result += header_row + "\n"
        result += "-" * len(header_row) + "\n"
        
        # Agregar filas de datos (limitadas)
        for i, row in enumerate(rows[1:max_rows], 1):
            # Asegurar que cada fila tenga la misma cantidad de columnas que los encabezados
            row_padded = row + [''] * (len(headers) - len(row))
            result += " | ".join(str(cell).ljust(w) for cell, w in zip(row_padded[:len(headers)], column_widths)) + "\n"
        
        # Indicar si hay más filas
        if len(rows) > max_rows:
            result += f"\n... y {len(rows) - max_rows} filas más (truncado) ..."
        
        return result
        
    except Exception as e:
        logger.error(f"Error extracting CSV content: {str(e)}")
        # Fallback: devolver el CSV como texto plano
        try:
            return csv_binary.decode('utf-8', errors='replace')
        except:
            return f"Error processing CSV: {str(e)}"


@router.delete("/documents")
async def clear_all_documents():
    """Delete all documents from the vector store.
    
    Returns:
        Result of the operation
    """
    try:
        success = vector_store.clear_all_documents()
        
        if not success:
            raise HTTPException(status_code=500, detail="Error clearing documents")
            
        return {
            "status": "success",
            "message": "All documents have been cleared"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing documents: {str(e)}") 