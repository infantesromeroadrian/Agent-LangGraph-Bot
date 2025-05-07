"""Service for handling vector storage and retrieval."""
from typing import List, Dict, Any, Optional
import os
import tempfile
import logging
import traceback
import chromadb
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStoreRetriever

from src.utils.config import config
from src.models.class_models import CompanyDocument

# Configure logging
logger = logging.getLogger(__name__)

class VectorStoreService:
    """Service for managing document vector storage and retrieval."""

    def __init__(self):
        """Initialize the vector store service."""
        self.embeddings = OpenAIEmbeddings(api_key=config.llm.openai_api_key)
        self.vector_store = None
        self.retriever = None
        self._initialize_vector_store()
        
    def _initialize_vector_store(self):
        """Initialize the vector store with the configuration."""
        try:
            # Create a temporary directory for persistence
            persist_directory = os.path.join(tempfile.gettempdir(), "chroma_db")
            os.makedirs(persist_directory, exist_ok=True)
            
            # Initialize using the simplest approach from documentation
            self.vector_store = Chroma(
                collection_name=config.chromadb.collection_name,
                embedding_function=self.embeddings,
                persist_directory=persist_directory
            )
            
            # Initialize retriever using the current LangChain API
            self.retriever = self.vector_store.as_retriever(
                search_kwargs={"k": 5}
            )
            
            logger.info(f"Vector store initialized: {config.chromadb.collection_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {e}")
            logger.error(traceback.format_exc())
            # Create a simple in-memory instance as fallback
            try:
                self.vector_store = Chroma(
                    collection_name="fallback_collection",
                    embedding_function=self.embeddings,
                )
                self.retriever = self.vector_store.as_retriever(
                    search_kwargs={"k": 5}
                )
                logger.info("Fallback vector store initialized")
            except Exception as e2:
                logger.error(f"Failed to initialize fallback vector store: {e2}")
                logger.error(traceback.format_exc())
                self.vector_store = None
                self.retriever = None
    
    def add_documents(self, documents: List[CompanyDocument]) -> List[str]:
        """Add documents to the vector store.
        
        Args:
            documents: List of CompanyDocument objects to add
            
        Returns:
            List of document IDs added
        """
        if not self.vector_store:
            logger.warning("Vector store not initialized, cannot add documents")
            return []
            
        langchain_docs = [
            Document(
                page_content=doc.content,
                metadata={
                    "id": doc.id,
                    "title": doc.title,
                    "document_type": doc.document_type,
                    "source": doc.source,
                    **doc.metadata
                }
            ) for doc in documents
        ]
        
        try:
            ids = self.vector_store.add_documents(langchain_docs)
            logger.info(f"Added {len(ids)} documents to vector store")
            return ids
        except Exception as e:
            logger.error(f"Error adding documents to vector store: {e}")
            logger.error(traceback.format_exc())
            return []
    
    def search(self, query: str, k: int = 5) -> List[CompanyDocument]:
        """Search for documents related to the query.
        
        Args:
            query: The search query text
            k: Number of documents to retrieve
            
        Returns:
            List of CompanyDocument objects
        """
        if not self.retriever:
            logger.warning("Retriever not initialized, cannot search")
            return []
        
        try:
            logger.info(f"Searching for: '{query}' with k={k}")
            
            # Use the new invoke method with proper parameters
            langchain_docs = self.retriever.invoke(query)
            
            logger.info(f"Found {len(langchain_docs)} documents")
            
            # Convert Langchain documents to CompanyDocument format
            result_docs = []
            for doc in langchain_docs:
                try:
                    company_doc = CompanyDocument(
                        id=doc.metadata.get("id", ""),
                        title=doc.metadata.get("title", ""),
                        content=doc.page_content,
                        document_type=doc.metadata.get("document_type", ""),
                        source=doc.metadata.get("source", ""),
                        metadata={k: v for k, v in doc.metadata.items() 
                                if k not in ["id", "title", "document_type", "source"]}
                    )
                    result_docs.append(company_doc)
                except Exception as e:
                    logger.error(f"Error converting document: {e}")
                    continue
            
            return result_docs
            
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            logger.error(traceback.format_exc())
            return []
    
    def get_retriever(self) -> VectorStoreRetriever:
        """Get the vector store retriever.
        
        Returns:
            The configured vector store retriever
        """
        return self.retriever
        
    def delete_document(self, document_id: str) -> None:
        """Delete a document from the vector store.
        
        Args:
            document_id: ID of the document to delete
        """
        if not self.vector_store:
            logger.warning(f"Vector store not initialized, cannot delete document {document_id}")
            return
            
        try:
            self.vector_store.delete(ids=[document_id])
            logger.info(f"Deleted document: {document_id}")
        except Exception as e:
            logger.error(f"Error deleting document {document_id}: {e}")
            logger.error(traceback.format_exc())

    def clear_all_documents(self) -> bool:
        """Delete all documents from the vector store.
        
        Returns:
            True if operation was successful, False otherwise
        """
        if not self.vector_store:
            logger.warning("Vector store not initialized, cannot clear documents")
            return False
            
        try:
            # Get the underlying collection
            collection = self.vector_store._collection
            
            # First, get all document IDs in the collection
            results = collection.get(include=[])
            
            # If there are no documents, we're done
            if not results or len(results["ids"]) == 0:
                logger.info("No documents to clear")
                return True
                
            # Delete all documents using their IDs
            collection.delete(ids=results["ids"])
            
            # Reinitialize the vector store
            self._initialize_vector_store()
            
            logger.info(f"Cleared {len(results['ids'])} documents from vector store")
            return True
        except Exception as e:
            logger.error(f"Error clearing documents from vector store: {e}")
            logger.error(traceback.format_exc())
            return False 