"""Utility for loading and ingesting documents into the system."""
import os
import uuid
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

from langchain_community.document_loaders import (
    DirectoryLoader,
    TextLoader,
    PyMuPDFLoader,
    CSVLoader,
    UnstructuredMarkdownLoader,
)
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.models.class_models import CompanyDocument
from src.services.vector_store_service import VectorStoreService


logger = logging.getLogger(__name__)


class DocumentLoader:
    """Utility for loading and ingesting documents into the system."""
    
    def __init__(self, vector_store_service: VectorStoreService):
        """Initialize document loader with vector store service.
        
        Args:
            vector_store_service: Instance of VectorStoreService
        """
        self.vector_store = vector_store_service
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=100,
        )
        
    def load_directory(self, directory_path: str, recursive: bool = True) -> Tuple[int, int]:
        """Load all supported documents from a directory.
        
        Args:
            directory_path: Path to directory containing documents
            recursive: Whether to search subdirectories
            
        Returns:
            Tuple of (number of documents processed, number of chunks stored)
        """
        if not os.path.exists(directory_path):
            logger.error(f"Directory not found: {directory_path}")
            return (0, 0)
            
        # Define loaders for different file types
        loaders = {
            ".txt": DirectoryLoader(directory_path, glob="**/*.txt" if recursive else "*.txt", loader_cls=TextLoader),
            ".pdf": DirectoryLoader(directory_path, glob="**/*.pdf" if recursive else "*.pdf", loader_cls=PyMuPDFLoader),
            ".csv": DirectoryLoader(directory_path, glob="**/*.csv" if recursive else "*.csv", loader_cls=CSVLoader),
            ".md": DirectoryLoader(directory_path, glob="**/*.md" if recursive else "*.md", loader_cls=UnstructuredMarkdownLoader),
        }
        
        total_docs = 0
        total_chunks = 0
        
        # Process each file type
        for ext, loader in loaders.items():
            try:
                # Load documents
                documents = loader.load()
                
                if not documents:
                    logger.info(f"No {ext} documents found in {directory_path}")
                    continue
                    
                logger.info(f"Loaded {len(documents)} {ext} documents from {directory_path}")
                
                # Split documents into chunks
                chunks = self.text_splitter.split_documents(documents)
                logger.info(f"Split into {len(chunks)} chunks")
                
                # Convert to CompanyDocument objects
                company_docs = []
                for chunk in chunks:
                    # Extract metadata
                    source = chunk.metadata.get("source", "")
                    title = os.path.basename(source) if source else f"Document {uuid.uuid4()}"
                    
                    company_doc = CompanyDocument(
                        id=str(uuid.uuid4()),
                        title=title,
                        content=chunk.page_content,
                        document_type=ext[1:],  # Remove leading dot
                        source=source,
                        metadata=chunk.metadata
                    )
                    company_docs.append(company_doc)
                
                # Add to vector store
                self.vector_store.add_documents(company_docs)
                
                total_docs += len(documents)
                total_chunks += len(chunks)
                
            except Exception as e:
                logger.error(f"Error processing {ext} documents: {e}")
        
        return (total_docs, total_chunks)
    
    def load_single_document(self, file_path: str) -> Tuple[bool, int]:
        """Load a single document into the system.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Tuple of (success, number of chunks stored)
        """
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return (False, 0)
        
        try:
            ext = os.path.splitext(file_path)[1].lower()
            
            # Select appropriate loader
            if ext == ".txt":
                loader = TextLoader(file_path)
            elif ext == ".pdf":
                loader = PyMuPDFLoader(file_path)
            elif ext == ".csv":
                loader = CSVLoader(file_path)
            elif ext == ".md":
                loader = UnstructuredMarkdownLoader(file_path)
            else:
                logger.error(f"Unsupported file type: {ext}")
                return (False, 0)
                
            # Load document
            documents = loader.load()
            
            if not documents:
                logger.warning(f"No content extracted from {file_path}")
                return (False, 0)
                
            # Split document into chunks
            chunks = self.text_splitter.split_documents(documents)
            
            # Convert to CompanyDocument objects
            company_docs = []
            for chunk in chunks:
                company_doc = CompanyDocument(
                    id=str(uuid.uuid4()),
                    title=os.path.basename(file_path),
                    content=chunk.page_content,
                    document_type=ext[1:],  # Remove leading dot
                    source=file_path,
                    metadata=chunk.metadata
                )
                company_docs.append(company_doc)
            
            # Add to vector store
            self.vector_store.add_documents(company_docs)
            
            logger.info(f"Loaded {file_path} and split into {len(chunks)} chunks")
            return (True, len(chunks))
            
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            return (False, 0) 