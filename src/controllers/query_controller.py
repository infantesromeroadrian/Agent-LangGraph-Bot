"""Query controller for handling user queries."""
import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import asyncio

from src.models.class_models import QueryInput
from src.services.query_service import QueryService

# Configure logging
logger = logging.getLogger(__name__)

# Create router - fix the prefix to avoid duplication with api_controller.py
router = APIRouter(prefix="/query", tags=["Query API"])

# Initialize services
query_service = QueryService()


@router.post("")
async def process_query(query_input: QueryInput):
    """Process a user query through the agent system.
    
    Args:
        query_input: User query input
        
    Returns:
        Processing result with agent responses
    """
    try:
        # Process the query using the query service
        result = await query_service.process_query(query_input)
        return result
        
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        logger.exception(e)
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")


@router.post("/stream")
async def stream_query(query_input: QueryInput):
    """Process a query and stream the response as it's generated.
    
    Args:
        query_input: User query input
        
    Returns:
        Streaming response with response chunks
    """
    async def generate():
        try:
            # Process the query and get streaming chunks
            chunks = await query_service.stream_query(query_input)
            
            # Stream each chunk as SSE
            for chunk in chunks:
                # Format as Server-Sent Event
                yield f"data: {chunk}\n\n"
                
            # End of stream marker
            yield "data: {\"type\": \"done\"}\n\n"
            
        except Exception as e:
            logger.error(f"Error streaming query: {str(e)}")
            logger.exception(e)
            yield f"data: {{\"type\": \"error\", \"content\": \"{str(e)}\"}}\n\n"
    
    # Return a streaming response
    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    ) 