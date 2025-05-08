"""Agent factory for creating and managing agent instances."""
from typing import Dict, Any, Type

from src.services.llm_service import LLMService
from src.services.vector_store_service import VectorStoreService
from src.utils.graph_utils import GraphManagerUtil

# Import core agents
from src.agents.core.language_detection_agent import LanguageDetectionAgent
from src.agents.core.context_retrieval_agent import ContextRetrievalAgent

# Import technical agents
from src.agents.technical.solution_architect_agent import SolutionArchitectAgent
from src.agents.technical.technical_research_agent import TechnicalResearchAgent
from src.agents.technical.code_review_agent import CodeReviewAgent
from src.agents.technical.systems_integration_agent import SystemsIntegrationAgent
from src.agents.technical.cloud_architecture_agent import CloudArchitectureAgent
from src.agents.technical.cyber_security_agent import CyberSecurityAgent

# Import business agents
from src.agents.business.project_management_agent import ProjectManagementAgent
from src.agents.business.market_analysis_agent import MarketAnalysisAgent
from src.agents.business.data_analysis_agent import DataAnalysisAgent
from src.agents.business.client_communication_agent import ClientCommunicationAgent

# Import specialized agents
from src.agents.specialized.digital_transformation_agent import DigitalTransformationAgent
from src.agents.specialized.agile_methodologies_agent import AgileMethodologiesAgent


