"""Agent nodes for the LangGraph workflow."""
from typing import Dict, List, Tuple, Any, Optional
from langchain_core.messages import HumanMessage

from src.models.class_models import GraphState, AgentRole, MessageType, CompanyDocument
from src.services.llm_service import LLMService
from src.services.vector_store_service import VectorStoreService
from src.utils.graph_utils import GraphManagerUtil
from src.agents.agent_utils import (
    create_agent_prompt,
    create_message,
    create_agent_response
)


class AgentNodes:
    """Nodes for the agent workflow graph."""
    
    def __init__(self):
        """Initialize agent nodes with services."""
        self.llm_service = LLMService()
        self.vector_store = VectorStoreService()
        self.graph_manager = GraphManagerUtil()
        
    def language_detection_agent(self, state: GraphState) -> GraphState:
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
    
    def retrieve_context(self, state: GraphState) -> GraphState:
        """Retrieve relevant context for the query.
        
        Args:
            state: Current graph state
            
        Returns:
            Updated graph state with context
        """
        if not state.human_query:
            return state
        
        # Check if this is a simple greeting or conversational query
        simple_query = self._is_simple_conversational_query(state.human_query)
        
        if simple_query:
            # For simple queries like greetings, don't retrieve documents
            # Just add a system message
            system_msg = create_message(
                f"Handling conversational query without document retrieval.",
                MessageType.SYSTEM,
                "system"
            )
            state.messages.append(system_msg)
            return state
            
        # Retrieve relevant documents
        documents = self.vector_store.search(state.human_query)
        
        # Update state with retrieved documents
        state.context = documents
        
        # Add a system message indicating context retrieval
        if documents:
            system_msg = create_message(
                f"Retrieved {len(documents)} relevant documents.",
                MessageType.SYSTEM,
                "system"
            )
            state.messages.append(system_msg)
            
        return state
        
    def _is_simple_conversational_query(self, query: str) -> bool:
        """Detect if a query is a simple greeting or conversational message.
        
        Args:
            query: User query
            
        Returns:
            Boolean indicating if this is a simple conversational query
        """
        # Convert to lowercase for case-insensitive matching
        query_lower = query.lower().strip()
        
        # Common greetings and simple queries in multiple languages
        greetings = [
            "hello", "hi", "hey", "howdy", "greetings", "good morning", "good afternoon", 
            "good evening", "hola", "buenos días", "buenas tardes", "buenas noches",
            "how are you", "how's it going", "what's up", "cómo estás", "qué tal",
            "thank you", "thanks", "gracias", "goodbye", "bye", "adiós", "chao"
        ]
        
        # Check for exact match or if query starts with any greeting
        for greeting in greetings:
            if query_lower == greeting or query_lower.startswith(greeting + " "):
                return True
        
        # More selective check for very short queries
        # Only treat single-word or very simple phrases as conversational
        words = query_lower.split()
        if len(words) <= 2:
            # But check if it contains any question-related keywords that indicate a real query
            question_indicators = ["what", "how", "why", "when", "where", "who", "which", 
                                   "qué", "cómo", "por qué", "cuándo", "dónde", "quién", "cuál"]
            
            # If it contains any question indicator, it might be a real query despite being short
            if not any(indicator in query_lower for indicator in question_indicators):
                return True
                
        return False
        
    def solution_architect_agent(self, state: GraphState) -> GraphState:
        """Solution Architect agent to evaluate technical requirements and design solutions.
        
        Args:
            state: Current graph state
            
        Returns:
            Updated graph state with solution architect response
        """
        # Set current agent
        state.current_agent = AgentRole.SOLUTION_ARCHITECT
        
        # Skip if node is disabled
        if self.graph_manager.should_skip_node(state, AgentRole.SOLUTION_ARCHITECT.value):
            return state
        
        # Create prompt for solution architect with detected language
        prompt = create_agent_prompt(
            AgentRole.SOLUTION_ARCHITECT,
            state.human_query or "",
            state.messages,
            state.context,
            state.detected_language
        )
        
        # Add relevant thoughts from shared memory if available
        if state.thought_vectors and state.human_query:
            similar_thoughts = self.graph_manager.find_similar_thoughts(
                state, 
                state.human_query, 
                threshold=0.6
            )
            
            if similar_thoughts:
                prompt += "\n\nRelevant thoughts from other agents:\n"
                for thought in similar_thoughts:
                    prompt += f"- {thought['thought']} (similarity: {thought['similarity']:.2f})\n"
        
        # Get response from LLM
        chain = self.llm_service.create_chain(
            "{input}",
        )
        response = chain.invoke({"input": prompt})
        
        # Create agent response
        agent_response = create_agent_response(
            content=response,
            agent_role=AgentRole.SOLUTION_ARCHITECT,
            sources=[doc.id for doc in state.context],
        )
        
        # Add thought vector to shared memory
        self.graph_manager.add_thought_to_shared_memory(
            state,
            AgentRole.SOLUTION_ARCHITECT,
            response
        )
        
        # Update state
        state.agent_responses[AgentRole.SOLUTION_ARCHITECT] = agent_response
        
        return state
        
    def technical_research_agent(self, state: GraphState) -> GraphState:
        """Technical Research agent with external knowledge capabilities.
        
        Args:
            state: Current graph state
            
        Returns:
            Updated graph state with technical research response
        """
        # Set current agent
        state.current_agent = AgentRole.TECHNICAL_RESEARCH
        
        # Skip if node is disabled
        if self.graph_manager.should_skip_node(state, AgentRole.TECHNICAL_RESEARCH.value):
            return state
        
        # Check if we need external knowledge
        external_docs = self._process_external_knowledge(state.human_query)
        
        # Add external knowledge to context
        if external_docs:
            state.context.extend(external_docs)
            
            # Add a system message about external sources
            system_msg = create_message(
                f"Retrieved information from {len(external_docs)} external sources.",
                MessageType.SYSTEM,
                "system"
            )
            state.messages.append(system_msg)
        
        # Create prompt for technical research with detected language
        prompt = create_agent_prompt(
            AgentRole.TECHNICAL_RESEARCH,
            state.human_query or "",
            state.messages,
            state.context,
            state.detected_language
        )
        
        # Add relevant thoughts from shared memory
        if state.thought_vectors and state.human_query:
            similar_thoughts = self.graph_manager.find_similar_thoughts(
                state, 
                state.human_query, 
                threshold=0.6
            )
            
            if similar_thoughts:
                prompt += "\n\nRelevant thoughts from other agents:\n"
                for thought in similar_thoughts:
                    prompt += f"- {thought['thought']} (similarity: {thought['similarity']:.2f})\n"
        
        # Get response from LLM
        chain = self.llm_service.create_chain(
            "{input}",
        )
        response = chain.invoke({"input": prompt})
        
        # Create agent response
        agent_response = create_agent_response(
            content=response,
            agent_role=AgentRole.TECHNICAL_RESEARCH,
            sources=[doc.id for doc in state.context],
        )
        
        # Add thought vector to shared memory
        self.graph_manager.add_thought_to_shared_memory(
            state,
            AgentRole.TECHNICAL_RESEARCH,
            response
        )
        
        # Update state
        state.agent_responses[AgentRole.TECHNICAL_RESEARCH] = agent_response
        
        return state
        
    def _process_external_knowledge(self, query: str) -> List[CompanyDocument]:
        """Process query for external knowledge needs.
        
        Args:
            query: User query
            
        Returns:
            List of CompanyDocument objects with external knowledge
        """
        from src.services.external_knowledge_service import ExternalKnowledgeService
        import logging
        
        logger = logging.getLogger(__name__)
        external_docs = []
        
        # Initialize external knowledge service if not already
        if not hasattr(self, "external_knowledge"):
            self.external_knowledge = ExternalKnowledgeService()
        
        # Extract entities and intents from query
        entities = self._extract_entities(query)
        intents = self._extract_intents(query)
        
        logger.info(f"Extracted entities: {entities}")
        logger.info(f"Extracted intents: {intents}")
        
        # Check weather intent
        if any(intent in ["weather", "clima", "temperatura"] for intent in intents):
            if "location" in entities:
                logger.info(f"Getting weather for location: {entities['location']}")
                weather_doc = self.external_knowledge.get_weather(entities["location"])
                external_docs.append(weather_doc)
        
        # Check wikipedia intent
        if any(intent in ["definition", "information", "wiki", "what is"] for intent in intents):
            if "topic" in entities:
                logger.info(f"Querying Wikipedia for topic: {entities['topic']}")
                wiki_doc = self.external_knowledge.query_wikipedia(entities["topic"])
                external_docs.append(wiki_doc)
        
        # Check news intent
        if any(intent in ["news", "noticias", "current events"] for intent in intents):
            if "topic" in entities:
                logger.info(f"Getting news for topic: {entities['topic']}")
                news_doc = self.external_knowledge.get_news(entities["topic"])
                external_docs.append(news_doc)
        
        # Check for technical stack intent
        if any(intent in ["technology", "stack", "framework", "library", "tool"] for intent in intents):
            if "topic" in entities:
                logger.info(f"Getting technical information for: {entities['topic']}")
                wiki_doc = self.external_knowledge.query_wikipedia(f"{entities['topic']} technology")
                external_docs.append(wiki_doc)
                
                # Also get news about this technology
                news_doc = self.external_knowledge.get_news(f"{entities['topic']} technology")
                external_docs.append(news_doc)
        
        return external_docs
    
    def _extract_entities(self, query: str) -> Dict[str, str]:
        """Extract entities from query using LLM.
        
        Args:
            query: User query
            
        Returns:
            Dictionary of entities
        """
        # Use LLM to extract entities
        prompt = """
        Extract entities from this query. Return a JSON with these possible keys:
        - location: any location mentioned (city, country, etc.)
        - topic: main topic, concept, or subject to search information about
        - time_period: any time period mentioned
        - technology: any technology, framework, or technical concept mentioned
        - language: programming languages mentioned
        - project_type: type of project discussed (web, mobile, AI, etc.)
        
        Query: {query}
        
        JSON:
        """
        
        chain = self.llm_service.create_chain(prompt)
        result = chain.invoke({"query": query})
        
        # Parse result (assuming JSON format)
        try:
            import json
            entities = json.loads(result)
            return entities
        except:
            # Fallback to simple keyword extraction if JSON parsing fails
            entities = {}
            
            # Simple location detection
            common_locations = ["madrid", "barcelona", "new york", "london", "paris"]
            for location in common_locations:
                if location.lower() in query.lower():
                    entities["location"] = location
                    break
            
            # Simple topic extraction (naive approach)
            if "about" in query.lower():
                parts = query.lower().split("about")
                if len(parts) > 1:
                    entities["topic"] = parts[1].strip()
            
            # Simple technology detection
            tech_keywords = ["python", "javascript", "react", "angular", "vue", "django", "flask", 
                           "node", "java", "spring", "docker", "kubernetes", "aws", "azure", 
                           "google cloud", "ai", "machine learning", "ml", "deep learning"]
            for tech in tech_keywords:
                if tech.lower() in query.lower():
                    entities["technology"] = tech
                    break
            
            return entities
    
    def _extract_intents(self, query: str) -> List[str]:
        """Extract intents from query.
        
        Args:
            query: User query
            
        Returns:
            List of intents
        """
        # Simple keyword-based intent detection
        intents = []
        query_lower = query.lower()
        
        # Technology intents
        if any(word in query_lower for word in ["technology", "tech stack", "framework", "library", "programming"]):
            intents.append("technology")
            
        # Project management intents
        if any(word in query_lower for word in ["timeline", "estimate", "project plan", "schedule", "team", "resources"]):
            intents.append("project_management")
            
        # Code review intents - AMPLIADOS
        code_keywords = ["code", "review", "bug", "issue", "error", "refactor", "function", "class", 
                         "variable", "algorithm", "programming", "developer", "debugging", "test", 
                         "python", "javascript", "java", "c++", "html", "css", "json", "api", 
                         "frontend", "backend", "desarrollador", "código", "función"]
                         
        if any(word in query_lower for word in code_keywords) or any(symbol in query for symbol in ["()", "{}", "[]", ";"]):
            intents.append("code_review")
            
        # Detección de fragmentos de código
        code_patterns = [
            "```", "def ", "function(", "class ", "import ", "from ", "var ", "let ", "const ", 
            "for(", "while(", "if(", "else{", "return ", "public ", "private "
        ]
        
        if any(pattern in query for pattern in code_patterns):
            intents.append("code_review")
            
        # Market analysis intents
        if any(word in query_lower for word in ["market", "competitor", "trend", "industry", "adoption"]):
            intents.append("market_analysis")
            
        # Data analysis intents
        if any(word in query_lower for word in ["data", "analytics", "metrics", "statistics", "dashboard"]):
            intents.append("data_analysis")
        
        # Information intents (for Wikipedia, etc.)
        if any(word in query_lower for word in ["what is", "definition", "explain", "how does", "information about"]):
            intents.append("information")
            
        # Weather intents
        if any(word in query_lower for word in ["weather", "temperature", "climate", "forecast"]):
            intents.append("weather")
            
        # News intents
        if any(word in query_lower for word in ["news", "latest", "recent", "update", "current events"]):
            intents.append("news")
            
        return intents
    
    def project_management_agent(self, state: GraphState) -> GraphState:
        """Project Management agent for estimating timelines and resources.
        
        Args:
            state: Current graph state
            
        Returns:
            Updated graph state with project management response
        """
        # Set current agent
        state.current_agent = AgentRole.PROJECT_MANAGEMENT
        
        # Create prompt for project management
        prompt = create_agent_prompt(
            AgentRole.PROJECT_MANAGEMENT,
            state.human_query or "",
            state.messages,
            state.context
        )
        
        # Get response from LLM
        chain = self.llm_service.create_chain(
            "{input}",
        )
        response = chain.invoke({"input": prompt})
        
        # Create agent response
        agent_response = create_agent_response(
            content=response,
            agent_role=AgentRole.PROJECT_MANAGEMENT,
            sources=[doc.id for doc in state.context],
        )
        
        # Update state
        state.agent_responses[AgentRole.PROJECT_MANAGEMENT] = agent_response
        
        return state
    
    def code_review_agent(self, state: GraphState) -> GraphState:
        """Code Review agent for analyzing code quality and suggesting improvements.
        
        Args:
            state: Current graph state
            
        Returns:
            Updated graph state with code review response
        """
        # Set current agent
        state.current_agent = AgentRole.CODE_REVIEW
        
        # Create prompt for code review
        prompt = create_agent_prompt(
            AgentRole.CODE_REVIEW,
            state.human_query or "",
            state.messages,
            state.context
        )
        
        # Get response from LLM
        chain = self.llm_service.create_chain(
            "{input}",
        )
        response = chain.invoke({"input": prompt})
        
        # Create agent response
        agent_response = create_agent_response(
            content=response,
            agent_role=AgentRole.CODE_REVIEW,
            sources=[doc.id for doc in state.context],
        )
        
        # Update state
        state.agent_responses[AgentRole.CODE_REVIEW] = agent_response
        
        return state
    
    def market_analysis_agent(self, state: GraphState) -> GraphState:
        """Market Analysis agent for analyzing technology trends and competition.
        
        Args:
            state: Current graph state
            
        Returns:
            Updated graph state with market analysis response
        """
        # Set current agent
        state.current_agent = AgentRole.MARKET_ANALYSIS
        
        # Create prompt for market analysis
        prompt = create_agent_prompt(
            AgentRole.MARKET_ANALYSIS,
            state.human_query or "",
            state.messages,
            state.context
        )
        
        # Get response from LLM
        chain = self.llm_service.create_chain(
            "{input}",
        )
        response = chain.invoke({"input": prompt})
        
        # Create agent response
        agent_response = create_agent_response(
            content=response,
            agent_role=AgentRole.MARKET_ANALYSIS,
            sources=[doc.id for doc in state.context],
        )
        
        # Update state
        state.agent_responses[AgentRole.MARKET_ANALYSIS] = agent_response
        
        return state
    
    def data_analysis_agent(self, state: GraphState) -> GraphState:
        """Data Analysis agent for interpreting data and extracting insights.
        
        Args:
            state: Current graph state
            
        Returns:
            Updated graph state with data analysis response
        """
        # Set current agent
        state.current_agent = AgentRole.DATA_ANALYSIS
        
        # Create prompt for data analysis
        prompt = create_agent_prompt(
            AgentRole.DATA_ANALYSIS,
            state.human_query or "",
            state.messages,
            state.context
        )
        
        # Get response from LLM
        chain = self.llm_service.create_chain(
            "{input}",
        )
        response = chain.invoke({"input": prompt})
        
        # Create agent response
        agent_response = create_agent_response(
            content=response,
            agent_role=AgentRole.DATA_ANALYSIS,
            sources=[doc.id for doc in state.context],
        )
        
        # Update state
        state.agent_responses[AgentRole.DATA_ANALYSIS] = agent_response
        
        return state
    
    def client_communication_agent(self, state: GraphState) -> GraphState:
        """Client Communication agent for final response generation.
        
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
            return self._streaming_client_communication(state)
        
        # Collect all thoughts and responses from previous agents
        previous_responses = []
        for agent_role, response in state.agent_responses.items():
            if agent_role != AgentRole.CLIENT_COMMUNICATION and response.content:
                previous_responses.append(f"{agent_role.value}: {response.content}")
        
        # Use the thought vectors to find the most relevant responses
        if state.thought_vectors and state.human_query:
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
        )
        response = chain.invoke({"input": prompt})
        
        # Create agent response
        agent_response = create_agent_response(
            content=response,
            agent_role=AgentRole.CLIENT_COMMUNICATION,
            sources=[doc.id for doc in state.context],
        )
        
        # Set final response in the state
        state.final_response = response
        
        # Update state
        state.agent_responses[AgentRole.CLIENT_COMMUNICATION] = agent_response
        
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

    def process_user_query(self, query: str, conversation_history: Optional[List[Dict]] = None, streaming: bool = False) -> Dict[str, Any]:
        """Process a user query through the agent workflow.
        
        Args:
            query: User query
            conversation_history: Previous conversation messages
            streaming: Whether to stream responses
            
        Returns:
            Dictionary with agent responses and final response
        """
        # Create initial state
        state = GraphState(
            human_query=query,
            is_streaming=streaming
        )
        
        # Convert conversation history to messages if provided
        if conversation_history:
            for msg in conversation_history:
                if msg.get("type") == "human":
                    state.messages.append(create_message(
                        msg.get("content", ""),
                        MessageType.HUMAN,
                        msg.get("sender", "user")
                    ))
                elif msg.get("type") == "ai":
                    state.messages.append(create_message(
                        msg.get("content", ""),
                        MessageType.AI,
                        msg.get("sender", "assistant")
                    ))
        
        # Add the current query as a message
        state.messages.append(create_message(
            query,
            MessageType.HUMAN,
            "user"
        ))
        
        # Set up the graph manager for this query
        self.graph_manager.initialize(query)
        
        # Process the query through the workflow
        try:
            # Get the graph - used to be a simple function call:
            # from src.graph.agent_graph import create_agent_graph
            # graph = create_agent_graph(self)
            
            # Now with dynamic agent graph
            from src.graph.agent_graph import DynamicAgentGraph
            dynamic_graph = DynamicAgentGraph(self)
            graph = dynamic_graph.get_compiled_graph()
            
            # Execute the graph
            result = graph.invoke(state)
            
            # Handle different result types from LangGraph
            # LangGraph 0.0.x returned a GraphState object directly
            # LangGraph 0.1.x returns an AddableValuesDict which needs special handling
            
            # Create response object
            response = {
                "agent_responses": {},
                "final_response": ""
            }
            
            # Determine the type of result and extract data accordingly
            if hasattr(result, 'get') and callable(getattr(result, 'get')):
                # It's an AddableValuesDict or similar dict-like object
                final_response = result.get('final_response', "")
                agent_responses = result.get('agent_responses', {})
                detected_language = result.get('detected_language', "en")
            elif isinstance(result, dict):
                # It's a regular dictionary
                final_response = result.get('final_response', "")
                agent_responses = result.get('agent_responses', {})
                detected_language = result.get('detected_language', "en")
            else:
                # Assume it's a GraphState object (older LangGraph versions)
                final_response = getattr(result, 'final_response', "")
                agent_responses = getattr(result, 'agent_responses', {})
                detected_language = getattr(result, 'detected_language', "en")
            
            # Set final response
            response["final_response"] = final_response
            
            # Add individual agent responses
            for role, agent_response in agent_responses.items():
                if hasattr(agent_response, 'content'):
                    # It's an AgentResponse object
                    response["agent_responses"][role] = {
                        "content": agent_response.content,
                        "confidence": getattr(agent_response, 'confidence', 1.0),
                        "sources": getattr(agent_response, 'sources', [])
                    }
                elif isinstance(agent_response, dict):
                    # It's already a dictionary
                    response["agent_responses"][role] = agent_response
            
            # Add detected language info
            response["detected_language"] = detected_language
            
            # If we don't have a final response yet, use a default message based on the detected language
            if not response["final_response"]:
                if detected_language == "es":
                    response["final_response"] = "Lo siento, no pude generar una respuesta completa. ¿Podrías reformular tu pregunta?"
                else:
                    response["final_response"] = "I'm sorry, I couldn't generate a complete response. Could you please rephrase your question?"
                
            return response
            
        except Exception as e:
            import traceback
            print(f"Error in agent workflow: {e}")
            print(traceback.format_exc())
            return {
                "agent_responses": {},
                "final_response": f"Lo siento, ocurrió un error al procesar tu consulta. Por favor, inténtalo de nuevo. Error: {str(e)}",
                "detected_language": getattr(state, 'detected_language', "es")
            }
    
    def _streaming_client_communication(self, state: GraphState) -> GraphState:
        """Versión streaming del agente de comunicación con el cliente.
        
        Args:
            state: Current graph state
            
        Returns:
            Updated graph state with partial responses
        """
        # Create prompt for client communication 
        prompt = create_agent_prompt(
            AgentRole.CLIENT_COMMUNICATION,
            state.human_query or "",
            state.messages,
            state.context
        )
        
        # Include all other agent responses in the prompt
        agent_responses_text = "Previous Agent Insights:\n"
        for role, response in state.agent_responses.items():
            if role != AgentRole.CLIENT_COMMUNICATION:
                agent_responses_text += f"\n--- {role} Agent ---\n{response.content}\n"
        
        # Integrate insights into the prompt
        full_prompt = f"{prompt}\n\n{agent_responses_text}\n\nPlease formulate a comprehensive final response to the user's query."
        
        # Generar respuesta incremental usando streaming
        try:
            # Obtener modelo LLM con capacidad de streaming
            streaming_model = self.llm_service.chat_model
            
            # Crear un mensaje para el chat
            from langchain_core.messages import HumanMessage
            message = HumanMessage(content=full_prompt)
            
            # Inicializar respuesta vacía
            full_response = ""
            partial_responses = []
            
            # Procesar el stream de tokens
            for chunk in streaming_model.stream([message]):
                if hasattr(chunk, 'content'):
                    content = chunk.content
                else:
                    content = str(chunk)
                    
                if content:
                    # Acumular respuesta completa
                    full_response += content
                    
                    # Crear mensaje parcial
                    partial_message = create_message(
                        content=full_response,
                        message_type=MessageType.STREAM,
                        sender=str(AgentRole.CLIENT_COMMUNICATION)
                    )
                    partial_message.is_partial = True
                    
                    # Añadir a la lista de mensajes parciales
                    partial_responses.append(partial_message)
                    
                    # Crear respuesta de agente parcial
                    partial_agent_response = create_agent_response(
                        content=full_response,
                        agent_role=AgentRole.CLIENT_COMMUNICATION,
                        sources=[doc.id for doc in state.context],
                    )
                    partial_agent_response.is_partial = True
                    
                    # Actualizar estado con respuesta parcial
                    state.partial_responses[AgentRole.CLIENT_COMMUNICATION] = partial_agent_response
            
            # Una vez completado el streaming, actualizar con la respuesta final
            agent_response = create_agent_response(
                content=full_response,
                agent_role=AgentRole.CLIENT_COMMUNICATION,
                sources=[doc.id for doc in state.context],
            )
            
            # Update state
            state.agent_responses[AgentRole.CLIENT_COMMUNICATION] = agent_response
            state.final_response = full_response
            
            # Añadir mensajes parciales al historial si se desea
            state.messages.extend(partial_responses)
            
        except Exception as e:
            # En caso de error, crear una respuesta de error
            error_message = f"Error al generar respuesta en streaming: {str(e)}"
            
            agent_response = create_agent_response(
                content=error_message,
                agent_role=AgentRole.CLIENT_COMMUNICATION,
                sources=[],
            )
            
            # Update state
            state.agent_responses[AgentRole.CLIENT_COMMUNICATION] = agent_response
            state.final_response = error_message
        
        return state
    
    def should_use_code_review(self, state: GraphState) -> str:
        """Determine if the Code Review agent should be used.
        
        Args:
            state: Current graph state
            
        Returns:
            Decision string ('use_code_review' or 'skip_code_review')
        """
        # Extraer los intents de la consulta
        intents = self._extract_intents(state.human_query or "")
        
        # Buscar palabras clave técnicas en la consulta
        query_lower = (state.human_query or "").lower()
        technical_keywords = ["develop", "programm", "cod", "software", "app", "application", 
                             "framework", "library", "function", "algorithm", "api", "database",
                             "backend", "frontend", "full-stack", "system"]
        
        # Activar el revisor de código si:
        # 1. Hay intent de code_review
        # 2. O es una consulta relacionada con tecnología
        # 3. O contiene alguna palabra clave técnica
        # 4. O la consulta está en nuestra lista de preguntas de prueba para revisor de código
        # 5. O es una consulta compleja técnica
        if ("code_review" in intents or
            "technology" in intents or
            any(keyword in query_lower for keyword in technical_keywords) or
            len(query_lower) > 200):  # Para consultas largas y complejas que pueden contener aspectos técnicos
            
            print("Activando revisor de código para la consulta:", state.human_query)
            return "use_code_review"
        else:
            return "skip_code_review"
    
    def should_use_project_management(self, state: GraphState) -> str:
        """Determine if the Project Management agent should be used.
        
        Args:
            state: Current graph state
            
        Returns:
            Decision string ('use_project_management' or 'skip_project_management')
        """
        intents = self._extract_intents(state.human_query or "")
        
        if "project_management" in intents:
            return "use_project_management"
        else:
            return "skip_project_management"
    
    def should_use_market_analysis(self, state: GraphState) -> str:
        """Determine if the Market Analysis agent should be used.
        
        Args:
            state: Current graph state
            
        Returns:
            Decision string ('use_market_analysis' or 'skip_market_analysis')
        """
        intents = self._extract_intents(state.human_query or "")
        
        if "market_analysis" in intents:
            return "use_market_analysis"
        else:
            return "skip_market_analysis"
    
    def should_use_data_analysis(self, state: GraphState) -> str:
        """Determine if the Data Analysis agent should be used.
        
        Args:
            state: Current graph state
            
        Returns:
            Decision string ('use_data_analysis' or 'skip_data_analysis')
        """
        intents = self._extract_intents(state.human_query or "")
        
        if "data_analysis" in intents:
            return "use_data_analysis"
        else:
            return "skip_data_analysis"
    
    def digital_transformation_agent(self, state: GraphState) -> GraphState:
        """Digital Transformation agent for evaluating digital maturity and proposing strategies.
        
        Args:
            state: Current graph state
            
        Returns:
            Updated graph state with digital transformation assessment
        """
        # Set current agent
        state.current_agent = AgentRole.DIGITAL_TRANSFORMATION
        
        # Skip if node is disabled
        if self.graph_manager.should_skip_node(state, AgentRole.DIGITAL_TRANSFORMATION.value):
            return state
        
        # Create prompt for digital transformation
        prompt = create_agent_prompt(
            AgentRole.DIGITAL_TRANSFORMATION,
            state.human_query or "",
            state.messages,
            state.context
        )
        
        # Add relevant thoughts from shared memory if available
        if state.thought_vectors and state.human_query:
            similar_thoughts = self.graph_manager.find_similar_thoughts(
                state, 
                state.human_query,
                threshold=0.6
            )
            
            if similar_thoughts:
                prompt += "\n\nRelevant thoughts from other agents:\n"
                for thought in similar_thoughts:
                    prompt += f"- {thought['thought']} (similarity: {thought['similarity']:.2f})\n"
        
        # Get response from LLM
        chain = self.llm_service.create_chain(
            "{input}",
        )
        response = chain.invoke({"input": prompt})
        
        # Create agent response
        agent_response = create_agent_response(
            content=response,
            agent_role=AgentRole.DIGITAL_TRANSFORMATION,
            sources=[doc.id for doc in state.context],
        )
        
        # Add thought vector to shared memory
        self.graph_manager.add_thought_to_shared_memory(
            state,
            AgentRole.DIGITAL_TRANSFORMATION,
            response
        )
        
        # Update state
        state.agent_responses[AgentRole.DIGITAL_TRANSFORMATION] = agent_response
        
        return state
        
    def cloud_architecture_agent(self, state: GraphState) -> GraphState:
        """Cloud Architecture agent for designing cloud solutions and migration strategies.
        
        Args:
            state: Current graph state
            
        Returns:
            Updated graph state with cloud architecture recommendations
        """
        # Set current agent
        state.current_agent = AgentRole.CLOUD_ARCHITECTURE
        
        # Skip if node is disabled
        if self.graph_manager.should_skip_node(state, AgentRole.CLOUD_ARCHITECTURE.value):
            return state
        
        # Create prompt for cloud architecture
        prompt = create_agent_prompt(
            AgentRole.CLOUD_ARCHITECTURE,
            state.human_query or "",
            state.messages,
            state.context
        )
        
        # Add relevant thoughts from shared memory if available
        if state.thought_vectors and state.human_query:
            similar_thoughts = self.graph_manager.find_similar_thoughts(
                state, 
                state.human_query,
                threshold=0.6
            )
            
            if similar_thoughts:
                prompt += "\n\nRelevant thoughts from other agents:\n"
                for thought in similar_thoughts:
                    prompt += f"- {thought['thought']} (similarity: {thought['similarity']:.2f})\n"
                    
        # Get response from LLM
        chain = self.llm_service.create_chain(
            "{input}",
        )
        response = chain.invoke({"input": prompt})
        
        # Create agent response
        agent_response = create_agent_response(
            content=response,
            agent_role=AgentRole.CLOUD_ARCHITECTURE,
            sources=[doc.id for doc in state.context],
        )
        
        # Add thought vector to shared memory
        self.graph_manager.add_thought_to_shared_memory(
            state,
            AgentRole.CLOUD_ARCHITECTURE,
            response
        )
        
        # Update state
        state.agent_responses[AgentRole.CLOUD_ARCHITECTURE] = agent_response
        
        return state
        
    def cyber_security_agent(self, state: GraphState) -> GraphState:
        """Cyber Security agent for assessing security risks and recommending controls.
        
        Args:
            state: Current graph state
            
        Returns:
            Updated graph state with security recommendations
        """
        # Set current agent
        state.current_agent = AgentRole.CYBER_SECURITY
        
        # Skip if node is disabled
        if self.graph_manager.should_skip_node(state, AgentRole.CYBER_SECURITY.value):
            return state
        
        # Create prompt for cyber security
        prompt = create_agent_prompt(
            AgentRole.CYBER_SECURITY,
            state.human_query or "",
            state.messages,
            state.context
        )
        
        # Add relevant thoughts from shared memory if available
        if state.thought_vectors and state.human_query:
            similar_thoughts = self.graph_manager.find_similar_thoughts(
                state, 
                state.human_query,
                threshold=0.6
            )
            
            if similar_thoughts:
                prompt += "\n\nRelevant thoughts from other agents:\n"
                for thought in similar_thoughts:
                    prompt += f"- {thought['thought']} (similarity: {thought['similarity']:.2f})\n"
                    
        # Get response from LLM
        chain = self.llm_service.create_chain(
            "{input}",
        )
        response = chain.invoke({"input": prompt})
        
        # Create agent response
        agent_response = create_agent_response(
            content=response,
            agent_role=AgentRole.CYBER_SECURITY,
            sources=[doc.id for doc in state.context],
        )
        
        # Add thought vector to shared memory
        self.graph_manager.add_thought_to_shared_memory(
            state,
            AgentRole.CYBER_SECURITY,
            response
        )
        
        # Update state
        state.agent_responses[AgentRole.CYBER_SECURITY] = agent_response
        
        return state
        
    def agile_methodologies_agent(self, state: GraphState) -> GraphState:
        """Agile Methodologies agent for recommending agile practices and transformations.
        
        Args:
            state: Current graph state
            
        Returns:
            Updated graph state with agile methodology recommendations
        """
        # Set current agent
        state.current_agent = AgentRole.AGILE_METHODOLOGIES
        
        # Skip if node is disabled
        if self.graph_manager.should_skip_node(state, AgentRole.AGILE_METHODOLOGIES.value):
            return state
        
        # Create prompt for agile methodologies
        prompt = create_agent_prompt(
            AgentRole.AGILE_METHODOLOGIES,
            state.human_query or "",
            state.messages,
            state.context
        )
        
        # Add relevant thoughts from shared memory if available
        if state.thought_vectors and state.human_query:
            similar_thoughts = self.graph_manager.find_similar_thoughts(
                state, 
                state.human_query,
                threshold=0.6
            )
            
            if similar_thoughts:
                prompt += "\n\nRelevant thoughts from other agents:\n"
                for thought in similar_thoughts:
                    prompt += f"- {thought['thought']} (similarity: {thought['similarity']:.2f})\n"
                    
        # Get response from LLM
        chain = self.llm_service.create_chain(
            "{input}",
        )
        response = chain.invoke({"input": prompt})
        
        # Create agent response
        agent_response = create_agent_response(
            content=response,
            agent_role=AgentRole.AGILE_METHODOLOGIES,
            sources=[doc.id for doc in state.context],
        )
        
        # Add thought vector to shared memory
        self.graph_manager.add_thought_to_shared_memory(
            state,
            AgentRole.AGILE_METHODOLOGIES,
            response
        )
        
        # Update state
        state.agent_responses[AgentRole.AGILE_METHODOLOGIES] = agent_response
        
        return state
        
    def systems_integration_agent(self, state: GraphState) -> GraphState:
        """Systems Integration agent for designing integration solutions.
        
        Args:
            state: Current graph state
            
        Returns:
            Updated graph state with systems integration recommendations
        """
        # Set current agent
        state.current_agent = AgentRole.SYSTEMS_INTEGRATION
        
        # Skip if node is disabled
        if self.graph_manager.should_skip_node(state, AgentRole.SYSTEMS_INTEGRATION.value):
            return state
        
        # Create prompt for systems integration
        prompt = create_agent_prompt(
            AgentRole.SYSTEMS_INTEGRATION,
            state.human_query or "",
            state.messages,
            state.context
        )
        
        # Add relevant thoughts from shared memory if available
        if state.thought_vectors and state.human_query:
            similar_thoughts = self.graph_manager.find_similar_thoughts(
                state, 
                state.human_query,
                threshold=0.6
            )
            
            if similar_thoughts:
                prompt += "\n\nRelevant thoughts from other agents:\n"
                for thought in similar_thoughts:
                    prompt += f"- {thought['thought']} (similarity: {thought['similarity']:.2f})\n"
                    
        # Get response from LLM
        chain = self.llm_service.create_chain(
            "{input}",
        )
        response = chain.invoke({"input": prompt})
        
        # Create agent response
        agent_response = create_agent_response(
            content=response,
            agent_role=AgentRole.SYSTEMS_INTEGRATION,
            sources=[doc.id for doc in state.context],
        )
        
        # Add thought vector to shared memory
        self.graph_manager.add_thought_to_shared_memory(
            state,
            AgentRole.SYSTEMS_INTEGRATION,
            response
        )
        
        # Update state
        state.agent_responses[AgentRole.SYSTEMS_INTEGRATION] = agent_response
        
        return state

    # Métodos para decidir si usar los nuevos agentes especializados
    
    def should_use_digital_transformation(self, state: GraphState) -> str:
        """Determine if the Digital Transformation agent should be used.
        
        Args:
            state: Current graph state
            
        Returns:
            Decision string ('use_digital_transformation' or 'skip_digital_transformation')
        """
        query_lower = (state.human_query or "").lower()
        
        # Buscar términos relacionados con transformación digital
        digital_keywords = [
            "digital transformation", "digital maturity", "digital strategy", 
            "digitalization", "digital initiative", "digital roadmap", "digital adoption",
            "transformación digital", "madurez digital", "digitalización"
        ]
        
        if any(keyword in query_lower for keyword in digital_keywords):
            return "use_digital_transformation"
        else:
            return "skip_digital_transformation"
    
    def should_use_cloud_architecture(self, state: GraphState) -> str:
        """Determine if the Cloud Architecture agent should be used.
        
        Args:
            state: Current graph state
            
        Returns:
            Decision string ('use_cloud_architecture' or 'skip_cloud_architecture')
        """
        query_lower = (state.human_query or "").lower()
        
        # Buscar términos relacionados con arquitectura cloud
        cloud_keywords = [
            "cloud", "aws", "azure", "gcp", "google cloud", "migration", "iaas", "paas", 
            "saas", "serverless", "container", "kubernetes", "docker", "microservices",
            "nube", "migración", "infraestructura", "contenedores"
        ]
        
        if any(keyword in query_lower for keyword in cloud_keywords):
            return "use_cloud_architecture"
        else:
            return "skip_cloud_architecture"
    
    def should_use_cyber_security(self, state: GraphState) -> str:
        """Determine if the Cyber Security agent should be used.
        
        Args:
            state: Current graph state
            
        Returns:
            Decision string ('use_cyber_security' or 'skip_cyber_security')
        """
        query_lower = (state.human_query or "").lower()
        
        # Buscar términos relacionados con seguridad
        security_keywords = [
            "security", "vulnerability", "threat", "risk", "hack", "breach", "compliance", 
            "authentication", "authorization", "encryption", "firewall", "malware", "virus",
            "seguridad", "vulnerabilidad", "amenaza", "riesgo", "ataque", "protección"
        ]
        
        if any(keyword in query_lower for keyword in security_keywords):
            return "use_cyber_security"
        else:
            return "skip_cyber_security"
    
    def should_use_agile_methodologies(self, state: GraphState) -> str:
        """Determine if the Agile Methodologies agent should be used.
        
        Args:
            state: Current graph state
            
        Returns:
            Decision string ('use_agile_methodologies' or 'skip_agile_methodologies')
        """
        query_lower = (state.human_query or "").lower()
        
        # Buscar términos relacionados con metodologías ágiles
        agile_keywords = [
            "agile", "scrum", "kanban", "sprint", "backlog", "retrospective", "standup", 
            "user story", "product owner", "scrum master", "extreme programming", "xp",
            "ágil", "metodología", "ceremonia", "historia de usuario", "dueño de producto"
        ]
        
        if any(keyword in query_lower for keyword in agile_keywords):
            return "use_agile_methodologies"
        else:
            return "skip_agile_methodologies"
    
    def should_use_systems_integration(self, state: GraphState) -> str:
        """Determine if the Systems Integration agent should be used.
        
        Args:
            state: Current graph state
            
        Returns:
            Decision string ('use_systems_integration' or 'skip_systems_integration')
        """
        query_lower = (state.human_query or "").lower()
        
        # Buscar términos relacionados con integración de sistemas
        integration_keywords = [
            "integration", "api", "middleware", "interface", "connect", "interoperability", 
            "data exchange", "soa", "esb", "etl", "webhook", "microservice", "message queue",
            "integración", "conectar", "interfaz", "interoperabilidad", "intercambio de datos"
        ]
        
        if any(keyword in query_lower for keyword in integration_keywords):
            return "use_systems_integration"
        else:
            return "skip_systems_integration" 