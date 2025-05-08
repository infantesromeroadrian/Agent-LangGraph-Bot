"""Utilities for managing dynamic agent graphs."""
from typing import Dict, List, Callable, Any, Optional
import logging
from langchain_core.language_models import BaseChatModel
from langchain_openai import OpenAIEmbeddings
import numpy as np
import os
import json

from src.models.class_models import GraphState, AgentRole

# Configure logging
logger = logging.getLogger(__name__)

class GraphManagerUtil:
    """Utility for managing dynamic graph structure during execution."""
    
    def __init__(self, embeddings_model=None):
        """Initialize the graph manager utility.
        
        Args:
            embeddings_model: Optional embedding model for thought vectors
        """
        # Initialize embeddings model for thought vectors if not provided
        self.embeddings = embeddings_model or OpenAIEmbeddings()
        self.thought_embeddings = {}
        self.current_query = ""
    
    def initialize(self, query: str):
        """Initialize the graph manager for a new query.
        
        Args:
            query: User query
        """
        self.current_query = query
        self.thought_embeddings = {}
        logger.info(f"GraphManager initialized with query: {query}")
        
    def modify_state_for_dynamic_execution(self, state: GraphState) -> GraphState:
        """Process state to handle dynamic graph execution.
        
        Args:
            state: Current graph state
            
        Returns:
            Modified state for dynamic execution
        """
        # Skip disabled nodes if present in state
        if state.disabled_nodes and state.current_agent:
            agent_name = state.current_agent.value if isinstance(state.current_agent, AgentRole) else str(state.current_agent)
            
            if agent_name in state.disabled_nodes:
                logger.info(f"Skipping disabled node: {agent_name}")
                # Mark the node as processed but skipped
                system_message = f"Agent {agent_name} is currently disabled and will be skipped."
                from src.agents.agent_utils import create_message
                from src.models.class_models import MessageType
                
                msg = create_message(
                    content=system_message,
                    message_type=MessageType.SYSTEM,
                    sender="system"
                )
                state.messages.append(msg)
        
        return state
    
    def create_thought_vector(self, thought: str) -> List[float]:
        """Create a thought vector from a text thought.
        
        Args:
            thought: Textual thought
            
        Returns:
            Vector representation of the thought
        """
        try:
            # Generate embedding for the thought
            vector = self.embeddings.embed_query(thought)
            return vector
        except Exception as e:
            logger.error(f"Error creating thought vector: {e}")
            # Return a zero vector as fallback
            return [0.0] * 1536  # Default OpenAI embedding size
    
    def calculate_thought_similarity(self, vector1: List[float], vector2: List[float]) -> float:
        """Calculate cosine similarity between two thought vectors.
        
        Args:
            vector1: First thought vector
            vector2: Second thought vector
            
        Returns:
            Similarity score (0-1)
        """
        # Convert to numpy arrays
        v1 = np.array(vector1)
        v2 = np.array(vector2)
        
        # Calculate cosine similarity
        dot_product = np.dot(v1, v2)
        norm_v1 = np.linalg.norm(v1)
        norm_v2 = np.linalg.norm(v2)
        
        # Avoid division by zero
        if norm_v1 == 0 or norm_v2 == 0:
            return 0.0
            
        similarity = dot_product / (norm_v1 * norm_v2)
        return float(similarity)
    
    def should_skip_node(self, state: GraphState, node_name: str) -> bool:
        """Check if a node should be skipped.
        
        Args:
            state: Current graph state
            node_name: Name of the node to check
            
        Returns:
            True if the node should be skipped, False otherwise
        """
        # Skip if the node is in the disabled_nodes list
        if node_name in state.disabled_nodes:
            return True
            
        # Skip if active_nodes is specified and this node is not in it
        if state.active_nodes and node_name not in state.active_nodes:
            return True
            
        return False
    
    def add_thought_to_shared_memory(self, state: GraphState, agent_role: AgentRole, thought: str):
        """Add a thought vector to shared memory.
        
        Args:
            state: Current graph state
            agent_role: Role of the agent generating the thought
            thought: Thought content
        """
        if not hasattr(state, 'thought_vectors') or state.thought_vectors is None:
            state.thought_vectors = {}
            
        # For now, just store the raw thought (no actual vector)
        role_str = agent_role.value if isinstance(agent_role, AgentRole) else str(agent_role)
        
        if role_str not in state.thought_vectors:
            state.thought_vectors[role_str] = []
            
        # Store the thought
        state.thought_vectors[role_str].append(thought)
        
        # Cache for local use
        self.thought_embeddings[role_str] = thought
        
    def find_similar_thoughts(self, state: GraphState, query: str, threshold: float = 0.7, max_results: int = 3) -> List[Dict[str, Any]]:
        """Find thoughts similar to the query.
        
        Args:
            state: Current graph state
            query: Query to find similar thoughts
            threshold: Similarity threshold
            max_results: Maximum number of results to return
            
        Returns:
            List of similar thoughts with similarity scores
        """
        results = []
        
        # Without actual embeddings, just do basic keyword matching
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        for role, thoughts in state.thought_vectors.items():
            for thought in thoughts:
                thought_lower = thought.lower()
                
                # Very simple similarity - count common words
                thought_words = set(thought_lower.split())
                common_words = query_words.intersection(thought_words)
                
                if common_words:
                    # Calculate a simple similarity score
                    similarity = len(common_words) / (len(query_words) + len(thought_words)) * 2
                    
                    if similarity >= threshold:
                        results.append({
                            "role": role,
                            "thought": thought,
                            "similarity": similarity
                        })
        
        # Sort by similarity and limit results
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:max_results] 