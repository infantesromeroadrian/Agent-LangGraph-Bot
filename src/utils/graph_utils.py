"""Utilities for managing dynamic agent graphs."""
from typing import Dict, List, Callable, Any, Optional
import logging
from langchain_core.language_models import BaseChatModel
from langchain_openai import OpenAIEmbeddings
import numpy as np

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
        """Check if a node should be skipped based on graph state.
        
        Args:
            state: Current graph state
            node_name: Name of the node to check
            
        Returns:
            True if the node should be skipped, False otherwise
        """
        if not state.disabled_nodes:
            return False
            
        return node_name in state.disabled_nodes
    
    def add_thought_to_shared_memory(self, state: GraphState, agent_role: AgentRole, 
                                    thought: str, key: Optional[str] = None) -> GraphState:
        """Add a thought vector to the shared memory.
        
        Args:
            state: Current graph state
            agent_role: Role of the agent adding the thought
            thought: Textual thought
            key: Optional key for the thought (defaults to agent_role)
            
        Returns:
            Updated graph state
        """
        # Create vector from thought
        vector = self.create_thought_vector(thought)
        
        # Use agent role as key if not specified
        memory_key = key or str(agent_role)
        
        # Store in thought vectors
        state.thought_vectors[memory_key] = vector
        
        # Also store the raw thought in shared memory for reference
        if "thoughts" not in state.shared_memory:
            state.shared_memory["thoughts"] = {}
            
        state.shared_memory["thoughts"][memory_key] = thought
        
        return state
    
    def find_similar_thoughts(self, state: GraphState, query_thought: str, 
                             threshold: float = 0.7, max_results: int = 3) -> List[Dict[str, Any]]:
        """Find similar thoughts in the shared memory.
        
        Args:
            state: Current graph state
            query_thought: Thought to compare against
            threshold: Similarity threshold (0-1)
            max_results: Maximum number of results to return
            
        Returns:
            List of similar thoughts with metadata
        """
        if not state.thought_vectors:
            return []
            
        # Create vector from query thought
        query_vector = self.create_thought_vector(query_thought)
        
        # Calculate similarity with all stored vectors
        similarities = []
        for key, vector in state.thought_vectors.items():
            similarity = self.calculate_thought_similarity(query_vector, vector)
            
            if similarity >= threshold:
                # Get the original thought text if available
                thought_text = state.shared_memory.get("thoughts", {}).get(key, "Unknown thought")
                
                similarities.append({
                    "key": key,
                    "similarity": similarity,
                    "thought": thought_text
                })
        
        # Sort by similarity (descending) and limit results
        similarities.sort(key=lambda x: x["similarity"], reverse=True)
        return similarities[:max_results] 