class AgentFactory:
    """Factory for creating and managing agent instances."""
    
    def __init__(self):
        """Initialize the agent factory with required services."""
        # Shared services
        self.llm_service = LLMService()
        self.vector_store = VectorStoreService()
        self.graph_manager = GraphManagerUtil()
        
        # Agent instances cache
        self._agent_instances: Dict[str, Any] = {}
    
    def get_agent(self, agent_type: str) -> Any:
        """Get or create an agent instance of the specified type.
        
        Args:
            agent_type: Type of agent to create
            
        Returns:
            Agent instance
        """
        # Check if we already have an instance
        if agent_type in self._agent_instances:
            return self._agent_instances[agent_type]
        
        # Create a new instance based on the agent type
        agent = self._create_agent(agent_type)
        
        # Cache the instance
        if agent:
            self._agent_instances[agent_type] = agent
            
        return agent
    
    def _create_agent(self, agent_type: str) -> Any:
        """Create a new agent instance of the specified type.
        
        Args:
            agent_type: Type of agent to create
            
        Returns:
            New agent instance
        """
        agent_map = {
            'language_detection': self._create_language_detection_agent,
            'context_retrieval': self._create_context_retrieval_agent,
            'solution_architect': self._create_solution_architect_agent,
            'technical_research': self._create_technical_research_agent,
            'project_management': self._create_project_management_agent,
            'code_review': self._create_code_review_agent,
            'market_analysis': self._create_market_analysis_agent,
            'data_analysis': self._create_data_analysis_agent,
            'client_communication': self._create_client_communication_agent,
            'digital_transformation': self._create_digital_transformation_agent,
            'cloud_architecture': self._create_cloud_architecture_agent,
            'cyber_security': self._create_cyber_security_agent,
            'agile_methodologies': self._create_agile_methodologies_agent,
            'systems_integration': self._create_systems_integration_agent,
            # Add more agent types as they are implemented
        }
        
        creator_func = agent_map.get(agent_type)
        if creator_func:
            return creator_func()
        
        return None
    
    def _create_language_detection_agent(self) -> LanguageDetectionAgent:
        """Create a language detection agent.
        
        Returns:
            New language detection agent
        """
        return LanguageDetectionAgent(
            llm_service=self.llm_service,
            graph_manager=self.graph_manager
        )
    
    def _create_context_retrieval_agent(self) -> ContextRetrievalAgent:
        """Create a context retrieval agent.
        
        Returns:
            New context retrieval agent
        """
        return ContextRetrievalAgent(
            vector_store=self.vector_store,
            graph_manager=self.graph_manager
        )
    
    def _create_solution_architect_agent(self) -> SolutionArchitectAgent:
        """Create a solution architect agent.
        
        Returns:
            New solution architect agent
        """
        return SolutionArchitectAgent(
            llm_service=self.llm_service,
            vector_store=self.vector_store,
            graph_manager=self.graph_manager
        )
    
    def _create_technical_research_agent(self) -> TechnicalResearchAgent:
        """Create a technical research agent.
        
        Returns:
            New technical research agent
        """
        return TechnicalResearchAgent(
            llm_service=self.llm_service,
            vector_store=self.vector_store,
            graph_manager=self.graph_manager
        )
        
    def _create_project_management_agent(self) -> ProjectManagementAgent:
        """Create a project management agent.
        
        Returns:
            New project management agent
        """
        return ProjectManagementAgent(
            llm_service=self.llm_service,
            vector_store=self.vector_store,
            graph_manager=self.graph_manager
        )
        
    def _create_code_review_agent(self) -> CodeReviewAgent:
        """Create a code review agent.
        
        Returns:
            New code review agent
        """
        return CodeReviewAgent(
            llm_service=self.llm_service,
            vector_store=self.vector_store,
            graph_manager=self.graph_manager
        )
        
    def _create_market_analysis_agent(self) -> MarketAnalysisAgent:
        """Create a market analysis agent.
        
        Returns:
            New market analysis agent
        """
        return MarketAnalysisAgent(
            llm_service=self.llm_service,
            vector_store=self.vector_store,
            graph_manager=self.graph_manager
        )
        
    def _create_data_analysis_agent(self) -> DataAnalysisAgent:
        """Create a data analysis agent.
        
        Returns:
            New data analysis agent
        """
        return DataAnalysisAgent(
            llm_service=self.llm_service,
            vector_store=self.vector_store,
            graph_manager=self.graph_manager
        )
        
    def _create_client_communication_agent(self) -> ClientCommunicationAgent:
        """Create a client communication agent.
        
        Returns:
            New client communication agent
        """
        return ClientCommunicationAgent(
            llm_service=self.llm_service,
            vector_store=self.vector_store,
            graph_manager=self.graph_manager
        )
    
    def _create_digital_transformation_agent(self) -> DigitalTransformationAgent:
        """Create a digital transformation agent.
        
        Returns:
            New digital transformation agent
        """
        return DigitalTransformationAgent(
            llm_service=self.llm_service,
            vector_store=self.vector_store,
            graph_manager=self.graph_manager
        )
    
    def _create_cloud_architecture_agent(self) -> CloudArchitectureAgent:
        """Create a cloud architecture agent.
        
        Returns:
            New cloud architecture agent
        """
        return CloudArchitectureAgent(
            llm_service=self.llm_service,
            vector_store=self.vector_store,
            graph_manager=self.graph_manager
        )
    
    def _create_cyber_security_agent(self) -> CyberSecurityAgent:
        """Create a cyber security agent.
        
        Returns:
            New cyber security agent
        """
        return CyberSecurityAgent(
            llm_service=self.llm_service,
            vector_store=self.vector_store,
            graph_manager=self.graph_manager
        )
    
    def _create_agile_methodologies_agent(self) -> AgileMethodologiesAgent:
        """Create an agile methodologies agent.
        
        Returns:
            New agile methodologies agent
        """
        return AgileMethodologiesAgent(
            llm_service=self.llm_service,
            vector_store=self.vector_store,
            graph_manager=self.graph_manager
        )
    
    def _create_systems_integration_agent(self) -> SystemsIntegrationAgent:
        """Create a systems integration agent.
        
        Returns:
            New systems integration agent
        """
        return SystemsIntegrationAgent(
            llm_service=self.llm_service,
            vector_store=self.vector_store,
            graph_manager=self.graph_manager
        ) 