"""Query processing service for handling user queries."""
import logging
from typing import Dict, List, Any, Optional

from src.models.class_models import QueryInput, MessageType
from src.agents.core.agent_nodes import AgentNodes
from src.utils.graph_utils import GraphManagerUtil

# Configure logging
logger = logging.getLogger(__name__)

class QueryService:
    """Service for processing user queries through the agent system."""
    
    def __init__(self):
        """Initialize the query service with required components."""
        self.agent_nodes = AgentNodes()
        self.graph_manager = GraphManagerUtil()
        
    async def process_query(self, query_input: QueryInput) -> Dict[str, Any]:
        """Process a user query through the agent system.
        
        Args:
            query_input: User query input
            
        Returns:
            Processing result with agent responses
        """
        try:
            logger.info(f"Processing query: {query_input.query}")
            
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
            result = self.agent_nodes.process_user_query(
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
            response = self._format_response(query_input.query, result)
            
            logger.info("Query processed successfully")
            return response
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            logger.exception(e)
            
            # Return a friendly error response
            return {
                "query": query_input.query,
                "response": f"Lo siento, ocurrió un error al procesar tu consulta: {str(e)}. Por favor intenta nuevamente.",
                "agent_responses": {},
                "context_documents": [],
                "error": str(e)
            }
    
    def _format_response(self, query: str, result: Dict[str, Any]) -> Dict[str, Any]:
        """Format the query processing result into a structured response.
        
        Args:
            query: Original user query
            result: Raw result from agent processing
            
        Returns:
            Formatted response dictionary
        """
        # Basic response structure
        response = {
            "query": query,
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
        response["context_documents"] = self._format_context_documents(context)
        
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
        
        return response
    
    def _format_context_documents(self, documents: List[Any]) -> List[Dict[str, Any]]:
        """Format context documents for the response.
        
        Args:
            documents: List of document objects
            
        Returns:
            List of formatted document dictionaries
        """
        formatted_documents = []
        
        for doc in documents:
            if not isinstance(doc, dict) and hasattr(doc, '__dict__'):
                # Extract attributes if object
                doc_dict = {
                    "id": getattr(doc, "id", ""),
                    "title": getattr(doc, "title", "Unknown Document"),
                    "snippet": getattr(doc, "content", "")[:200] + "..." if len(getattr(doc, "content", "")) > 200 else getattr(doc, "content", ""),
                    "document_type": getattr(doc, "document_type", "unknown"),
                    "source": getattr(doc, "source", "")
                }
                formatted_documents.append(doc_dict)
            else:
                # Already a dict or other structure
                formatted_documents.append(doc)
                
        return formatted_documents
    
    async def stream_query(self, query_input: QueryInput) -> List[Dict[str, Any]]:
        """Process a query and prepare it for streaming.
        
        Args:
            query_input: User query input
            
        Returns:
            List of streaming response chunks
        """
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
            
            # Process query
            result = self.agent_nodes.process_user_query(
                query=query_input.query,
                conversation_history=context_dict,
                streaming=True
            )
            
            # Prepare streaming chunks
            chunks = []
            
            # Initial response
            chunks.append({"type": "start", "content": ""})
            
            # Stream partial responses
            partial_responses = result.get("partial_responses", {})
            if partial_responses:
                for role, response in partial_responses.items():
                    if hasattr(response, "content"):
                        content = response.content
                    elif isinstance(response, dict) and "content" in response:
                        content = response["content"]
                    else:
                        content = str(response)
                        
                    chunks.append({
                        "type": "partial", 
                        "role": role,
                        "content": content
                    })
            
            # Final response
            final_response = result.get("final_response", "")
            chunks.append({
                "type": "final",
                "content": final_response
            })
            
            return chunks
            
        except Exception as e:
            logger.error(f"Error streaming query: {str(e)}")
            logger.exception(e)
            
            # Return error chunk
            return [{
                "type": "error",
                "content": f"Error processing query: {str(e)}"
            }] 