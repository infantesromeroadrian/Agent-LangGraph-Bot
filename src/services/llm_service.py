"""Service for interacting with Language Models."""
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableParallel, RunnablePassthrough

from src.utils.config import config


class LLMService:
    """Service for handling interactions with language models."""
    
    def __init__(self):
        """Initialize the LLM service with configured models."""
        self.chat_model = self._initialize_chat_model()
        
    def _initialize_chat_model(self) -> BaseChatModel:
        """Initialize the chat model with configuration settings."""
        # Prefer Groq if API key is available
        if config.llm.groq_api_key:
            return ChatGroq(
                model=config.llm.model_name,
                temperature=config.llm.temperature,
                max_tokens=config.llm.max_tokens,
                groq_api_key=config.llm.groq_api_key,
            )
        # Fall back to OpenAI if Groq not configured
        return ChatOpenAI(
            model=config.llm.model_name if "gpt" in config.llm.model_name else "gpt-4o",  # ensure model name is compatible
            temperature=config.llm.temperature,
            max_tokens=config.llm.max_tokens,
            api_key=config.llm.openai_api_key,
        )
    
    def create_chain(self, prompt_template: str, output_parser=None):
        """Create a simple chain with the given prompt template.
        
        Args:
            prompt_template: The template string for the prompt
            output_parser: Optional parser for the output (defaults to string)
            
        Returns:
            A runnable chain
        """
        prompt = PromptTemplate.from_template(prompt_template)
        
        if output_parser is None:
            output_parser = StrOutputParser()
            
        return prompt | self.chat_model | output_parser
    
    def create_rag_chain(self, prompt_template: str, retriever, output_parser=None):
        """Create a RAG (Retrieval Augmented Generation) chain.
        
        Args:
            prompt_template: The template string for the prompt
            retriever: The retriever component to use
            output_parser: Optional parser for the output (defaults to string)
            
        Returns:
            A runnable RAG chain
        """
        prompt = PromptTemplate.from_template(prompt_template)
        
        if output_parser is None:
            output_parser = StrOutputParser()
        
        setup_and_retrieval = RunnableParallel(
            {"context": retriever, "question": RunnablePassthrough()}
        )
        
        chain = setup_and_retrieval | prompt | self.chat_model | output_parser
        return chain 