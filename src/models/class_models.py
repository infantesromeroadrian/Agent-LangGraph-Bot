"""Data models for the company agent application."""
from enum import Enum
from typing import Dict, List, Optional, Union, Any
from pydantic import BaseModel, Field


class AgentRole(str, Enum):
    """Roles that agents can have in the system."""
    SOLUTION_ARCHITECT = "solution_architect"
    TECHNICAL_RESEARCH = "technical_research"
    PROJECT_MANAGEMENT = "project_management"
    CODE_REVIEW = "code_review"
    CLIENT_COMMUNICATION = "client_communication"
    MARKET_ANALYSIS = "market_analysis"
    DATA_ANALYSIS = "data_analysis"
    # Nuevos roles para consultora tecnológica
    DIGITAL_TRANSFORMATION = "digital_transformation"
    CLOUD_ARCHITECTURE = "cloud_architecture"
    CYBER_SECURITY = "cyber_security"
    AGILE_METHODOLOGIES = "agile_methodologies"
    SYSTEMS_INTEGRATION = "systems_integration"
    # Nuevo rol para detección de idioma
    LANGUAGE_DETECTION = "language_detection"


class MessageType(str, Enum):
    """Types of messages that can be exchanged."""
    HUMAN = "human"
    AI = "ai"
    SYSTEM = "system"
    TOOL = "tool"
    STREAM = "stream"  # Nueva categoría para mensajes parciales


class ToolResultType(str, Enum):
    """Types of results from tool execution."""
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"


class Message(BaseModel):
    """Message exchanged between user and system."""
    content: str
    type: MessageType
    sender: Optional[str] = None
    timestamp: Optional[str] = None
    metadata: Optional[Dict] = Field(default_factory=dict)
    # Campo para indicar si este es un mensaje parcial en streaming
    is_partial: bool = False


class CompanyDocument(BaseModel):
    """Document stored in the company knowledge base."""
    id: str
    title: str
    content: str
    document_type: str
    metadata: Dict = Field(default_factory=dict)
    source: Optional[str] = None
    embedding: Optional[List[float]] = None


class ToolResult(BaseModel):
    """Result of a tool execution."""
    tool_name: str
    status: ToolResultType
    result: Optional[Union[str, Dict, List, None]] = None
    error_message: Optional[str] = None
    metadata: Dict = Field(default_factory=dict)


class QueryInput(BaseModel):
    """Input for a user query."""
    query: str
    context: Optional[List[Message]] = Field(default_factory=list)
    metadata: Optional[Dict] = Field(default_factory=dict)


class AgentResponse(BaseModel):
    """Response from an agent."""
    content: str
    agent_id: str
    agent_role: AgentRole
    confidence: float = 1.0
    sources: List[str] = Field(default_factory=list)
    thought_process: Optional[str] = None
    metadata: Dict = Field(default_factory=dict)
    is_partial: bool = False
    # Vector de pensamiento para compartir entre agentes
    thought_vector: Optional[List[float]] = None


class GraphState(BaseModel):
    """State maintained throughout the agent graph execution."""
    messages: List[Message] = Field(default_factory=list)
    current_agent: Optional[AgentRole] = None
    human_query: Optional[str] = None
    context: List[CompanyDocument] = Field(default_factory=list)
    tool_results: List[ToolResult] = Field(default_factory=list)
    agent_responses: Dict[str, AgentResponse] = Field(default_factory=dict)
    final_response: Optional[str] = None
    metadata: Dict = Field(default_factory=dict)
    # Nuevos campos para memoria compartida avanzada
    thought_vectors: Dict[str, List[float]] = Field(default_factory=dict)
    shared_memory: Dict[str, Any] = Field(default_factory=dict)
    # Configuración dinámica del grafo
    active_nodes: List[str] = Field(default_factory=list)
    disabled_nodes: List[str] = Field(default_factory=list)
    # Control de streaming
    is_streaming: bool = False
    partial_responses: Dict[str, AgentResponse] = Field(default_factory=dict)
    # Campo para el idioma detectado del usuario
    detected_language: str = "en" 