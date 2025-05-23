"""LangGraph workflow for the agent system."""
from typing import Dict, List, Any, Optional, TypedDict, Callable
from langgraph.graph import StateGraph, END

from src.models.class_models import GraphState, AgentRole


class DynamicAgentGraph:
    """Clase que permite modificar dinámicamente el grafo de agentes durante la ejecución."""
    
    def __init__(self, agent_nodes):
        """Inicializa el grafo dinámico.
        
        Args:
            agent_nodes: Instance of AgentNodes class
        """
        self.agent_nodes = agent_nodes
        self.graph = None
        self.compiled_graph = None
        self._create_initial_graph()
        
    def _create_initial_graph(self):
        """Crea el grafo inicial con todos los nodos base."""
        # Create a new graph
        workflow = StateGraph(GraphState)
        
        # Add nodes to the graph - Base agents
        workflow.add_node("language_detection", self.agent_nodes.language_detection_agent)
        workflow.add_node("retrieve_context", self.agent_nodes.retrieve_context)
        workflow.add_node("solution_architect", self.agent_nodes.solution_architect_agent)
        workflow.add_node("technical_research", self.agent_nodes.technical_research_agent)
        workflow.add_node("project_management", self.agent_nodes.project_management_agent)
        workflow.add_node("code_review", self.agent_nodes.code_review_agent)
        workflow.add_node("market_analysis", self.agent_nodes.market_analysis_agent)
        workflow.add_node("data_analysis", self.agent_nodes.data_analysis_agent)
        workflow.add_node("client_communication", self.agent_nodes.client_communication_agent)
        
        # Add nodes for new consulting agents
        workflow.add_node("digital_transformation", self.agent_nodes.digital_transformation_agent)
        workflow.add_node("cloud_architecture", self.agent_nodes.cloud_architecture_agent)
        workflow.add_node("cyber_security", self.agent_nodes.cyber_security_agent)
        workflow.add_node("agile_methodologies", self.agent_nodes.agile_methodologies_agent)
        workflow.add_node("systems_integration", self.agent_nodes.systems_integration_agent)
        
        # Define the workflow edges
        # Start with language detection
        workflow.set_entry_point("language_detection")
        workflow.add_edge("language_detection", "retrieve_context")
        workflow.add_edge("retrieve_context", "solution_architect")
        workflow.add_edge("solution_architect", "technical_research")
        
        # Conditional edges for specialized agents - Base path
        workflow.add_conditional_edges(
            "technical_research",
            self.agent_nodes.should_use_code_review,
            {
                "use_code_review": "code_review",
                "skip_code_review": "project_management"
            }
        )
        
        workflow.add_conditional_edges(
            "code_review",
            self.agent_nodes.should_use_project_management,
            {
                "use_project_management": "project_management",
                "skip_project_management": "market_analysis"
            }
        )
        
        workflow.add_conditional_edges(
            "project_management",
            self.agent_nodes.should_use_market_analysis,
            {
                "use_market_analysis": "market_analysis",
                "skip_market_analysis": "data_analysis"
            }
        )
        
        workflow.add_conditional_edges(
            "market_analysis",
            self.agent_nodes.should_use_data_analysis,
            {
                "use_data_analysis": "data_analysis",
                "skip_data_analysis": "client_communication"
            }
        )
        
        workflow.add_edge("data_analysis", "client_communication")
        
        # Create a mock state for static checks during initialization
        mock_state = GraphState(human_query="")
        
        # New conditional edges for consulting specialized agents
        workflow.add_conditional_edges(
            "technical_research",
            self.agent_nodes.should_use_digital_transformation,
            {
                "use_digital_transformation": "digital_transformation",
                "skip_digital_transformation": "code_review" if self.agent_nodes.should_use_code_review(mock_state) == "use_code_review" else "project_management"
            }
        )
        
        workflow.add_conditional_edges(
            "digital_transformation",
            self.agent_nodes.should_use_cloud_architecture,
            {
                "use_cloud_architecture": "cloud_architecture",
                "skip_cloud_architecture": "cyber_security" if self.agent_nodes.should_use_cyber_security(mock_state) == "use_cyber_security" else "code_review"
            }
        )
        
        workflow.add_conditional_edges(
            "cloud_architecture",
            self.agent_nodes.should_use_cyber_security,
            {
                "use_cyber_security": "cyber_security",
                "skip_cyber_security": "code_review" if self.agent_nodes.should_use_code_review(mock_state) == "use_code_review" else "project_management"
            }
        )
        
        workflow.add_edge("cyber_security", "code_review")
        
        workflow.add_conditional_edges(
            "project_management", 
            self.agent_nodes.should_use_agile_methodologies,
            {
                "use_agile_methodologies": "agile_methodologies",
                "skip_agile_methodologies": "market_analysis" if self.agent_nodes.should_use_market_analysis(mock_state) == "use_market_analysis" else "data_analysis"
            }
        )
        
        workflow.add_edge("agile_methodologies", "market_analysis")
        
        workflow.add_conditional_edges(
            "data_analysis",
            self.agent_nodes.should_use_systems_integration,
            {
                "use_systems_integration": "systems_integration",
                "skip_systems_integration": "client_communication"
            }
        )
        
        workflow.add_edge("systems_integration", "client_communication")
        workflow.add_edge("client_communication", END)
        
        self.graph = workflow
        self.compiled_graph = workflow.compile()
    
    def add_custom_node(self, node_name: str, node_function: Callable):
        """Añade un nuevo nodo al grafo.
        
        Args:
            node_name: Nombre del nuevo nodo
            node_function: Función que implementa el nodo
            
        Returns:
            True si se añadió correctamente, False en caso contrario
        """
        try:
            # Recuperamos el grafo original no compilado
            workflow = self.graph
            
            # Añadimos el nuevo nodo
            workflow.add_node(node_name, node_function)
            
            # Recompilamos el grafo
            self.compiled_graph = workflow.compile()
            return True
        except Exception as e:
            print(f"Error al añadir nodo: {e}")
            return False
    
    def remove_node(self, node_name: str):
        """Elimina un nodo del grafo.
        
        Args:
            node_name: Nombre del nodo a eliminar
            
        Returns:
            True si se eliminó correctamente, False en caso contrario
        """
        try:
            # En LangGraph no hay una función directa para eliminar nodos
            # Debemos recrear el grafo sin el nodo que queremos eliminar
            self._create_initial_graph()
            
            # Marcar el nodo como deshabilitado en el estado
            def disable_node_processor(state: GraphState) -> GraphState:
                state.disabled_nodes.append(node_name)
                return state
                
            # Añadir un preprocesador que verificará los nodos deshabilitados
            self.add_preprocessor(disable_node_processor)
            
            return True
        except Exception as e:
            print(f"Error al eliminar nodo: {e}")
            return False
    
    def add_edge(self, start_node: str, end_node: str):
        """Añade un borde entre dos nodos.
        
        Args:
            start_node: Nodo de origen
            end_node: Nodo de destino
            
        Returns:
            True si se añadió correctamente, False en caso contrario
        """
        try:
            workflow = self.graph
            workflow.add_edge(start_node, end_node)
            self.compiled_graph = workflow.compile()
            return True
        except Exception as e:
            print(f"Error al añadir borde: {e}")
            return False
    
    def add_conditional_edge(self, start_node: str, condition_function: Callable, routes: Dict[str, str]):
        """Añade un borde condicional.
        
        Args:
            start_node: Nodo de origen
            condition_function: Función que determina la ruta a seguir
            routes: Diccionario con las posibles rutas {condición: nodo_destino}
            
        Returns:
            True si se añadió correctamente, False en caso contrario
        """
        try:
            workflow = self.graph
            workflow.add_conditional_edges(start_node, condition_function, routes)
            self.compiled_graph = workflow.compile()
            return True
        except Exception as e:
            print(f"Error al añadir borde condicional: {e}")
            return False
    
    def add_preprocessor(self, preprocessor_function: Callable):
        """Add a preprocessor function to the graph.
        
        Args:
            preprocessor_function: Function to preprocess the state
            
        Returns:
            True if added successfully, False otherwise
        """
        try:
            # Get the original graph
            workflow = self.graph
            
            # Add the preprocessor
            workflow.add_preprocessor(preprocessor_function)
            
            # Recompile the graph
            self.compiled_graph = workflow.compile()
            return True
        except Exception as e:
            print(f"Error adding preprocessor: {e}")
            return False
    
    def get_compiled_graph(self):
        """Get the compiled graph.
        
        Returns:
            Compiled graph
        """
        if self.compiled_graph is None:
            self._create_initial_graph()
            
        return self.compiled_graph


def create_agent_graph(agent_nodes):
    """Create the agent workflow graph.
    
    Args:
        agent_nodes: Instance of AgentNodes class
        
    Returns:
        Compiled StateGraph for agent workflow
    """
    # Create a dynamic graph instance
    dynamic_graph = DynamicAgentGraph(agent_nodes)
    
    # Return the compiled graph
    return dynamic_graph.get_compiled_graph() 