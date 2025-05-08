"""Document controller for handling document operations."""
import logging
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Body

from src.services.vector_store_service import VectorStoreService
from src.services.file_processing_service import FileProcessingService
from src.utils.tools import DocumentTool, AddDocumentInput

# Configure logging
logger = logging.getLogger(__name__)

# Create router - fix the prefix to avoid duplication with api_controller.py
router = APIRouter(prefix="/documents", tags=["Documents API"])

# Initialize services
vector_store = VectorStoreService()
document_tool = DocumentTool(vector_store)
file_processor = FileProcessingService()


@router.post("/search")
async def search_documents(search_input: Dict[str, Any] = Body(...)):
    """Search for documents in the vector store.
    
    Args:
        search_input: Search parameters
        
    Returns:
        List of matching documents
    """
    try:
        query = search_input.get("query", "")
        filters = search_input.get("filters", {})
        limit = search_input.get("limit", 5)
        
        if not query:
            return {"results": [], "count": 0}
            
        # Search for documents
        documents = vector_store.search(
            query=query,
            filters=filters,
            limit=limit
        )
        
        # Format results
        results = []
        for doc in documents:
            # Format document for API response
            doc_dict = {
                "id": doc.id,
                "title": doc.title,
                "snippet": doc.content[:200] + "..." if len(doc.content) > 200 else doc.content,
                "document_type": doc.document_type,
                "source": doc.source,
                "metadata": doc.metadata
            }
            results.append(doc_dict)
            
        return {"results": results, "count": len(results)}
        
    except Exception as e:
        logger.error(f"Error searching documents: {str(e)}")
        logger.exception(e)
        raise HTTPException(status_code=500, detail=f"Error searching documents: {str(e)}")


@router.post("")
async def add_document(document_input: AddDocumentInput):
    """Add a document to the vector store.
    
    Args:
        document_input: Document to add
        
    Returns:
        Result of adding the document
    """
    try:
        # Use the document tool to add the document
        result = document_tool.add_document(document_input)
        
        if result.status != "success" or result.result is None:
            error_msg = result.error_message or "Unknown error adding document"
            raise HTTPException(status_code=500, detail=error_msg)
            
        return {"success": True, "document_id": result.result["id"]}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding document: {str(e)}")
        logger.exception(e)
        raise HTTPException(status_code=500, detail=f"Error adding document: {str(e)}")


@router.delete("/{document_id}")
async def delete_document(document_id: str):
    """Delete a document from the vector store.
    
    Args:
        document_id: ID of the document to delete
        
    Returns:
        Result of deleting the document
    """
    try:
        # Delete the document
        success = vector_store.delete(document_id)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Document not found: {document_id}")
            
        return {"success": True, "document_id": document_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document: {str(e)}")
        logger.exception(e)
        raise HTTPException(status_code=500, detail=f"Error deleting document: {str(e)}")


@router.post("/upload-file")
async def upload_file(
    file: UploadFile = File(...),
    title: str = Form(...),
    document_type: str = Form(...),
    source: str = Form("user_upload")
):
    """Upload a file and add it as a document to the vector store.
    
    Args:
        file: File to upload
        title: Document title
        document_type: Type of document
        source: Source of the document
        
    Returns:
        Result of adding the document
    """
    try:
        # Read file content
        file_content = await file.read()
        
        # Process the file based on its type
        content, metadata = file_processor.process_file(file_content, file.filename)
        
        # Create document input
        document_input = AddDocumentInput(
            title=title,
            content=content,
            document_type=document_type,
            source=source,
            metadata={
                "filename": file.filename,
                "content_type": file.content_type,
                **metadata
            }
        )
        
        # Add document
        result = document_tool.add_document(document_input)
        
        if result.status != "success" or result.result is None:
            error_msg = result.error_message or "Unknown error uploading file"
            raise HTTPException(status_code=500, detail=error_msg)
        
        return {
            "success": True,
            "document_id": result.result["id"],
            "title": title,
            "document_type": document_type,
            "filename": file.filename,
            "metadata": metadata
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        logger.exception(e)
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")


@router.delete("")
async def clear_all_documents():
    """Clear all documents from the vector store.
    
    Returns:
        Result of clearing documents
    """
    try:
        # Clear all documents
        count = vector_store.clear()
        return {"success": True, "deleted_count": count}
        
    except Exception as e:
        logger.error(f"Error clearing documents: {str(e)}")
        logger.exception(e)
        raise HTTPException(status_code=500, detail=f"Error clearing documents: {str(e)}")


@router.get("")
async def get_all_documents():
    """Get all documents from the vector store.
    
    Returns:
        List of all documents
    """
    try:
        # Get all documents
        documents = vector_store.get_all()
        
        # Format results
        results = []
        for doc in documents:
            # Format document for API response
            doc_dict = {
                "id": doc.id,
                "title": doc.title,
                "snippet": doc.content[:200] + "..." if len(doc.content) > 200 else doc.content,
                "document_type": doc.document_type,
                "source": doc.source,
                "metadata": doc.metadata
            }
            results.append(doc_dict)
            
        return {"results": results, "count": len(results)}
        
    except Exception as e:
        logger.error(f"Error getting documents: {str(e)}")
        logger.exception(e)
        raise HTTPException(status_code=500, detail=f"Error getting documents: {str(e)}") 