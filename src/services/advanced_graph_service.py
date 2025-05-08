"""Servicio para gestionar grafos avanzados con paralelismo, ciclos y observabilidad."""
import logging
from typing import Dict, List, Any, Optional, Callable
from langsmith import Client

from src.graph.advanced_graph import AdvancedAgentGraph, create_advanced_agent_graph
from src.models.class_models import GraphState, QueryInput
from src.agents.core.agent_nodes import AgentNodes
from src.utils.config import config
from src.services.vector_store_service import VectorStoreService

# Configure logging
logger = logging.getLogger(__name__)


class AdvancedGraphService:
    """Servicio para trabajar con grafos avanzados de LangGraph."""
    
    def __init__(self):
        """Inicializa el servicio de grafos avanzados."""
        self.vector_store = VectorStoreService()
        
        # Inicializar AgentNodes correctamente sin argumentos
        self.agent_nodes = AgentNodes()
        
        # Inicializar el cliente de LangSmith si está configurado
        self.langsmith_client = None
        if config.langsmith.api_key:
            try:
                self.langsmith_client = Client(
                    api_key=config.langsmith.api_key,
                    api_url=config.langsmith.api_url,
                )
                logger.info(f"LangSmith inicializado en el servicio de grafos avanzados: {config.langsmith.project_name}")
            except Exception as e:
                logger.warning(f"Error al inicializar LangSmith en el servicio: {e}")
        
        # Crear el grafo avanzado
        self.advanced_graph = create_advanced_agent_graph(self.agent_nodes, self.langsmith_client)
    
    async def process_with_parallel_agents(self, query_input: QueryInput, agents_config: Dict[str, List[str]]):
        """Procesa una consulta utilizando múltiples agentes en paralelo.
        
        Args:
            query_input: Entrada de la consulta del usuario
            agents_config: Configuración de ramas paralelas con agentes
                {branch_name: [lista_de_agentes]}
                
        Returns:
            Resultados del procesamiento con agentes en paralelo
        """
        try:
            # Crear el estado inicial
            state = GraphState(
                human_query=query_input.query,
                conversation_id=query_input.conversation_id,
                document_ids=query_input.document_ids or [],
                metadata=query_input.metadata or {}
            )
            
            # Crear las ramas paralelas
            for branch_name, agent_list in agents_config.items():
                # Verificar que todos los agentes solicitados existen
                nodes = {}
                for agent_name in agent_list:
                    if hasattr(self.agent_nodes, f"{agent_name}_agent"):
                        nodes[agent_name] = getattr(self.agent_nodes, f"{agent_name}_agent")
                    else:
                        logger.warning(f"Agente no encontrado: {agent_name}")
                
                # Crear la rama si tiene al menos un agente válido
                if nodes:
                    self.advanced_graph.create_parallel_branch(branch_name, nodes)
                else:
                    logger.error(f"No se pudo crear la rama {branch_name}: No hay agentes válidos")
            
            # Obtener la lista de nombres de ramas creadas
            branch_names = list(agents_config.keys())
            
            # Ejecutar las ramas en paralelo
            result_state = await self.advanced_graph.execute_parallel(state, branch_names)
            
            # Procesar y formatear los resultados
            formatted_results = self._format_parallel_results(result_state)
            
            return {
                "conversation_id": query_input.conversation_id,
                "query": query_input.query,
                "results": formatted_results
            }
            
        except Exception as e:
            logger.error(f"Error en el procesamiento paralelo: {e}")
            logger.exception(e)
            return {
                "conversation_id": query_input.conversation_id,
                "query": query_input.query,
                "error": str(e)
            }
    
    def _format_parallel_results(self, state: GraphState) -> Dict[str, Any]:
        """Formatea los resultados de la ejecución paralela.
        
        Args:
            state: Estado del grafo después de la ejecución
            
        Returns:
            Resultados formateados
        """
        # Extraer los resultados de las ramas paralelas
        if "parallel_results" not in state.metadata:
            return {"error": "No se encontraron resultados de ejecución paralela"}
        
        results = {}
        for branch_result in state.metadata["parallel_results"]:
            branch_name = branch_result.branch_name
            branch_data = branch_result.result
            
            # Extraer las respuestas de los agentes
            agent_responses = {}
            if "agent_responses" in branch_data:
                agent_responses = branch_data["agent_responses"]
            
            results[branch_name] = {
                "agent_responses": agent_responses,
                "raw_data": branch_data
            }
        
        return results
    
    async def process_with_feedback_loop(self, query_input: QueryInput, loop_config: Dict[str, Any]):
        """Procesa una consulta utilizando un bucle de retroalimentación entre agentes.
        
        Args:
            query_input: Entrada de la consulta del usuario
            loop_config: Configuración del bucle
                {
                    "loop_name": str,
                    "start_node": str,
                    "end_node": str,
                    "max_iterations": int
                }
                
        Returns:
            Resultados del procesamiento con el bucle de retroalimentación
        """
        try:
            # Crear el estado inicial
            state = GraphState(
                human_query=query_input.query,
                conversation_id=query_input.conversation_id,
                document_ids=query_input.document_ids or [],
                metadata=query_input.metadata or {}
            )
            
            # Definir la condición del bucle
            def should_continue_loop(state: GraphState) -> bool:
                # Aquí implementamos la lógica para decidir si continuar el bucle
                # Por ejemplo, podemos verificar si la confianza de la respuesta es baja
                if "confidence_score" in state.metadata:
                    return state.metadata["confidence_score"] < 0.8
                return False
            
            # Crear el bucle de retroalimentación
            self.advanced_graph.create_feedback_loop(
                loop_name=loop_config.get("loop_name", "refinement_loop"),
                start_node=loop_config.get("start_node", "solution_architect"),
                end_node=loop_config.get("end_node", "technical_research"),
                loop_condition=should_continue_loop,
                max_iterations=loop_config.get("max_iterations", 3)
            )
            
            # Ejecutar el grafo con el bucle de retroalimentación
            result = await self.advanced_graph.get_compiled_graph().acontinue_(state)
            
            # Formatear los resultados
            return {
                "conversation_id": query_input.conversation_id,
                "query": query_input.query,
                "iterations": result.metadata.get("loop_counters", {}),
                "final_response": result.agent_responses.get("client_communication", "No response generated"),
                "intermediate_responses": result.agent_responses
            }
            
        except Exception as e:
            logger.error(f"Error en el procesamiento con bucle de retroalimentación: {e}")
            logger.exception(e)
            return {
                "conversation_id": query_input.conversation_id,
                "query": query_input.query,
                "error": str(e)
            }
    
    def enable_advanced_observability(self):
        """Habilita la observabilidad avanzada con LangSmith para todo el grafo.
        
        Returns:
            True si se habilitó correctamente, False en caso contrario
        """
        return self.advanced_graph.enable_full_observability()
    
    async def process_with_observability(self, query_input: QueryInput) -> Dict[str, Any]:
        """Procesa una consulta con observabilidad avanzada.
        
        Args:
            query_input: Entrada de la consulta del usuario
            
        Returns:
            Resultados del procesamiento con enlaces a trazas en LangSmith
        """
        try:
            # Habilitar observabilidad si no está habilitada
            self.enable_advanced_observability()
            
            # Crear el estado inicial
            state = GraphState(
                human_query=query_input.query,
                conversation_id=query_input.conversation_id,
                document_ids=query_input.document_ids or [],
                metadata=query_input.metadata or {
                    "run_name": f"query_{query_input.conversation_id}"
                }
            )
            
            # Ejecutar el grafo con observabilidad
            result = await self.advanced_graph.get_compiled_graph().acontinue_(state)
            
            # Si tenemos el cliente de LangSmith, devolver info de trazas
            trace_info = {}
            if self.langsmith_client:
                # Aquí se podría recuperar información sobre las trazas
                trace_info = {
                    "project_name": config.langsmith.project_name,
                    "run_id": state.metadata.get("langsmith_run_id"),
                    "dashboard_url": f"{config.langsmith.api_url}/projects/{config.langsmith.project_name}/runs"
                }
            
            return {
                "conversation_id": query_input.conversation_id,
                "query": query_input.query,
                "response": result.agent_responses.get("client_communication", "No response generated"),
                "trace_info": trace_info
            }
            
        except Exception as e:
            logger.error(f"Error en el procesamiento con observabilidad: {e}")
            logger.exception(e)
            return {
                "conversation_id": query_input.conversation_id,
                "query": query_input.query,
                "error": str(e)
            } 