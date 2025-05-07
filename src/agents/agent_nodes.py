"""Agent nodes for the LangGraph workflow."""
from typing import Dict, List, Tuple, Any, Optional
from langchain_core.messages import HumanMessage

from src.models.class_models import GraphState, AgentRole, MessageType, CompanyDocument
from src.services.llm_service import LLMService
from src.services.vector_store_service import VectorStoreService
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
        
        # Create prompt for solution architect
        prompt = create_agent_prompt(
            AgentRole.SOLUTION_ARCHITECT,
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
            agent_role=AgentRole.SOLUTION_ARCHITECT,
            sources=[doc.id for doc in state.context],
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
        """Client Communication agent for crafting clear, professional responses.
        
        Args:
            state: Current graph state
            
        Returns:
            Updated graph state with client communication response
        """
        # Set current agent
        state.current_agent = AgentRole.CLIENT_COMMUNICATION
        
        # Check if this is a simple conversational query
        if not state.context and self._is_simple_conversational_query(state.human_query):
            # Generate a simple conversational response directly
            simple_response = self._generate_conversational_response(state.human_query, state.messages)
            
            # Create agent response
            agent_response = create_agent_response(
                content=simple_response,
                agent_role=AgentRole.CLIENT_COMMUNICATION,
                sources=[],  # No sources for conversational responses
            )
            
            # Set final response in state
            state.final_response = simple_response
            
            # Add AI message to conversation history
            ai_msg = create_message(
                simple_response,
                MessageType.AI,
                "company_bot"
            )
            state.messages.append(ai_msg)
            
            # Update state
            state.agent_responses[AgentRole.CLIENT_COMMUNICATION] = agent_response
            
            return state
        
        # For regular queries, continue with normal processing
        # Prepare context from other agent responses for comprehensive communication
        from src.models.class_models import CompanyDocument
        context = state.context.copy()
        
        # Add responses from other agents as context
        for role, response in state.agent_responses.items():
            if role != AgentRole.CLIENT_COMMUNICATION:  # Avoid circular reference
                agent_doc = CompanyDocument(
                    id=f"{role.value}_analysis",
                    title=f"{role.value.capitalize()} Agent Analysis",
                    content=response.content,
                    document_type="agent_response",
                    source=f"{role.value}_agent"
                )
                context.append(agent_doc)
        
        # Create prompt for client communication
        prompt = create_agent_prompt(
            AgentRole.CLIENT_COMMUNICATION,
            state.human_query or "",
            state.messages,
            context
        )
        
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
        
        # Set final response in state
        state.final_response = response
        
        # Add AI message to conversation history
        ai_msg = create_message(
            response,
            MessageType.AI,
            "company_bot"
        )
        state.messages.append(ai_msg)
        
        # Update state
        state.agent_responses[AgentRole.CLIENT_COMMUNICATION] = agent_response
        
        return state
        
    def _generate_conversational_response(self, query: str, conversation_history: List[Any]) -> str:
        """Generate a simple conversational response.
        
        Args:
            query: User query
            conversation_history: Conversation history
            
        Returns:
            Simple conversational response
        """
        # Simple templates for different types of conversational queries
        query_lower = query.lower().strip()
        
        # Process greetings
        if any(greeting in query_lower for greeting in ["hello", "hi", "hey", "hola", "buenos", "buenas"]):
            return "¡Hola! Soy el asistente de consultoría tecnológica AI. ¿En qué puedo ayudarte hoy?"
            
        # Process how are you
        if any(phrase in query_lower for phrase in ["how are you", "cómo estás", "qué tal", "como estas", "que tal"]):
            return "¡Estoy muy bien, gracias por preguntar! ¿En qué proyecto tecnológico puedo ayudarte hoy?"
            
        # Process thanks
        if any(phrase in query_lower for phrase in ["thank", "thanks", "gracias"]):
            return "¡De nada! Estoy aquí para ayudarte con tus consultas y proyectos tecnológicos. ¿Hay algo más en lo que pueda asistirte?"
            
        # Process goodbye
        if any(phrase in query_lower for phrase in ["bye", "goodbye", "adiós", "adios", "chao"]):
            return "¡Hasta luego! No dudes en volver si necesitas más ayuda con tus proyectos tecnológicos."
            
        # Default response for other short queries
        return "Estoy aquí para ayudarte con consultas técnicas y proyectos tecnológicos. ¿Tienes alguna pregunta específica o necesitas información sobre algún tema en particular?"
    
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
    
    def process_user_query(self, query: str, conversation_history: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """Process a user query through the agent workflow.
        
        Args:
            query: User query string
            conversation_history: Optional list of previous messages
            
        Returns:
            Result dictionary with agent responses and final response
        """
        from src.graph.agent_graph import create_agent_graph
        import logging
        
        logger = logging.getLogger(__name__)
        
        # Initialize messages from conversation history
        messages = []
        if conversation_history:
            for msg in conversation_history:
                message_type = MessageType(msg.get("type", "human"))
                messages.append(create_message(
                    msg.get("content", ""),
                    message_type,
                    msg.get("sender")
                ))
        
        # Fast path for simple conversational queries
        if self._is_simple_conversational_query(query):
            logger.info(f"Detected simple conversational query: '{query}'. Using fast path response.")
            
            # Generate simple response
            simple_response = self._generate_conversational_response(query, messages)
            
            # Create a simple agent response
            agent_response = create_agent_response(
                content=simple_response,
                agent_role=AgentRole.CLIENT_COMMUNICATION,
                sources=[],
            )
            
            # Return minimal result dictionary
            return {
                "final_response": simple_response,
                "agent_responses": {
                    AgentRole.CLIENT_COMMUNICATION: agent_response
                },
                "context": []
            }
        
        # Regular processing for non-conversational queries
        logger.info(f"Processing complex query: '{query}' through full agent workflow")
        
        # Create agent graph
        graph = create_agent_graph(self)
        
        # Create initial state
        state = GraphState(
            messages=messages,
            human_query=query
        )
        
        # Run the workflow
        try:
            result = graph.invoke(state)
            logger.info("Graph execution completed successfully")
            
            # Check if result is an AddableValuesDict
            if hasattr(result, "get"):
                logger.info("Result is an AddableValuesDict, extracting values")
                # Try to extract client_communication agent's response as final response
                agent_responses = {}
                final_response = None
                context = []
                
                # Extract agent responses if available
                if hasattr(result, "agent_responses") or (hasattr(result, "get") and result.get("agent_responses")):
                    agent_responses = result.agent_responses if hasattr(result, "agent_responses") else result.get("agent_responses", {})
                    
                    # Get final response from client communication agent
                    if AgentRole.CLIENT_COMMUNICATION in agent_responses:
                        final_response = agent_responses[AgentRole.CLIENT_COMMUNICATION].content
                
                # Extract context if available
                if hasattr(result, "context") or (hasattr(result, "get") and result.get("context")):
                    context = result.context if hasattr(result, "context") else result.get("context", [])
                
                # Extract final_response if not already set
                if final_response is None and (hasattr(result, "final_response") or (hasattr(result, "get") and result.get("final_response"))):
                    final_response = result.final_response if hasattr(result, "final_response") else result.get("final_response")
                
                # Fallback response if still not set
                if not final_response:
                    logger.warning("No final response available, using fallback")
                    if agent_responses and len(agent_responses) > 0:
                        # Use the last agent's response as fallback
                        last_agent = list(agent_responses.values())[-1]
                        final_response = last_agent.content
                    else:
                        final_response = "Lo siento, no pude generar una respuesta específica para tu consulta. Por favor intenta reformular tu pregunta."
                
                return {
                    "final_response": final_response,
                    "agent_responses": agent_responses,
                    "context": context
                }
            else:
                # Traditional access pattern if result is as expected
                final_response = result.final_response if hasattr(result, "final_response") else "¡Hola! Soy el asistente de empresa con Agentes IA. ¿En qué puedo ayudarte hoy?"
                agent_responses = result.agent_responses if hasattr(result, "agent_responses") else {}
                context = result.context if hasattr(result, "context") else []
                
                return {
                    "final_response": final_response,
                    "agent_responses": agent_responses,
                    "context": context
                }
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            
            # Return a friendly default response in case of error
            return {
                "final_response": f"¡Hola! Soy el asistente de empresa con Agentes IA. Hubo un problema procesando tu consulta: {str(e)}. Por favor intenta con otra pregunta.",
                "agent_responses": {},
                "context": []
            } 