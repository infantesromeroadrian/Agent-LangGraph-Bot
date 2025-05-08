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
        
        # Add nodes to the graph
        workflow.add_node("retrieve_context", self.agent_nodes.retrieve_context)
        workflow.add_node("solution_architect", self.agent_nodes.solution_architect_agent)
        workflow.add_node("technical_research", self.agent_nodes.technical_research_agent)
        workflow.add_node("project_management", self.agent_nodes.project_management_agent)
        workflow.add_node("code_review", self.agent_nodes.code_review_agent)
        workflow.add_node("market_analysis", self.agent_nodes.market_analysis_agent)
        workflow.add_node("data_analysis", self.agent_nodes.data_analysis_agent)
        workflow.add_node("client_communication", self.agent_nodes.client_communication_agent)
        
        # Define the workflow edges
        workflow.set_entry_point("retrieve_context")
        workflow.add_edge("retrieve_context", "solution_architect")
        workflow.add_edge("solution_architect", "technical_research")
        
        # Conditional edges based on whether to use specialized agents
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
        """Añade un preprocesador al grafo.
        
        Args:
            preprocessor_function: Función de preprocesamiento
            
        Returns:
            True si se añadió correctamente, False en caso contrario
        """
        try:
            self.compiled_graph = self.graph.compile(
                checkpointer=None,
                executor=None,
                channel_factory=None,
                interrupt_before=None,
                interrupt_after=None,
                state_transition_logger=None,
                custom_executor=None,
                # Añadimos el preprocesador
                state_preprocessors=[preprocessor_function]
            )
            return True
        except Exception as e:
            print(f"Error al añadir preprocesador: {e}")
            return False
            
    def get_compiled_graph(self):
        """Devuelve el grafo compilado actual.
        
        Returns:
            El grafo compilado
        """
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