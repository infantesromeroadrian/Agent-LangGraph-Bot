"""Agents package for the AI Consulting platform."""

# Re-export core agent functionality
from src.agents.core.agent_factory import AgentFactory
from src.agents.core.agent_nodes import AgentNodes

# Re-export agent utilities
from src.agents.base.agent_utils import (
    create_agent_prompt,
    create_message,
    create_agent_response,
    format_conversation_history,
    format_context_documents
)

# Re-export agent classes for backward compatibility
# Core agents
from src.agents.core.language_detection_agent import LanguageDetectionAgent
from src.agents.core.context_retrieval_agent import ContextRetrievalAgent

# Technical agents
from src.agents.technical.solution_architect_agent import SolutionArchitectAgent
from src.agents.technical.technical_research_agent import TechnicalResearchAgent
from src.agents.technical.code_review_agent import CodeReviewAgent
from src.agents.technical.systems_integration_agent import SystemsIntegrationAgent
from src.agents.technical.cloud_architecture_agent import CloudArchitectureAgent
from src.agents.technical.cyber_security_agent import CyberSecurityAgent

# Business agents
from src.agents.business.project_management_agent import ProjectManagementAgent
from src.agents.business.market_analysis_agent import MarketAnalysisAgent
from src.agents.business.data_analysis_agent import DataAnalysisAgent
from src.agents.business.client_communication_agent import ClientCommunicationAgent

# Specialized agents
from src.agents.specialized.digital_transformation_agent import DigitalTransformationAgent
from src.agents.specialized.agile_methodologies_agent import AgileMethodologiesAgent 