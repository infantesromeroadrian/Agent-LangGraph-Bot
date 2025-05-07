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
    workflow.add_node("supervisor", agent_nodes.supervisor_agent)
    workflow.add_node("researcher", agent_nodes.researcher_agent)
    workflow.add_node("analyst", agent_nodes.analyst_agent)
    workflow.add_node("communicator", agent_nodes.communicator_agent)
    
    # Define the workflow edges
    workflow.set_entry_point("retrieve_context")
    workflow.add_edge("retrieve_context", "supervisor")
    workflow.add_edge("supervisor", "researcher")
    
    # Conditional edge based on whether to use analyst
    workflow.add_conditional_edges(
        "researcher",
        agent_nodes.should_use_analyst,
        {
            "use_analyst": "analyst",
            "skip_analyst": "communicator"
        }
    )
    
    workflow.add_edge("analyst", "communicator")
    workflow.add_edge("communicator", END)
    
    # Compile the graph
    return workflow.compile() 