"""Utilities for working with agents in the system."""
from typing import Dict, List, Optional
from datetime import datetime
import uuid

from src.models.class_models import (
    Message,
    MessageType,
    CompanyDocument,
    AgentRole,
    AgentResponse
)


# System prompts for different agent roles
AGENT_PROMPTS = {
    AgentRole.SUPERVISOR: """You are a Supervisor Agent responsible for orchestrating the company bot system.
Your responsibilities include:
1. Understanding the user's query
2. Deciding which specialized agent(s) to involve
3. Evaluating and synthesizing responses from other agents
4. Providing a final, comprehensive response to the user

Current conversation history:
{conversation_history}

User query: {query}

Available context information:
{context}

Think through what's being asked and determine the best way to respond.
""",
    
    AgentRole.RESEARCHER: """You are a Researcher Agent specialized in finding and retrieving relevant information.
Your responsibilities include:
1. Reviewing company documents to find relevant information
2. Extracting key facts, figures, and details
3. Providing accurate information with proper citations
4. Indicating areas where information may be missing or incomplete

Current conversation history:
{conversation_history}

User query: {query}

Available documents:
{context}

Based on these documents, provide accurate and relevant information to address the query.
""",
    
    AgentRole.ANALYST: """You are an Analyst Agent specialized in analyzing data and drawing insights.
Your responsibilities include:
1. Interpreting data and information retrieved by the Researcher
2. Identifying patterns, trends, and relationships
3. Drawing meaningful insights and implications
4. Making data-driven recommendations

Current conversation history:
{conversation_history}

User query: {query}

Information to analyze:
{context}

Analyze this information and provide insights relevant to the query.
""",
    
    AgentRole.COMMUNICATOR: """You are a Communicator Agent specialized in crafting clear, concise, and engaging responses.
Your responsibilities include:
1. Taking information and insights from other agents
2. Organizing information in a logical and user-friendly manner
3. Using appropriate tone and language for the audience
4. Ensuring all responses are complete, accurate, and helpful

Current conversation history:
{conversation_history}

User query: {query}

Information to communicate:
{context}

Craft a clear, comprehensive response to the user's query.
"""
}


def format_conversation_history(messages: List[Message]) -> str:
    """Format the conversation history into a string.
    
    Args:
        messages: List of Message objects
        
    Returns:
        Formatted conversation history string
    """
    if not messages:
        return "No previous conversation."
        
    formatted = []
    for msg in messages:
        sender = msg.sender or "Unknown"
        if msg.type == MessageType.HUMAN:
            formatted.append(f"User: {msg.content}")
        elif msg.type == MessageType.AI:
            formatted.append(f"AI: {msg.content}")
        elif msg.type == MessageType.SYSTEM:
            formatted.append(f"System: {msg.content}")
        
    return "\n".join(formatted)


def format_context_documents(documents: List[CompanyDocument]) -> str:
    """Format the context documents into a string.
    
    Args:
        documents: List of CompanyDocument objects
        
    Returns:
        Formatted context string
    """
    if not documents:
        return "No relevant documents available."
        
    formatted = []
    for i, doc in enumerate(documents):
        formatted.append(f"Document {i+1}: {doc.title}")
        formatted.append(f"Source: {doc.source or 'Unknown'}")
        formatted.append(f"Content: {doc.content}")
        formatted.append("-" * 40)
        
    return "\n".join(formatted)


def create_agent_prompt(
    role: AgentRole,
    query: str,
    conversation_history: List[Message],
    context: List[CompanyDocument]
) -> str:
    """Create a prompt for a specific agent role.
    
    Args:
        role: The agent role
        query: The user query
        conversation_history: List of messages in the conversation
        context: Relevant document context
        
    Returns:
        Formatted prompt string
    """
    prompt_template = AGENT_PROMPTS.get(role, AGENT_PROMPTS[AgentRole.SUPERVISOR])
    
    return prompt_template.format(
        query=query,
        conversation_history=format_conversation_history(conversation_history),
        context=format_context_documents(context)
    )


def create_message(
    content: str,
    message_type: MessageType,
    sender: Optional[str] = None
) -> Message:
    """Create a new message.
    
    Args:
        content: Message content
        message_type: Type of message
        sender: Optional sender identifier
        
    Returns:
        Message object
    """
    return Message(
        content=content,
        type=message_type,
        sender=sender,
        timestamp=datetime.now().isoformat(),
    )


def create_agent_response(
    content: str,
    agent_role: AgentRole,
    sources: List[str] = None,
    thought_process: Optional[str] = None
) -> AgentResponse:
    """Create a response from an agent.
    
    Args:
        content: Response content
        agent_role: Role of the agent
        sources: Optional list of source references
        thought_process: Optional explanation of reasoning
        
    Returns:
        AgentResponse object
    """
    if sources is None:
        sources = []
        
    return AgentResponse(
        content=content,
        agent_id=str(uuid.uuid4()),
        agent_role=agent_role,
        sources=sources,
        thought_process=thought_process
    ) 