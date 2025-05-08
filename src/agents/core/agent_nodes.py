"""Agent nodes for the LangGraph workflow."""
from typing import Dict, List, Tuple, Any, Optional
from langchain_core.messages import HumanMessage

from src.models.class_models import GraphState, AgentRole, MessageType, CompanyDocument
from src.services.llm_service import LLMService
from src.services.vector_store_service import VectorStoreService
from src.utils.graph_utils import GraphManagerUtil
from src.agents.core.agent_factory import AgentFactory
from src.utils.intent_detection_service import IntentDetectionService
from src.agents.base.agent_utils import (
    create_message,
    create_agent_response
)


class AgentNodes:
    """Nodes for the agent workflow graph."""
    
    def __init__(self):
        """Initialize agent nodes with services."""
        self.llm_service = LLMService()
        self.vector_store = VectorStoreService()
        self.graph_manager = GraphManagerUtil()
        self.agent_factory = AgentFactory()
        self.intent_detector = IntentDetectionService()
        
    def language_detection_agent(self, state: GraphState) -> GraphState:
        """Node for language detection agent.
        
        Args:
            state: Current graph state
            
        Returns:
            Updated graph state with detected language
        """
        agent = self.agent_factory.get_agent('language_detection')
        return agent.process(state)
    
    def retrieve_context(self, state: GraphState) -> GraphState:
        """Node for context retrieval agent.
        
        Args:
            state: Current graph state
            
        Returns:
            Updated graph state with context
        """
        agent = self.agent_factory.get_agent('context_retrieval')
        return agent.process(state)
        
    def solution_architect_agent(self, state: GraphState) -> GraphState:
        """Node for solution architect agent.
        
        Args:
            state: Current graph state
            
        Returns:
            Updated graph state with solution architect response
        """
        agent = self.agent_factory.get_agent('solution_architect')
        return agent.process(state)
        
    def technical_research_agent(self, state: GraphState) -> GraphState:
        """Node for technical research agent.
        
        Args:
            state: Current graph state
            
        Returns:
            Updated graph state with technical research response
        """
        agent = self.agent_factory.get_agent('technical_research')
        return agent.process(state)
        
    def project_management_agent(self, state: GraphState) -> GraphState:
        """Node for project management agent.
        
        Args:
            state: Current graph state
            
        Returns:
            Updated graph state with project management response
        """
        agent = self.agent_factory.get_agent('project_management')
        return agent.process(state)
        
    def code_review_agent(self, state: GraphState) -> GraphState:
        """Node for code review agent.
        
        Args:
            state: Current graph state
            
        Returns:
            Updated graph state with code review response
        """
        agent = self.agent_factory.get_agent('code_review')
        return agent.process(state)
        
    def market_analysis_agent(self, state: GraphState) -> GraphState:
        """Node for market analysis agent.
        
        Args:
            state: Current graph state
            
        Returns:
            Updated graph state with market analysis response
        """
        agent = self.agent_factory.get_agent('market_analysis')
        return agent.process(state)
        
    def data_analysis_agent(self, state: GraphState) -> GraphState:
        """Node for data analysis agent.
        
        Args:
            state: Current graph state
            
        Returns:
            Updated graph state with data analysis response
        """
        agent = self.agent_factory.get_agent('data_analysis')
        return agent.process(state)
        
    def client_communication_agent(self, state: GraphState) -> GraphState:
        """Node for client communication agent.
        
        Args:
            state: Current graph state
            
        Returns:
            Updated graph state with client communication response
        """
        agent = self.agent_factory.get_agent('client_communication')
        return agent.process(state)
    
    def digital_transformation_agent(self, state: GraphState) -> GraphState:
        """Node for digital transformation agent.
        
        Args:
            state: Current graph state
            
        Returns:
            Updated graph state with digital transformation response
        """
        agent = self.agent_factory.get_agent('digital_transformation')
        return agent.process(state)
    
    def cloud_architecture_agent(self, state: GraphState) -> GraphState:
        """Node for cloud architecture agent.
        
        Args:
            state: Current graph state
            
        Returns:
            Updated graph state with cloud architecture response
        """
        agent = self.agent_factory.get_agent('cloud_architecture')
        return agent.process(state)
    
    def cyber_security_agent(self, state: GraphState) -> GraphState:
        """Node for cyber security agent.
        
        Args:
            state: Current graph state
            
        Returns:
            Updated graph state with cyber security response
        """
        agent = self.agent_factory.get_agent('cyber_security')
        return agent.process(state)
    
    def agile_methodologies_agent(self, state: GraphState) -> GraphState:
        """Node for agile methodologies agent.
        
        Args:
            state: Current graph state
            
        Returns:
            Updated graph state with agile methodologies response
        """
        agent = self.agent_factory.get_agent('agile_methodologies')
        return agent.process(state)
    
    def systems_integration_agent(self, state: GraphState) -> GraphState:
        """Node for systems integration agent.
        
        Args:
            state: Current graph state
            
        Returns:
            Updated graph state with systems integration response
        """
        agent = self.agent_factory.get_agent('systems_integration')
        return agent.process(state)
        
    def process_user_query(self, query: str, conversation_history: Optional[List[Dict]] = None, streaming: bool = False) -> Dict[str, Any]:
        """Process a user query through the agent workflow.
        
        Args:
            query: User query
            conversation_history: Previous conversation messages
            streaming: Whether to stream responses
            
        Returns:
            Dictionary with agent responses and final response
        """
        # Create initial state
        state = GraphState(
            human_query=query,
            is_streaming=streaming
        )
        
        # Convert conversation history to messages if provided
        if conversation_history:
            for msg in conversation_history:
                if msg.get("type") == "human":
                    state.messages.append(create_message(
                        msg.get("content", ""),
                        MessageType.HUMAN,
                        msg.get("sender", "user")
                    ))
                elif msg.get("type") == "ai":
                    state.messages.append(create_message(
                        msg.get("content", ""),
                        MessageType.AI,
                        msg.get("sender", "assistant")
                    ))
        
        # Add the current query as a message
        state.messages.append(create_message(
            query,
            MessageType.HUMAN,
            "user"
        ))
        
        # Set up the graph manager for this query
        self.graph_manager.initialize(query)
        
        # Process the query through the workflow
        try:
            # Get the graph - used to be a simple function call:
            # from src.graph.agent_graph import create_agent_graph
            # graph = create_agent_graph(self)
            
            # Now with dynamic agent graph
            from src.graph.agent_graph import DynamicAgentGraph
            dynamic_graph = DynamicAgentGraph(self)
            graph = dynamic_graph.get_compiled_graph()
            
            # Execute the graph
            result = graph.invoke(state)
            
            # Handle different result types from LangGraph
            # LangGraph 0.0.x returned a GraphState object directly
            # LangGraph 0.1.x returns an AddableValuesDict which needs special handling
            
            # Create response object
            response = {
                "agent_responses": {},
                "final_response": ""
            }
            
            # Determine the type of result and extract data accordingly
            if hasattr(result, 'get') and callable(getattr(result, 'get')):
                # It's an AddableValuesDict or similar dict-like object
                final_response = result.get('final_response', "")
                agent_responses = result.get('agent_responses', {})
                detected_language = result.get('detected_language', "en")
            elif isinstance(result, dict):
                # It's a regular dictionary
                final_response = result.get('final_response', "")
                agent_responses = result.get('agent_responses', {})
                detected_language = result.get('detected_language', "en")
            else:
                # Assume it's a GraphState object (older LangGraph versions)
                final_response = getattr(result, 'final_response', "")
                agent_responses = getattr(result, 'agent_responses', {})
                detected_language = getattr(result, 'detected_language', "en")
            
            # Set final response
            response["final_response"] = final_response
            
            # Add individual agent responses
            for role, agent_response in agent_responses.items():
                if hasattr(agent_response, 'content'):
                    # It's an AgentResponse object
                    response["agent_responses"][role] = {
                        "content": agent_response.content,
                        "confidence": getattr(agent_response, 'confidence', 1.0),
                        "sources": getattr(agent_response, 'sources', [])
                    }
                elif isinstance(agent_response, dict):
                    # It's already a dictionary
                    response["agent_responses"][role] = agent_response
            
            # Add detected language info
            response["detected_language"] = detected_language
            
            # If we don't have a final response yet, use a default message based on the detected language
            if not response["final_response"]:
                if detected_language == "es":
                    response["final_response"] = "Lo siento, no pude generar una respuesta completa. ¿Podrías reformular tu pregunta?"
                else:
                    response["final_response"] = "I'm sorry, I couldn't generate a complete response. Could you please rephrase your question?"
                    
            return response
            
        except Exception as e:
            import traceback
            print(f"Error in agent workflow: {e}")
            print(traceback.format_exc())
            return {
                "agent_responses": {},
                "final_response": f"Lo siento, ocurrió un error al procesar tu consulta. Por favor, inténtalo de nuevo. Error: {str(e)}",
                "detected_language": getattr(state, 'detected_language', "es")
            }
        
    # Routing decision methods
    def should_use_code_review(self, state: GraphState) -> str:
        """Determine if the Code Review agent should be used.
        
        Args:
            state: Current graph state
            
        Returns:
            Decision string ('use_code_review' or 'skip_code_review')
        """
        # Extract intents from the query
        intents = self.intent_detector.extract_intents(state.human_query or "")
        
        # Check for technical keywords
        query_lower = (state.human_query or "").lower()
        technical_keywords = ["develop", "programm", "cod", "software", "app", "application", 
                             "framework", "library", "function", "algorithm", "api", "database",
                             "backend", "frontend", "full-stack", "system"]
        
        # Activate code review agent if:
        # 1. There's a code_review intent
        # 2. Or it's a technology-related query
        # 3. Or it contains technical keywords
        # 4. Or it's a complex technical query
        if ("code_review" in intents or
            "technology" in intents or
            any(keyword in query_lower for keyword in technical_keywords) or
            len(query_lower) > 200):  # For long complex queries that may contain technical aspects
            
            print("Activating code review agent for query:", state.human_query)
            return "use_code_review"
        else:
            return "skip_code_review"
    
    def should_use_project_management(self, state: GraphState) -> str:
        """Determine if the Project Management agent should be used.
        
        Args:
            state: Current graph state
            
        Returns:
            Decision string ('use_project_management' or 'skip_project_management')
        """
        intents = self.intent_detector.extract_intents(state.human_query or "")
        
        if "project_management" in intents:
            return "use_project_management"
        else:
            return "skip_project_management"
    
    def should_use_market_analysis(self, state: GraphState) -> str:
        """Determine if the Market Analysis agent should be used.
        
        Args:
            state: Current graph state
            
        Returns:
            Decision string ('use_market_analysis' or 'skip_market_analysis')
        """
        intents = self.intent_detector.extract_intents(state.human_query or "")
        
        if "market_analysis" in intents:
            return "use_market_analysis"
        else:
            return "skip_market_analysis"
    
    def should_use_data_analysis(self, state: GraphState) -> str:
        """Determine if the Data Analysis agent should be used.
        
        Args:
            state: Current graph state
            
        Returns:
            Decision string ('use_data_analysis' or 'skip_data_analysis')
        """
        intents = self.intent_detector.extract_intents(state.human_query or "")
        
        if "data_analysis" in intents:
            return "use_data_analysis"
        else:
            return "skip_data_analysis"
            
    def should_use_digital_transformation(self, state: GraphState) -> str:
        """Determine if the Digital Transformation agent should be used.
        
        Args:
            state: Current graph state
            
        Returns:
            Decision string ('use_digital_transformation' or 'skip_digital_transformation')
        """
        intents = self.intent_detector.extract_intents(state.human_query or "")
        
        if "digital_transformation" in intents:
            return "use_digital_transformation"
        else:
            return "skip_digital_transformation"
    
    def should_use_cloud_architecture(self, state: GraphState) -> str:
        """Determine if the Cloud Architecture agent should be used.
        
        Args:
            state: Current graph state
            
        Returns:
            Decision string ('use_cloud_architecture' or 'skip_cloud_architecture')
        """
        intents = self.intent_detector.extract_intents(state.human_query or "")
        
        if "cloud_architecture" in intents:
            return "use_cloud_architecture"
        else:
            return "skip_cloud_architecture"
    
    def should_use_cyber_security(self, state: GraphState) -> str:
        """Determine if the Cyber Security agent should be used.
        
        Args:
            state: Current graph state
            
        Returns:
            Decision string ('use_cyber_security' or 'skip_cyber_security')
        """
        intents = self.intent_detector.extract_intents(state.human_query or "")
        
        if "cyber_security" in intents:
            return "use_cyber_security"
        else:
            return "skip_cyber_security"
    
    def should_use_agile_methodologies(self, state: GraphState) -> str:
        """Determine if the Agile Methodologies agent should be used.
        
        Args:
            state: Current graph state
            
        Returns:
            Decision string ('use_agile_methodologies' or 'skip_agile_methodologies')
        """
        intents = self.intent_detector.extract_intents(state.human_query or "")
        
        if "agile_methodologies" in intents:
            return "use_agile_methodologies"
        else:
            return "skip_agile_methodologies"
    
    def should_use_systems_integration(self, state: GraphState) -> str:
        """Determine if the Systems Integration agent should be used.
        
        Args:
            state: Current graph state
            
        Returns:
            Decision string ('use_systems_integration' or 'skip_systems_integration')
        """
        intents = self.intent_detector.extract_intents(state.human_query or "")
        
        if "systems_integration" in intents:
            return "use_systems_integration"
        else:
            return "skip_systems_integration" 