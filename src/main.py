"""Main entry point for the company bot application."""
import os
import logging
import sys
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn
from langsmith import Client
import importlib.util

from src.controllers.api_controller import router as api_router
from src.utils.config import config
from src.services.vector_store_service import VectorStoreService


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
    title="Consultoría Tecnológica AI",
    description="API para una consultora tecnológica con agentes de IA desarrollados con Langchain, Langsmith y Langgraph",
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


@app.on_event("startup")
async def load_consulting_methodologies():
    """Carga los documentos de las metodologías de consultoría en el vector store al iniciar la aplicación."""
    try:
        # Verificar si el archivo de carga existe
        load_script_path = "src/utils/load_sample_data.py"
        if not os.path.exists(load_script_path):
            logger.warning(f"Script de carga de datos no encontrado: {load_script_path}")
            return
            
        # Cargar dinámicamente el script
        spec = importlib.util.spec_from_file_location("load_sample_data", load_script_path)
        load_sample_data = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(load_sample_data)
        
        # Crear el servicio del vector store
        vector_store = VectorStoreService()
        
        # Verificar si ya hay documentos cargados
        if vector_store.count_documents() > 0:
            logger.info(f"Ya existen {vector_store.count_documents()} documentos en el vector store. No se cargarán documentos de muestra.")
            return
            
        # Crear documentos de muestra
        logger.info("Creando documentos de metodologías de consultoría...")
        sample_docs = load_sample_data.create_sample_documents()
        
        # Cargar documentos en el vector store
        logger.info("Cargando documentos en el vector store...")
        load_sample_data.load_documents(vector_store, sample_docs)
        
        logger.info(f"Se cargaron documentos de metodologías de consultoría: {len(sample_docs)} documentos")
    except Exception as e:
        logger.error(f"Error al cargar documentos de consultoría: {e}")
        logger.exception(e)


if __name__ == "__main__":
    # Run the API server
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("src.main:app", host="0.0.0.0", port=port, reload=True) 