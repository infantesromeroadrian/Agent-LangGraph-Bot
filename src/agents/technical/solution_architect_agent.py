"""Solution Architect agent for the LangGraph workflow."""
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


class SolutionArchitectAgent:
    """Solution Architect agent to evaluate technical requirements and design solutions."""
    
    def __init__(self, llm_service: LLMService, vector_store: VectorStoreService, graph_manager: GraphManagerUtil):
        """Initialize the Solution Architect agent with services.
        
        Args:
            llm_service: LLM service for generating agent responses
            vector_store: Vector store service for context retrieval
            graph_manager: Graph manager for workflow utilities
        """
        self.llm_service = llm_service
        self.vector_store = vector_store
        self.graph_manager = graph_manager
        
    def process(self, state: GraphState) -> GraphState:
        """Process the current state with the Solution Architect agent.
        
        Args:
            state: Current graph state
            
        Returns:
            Updated graph state with solution architect response
        """
        # Set current agent
        state.current_agent = AgentRole.SOLUTION_ARCHITECT
        
        # Skip if node is disabled
        if self.graph_manager.should_skip_node(state, AgentRole.SOLUTION_ARCHITECT.value):
            return state
        
        # Create prompt for solution architect with detected language
        prompt = create_agent_prompt(
            AgentRole.SOLUTION_ARCHITECT,
            state.human_query or "",
            state.messages,
            state.context,
            state.detected_language
        )
        
        # Add relevant thoughts from shared memory if available
        relevant_thoughts = state.shared_memory.get("technical_thoughts", [])
        if relevant_thoughts:
            prompt += "\n\nRelevant technical insights from previous analyses:\n"
            for thought in relevant_thoughts:
                prompt += f"- {thought}\n"
        
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
                    AgentRole.SOLUTION_ARCHITECT,
                    is_partial=True
                )
                state.partial_responses[AgentRole.SOLUTION_ARCHITECT.value] = agent_response
            
            response = final_response
        else:
            # Non-streaming response
            response = chain.invoke({"input": prompt})
        
        # Create agent response
        agent_response = create_agent_response(
            response,
            AgentRole.SOLUTION_ARCHITECT
        )
        
        # Update state with agent response
        state.agent_responses[AgentRole.SOLUTION_ARCHITECT.value] = agent_response
        
        # Add message to conversation history
        ai_msg = create_message(
            response,
            MessageType.AI,
            f"agent.{AgentRole.SOLUTION_ARCHITECT.value}"
        )
        state.messages.append(ai_msg)
        
        # Extract and save architecture thoughts to shared memory
        if "shared_memory" not in state.__dict__:
            state.shared_memory = {}
        
        architectural_insights = self._extract_architectural_insights(response)
        state.shared_memory["architecture_insights"] = architectural_insights
        
        return state
    
    def _extract_architectural_insights(self, response: str) -> List[str]:
        """Extract key architectural insights from the response.
        
        Args:
            response: Agent response text
            
        Returns:
            List of architectural insights
        """
        # Simple extraction based on paragraphs (can be enhanced with more sophisticated extraction)
        insights = []
        paragraphs = response.split("\n\n")
        
        for paragraph in paragraphs:
            # Filter paragraphs that contain architectural keywords
            architectural_keywords = [
                "architecture", "design", "structure", "component", "system", 
                "module", "integration", "interface", "API", "service"
            ]
            
            if any(keyword in paragraph.lower() for keyword in architectural_keywords):
                if len(paragraph) > 30:  # Avoid very short snippets
                    insights.append(paragraph.strip())
        
        # Ensure we don't have too many insights (keep top 3)
        return insights[:3] 
