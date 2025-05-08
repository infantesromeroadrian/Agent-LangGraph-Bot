"""File processing service for handling different file types."""
import io
import os
import tempfile
import logging
from typing import Dict, Any, Tuple, Optional
import pandas as pd
import csv

# Configure logging
logger = logging.getLogger(__name__)

class FileProcessingService:
    """Service for processing and extracting content from various file types."""
    
    def __init__(self):
        """Initialize the file processing service."""
        try:
            # Try to import optional dependencies
            import PyPDF2
            self.pdf_parser = PyPDF2
            self._has_pdf_support = True
        except ImportError:
            logger.warning("PyPDF2 not installed. PDF support will be limited.")
            self._has_pdf_support = False
    
    def process_file(self, file_content: bytes, filename: str) -> Tuple[str, Dict[str, Any]]:
        """Process a file and extract its content.
        
        Args:
            file_content: Binary content of the file
            filename: Name of the file with extension
            
        Returns:
            Tuple of (extracted_text, metadata)
        """
        # Get file extension
        _, ext = os.path.splitext(filename.lower())
        
        # Process based on file type
        if ext == '.pdf':
            return self.extract_pdf_content(file_content)
        elif ext == '.csv':
            return self.extract_csv_content(file_content)
        elif ext in ['.txt', '.md', '.py', '.js', '.html', '.css', '.json', '.xml']:
            # Text files
            try:
                text_content = file_content.decode('utf-8')
                return text_content, {"format": "text", "extension": ext}
            except UnicodeDecodeError:
                # Try another common encoding
                try:
                    text_content = file_content.decode('latin-1')
                    return text_content, {"format": "text", "extension": ext}
                except Exception as e:
                    logger.error(f"Failed to decode text file: {e}")
                    return f"Error decoding file: {str(e)}", {"error": str(e)}
        else:
            # Unsupported file type
            return f"Unsupported file type: {ext}", {"error": "unsupported_file_type"}
    
    def extract_pdf_content(self, pdf_binary: bytes) -> Tuple[str, Dict[str, Any]]:
        """Extract text content from a PDF file.
        
        Args:
            pdf_binary: Binary content of the PDF file
            
        Returns:
            Tuple of (extracted_text, metadata)
        """
        if not self._has_pdf_support:
            return "PDF processing is not available.", {"error": "pdf_support_not_available"}
            
        try:
            # Create a temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                temp_file.write(pdf_binary)
                temp_file_path = temp_file.name
                
            # Extract text using PyPDF2
            pdf_text = ""
            metadata = {"page_count": 0, "format": "pdf"}
            
            with open(temp_file_path, 'rb') as file:
                pdf_reader = self.pdf_parser.PdfReader(file)
                metadata["page_count"] = len(pdf_reader.pages)
                
                # Extract metadata if available
                if pdf_reader.metadata:
                    for key, value in pdf_reader.metadata.items():
                        # Convert key to string and remove leading '/'
                        clean_key = str(key)
                        if clean_key.startswith('/'):
                            clean_key = clean_key[1:]
                        metadata[clean_key] = str(value)
                
                # Extract text from each page
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    pdf_text += page.extract_text() + "\n\n"
                    
            # Clean up the temporary file
            os.unlink(temp_file_path)
            
            return pdf_text, metadata
            
        except Exception as e:
            logger.error(f"Error extracting PDF content: {e}")
            return f"Error extracting PDF content: {str(e)}", {"error": str(e)}
    
    def extract_csv_content(self, csv_binary: bytes) -> Tuple[str, Dict[str, Any]]:
        """Extract structured content from a CSV file.
        
        Args:
            csv_binary: Binary content of the CSV file
            
        Returns:
            Tuple of (structured_content_as_text, metadata)
        """
        try:
            # Try to determine dialect and encoding
            encoding = 'utf-8'
            try:
                csv_text = csv_binary.decode(encoding)
            except UnicodeDecodeError:
                # Try another encoding
                encoding = 'latin-1'
                csv_text = csv_binary.decode(encoding)
                
            # Use pandas to read CSV (handles many edge cases)
            df = pd.read_csv(io.StringIO(csv_text))
            
            # Get basic metadata
            metadata = {
                "format": "csv",
                "encoding": encoding,
                "row_count": len(df),
                "column_count": len(df.columns),
                "columns": list(df.columns)
            }
            
            # Convert to a readable format
            # For small CSVs: full content
            # For large CSVs: summary with headers and sample rows
            MAX_ROWS_TO_INCLUDE = 100
            
            if len(df) <= MAX_ROWS_TO_INCLUDE:
                # Small CSV - include everything as formatted text
                content = df.to_string(index=False)
            else:
                # Large CSV - include a summary
                sample_head = df.head(10).to_string(index=False)
                sample_tail = df.tail(10).to_string(index=False)
                summary = (
                    f"CSV with {len(df)} rows and {len(df.columns)} columns.\n"
                    f"Columns: {', '.join(df.columns)}\n\n"
                    f"First 10 rows:\n{sample_head}\n\n"
                    f"Last 10 rows:\n{sample_tail}"
                )
                content = summary
                
            return content, metadata
            
        except Exception as e:
            logger.error(f"Error extracting CSV content: {e}")
            return f"Error extracting CSV content: {str(e)}", {"error": str(e)} 