"""Main entry point for the company bot application."""
import os
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn
from langsmith import Client

from src.controllers.api_controller import router as api_router
from src.utils.config import config


# Configure logging
logging.basicConfig(
    level=logging.INFO if not config.debug else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize LangSmith if API key is provided
if config.langsmith.api_key:
    try:
        langsmith_client = Client(
            api_key=config.langsmith.api_key,
            api_url=config.langsmith.api_url,
        )
        logger.info(f"LangSmith initialized with project: {config.langsmith.project_name}")
    except Exception as e:
        logger.warning(f"Failed to initialize LangSmith: {e}")

# Create FastAPI app
app = FastAPI(
    title="Company Bot API",
    description="API for the AI-powered company bot built with Langchain, Langsmith, and Langgraph",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(api_router)

# Mount static files
app.mount("/static", StaticFiles(directory="src/static"), name="static")


@app.get("/")
async def root():
    """Serve the main HTML page."""
    return FileResponse("src/static/index.html")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    # Run the API server
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("src.main:app", host="0.0.0.0", port=port, reload=True) 