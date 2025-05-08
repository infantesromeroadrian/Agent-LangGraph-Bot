"""Implementación avanzada de LangGraph con soporte para grafos paralelos, cíclicos y observabilidad."""
from typing import Dict, List, Any, Optional, Callable, Union
from langgraph.graph import StateGraph, END, START
from langsmith import Client
import logging
import asyncio
from pydantic import BaseModel, Field

from src.models.class_models import GraphState
from src.utils.config import config

# Configure logging
logger = logging.getLogger(__name__)

class ParallelBranchOutput(BaseModel):
    """Modelo para la salida de ramas paralelas."""
    branch_name: str = Field(description="Nombre de la rama paralela")
    result: Dict[str, Any] = Field(description="Resultado de la ejecución de la rama")


class AdvancedAgentGraph:
    """Implementación avanzada del grafo de agentes con soporte para:
    - Ejecución paralela de agentes
    - Grafos cíclicos con retroalimentación
    - Observabilidad avanzada con LangSmith
    """
    
    def __init__(self, agent_nodes, langsmith_client=None):
        """Inicializa el grafo avanzado.
        
        Args:
            agent_nodes: Instancia de la clase AgentNodes
            langsmith_client: Cliente de LangSmith opcional
        """
        self.agent_nodes = agent_nodes
        self.graph = None
        self.compiled_graph = None
        self.parallel_branches = {}
        self.feedback_loops = {}
        
        # Configurar LangSmith si está disponible
        self.langsmith_client = langsmith_client
        if not self.langsmith_client and config.langsmith.api_key:
            try:
                self.langsmith_client = Client(
                    api_key=config.langsmith.api_key,
                    api_url=config.langsmith.api_url,
                )
                logger.info(f"LangSmith inicializado para observabilidad avanzada")
            except Exception as e:
                logger.warning(f"No se pudo inicializar LangSmith: {e}")
        
        # Inicializar el grafo base
        self._create_initial_graph()
    
    def _create_initial_graph(self):
        """Crea el grafo inicial con capacidades avanzadas."""
        # Crear un nuevo grafo sin usar MemorySaver
        workflow = StateGraph(GraphState)
        
        # Añadir nodos base al grafo
        workflow.add_node("language_detection", self.agent_nodes.language_detection_agent)
        workflow.add_node("retrieve_context", self.agent_nodes.retrieve_context)
        workflow.add_node("solution_architect", self.agent_nodes.solution_architect_agent)
        workflow.add_node("technical_research", self.agent_nodes.technical_research_agent)
        workflow.add_node("client_communication", self.agent_nodes.client_communication_agent)
        
        # Configurar el flujo básico
        workflow.set_entry_point("language_detection")
        workflow.add_edge("language_detection", "retrieve_context")
        workflow.add_edge("retrieve_context", "solution_architect")
        workflow.add_edge("solution_architect", "technical_research")
        workflow.add_edge("technical_research", "client_communication")
        workflow.add_edge("client_communication", END)
        
        # Guardar el grafo
        self.graph = workflow
        self.compiled_graph = workflow.compile()
    
    def create_parallel_branch(self, branch_name: str, nodes: Dict[str, Callable]):
        """Crea una rama paralela con múltiples agentes ejecutándose simultáneamente.
        
        Args:
            branch_name: Nombre único para la rama paralela
            nodes: Diccionario de nodos {nombre: función} para ejecutar en paralelo
            
        Returns:
            La rama paralela creada
        """
        # Crear un nuevo grafo para la rama paralela
        branch_graph = StateGraph(GraphState)
        
        # Añadir nodos a la rama
        for node_name, node_function in nodes.items():
            branch_graph.add_node(node_name, node_function)
        
        # Crear un nodo de agregación para combinar resultados
        def aggregator(state: GraphState):
            """Combina los resultados de los nodos paralelos."""
            # Aquí implementaríamos la lógica para combinar resultados
            return state
        
        branch_graph.add_node("aggregator", aggregator)
        
        # Conectar todos los nodos al agregador
        for node_name in nodes.keys():
            branch_graph.add_edge(START, node_name)
            branch_graph.add_edge(node_name, "aggregator")
        
        branch_graph.add_edge("aggregator", END)
        
        # Compilar la rama
        compiled_branch = branch_graph.compile()
        
        # Almacenar la rama para uso posterior
        self.parallel_branches[branch_name] = compiled_branch
        
        return compiled_branch
    
    def create_feedback_loop(self, loop_name: str, start_node: str, end_node: str, 
                           loop_condition: Callable, max_iterations: int = 3):
        """Crea un bucle de retroalimentación entre nodos.
        
        Args:
            loop_name: Nombre único para el bucle
            start_node: Nodo de inicio del bucle
            end_node: Nodo final del bucle 
            loop_condition: Función que determina si continuar el bucle
            max_iterations: Número máximo de iteraciones permitidas
            
        Returns:
            True si se creó correctamente, False en caso contrario
        """
        try:
            # Recuperar el grafo original
            workflow = self.graph
            
            # Crear un contador de iteraciones en el estado
            def initialize_loop_counter(state: GraphState):
                if "loop_counters" not in state.metadata:
                    state.metadata["loop_counters"] = {}
                if loop_name not in state.metadata["loop_counters"]:
                    state.metadata["loop_counters"][loop_name] = 0
                return state
            
            # Añadir el nodo de inicialización
            loop_init_node = f"{loop_name}_init"
            workflow.add_node(loop_init_node, initialize_loop_counter)
            
            # Crear un nodo de decisión que evalúa si continuar el bucle
            def loop_decision(state: GraphState):
                # Incrementar el contador
                state.metadata["loop_counters"][loop_name] += 1
                
                # Verificar si hemos alcanzado el límite de iteraciones
                if state.metadata["loop_counters"][loop_name] >= max_iterations:
                    return "exit_loop"
                
                # Evaluar la condición de continuación
                continue_loop = loop_condition(state)
                return "continue_loop" if continue_loop else "exit_loop"
            
            # Añadir el nodo de decisión
            loop_decision_node = f"{loop_name}_decision"
            workflow.add_node(loop_decision_node, loop_decision)
            
            # Añadir las conexiones del bucle
            workflow.add_edge(end_node, loop_decision_node)
            
            # Añadir las rutas condicionales
            workflow.add_conditional_edges(
                loop_decision_node,
                lambda state: loop_decision(state),
                {
                    "continue_loop": start_node,  # Volver al inicio del bucle
                    "exit_loop": "client_communication"  # Salir del bucle
                }
            )
            
            # Almacenar información del bucle
            self.feedback_loops[loop_name] = {
                "start_node": start_node,
                "end_node": end_node,
                "decision_node": loop_decision_node,
                "max_iterations": max_iterations
            }
            
            # Recompilar el grafo
            self.compiled_graph = workflow.compile()
            return True
            
        except Exception as e:
            logger.error(f"Error al crear bucle de retroalimentación: {e}")
            return False
    
    async def execute_parallel(self, state: GraphState, branch_names: List[str]) -> GraphState:
        """Ejecuta múltiples ramas en paralelo y combina sus resultados.
        
        Args:
            state: Estado inicial del grafo
            branch_names: Lista de nombres de ramas a ejecutar
            
        Returns:
            Estado actualizado con los resultados de todas las ramas
        """
        # Verificar que todas las ramas existan
        for branch_name in branch_names:
            if branch_name not in self.parallel_branches:
                raise ValueError(f"Rama paralela no encontrada: {branch_name}")
        
        # Preparar las tareas para ejecución asíncrona
        tasks = []
        for branch_name in branch_names:
            branch = self.parallel_branches[branch_name]
            # Crear una copia del estado para cada rama
            branch_state = GraphState(**state.model_dump())
            
            # Añadir la tarea a la lista
            task = asyncio.create_task(self._execute_branch(branch_name, branch, branch_state))
            tasks.append(task)
        
        # Ejecutar todas las ramas en paralelo
        branch_results = await asyncio.gather(*tasks)
        
        # Combinar los resultados en el estado original
        for result in branch_results:
            # Aquí implementaríamos la lógica específica para combinar resultados
            # Por ejemplo, podríamos agregar los resultados de cada rama a una lista
            if "parallel_results" not in state.metadata:
                state.metadata["parallel_results"] = []
            
            state.metadata["parallel_results"].append(result)
        
        return state
    
    async def _execute_branch(self, branch_name: str, branch, state: GraphState) -> ParallelBranchOutput:
        """Ejecuta una rama paralela y devuelve su resultado.
        
        Args:
            branch_name: Nombre de la rama
            branch: Grafo compilado de la rama
            state: Estado inicial
            
        Returns:
            Resultado de la ejecución de la rama
        """
        # Ejecutar la rama con observabilidad si LangSmith está disponible
        trace_name = f"parallel_branch_{branch_name}"
        
        if self.langsmith_client:
            # Ejecutar con trazas de LangSmith
            result = await branch.acontinue_with_feedback(
                state,
                tracer=self.langsmith_client.as_tracer(
                    project_name=config.langsmith.project_name,
                    run_name=trace_name
                )
            )
        else:
            # Ejecutar sin trazas
            result = await branch.acontinue_(state)
        
        # Formatear el resultado
        return ParallelBranchOutput(
            branch_name=branch_name,
            result=result.model_dump()
        )
    
    def enable_full_observability(self):
        """Habilita la observabilidad completa con LangSmith para todo el grafo."""
        if not self.langsmith_client:
            logger.warning("No se puede habilitar observabilidad: Cliente LangSmith no disponible")
            return False
        
        try:
            # Recompilar el grafo con observabilidad completa
            self.compiled_graph = self.graph.compile(
                tracer=self.langsmith_client.as_tracer(
                    project_name=config.langsmith.project_name
                )
            )
            logger.info("Observabilidad avanzada habilitada con LangSmith")
            return True
        except Exception as e:
            logger.error(f"Error al habilitar observabilidad avanzada: {e}")
            return False
    
    def get_compiled_graph(self):
        """Devuelve el grafo compilado para su ejecución."""
        return self.compiled_graph


def create_advanced_agent_graph(agent_nodes, langsmith_client=None):
    """Función de fábrica para crear un grafo avanzado.
    
    Args:
        agent_nodes: Instancia de la clase AgentNodes
        langsmith_client: Cliente opcional de LangSmith
        
    Returns:
        Instancia de AdvancedAgentGraph
    """
    return AdvancedAgentGraph(agent_nodes, langsmith_client) 