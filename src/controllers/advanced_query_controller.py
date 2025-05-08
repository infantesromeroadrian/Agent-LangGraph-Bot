"""Controlador para operaciones avanzadas de grafos y consultas paralelas."""
import logging
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
import json

from src.models.class_models import QueryInput
from src.services.advanced_graph_service import AdvancedGraphService

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/advanced", tags=["Advanced Graph API"])

# Initialize service
advanced_graph_service = AdvancedGraphService()


@router.post("/parallel")
async def process_parallel_query(query_input: QueryInput, agents_config: Dict[str, List[str]]):
    """Procesa una consulta utilizando múltiples agentes en paralelo.
    
    Args:
        query_input: Entrada de la consulta del usuario
        agents_config: Configuración de ramas paralelas con agentes
            {branch_name: [lista_de_agentes]}
            
    Returns:
        Resultados del procesamiento con agentes en paralelo
    """
    try:
        result = await advanced_graph_service.process_with_parallel_agents(query_input, agents_config)
        return result
    except Exception as e:
        logger.error(f"Error en el procesamiento paralelo: {e}")
        logger.exception(e)
        raise HTTPException(status_code=500, detail=f"Error en el procesamiento paralelo: {str(e)}")


@router.post("/feedback-loop")
async def process_feedback_loop_query(query_input: QueryInput, loop_config: Dict[str, Any]):
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
        result = await advanced_graph_service.process_with_feedback_loop(query_input, loop_config)
        return result
    except Exception as e:
        logger.error(f"Error en el procesamiento con bucle de retroalimentación: {e}")
        logger.exception(e)
        raise HTTPException(
            status_code=500, 
            detail=f"Error en el procesamiento con bucle de retroalimentación: {str(e)}"
        )


@router.post("/observable")
async def process_observable_query(query_input: QueryInput):
    """Procesa una consulta con observabilidad avanzada usando LangSmith.
    
    Args:
        query_input: Entrada de la consulta del usuario
        
    Returns:
        Resultados del procesamiento con enlaces a trazas en LangSmith
    """
    try:
        result = await advanced_graph_service.process_with_observability(query_input)
        return result
    except Exception as e:
        logger.error(f"Error en el procesamiento con observabilidad: {e}")
        logger.exception(e)
        raise HTTPException(
            status_code=500,
            detail=f"Error en el procesamiento con observabilidad: {str(e)}"
        )


@router.post("/parallel/stream")
async def stream_parallel_query(query_input: QueryInput, agents_config: Dict[str, List[str]]):
    """Procesa una consulta con agentes paralelos y devuelve el resultado en streaming.
    
    Args:
        query_input: Entrada de la consulta del usuario
        agents_config: Configuración de ramas paralelas con agentes
        
    Returns:
        Streaming response con los resultados parciales
    """
    async def generate():
        try:
            # Crear las ramas paralelas según la configuración
            for branch_name, agent_list in agents_config.items():
                # Señalizar la creación de cada rama - Corregido para evitar mezclar diccionarios y f-strings
                branch_data = {
                    'type': 'branch_created',
                    'branch_name': branch_name,
                    'agents': agent_list
                }
                yield f"data: {json.dumps(branch_data)}\n\n"
            
            # Notificar que se inicia el procesamiento
            start_data = {'type': 'processing_started'}
            yield f"data: {json.dumps(start_data)}\n\n"
            
            # Procesar la consulta
            result = await advanced_graph_service.process_with_parallel_agents(query_input, agents_config)
            
            # Enviar el resultado completo
            result_data = {
                'type': 'result',
                'content': result
            }
            yield f"data: {json.dumps(result_data)}\n\n"
            
            # Señal de fin
            yield "data: {\"type\": \"done\"}\n\n"
            
        except Exception as e:
            logger.error(f"Error en streaming paralelo: {e}")
            logger.exception(e)
            error_msg = str(e).replace('"', '\\"')  # Escapar comillas para evitar problemas JSON
            yield f"data: {{\"type\": \"error\", \"content\": \"{error_msg}\"}}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )


@router.post("/feedback-loop/stream")
async def stream_feedback_loop_query(query_input: QueryInput, loop_config: Dict[str, Any]):
    """Procesa una consulta con bucle de retroalimentación y devuelve el resultado en streaming.
    
    Args:
        query_input: Entrada de la consulta del usuario
        loop_config: Configuración del bucle
        
    Returns:
        Streaming response con los resultados de cada iteración
    """
    async def generate():
        try:
            # Notificar la configuración del bucle
            config_data = {
                'type': 'loop_configured',
                'config': loop_config
            }
            yield f"data: {json.dumps(config_data)}\n\n"
            
            # Iniciar procesamiento
            start_data = {'type': 'processing_started'}
            yield f"data: {json.dumps(start_data)}\n\n"
            
            # Ejecutar el bucle de retroalimentación
            # En un caso real, necesitaríamos modificar el método en el servicio
            # para que devuelva eventos de streaming durante el procesamiento
            result = await advanced_graph_service.process_with_feedback_loop(query_input, loop_config)
            
            # Enviar el resultado final
            result_data = {
                'type': 'result',
                'content': result
            }
            yield f"data: {json.dumps(result_data)}\n\n"
            
            # Señal de fin
            yield "data: {\"type\": \"done\"}\n\n"
            
        except Exception as e:
            logger.error(f"Error en streaming de bucle: {e}")
            logger.exception(e)
            error_msg = str(e).replace('"', '\\"')  # Escapar comillas para evitar problemas JSON
            yield f"data: {{\"type\": \"error\", \"content\": \"{error_msg}\"}}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    ) 