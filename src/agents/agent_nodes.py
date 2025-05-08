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
        
        # Create prompt for solution architect
        prompt = create_agent_prompt(
            AgentRole.SOLUTION_ARCHITECT,
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
        
        # Create prompt for technical research
        prompt = create_agent_prompt(
            AgentRole.TECHNICAL_RESEARCH,
            state.human_query or "",
            state.messages,
            state.context
        )
        
        # Add relevant thoughts from shared memory if available
        if state.thought_vectors:
            similar_thoughts = self.graph_manager.find_similar_thoughts(
                state, 
                state.human_query or "", 
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
        """Client Communication agent to format the final response.
        
        Args:
            state: Current graph state
            
        Returns:
            Updated graph state with final response
        """
        # Set current agent
        state.current_agent = AgentRole.CLIENT_COMMUNICATION
        
        # Check if streaming is enabled
        if state.is_streaming:
            return self._streaming_client_communication(state)
        
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
        
        # Get response from LLM
        chain = self.llm_service.create_chain(
            "{input}",
        )
        response = chain.invoke({"input": full_prompt})
        
        # Create agent response
        agent_response = create_agent_response(
            content=response,
            agent_role=AgentRole.CLIENT_COMMUNICATION,
            sources=[doc.id for doc in state.context],
        )
        
        # Update state
        state.agent_responses[AgentRole.CLIENT_COMMUNICATION] = agent_response
        state.final_response = response
        
        return state
    
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
    
    def process_user_query(self, query: str, conversation_history: Optional[List[Dict]] = None, streaming: bool = False) -> Dict[str, Any]:
        """Process a user query through the agent workflow.
        
        Args:
            query: User query text
            conversation_history: Optional list of previous conversation messages
            streaming: Whether to enable streaming responses
            
        Returns:
            Dictionary with the processing results
        """
        # Initialize graph state
        state = GraphState(
            human_query=query,
            is_streaming=streaming
        )
        
        # Convert conversation history to Message objects
        if conversation_history:
            for message in conversation_history:
                msg_type = message.get("type", MessageType.HUMAN)
                msg = create_message(
                    content=message.get("content", ""),
                    message_type=msg_type,
                    sender=message.get("sender", "user" if msg_type == MessageType.HUMAN else "assistant")
                )
                state.messages.append(msg)
        
        # Add the current query as a message
        msg = create_message(
            content=query,
            message_type=MessageType.HUMAN,
            sender="user"
        )
        state.messages.append(msg)
        
        # Get the graph from the create_agent_graph function
        from src.graph.agent_graph import create_agent_graph
        graph = create_agent_graph(self)
        
        # Run the workflow
        final_state = graph.invoke(state)
        
        # Manejar correctamente el tipo AddableValuesDict para las versiones nuevas de LangGraph
        if not isinstance(final_state, dict) and hasattr(final_state, "get"):
            # Es un AddableValuesDict, acceder usando .get()
            return {
                "final_response": final_state.get("final_response", ""),
                "agent_responses": final_state.get("agent_responses", {}),
                "context": final_state.get("context", []),
                "is_streaming": final_state.get("is_streaming", False),
                "partial_responses": final_state.get("partial_responses", {}) if final_state.get("is_streaming", False) else {}
            }
        elif isinstance(final_state, dict):
            # Ya es un diccionario normal
            return {
                "final_response": final_state.get("final_response", ""),
                "agent_responses": final_state.get("agent_responses", {}),
                "context": final_state.get("context", []),
                "is_streaming": final_state.get("is_streaming", False),
                "partial_responses": final_state.get("partial_responses", {}) if final_state.get("is_streaming", False) else {}
            }
        else:
            # Intentar acceder directamente a los atributos de GraphState
            return {
                "final_response": getattr(final_state, "final_response", ""),
                "agent_responses": getattr(final_state, "agent_responses", {}),
                "context": getattr(final_state, "context", []),
                "is_streaming": getattr(final_state, "is_streaming", False),
                "partial_responses": getattr(final_state, "partial_responses", {}) if getattr(final_state, "is_streaming", False) else {}
            } 