"""Main API controller that includes all other controllers."""
import logging
from fastapi import APIRouter

from src.controllers.query_controller import router as query_router
from src.controllers.document_controller import router as document_router

# Configure logging
logger = logging.getLogger(__name__)

# Create main router
router = APIRouter(prefix="/api", tags=["API"])

# Include sub-routers
router.include_router(query_router, prefix="")
router.include_router(document_router, prefix="") 