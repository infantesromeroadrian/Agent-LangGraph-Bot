"""LangGraph workflow for the agent system."""
from typing import Dict, List, Any, Optional, TypedDict
from langgraph.graph import StateGraph, END

from src.models.class_models import GraphState


def create_agent_graph(agent_nodes):
    """Create the agent workflow graph.
    
    Args:
        agent_nodes: Instance of AgentNodes class
        
    Returns:
        Compiled StateGraph for agent workflow
    """
    # Create a new graph
    workflow = StateGraph(GraphState)
    
    # Add nodes to the graph
    workflow.add_node("retrieve_context", agent_nodes.retrieve_context)
    workflow.add_node("solution_architect", agent_nodes.solution_architect_agent)
    workflow.add_node("technical_research", agent_nodes.technical_research_agent)
    workflow.add_node("project_management", agent_nodes.project_management_agent)
    workflow.add_node("code_review", agent_nodes.code_review_agent)
    workflow.add_node("market_analysis", agent_nodes.market_analysis_agent)
    workflow.add_node("data_analysis", agent_nodes.data_analysis_agent)
    workflow.add_node("client_communication", agent_nodes.client_communication_agent)
    
    # Define the workflow edges
    workflow.set_entry_point("retrieve_context")
    workflow.add_edge("retrieve_context", "solution_architect")
    workflow.add_edge("solution_architect", "technical_research")
    
    # Conditional edges based on whether to use specialized agents
    workflow.add_conditional_edges(
        "technical_research",
        agent_nodes.should_use_code_review,
        {
            "use_code_review": "code_review",
            "skip_code_review": "project_management"
        }
    )
    
    workflow.add_conditional_edges(
        "code_review",
        agent_nodes.should_use_project_management,
        {
            "use_project_management": "project_management",
            "skip_project_management": "market_analysis"
        }
    )
    
    workflow.add_conditional_edges(
        "project_management",
        agent_nodes.should_use_market_analysis,
        {
            "use_market_analysis": "market_analysis",
            "skip_market_analysis": "data_analysis"
        }
    )
    
    workflow.add_conditional_edges(
        "market_analysis",
        agent_nodes.should_use_data_analysis,
        {
            "use_data_analysis": "data_analysis",
            "skip_data_analysis": "client_communication"
        }
    )
    
    workflow.add_edge("data_analysis", "client_communication")
    workflow.add_edge("client_communication", END)
    
    # Compile the graph
    return workflow.compile() 