"""Language detection agent for the LangGraph workflow."""
from typing import List, Dict, Any, Optional

from src.models.class_models import GraphState, AgentRole, MessageType
from src.services.llm_service import LLMService
from src.utils.graph_utils import GraphManagerUtil
from src.agents.base.agent_utils import (
    create_agent_prompt,
    create_message
)


class LanguageDetectionAgent:
    """Agent responsible for detecting the language used by the user."""
    
    def __init__(self, llm_service: LLMService, graph_manager: GraphManagerUtil):
        """Initialize the Language Detection agent with services.
        
        Args:
            llm_service: LLM service for generating agent responses
            graph_manager: Graph manager for workflow utilities
        """
        self.llm_service = llm_service
        self.graph_manager = graph_manager
    
    def process(self, state: GraphState) -> GraphState:
        """Detect the language used by the user in their query.
        
        Args:
            state: Current graph state
            
        Returns:
            Updated graph state with detected language
        """
        # Set current agent
        state.current_agent = AgentRole.LANGUAGE_DETECTION
        
        # Skip if node is disabled
        if self.graph_manager.should_skip_node(state, AgentRole.LANGUAGE_DETECTION.value):
            return state
            
        # If no query, default to English
        if not state.human_query or state.human_query.strip() == "":
            state.detected_language = "en"
            return state
            
        # Create prompt for language detection
        prompt = create_agent_prompt(
            AgentRole.LANGUAGE_DETECTION,
            state.human_query or "",
            state.messages,
            []  # No context needed for language detection
        )
        
        # Get response from LLM
        chain = self.llm_service.create_chain(
            "{input}",
        )
        response = chain.invoke({"input": prompt})
        
        # Clean the response to get just the language code
        lang_code = response.strip().lower()
        
        # Validate language code format (should be 2-5 chars)
        if len(lang_code) < 2 or len(lang_code) > 7:
            # Default to English if invalid format
            lang_code = "en"
            
        # If the model returned a verbose response, try to extract just the code
        if len(lang_code) > 7:
            # Look for common language codes
            common_codes = ["en", "es", "fr", "de", "it", "pt", "ru", "zh", "ja", "ko", "ar"]
            for code in common_codes:
                if code in lang_code:
                    lang_code = code
                    break
            else:
                # Default to English if no valid code found
                lang_code = "en"
                
        # Update state with detected language
        state.detected_language = lang_code
        
        # Add a system message about the detected language
        system_msg = create_message(
            f"Detected language: {lang_code}",
            MessageType.SYSTEM,
            "system"
        )
        state.messages.append(system_msg)
        
        return state
    
    def get_language_name(self, language_code: str) -> str:
        """Get the human-readable language name from a language code.
        
        Args:
            language_code: ISO language code
            
        Returns:
            Human-readable language name
        """
        language_map = {
            "en": "English",
            "es": "Spanish",
            "fr": "French",
            "de": "German",
            "it": "Italian",
            "pt": "Portuguese",
            "ru": "Russian",
            "zh": "Chinese",
            "ja": "Japanese",
            "ko": "Korean",
            "ar": "Arabic"
        }
        
        return language_map.get(language_code.lower(), "Unknown") 