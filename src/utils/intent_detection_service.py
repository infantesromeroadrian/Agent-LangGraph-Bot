"""Intent and entity detection service."""
from typing import Dict, List, Any, Optional


class IntentDetectionService:
    """Service for detecting intents and entities in user queries."""
    
    def __init__(self):
        """Initialize the intent detection service."""
        pass
    
    def is_simple_conversational_query(self, query: str) -> bool:
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
    
    def extract_intents(self, query: str) -> List[str]:
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
            
        # Digital transformation intents
        if any(word in query_lower for word in ["digital transformation", "digital maturity", "digital strategy", 
                                                "transformación digital", "madurez digital", "digitalización"]):
            intents.append("digital_transformation")
            
        # Cloud architecture intents
        if any(word in query_lower for word in ["cloud", "aws", "azure", "gcp", "nube", "infraestructura"]):
            intents.append("cloud_architecture")
            
        # Cybersecurity intents
        if any(word in query_lower for word in ["security", "vulnerability", "threat", "seguridad", "ciberseguridad"]):
            intents.append("cyber_security")
            
        # Agile methodologies intents
        if any(word in query_lower for word in ["agile", "scrum", "kanban", "sprint", "ágil", "metodología"]):
            intents.append("agile_methodologies")
            
        # Systems integration intents
        if any(word in query_lower for word in ["integration", "api", "middleware", "integración", "conectar"]):
            intents.append("systems_integration")
            
        return intents
    
    def extract_entities(self, query: str) -> Dict[str, str]:
        """Extract key entities from a query using keyword matching.
        
        Args:
            query: User query
            
        Returns:
            Dictionary of entity types and values
        """
        entities = {}
        query_lower = query.lower()
        
        # Simple location detection
        common_locations = ["madrid", "barcelona", "new york", "london", "paris"]
        for location in common_locations:
            if location.lower() in query_lower:
                entities["location"] = location
                break
        
        # Simple topic extraction (naive approach)
        if "about" in query_lower:
            parts = query_lower.split("about")
            if len(parts) > 1:
                entities["topic"] = parts[1].strip()
        
        # Simple technology detection
        tech_keywords = ["python", "javascript", "react", "angular", "vue", "django", "flask", 
                       "node", "java", "spring", "docker", "kubernetes", "aws", "azure", 
                       "google cloud", "ai", "machine learning", "ml", "deep learning"]
        for tech in tech_keywords:
            if tech.lower() in query_lower:
                entities["technology"] = tech
                break
                
        # Simple project type detection
        project_types = ["web", "mobile", "desktop", "api", "backend", "frontend", "fullstack", 
                       "database", "cloud", "devops", "data science", "machine learning"]
        for proj_type in project_types:
            if proj_type.lower() in query_lower:
                entities["project_type"] = proj_type
                break
                
        # Simple time period detection
        time_periods = ["today", "yesterday", "last week", "last month", "next week", 
                       "next month", "this year", "last year"]
        for period in time_periods:
            if period.lower() in query_lower:
                entities["time_period"] = period
                break
        
        return entities 