"""Client Communication agent for the LangGraph workflow."""
from typing import Dict, List, Any, Optional
from langchain_core.messages import HumanMessage

from src.models.class_models import GraphState, AgentRole, MessageType, CompanyDocument
from src.services.llm_service import LLMService
from src.services.vector_store_service import VectorStoreService
from src.utils.graph_utils import GraphManagerUtil
from src.agents.base.agent_utils import (
    create_agent_prompt,
    create_message,
    create_agent_response
)


class ClientCommunicationAgent:
    """Client Communication agent for final response generation."""
    
    def __init__(self, llm_service: LLMService, vector_store: VectorStoreService, graph_manager: GraphManagerUtil):
        """Initialize the Client Communication agent with services.
        
        Args:
            llm_service: LLM service for generating agent responses
            vector_store: Vector store service for context retrieval
            graph_manager: Graph manager for workflow utilities
        """
        self.llm_service = llm_service
        self.vector_store = vector_store
        self.graph_manager = graph_manager
        
    def process(self, state: GraphState) -> GraphState:
        """Process the current state with the Client Communication agent.
        
        Args:
            state: Current graph state
            
        Returns:
            Updated graph state with client communication response
        """
        # Set current agent
        state.current_agent = AgentRole.CLIENT_COMMUNICATION
        
        # Skip if node is disabled
        if self.graph_manager.should_skip_node(state, AgentRole.CLIENT_COMMUNICATION.value):
            return state
        
        # Handle streaming mode
        if state.is_streaming:
            return self._streaming_process(state)
        
        # Collect all thoughts and responses from previous agents
        previous_responses = []
        for agent_role, response in state.agent_responses.items():
            if agent_role != AgentRole.CLIENT_COMMUNICATION.value and response.content:
                # Use agent_role directly as it's already a string
                previous_responses.append(f"{agent_role}: {response.content}")
        
        # Use the thought vectors to find the most relevant responses
        if hasattr(state, 'thought_vectors') and state.thought_vectors and state.human_query:
            relevant_thoughts = self.graph_manager.find_similar_thoughts(
                state, 
                state.human_query, 
                threshold=0.5,
                max_results=5
            )
            
            if relevant_thoughts:
                previous_responses.append("\nMost relevant insights from agents:")
                for thought in relevant_thoughts:
                    previous_responses.append(f"- {thought['thought']} (similarity: {thought['similarity']:.2f})")
        
        # Combine responses
        combined_insights = "\n\n".join(previous_responses)
        
        # Create a virtual document with combined insights
        if combined_insights:
            insight_doc = CompanyDocument(
                id="agent_insights",
                title="Combined Agent Insights",
                content=combined_insights,
                document_type="internal",
                source="agent_collaboration"
            )
            
            # Add to context
            if insight_doc not in state.context:
                state.context.append(insight_doc)
        
        # Create prompt for client communication with detected language
        prompt = create_agent_prompt(
            AgentRole.CLIENT_COMMUNICATION,
            state.human_query or "",
            state.messages,
            state.context,
            state.detected_language
        )
        
        # Add a reminder to respond in the same language as the user
        lang_name = self._get_language_name(state.detected_language)
        prompt += f"\n\nIMPORTANT REMINDER: You must respond in {lang_name} ({state.detected_language}) as this is the language used by the user."
        
        # Get response from LLM
        chain = self.llm_service.create_chain(
            "{input}",
            streaming=False
        )
        response = chain.invoke({"input": prompt})
        
        # Create agent response
        agent_response = create_agent_response(
            response,
            AgentRole.CLIENT_COMMUNICATION,
            sources=[doc.id for doc in state.context if hasattr(doc, 'id')]
        )
        
        # Set final response in the state
        state.final_response = response
        
        # Update state
        state.agent_responses[AgentRole.CLIENT_COMMUNICATION.value] = agent_response
        
        # Add message to conversation history
        ai_msg = create_message(
            response,
            MessageType.AI,
            f"agent.{AgentRole.CLIENT_COMMUNICATION.value}"
        )
        state.messages.append(ai_msg)
        
        return state
    
    def _streaming_process(self, state: GraphState) -> GraphState:
        """Handle streaming response generation.
        
        Args:
            state: Current graph state
            
        Returns:
            Updated graph state with streaming response
        """
        # Create prompt for client communication 
        prompt = create_agent_prompt(
            AgentRole.CLIENT_COMMUNICATION,
            state.human_query or "",
            state.messages,
            state.context,
            state.detected_language
        )
        
        # Include all other agent responses in the prompt
        agent_responses_text = "Previous Agent Insights:\n"
        for role, response in state.agent_responses.items():
            if role != AgentRole.CLIENT_COMMUNICATION.value:
                agent_responses_text += f"\n--- {role} Agent ---\n{response.content}\n"
        
        # Integrate insights into the prompt
        full_prompt = f"{prompt}\n\n{agent_responses_text}\n\nPlease formulate a comprehensive final response to the user's query."
        
        # Add language reminder
        lang_name = self._get_language_name(state.detected_language)
        full_prompt += f"\n\nIMPORTANT REMINDER: You must respond in {lang_name} ({state.detected_language}) as this is the language used by the user."
        
        # Generate incremental response using streaming
        try:
            # Get LLM model with streaming capability
            streaming_model = self.llm_service.chat_model
            
            # Create a message for the chat
            message = HumanMessage(content=full_prompt)
            
            # Initialize empty response
            full_response = ""
            partial_responses = []
            
            # Process the token stream
            for chunk in streaming_model.stream([message]):
                if hasattr(chunk, 'content'):
                    content = chunk.content
                else:
                    content = str(chunk)
                    
                if content:
                    # Accumulate complete response
                    full_response += content
                    
                    # Create partial message
                    partial_message = create_message(
                        content=full_response,
                        message_type=MessageType.STREAM,
                        sender=str(AgentRole.CLIENT_COMMUNICATION)
                    )
                    
                    # Add to partial messages list
                    partial_responses.append(partial_message)
                    
                    # Create partial agent response
                    partial_agent_response = create_agent_response(
                        content=full_response,
                        agent_role=AgentRole.CLIENT_COMMUNICATION,
                        sources=[doc.id for doc in state.context if hasattr(doc, 'id')],
                        is_partial=True
                    )
                    
                    # Update state with partial response
                    state.partial_responses[AgentRole.CLIENT_COMMUNICATION.value] = partial_agent_response
            
            # Once streaming is complete, update with final response
            agent_response = create_agent_response(
                content=full_response,
                agent_role=AgentRole.CLIENT_COMMUNICATION,
                sources=[doc.id for doc in state.context if hasattr(doc, 'id')]
            )
            
            # Update state
            state.agent_responses[AgentRole.CLIENT_COMMUNICATION.value] = agent_response
            state.final_response = full_response
            
            # Add partial messages to history if desired
            # state.messages.extend(partial_responses)
            
            # Add final message to conversation history
            ai_msg = create_message(
                full_response,
                MessageType.AI,
                f"agent.{AgentRole.CLIENT_COMMUNICATION.value}"
            )
            state.messages.append(ai_msg)
            
        except Exception as e:
            # In case of error, create an error response
            error_message = f"Error generating streaming response: {str(e)}"
            
            agent_response = create_agent_response(
                content=error_message,
                agent_role=AgentRole.CLIENT_COMMUNICATION,
                sources=[]
            )
            
            # Update state
            state.agent_responses[AgentRole.CLIENT_COMMUNICATION.value] = agent_response
            state.final_response = error_message
            
            # Add error message to conversation history
            error_msg = create_message(
                error_message,
                MessageType.SYSTEM,
                "system"
            )
            state.messages.append(error_msg)
        
        return state
    
    def _get_language_name(self, language_code: str) -> str:
        """Get the full language name from the ISO code.
        
        Args:
            language_code: ISO language code
            
        Returns:
            Full language name
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
        
        return language_map.get(language_code, "the detected language") 
