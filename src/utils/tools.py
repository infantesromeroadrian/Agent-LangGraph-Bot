"""Tools for agents to use in the company bot system."""
from typing import List, Dict, Any, Optional
import uuid
import json
from datetime import datetime
from pydantic import BaseModel, Field

from src.models.class_models import CompanyDocument, ToolResult, ToolResultType
from src.services.vector_store_service import VectorStoreService


class SearchDocumentsInput(BaseModel):
    """Input for searching documents."""
    query: str = Field(description="The search query text")
    limit: int = Field(default=5, description="Maximum number of documents to return")


class AddDocumentInput(BaseModel):
    """Input for adding a document."""
    title: str = Field(description="Document title")
    content: str = Field(description="Document content")
    document_type: str = Field(description="Type of document")
    source: Optional[str] = Field(default=None, description="Source of the document")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")


class SearchTool:
    """Tool for searching documents in the vector store."""
    
    def __init__(self, vector_store_service: VectorStoreService):
        """Initialize the search tool.
        
        Args:
            vector_store_service: Instance of VectorStoreService
        """
        self.vector_store = vector_store_service
        
    def search_documents(self, input_data: Dict[str, Any]) -> ToolResult:
        """Search for documents based on a query.
        
        Args:
            input_data: Dictionary with 'query' and optional 'limit'
            
        Returns:
            ToolResult with search results
        """
        try:
            # Parse input
            validated_input = SearchDocumentsInput(**input_data)
            
            # Search documents
            documents = self.vector_store.search(
                validated_input.query,
                k=validated_input.limit
            )
            
            # Format results
            results = []
            for doc in documents:
                results.append({
                    "id": doc.id,
                    "title": doc.title,
                    "snippet": doc.content[:200] + "..." if len(doc.content) > 200 else doc.content,
                    "document_type": doc.document_type,
                    "source": doc.source
                })
                
            return ToolResult(
                tool_name="search_documents",
                status=ToolResultType.SUCCESS,
                result=results,
                metadata={"query": validated_input.query, "count": len(results)}
            )
            
        except Exception as e:
            return ToolResult(
                tool_name="search_documents",
                status=ToolResultType.ERROR,
                error_message=str(e)
            )
            

class DocumentTool:
    """Tool for managing documents in the system."""
    
    def __init__(self, vector_store_service: VectorStoreService):
        """Initialize the document tool.
        
        Args:
            vector_store_service: Instance of VectorStoreService
        """
        self.vector_store = vector_store_service
        
    def add_document(self, input_data: Dict[str, Any]) -> ToolResult:
        """Add a document to the vector store.
        
        Args:
            input_data: Dictionary with document information
            
        Returns:
            ToolResult with operation result
        """
        try:
            # Parse input
            validated_input = AddDocumentInput(**input_data)
            
            # Create a unique ID for the document
            doc_id = str(uuid.uuid4())
            
            # Create the document object
            document = CompanyDocument(
                id=doc_id,
                title=validated_input.title,
                content=validated_input.content,
                document_type=validated_input.document_type,
                source=validated_input.source,
                metadata=validated_input.metadata
            )
            
            # Add to vector store
            self.vector_store.add_documents([document])
            
            return ToolResult(
                tool_name="add_document",
                status=ToolResultType.SUCCESS,
                result={"id": doc_id, "title": document.title},
                metadata={"timestamp": datetime.now().isoformat()}
            )
            
        except Exception as e:
            return ToolResult(
                tool_name="add_document",
                status=ToolResultType.ERROR,
                error_message=str(e)
            )
            
    def delete_document(self, document_id: str) -> ToolResult:
        """Delete a document from the vector store.
        
        Args:
            document_id: ID of the document to delete
            
        Returns:
            ToolResult with operation result
        """
        try:
            # Delete the document
            self.vector_store.delete_document(document_id)
            
            return ToolResult(
                tool_name="delete_document",
                status=ToolResultType.SUCCESS,
                result={"id": document_id, "deleted": True},
                metadata={"timestamp": datetime.now().isoformat()}
            )
            
        except Exception as e:
            return ToolResult(
                tool_name="delete_document",
                status=ToolResultType.ERROR,
                error_message=str(e)
            ) 