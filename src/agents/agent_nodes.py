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
        
    def supervisor_agent(self, state: GraphState) -> GraphState:
        """Supervisor agent to coordinate the workflow.
        
        Args:
            state: Current graph state
            
        Returns:
            Updated graph state with supervisor response
        """
        # Set current agent
        state.current_agent = AgentRole.SUPERVISOR
        
        # Create prompt for supervisor
        prompt = create_agent_prompt(
            AgentRole.SUPERVISOR,
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
            agent_role=AgentRole.SUPERVISOR,
            sources=[doc.id for doc in state.context],
        )
        
        # Update state
        state.agent_responses[AgentRole.SUPERVISOR] = agent_response
        
        return state
        
    def researcher_agent(self, state: GraphState) -> GraphState:
        """Researcher agent with external knowledge capabilities.
        
        Args:
            state: Current graph state
            
        Returns:
            Updated graph state with researcher response
        """
        # Set current agent
        state.current_agent = AgentRole.RESEARCHER
        
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
        
        # Create prompt for researcher
        prompt = create_agent_prompt(
            AgentRole.RESEARCHER,
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
            agent_role=AgentRole.RESEARCHER,
            sources=[doc.id for doc in state.context],
        )
        
        # Update state
        state.agent_responses[AgentRole.RESEARCHER] = agent_response
        
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
        
        # Weather intent
        weather_keywords = ["weather", "clima", "temperatura", "forecast", "lluvia", "sol"]
        if any(keyword in query.lower() for keyword in weather_keywords):
            intents.append("weather")
        
        # Wikipedia/information intent
        wiki_keywords = ["what is", "definition", "información sobre", "qué es", "tell me about", "wiki"]
        if any(keyword in query.lower() for keyword in wiki_keywords):
            intents.append("information")
        
        # News intent
        news_keywords = ["news", "noticias", "current events", "actualidad", "últimas noticias"]
        if any(keyword in query.lower() for keyword in news_keywords):
            intents.append("news")
        
        return intents
        
    def analyst_agent(self, state: GraphState) -> GraphState:
        """Analyst agent to analyze information.
        
        Args:
            state: Current graph state
            
        Returns:
            Updated graph state with analyst response
        """
        # Set current agent
        state.current_agent = AgentRole.ANALYST
        
        # Create context including researcher's findings
        context = state.context.copy()
        
        # Add researcher response as additional context if available
        researcher_response = state.agent_responses.get(AgentRole.RESEARCHER)
        if researcher_response:
            from src.models.class_models import CompanyDocument
            researcher_doc = CompanyDocument(
                id="researcher_analysis",
                title="Researcher Agent Analysis",
                content=researcher_response.content,
                document_type="agent_response",
                source="researcher_agent"
            )
            context.append(researcher_doc)
        
        # Create prompt for analyst
        prompt = create_agent_prompt(
            AgentRole.ANALYST,
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
            agent_role=AgentRole.ANALYST,
            sources=[doc.id for doc in state.context],
        )
        
        # Update state
        state.agent_responses[AgentRole.ANALYST] = agent_response
        
        return state
        
    def communicator_agent(self, state: GraphState) -> GraphState:
        """Communicator agent to create the final response.
        
        Args:
            state: Current graph state
            
        Returns:
            Updated graph state with final response
        """
        # Set current agent
        state.current_agent = AgentRole.COMMUNICATOR
        
        # Create context including all agent responses
        from src.models.class_models import CompanyDocument
        context = []
        
        for role, response in state.agent_responses.items():
            if role != AgentRole.COMMUNICATOR:  # Avoid circular reference
                agent_doc = CompanyDocument(
                    id=f"{role.value}_analysis",
                    title=f"{role.value.capitalize()} Agent Analysis",
                    content=response.content,
                    document_type="agent_response",
                    source=f"{role.value}_agent"
                )
                context.append(agent_doc)
        
        # Add original context documents
        context.extend(state.context)
        
        # Create prompt for communicator
        prompt = create_agent_prompt(
            AgentRole.COMMUNICATOR,
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
            agent_role=AgentRole.COMMUNICATOR,
            sources=[doc.id for doc in state.context],
        )
        
        # Update state
        state.agent_responses[AgentRole.COMMUNICATOR] = agent_response
        state.final_response = response
        
        # Add AI message to conversation history
        ai_msg = create_message(
            response,
            MessageType.AI,
            "company_bot"
        )
        state.messages.append(ai_msg)
        
        return state
    
    def should_use_analyst(self, state: GraphState) -> str:
        """Decide whether to use the analyst agent.
        
        Args:
            state: Current graph state
            
        Returns:
            Decision: "use_analyst" or "skip_analyst"
        """
        # Simple logic: if we have researcher response, use analyst
        if AgentRole.RESEARCHER in state.agent_responses:
            return "use_analyst"
        
        return "skip_analyst"
    
    def process_user_query(self, query: str, conversation_history: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """Process a user query through the agent workflow.
        
        Args:
            query: User query text
            conversation_history: Optional previous conversation history
            
        Returns:
            Final state after processing
        """
        from src.graph.agent_graph import create_agent_graph
        import logging
        
        logger = logging.getLogger(__name__)
        
        # Initialize messages from conversation history
        messages = []
        if conversation_history:
            for msg in conversation_history:
                msg_type = MessageType(msg.get("type", "human"))
                messages.append(create_message(
                    msg.get("content", ""),
                    msg_type,
                    msg.get("sender")
                ))
        
        # Add the new human message
        human_msg = create_message(
            query,
            MessageType.HUMAN,
            "user"
        )
        messages.append(human_msg)
        
        # Create initial state
        initial_state = GraphState(
            messages=messages,
            human_query=query
        )
        
        # Get agent graph
        agent_graph = create_agent_graph(self)
        
        # Run the graph with initial state
        result = agent_graph.invoke(initial_state)
        
        # Log the type of result we got
        logger.info(f"Graph result type: {type(result)}")
        
        # Respuesta por defecto en caso de que no se pueda extraer
        default_response = "¡Hola! Soy el asistente de empresa con Agentes IA. ¿En qué puedo ayudarte hoy?"
        if "hola" in query.lower():
            final_response = default_response
        else:
            final_response = "Lo siento, no pude procesar tu consulta correctamente. Por favor, intenta ser más específico o reformula tu pregunta."
        
        agent_responses = {}
        context_docs = []
        
        try:
            # Imprimir la estructura completa del resultado para diagnóstico
            logger.info(f"Result structure: {repr(result)[:200]}...")
            
            # Extract directly from the AddableValuesDict if possible
            found_response = False
            
            # Método 1: Usar values() si es callable
            if hasattr(result, "values") and callable(result.values):
                logger.info("Extracting values from AddableValuesDict")
                values_dict = result.values()
                
                # El objeto values_dict es de tipo dict_values, intentamos extraer usando nombres conocidos
                values_list = list(values_dict)
                if values_list:
                    logger.info(f"Values list first element type: {type(values_list[0])}")
                    
                    # Si el primer elemento es un diccionario, intenta extraer directamente
                    if values_list and isinstance(values_list[0], dict):
                        for value_dict in values_list:
                            if "agent_responses" in value_dict:
                                agent_responses = value_dict["agent_responses"]
                                
                                # Get final response from communicator
                                if AgentRole.COMMUNICATOR in agent_responses:
                                    final_response = agent_responses[AgentRole.COMMUNICATOR].content
                                    found_response = True
                                    logger.info(f"Found communicator response in values dict: {final_response[:50]}...")
                            
                            if "context" in value_dict:
                                context_docs = value_dict["context"]
            
            # Método 2: Acceso directo a atributos
            if not found_response and hasattr(result, "agent_responses"):
                agent_responses = result.agent_responses
                
                if AgentRole.COMMUNICATOR in agent_responses:
                    final_response = agent_responses[AgentRole.COMMUNICATOR].content
                    found_response = True
                    logger.info(f"Found communicator response in attributes: {final_response[:50]}...")
                    
                if hasattr(result, "context"):
                    context_docs = result.context
            
            # Método 3: Probar atributos conocidos específicos de LangGraph
            if not found_response and hasattr(result, "get"):
                try:
                    # Intenta obtener directamente los resultados usando get
                    logger.info("Trying to extract using get method")
                    
                    # Intenta con diferentes posibles nombres de clave
                    for key in ["final_response", "response", "communicator", "output"]:
                        try:
                            value = result.get(key)
                            if value and isinstance(value, str):
                                final_response = value
                                found_response = True
                                logger.info(f"Found response using get({key}): {final_response[:50]}...")
                                break
                        except:
                            pass
                    
                    # Intenta obtener agent_responses
                    if hasattr(result, "get") and not agent_responses:
                        try:
                            responses = result.get("agent_responses")
                            if responses:
                                agent_responses = responses
                            
                                # Intenta obtener la respuesta final
                                if not found_response and AgentRole.COMMUNICATOR in agent_responses:
                                    final_response = agent_responses[AgentRole.COMMUNICATOR].content
                                    found_response = True
                        except:
                            pass
                except Exception as e:
                    logger.error(f"Error using get method: {str(e)}")
            
            logger.info(f"Final response extracted: {final_response[:50]}...")
            
        except Exception as e:
            logger.error(f"Error extracting data from graph result: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
        
        # Return a dictionary with the extracted data
        return {
            "final_response": final_response,
            "agent_responses": agent_responses,
            "context": context_docs
        } 