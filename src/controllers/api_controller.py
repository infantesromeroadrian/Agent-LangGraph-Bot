"""API controller for the company bot application."""
from typing import List, Dict, Any, Optional
import logging
import traceback
from fastapi import APIRouter, HTTPException, Depends, Body

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
        
        # Format response - result is now a dictionary
        logger.info("Formatting response")
        response = {
            "query": query_input.query,
            "response": result["final_response"],
            "agent_responses": {},
            "context_documents": []
        }
        
        # Add agent responses
        for role, agent_response in result["agent_responses"].items():
            response["agent_responses"][role] = {
                "content": agent_response.content,
                "agent_id": agent_response.agent_id,
                "agent_role": agent_response.agent_role,
                "sources": agent_response.sources
            }
            
        # Add context documents
        for doc in result["context"]:
            response["context_documents"].append({
                "id": doc.id,
                "title": doc.title,
                "snippet": doc.content[:200] + "..." if len(doc.content) > 200 else doc.content,
                "document_type": doc.document_type,
                "source": doc.source
            })
            
        logger.info("Query processed successfully")
        return response
        
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")


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