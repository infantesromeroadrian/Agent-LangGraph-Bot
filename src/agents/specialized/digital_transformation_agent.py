"""Digital Transformation agent for the LangGraph workflow."""
from typing import Dict, List, Any, Optional

from src.models.class_models import GraphState, AgentRole, MessageType, CompanyDocument
from src.services.llm_service import LLMService
from src.services.vector_store_service import VectorStoreService
from src.utils.graph_utils import GraphManagerUtil
from src.agents.base.agent_utils import (
    create_agent_prompt,
    create_message,
    create_agent_response
)


class DigitalTransformationAgent:
    """Digital Transformation agent for evaluating digital maturity and proposing strategies."""
    
    def __init__(self, llm_service: LLMService, vector_store: VectorStoreService, graph_manager: GraphManagerUtil):
        """Initialize the Digital Transformation agent with services.
        
        Args:
            llm_service: LLM service for generating agent responses
            vector_store: Vector store service for context retrieval
            graph_manager: Graph manager for workflow utilities
        """
        self.llm_service = llm_service
        self.vector_store = vector_store
        self.graph_manager = graph_manager
        
    def process(self, state: GraphState) -> GraphState:
        """Process the current state with the Digital Transformation agent.
        
        Args:
            state: Current graph state
            
        Returns:
            Updated graph state with digital transformation assessment
        """
        # Set current agent
        state.current_agent = AgentRole.DIGITAL_TRANSFORMATION
        
        # Skip if node is disabled
        if self.graph_manager.should_skip_node(state, AgentRole.DIGITAL_TRANSFORMATION.value):
            return state
        
        # Create prompt for digital transformation
        prompt = create_agent_prompt(
            AgentRole.DIGITAL_TRANSFORMATION,
            state.human_query or "",
            state.messages,
            state.context,
            state.detected_language
        )
        
        # Add relevant thoughts from shared memory if available
        if hasattr(state, 'thought_vectors') and state.thought_vectors and state.human_query:
            relevant_thoughts = self.graph_manager.find_similar_thoughts(
                state,
                state.human_query,
                threshold=0.6
            )
            
            if relevant_thoughts:
                prompt += "\n\nRelevant insights from previous analyses:\n"
                for thought in relevant_thoughts:
                    prompt += f"- {thought['thought']}\n"
        
        # Get response from LLM
        chain = self.llm_service.create_chain(
            "{input}",
            streaming=state.is_streaming
        )
        
        if state.is_streaming:
            # For streaming, we need to handle differently
            response_chunks = []
            final_response = ""
            
            for chunk in chain.stream({"input": prompt}):
                response_chunks.append(chunk)
                final_response += chunk
                
                # Update partial response in state
                agent_response = create_agent_response(
                    final_response,
                    AgentRole.DIGITAL_TRANSFORMATION,
                    is_partial=True
                )
                state.partial_responses[AgentRole.DIGITAL_TRANSFORMATION.value] = agent_response
            
            response = final_response
        else:
            # Non-streaming response
            response = chain.invoke({"input": prompt})
        
        # Create agent response
        agent_response = create_agent_response(
            response,
            AgentRole.DIGITAL_TRANSFORMATION,
            sources=[doc.id for doc in state.context]
        )
        
        # Update state with agent response
        state.agent_responses[AgentRole.DIGITAL_TRANSFORMATION.value] = agent_response
        
        # Add message to conversation history
        ai_msg = create_message(
            response,
            MessageType.AI,
            f"agent.{AgentRole.DIGITAL_TRANSFORMATION.value}"
        )
        state.messages.append(ai_msg)
        
        # Extract and save digital transformation thoughts to shared memory
        self.graph_manager.add_thought_to_shared_memory(
            state,
            AgentRole.DIGITAL_TRANSFORMATION,
            response
        )
        
        return state 