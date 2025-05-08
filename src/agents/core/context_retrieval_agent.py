"""Context retrieval agent for the LangGraph workflow."""
from typing import List, Dict, Any, Optional

from src.models.class_models import GraphState, MessageType
from src.services.vector_store_service import VectorStoreService
from src.utils.graph_utils import GraphManagerUtil
from src.agents.base.agent_utils import create_message


class ContextRetrievalAgent:
    """Agent responsible for retrieving relevant context for user queries."""
    
    def __init__(self, vector_store: VectorStoreService, graph_manager: GraphManagerUtil):
        """Initialize the Context Retrieval agent with services.
        
        Args:
            vector_store: Vector store service for retrieving documents
            graph_manager: Graph manager for workflow utilities
        """
        self.vector_store = vector_store
        self.graph_manager = graph_manager
    
    def process(self, state: GraphState) -> GraphState:
        """Retrieve relevant context for the query.
        
        Args:
            state: Current graph state
            
        Returns:
            Updated graph state with context
        """
        if not state.human_query:
            return state
        
        # Check if this is a simple greeting or conversational query
        simple_query = self._is_simple_conversational_query(state.human_query)
        
        if simple_query:
            # For simple queries like greetings, don't retrieve documents
            # Just add a system message
            system_msg = create_message(
                f"Handling conversational query without document retrieval.",
                MessageType.SYSTEM,
                "system"
            )
            state.messages.append(system_msg)
            return state
            
        # Retrieve relevant documents
        documents = self.vector_store.search(state.human_query)
        
        # Update state with retrieved documents
        state.context = documents
        
        # Add a system message indicating context retrieval
        if documents:
            system_msg = create_message(
                f"Retrieved {len(documents)} relevant documents.",
                MessageType.SYSTEM,
                "system"
            )
            state.messages.append(system_msg)
            
        return state
        
    def _is_simple_conversational_query(self, query: str) -> bool:
        """Detect if a query is a simple greeting or conversational message.
        
        Args:
            query: User query
            
        Returns:
            Boolean indicating if this is a simple conversational query
        """
        # Convert to lowercase for case-insensitive matching
        query_lower = query.lower().strip()
        
        # Common greetings and simple queries in multiple languages
        greetings = [
            "hello", "hi", "hey", "howdy", "greetings", "good morning", "good afternoon", 
            "good evening", "hola", "buenos días", "buenas tardes", "buenas noches",
            "how are you", "how's it going", "what's up", "cómo estás", "qué tal",
            "thank you", "thanks", "gracias", "goodbye", "bye", "adiós", "chao"
        ]
        
        # Check for exact match or if query starts with any greeting
        for greeting in greetings:
            if query_lower == greeting or query_lower.startswith(greeting + " "):
                return True
        
        # More selective check for very short queries
        # Only treat single-word or very simple phrases as conversational
        words = query_lower.split()
        if len(words) <= 2:
            # But check if it contains any question-related keywords that indicate a real query
            question_indicators = ["what", "how", "why", "when", "where", "who", "which", 
                                   "qué", "cómo", "por qué", "cuándo", "dónde", "quién", "cuál"]
            
            # If it contains any question indicator, it might be a real query despite being short
            if not any(indicator in query_lower for indicator in question_indicators):
                return True
                
        return False 