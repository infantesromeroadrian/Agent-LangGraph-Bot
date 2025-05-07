"""Configuration utilities for the application."""
import os
from dotenv import load_dotenv
from pydantic import BaseModel

# Load environment variables from .env file
load_dotenv()

class LangSmithConfig(BaseModel):
    """Configuration for LangSmith."""
    api_key: str = os.getenv("LANGCHAIN_API_KEY", "")
    api_url: str = os.getenv("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com")
    project_name: str = os.getenv("LANGCHAIN_PROJECT", "company-bot")
    tracing_enabled: bool = os.getenv("LANGCHAIN_TRACING_V2", "true").lower() == "true"

class LLMConfig(BaseModel):
    """Configuration for Language Models."""
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    model_name: str = os.getenv("LLM_MODEL_NAME", "llama-3.3-70b-versatile")
    temperature: float = float(os.getenv("LLM_TEMPERATURE", "0.0"))
    max_tokens: int = int(os.getenv("LLM_MAX_TOKENS", "2000"))

class ChromaDBConfig(BaseModel):
    """Configuration for ChromaDB."""
    host: str = os.getenv("CHROMA_HOST", "chroma-db")
    port: int = int(os.getenv("CHROMA_PORT", "8000"))
    collection_name: str = os.getenv("CHROMA_COLLECTION", "company_documents")

class AppConfig(BaseModel):
    """Main application configuration."""
    langsmith: LangSmithConfig = LangSmithConfig()
    llm: LLMConfig = LLMConfig()
    chromadb: ChromaDBConfig = ChromaDBConfig()
    data_path: str = os.getenv("DATA_PATH", "data")
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"

# Create a global configuration instance
config = AppConfig() 