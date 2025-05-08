"""Technical Research agent for the LangGraph workflow."""
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


class TechnicalResearchAgent:
    """Technical Research agent to investigate technologies and solutions."""
    
    def __init__(self, llm_service: LLMService, vector_store: VectorStoreService, graph_manager: GraphManagerUtil):
        """Initialize the Technical Research agent with services.
        
        Args:
            llm_service: LLM service for generating agent responses
            vector_store: Vector store service for context retrieval
            graph_manager: Graph manager for workflow utilities
        """
        self.llm_service = llm_service
        self.vector_store = vector_store
        self.graph_manager = graph_manager
        
    def process(self, state: GraphState) -> GraphState:
        """Process the current state with the Technical Research agent.
        
        Args:
            state: Current graph state
            
        Returns:
            Updated graph state with technical research response
        """
        # Set current agent
        state.current_agent = AgentRole.TECHNICAL_RESEARCH
        
        # Skip if node is disabled
        if self.graph_manager.should_skip_node(state, AgentRole.TECHNICAL_RESEARCH.value):
            return state
            
        # Get any architectural insights from previous agents
        architectural_insights = state.shared_memory.get("architecture_insights", [])
        
        # Create prompt for technical research
        prompt = create_agent_prompt(
            AgentRole.TECHNICAL_RESEARCH,
            state.human_query or "",
            state.messages,
            state.context,
            state.detected_language
        )
        
        # Add architectural insights to the prompt if available
        if architectural_insights:
            prompt += "\n\nArchitectural insights from previous analysis:\n"
            for insight in architectural_insights:
                prompt += f"- {insight}\n"
                
        # Check if we need external knowledge
        supplemental_docs = self._process_external_knowledge(state.human_query or "")
        if supplemental_docs:
            prompt += "\n\nSupplemental external knowledge:\n"
            for doc in supplemental_docs:
                prompt += f"--- {doc.title} ---\n{doc.content[:500]}...\n\n"
                
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
                    AgentRole.TECHNICAL_RESEARCH,
                    is_partial=True
                )
                state.partial_responses[AgentRole.TECHNICAL_RESEARCH.value] = agent_response
            
            response = final_response
        else:
            # Non-streaming response
            response = chain.invoke({"input": prompt})
        
        # Create agent response
        agent_response = create_agent_response(
            response,
            AgentRole.TECHNICAL_RESEARCH
        )
        
        # Update state with agent response
        state.agent_responses[AgentRole.TECHNICAL_RESEARCH.value] = agent_response
        
        # Add message to conversation history
        ai_msg = create_message(
            response,
            MessageType.AI,
            f"agent.{AgentRole.TECHNICAL_RESEARCH.value}"
        )
        state.messages.append(ai_msg)
        
        # Extract and save technical insights to shared memory
        if "shared_memory" not in state.__dict__:
            state.shared_memory = {}
            
        technical_insights = self._extract_technical_insights(response)
        state.shared_memory["technical_thoughts"] = technical_insights
        
        # Extract entities for future reference
        entities = self._extract_entities(state.human_query or "")
        state.shared_memory["entities"] = entities
        
        # Extract intents for routing decisions
        intents = self._extract_intents(state.human_query or "")
        state.shared_memory["intents"] = intents
        
        return state
    
    def _process_external_knowledge(self, query: str) -> List[CompanyDocument]:
        """Process external knowledge relevant to the query.
        
        Args:
            query: User query
            
        Returns:
            List of supplemental documents
        """
        # This is a placeholder. In a real implementation, this might:
        # 1. Call an external API
        # 2. Do a web search
        # 3. Query a specialized database
        
        # For now, we'll return an empty list
        return []
    
    def _extract_entities(self, query: str) -> Dict[str, str]:
        """Extract key entities from a query.
        
        Args:
            query: User query
            
        Returns:
            Dictionary of entity types and values
        """
        # This method would normally use NLP techniques to extract entities
        # For now, we'll just do a simple keyword extraction
        
        entities = {}
        
        # Look for technology keywords
        tech_keywords = ["cloud", "AI", "ML", "database", "frontend", "backend", "DevOps"]
        for keyword in tech_keywords:
            if keyword.lower() in query.lower():
                if "technologies" not in entities:
                    entities["technologies"] = []
                entities["technologies"].append(keyword)
                
        # Look for company or product names (simplified approach)
        company_keywords = ["Microsoft", "Google", "AWS", "Azure", "GCP"]
        for keyword in company_keywords:
            if keyword in query:
                if "companies" not in entities:
                    entities["companies"] = []
                entities["companies"].append(keyword)
                
        return entities
    
    def _extract_intents(self, query: str) -> List[str]:
        """Extract intents from the query to help with routing decisions.
        
        Args:
            query: User query
            
        Returns:
            List of detected intents
        """
        # Simple keyword-based intent detection
        intents = []
        
        # Technical implementation details
        if any(keyword in query.lower() for keyword in ["how to implement", "code", "develop", "programming", "implementation"]):
            intents.append("technical_implementation")
            
        # Architecture concerns
        if any(keyword in query.lower() for keyword in ["architecture", "design", "structure", "system design"]):
            intents.append("architecture")
            
        # Project management concerns
        if any(keyword in query.lower() for keyword in ["timeline", "project plan", "schedule", "team", "resource", "budget"]):
            intents.append("project_management")
            
        # Code review concerns
        if any(keyword in query.lower() for keyword in ["review", "code quality", "best practices", "refactor"]):
            intents.append("code_review")
            
        # Market analysis concerns
        if any(keyword in query.lower() for keyword in ["market", "competitor", "industry", "trend", "analysis"]):
            intents.append("market_analysis")
            
        # Data analysis concerns
        if any(keyword in query.lower() for keyword in ["data", "analytics", "statistics", "metrics", "KPI"]):
            intents.append("data_analysis")
            
        return intents
    
    def _extract_technical_insights(self, response: str) -> List[str]:
        """Extract key technical insights from the response.
        
        Args:
            response: Agent response text
            
        Returns:
            List of technical insights
        """
        # Simple extraction based on paragraphs
        insights = []
        paragraphs = response.split("\n\n")
        
        for paragraph in paragraphs:
            # Filter paragraphs that contain technical keywords
            technical_keywords = [
                "technology", "solution", "implementation", "tool", "framework", 
                "library", "platform", "language", "protocol", "algorithm"
            ]
            
            if any(keyword in paragraph.lower() for keyword in technical_keywords):
                if len(paragraph) > 30:  # Avoid very short snippets
                    insights.append(paragraph.strip())
        
        # Ensure we don't have too many insights (keep top 3)
        return insights[:3] 
