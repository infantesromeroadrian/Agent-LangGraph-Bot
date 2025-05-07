from typing import Dict, List, Optional, Any
import os
import logging
import requests
from datetime import datetime
from langchain_community.tools import WikipediaQueryRun, BaseTool
from langchain_community.utilities import WikipediaAPIWrapper
from langchain_community.tools.openweathermap.tool import OpenWeatherMapQueryRun
from langchain_community.utilities.openweathermap import OpenWeatherMapAPIWrapper
from langchain_core.tools import Tool

from src.models.class_models import CompanyDocument, ToolResult, ToolResultType

logger = logging.getLogger(__name__)

class ExternalKnowledgeService:
    """Service for accessing external knowledge sources."""
    
    def __init__(self):
        """Initialize external knowledge tools."""
        self.tools = {}
        
        # Initialize Wikipedia tool
        try:
            wikipedia = WikipediaAPIWrapper(top_k_results=3)
            self.tools["wikipedia"] = Tool(
                name="Wikipedia",
                description="Search for information on Wikipedia",
                func=WikipediaQueryRun(api_wrapper=wikipedia).run
            )
            logger.info("Wikipedia tool initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Wikipedia tool: {e}")
            
        # Initialize Weather tool
        try:
            weather_api_key = os.getenv("OPENWEATHERMAP_API_KEY")
            if weather_api_key:
                weather = OpenWeatherMapAPIWrapper(openweathermap_api_key=weather_api_key)
                self.tools["weather"] = Tool(
                    name="WeatherInfo",
                    description="Get current weather information for a location",
                    func=OpenWeatherMapQueryRun(api_wrapper=weather).run
                )
                logger.info("Weather tool initialized successfully")
            else:
                logger.warning("OpenWeatherMap API key not found")
        except Exception as e:
            logger.error(f"Failed to initialize Weather tool: {e}")
            
        # Initialize News API tool
        try:
            news_api_key = os.getenv("NEWS_API_KEY")
            if news_api_key:
                self.news_api_key = news_api_key
                logger.info("News API tool initialized successfully")
            else:
                logger.warning("News API key not found")
        except Exception as e:
            logger.error(f"Failed to initialize News tool: {e}")
    
    def query_wikipedia(self, query: str) -> CompanyDocument:
        """Query Wikipedia for information.
        
        Args:
            query: Search query
            
        Returns:
            CompanyDocument with Wikipedia information
        """
        try:
            if "wikipedia" not in self.tools:
                return self._create_error_document("Wikipedia tool not available")
                
            wiki_tool = self.tools["wikipedia"]
            result = wiki_tool.run(query)
            
            return CompanyDocument(
                id=f"wikipedia_{datetime.now().timestamp()}",
                title=f"Wikipedia: {query}",
                content=result,
                document_type="external_api",
                source="wikipedia",
                metadata={"query": query, "timestamp": datetime.now().isoformat()}
            )
        except Exception as e:
            logger.error(f"Error querying Wikipedia: {e}")
            return self._create_error_document(f"Error querying Wikipedia: {str(e)}")
    
    def get_weather(self, location: str) -> CompanyDocument:
        """Get weather information for a location.
        
        Args:
            location: Location to get weather for
            
        Returns:
            CompanyDocument with weather information
        """
        try:
            if "weather" not in self.tools:
                error_msg = "Weather tool not available. Make sure the OPENWEATHERMAP_API_KEY is set and pyowm is installed."
                logger.error(error_msg)
                return self._create_error_document(error_msg)
                
            weather_tool = self.tools["weather"]
            result = weather_tool.run(location)
            
            return CompanyDocument(
                id=f"weather_{datetime.now().timestamp()}",
                title=f"Weather in {location}",
                content=result,
                document_type="external_api",
                source="openweathermap",
                metadata={"location": location, "timestamp": datetime.now().isoformat()}
            )
        except Exception as e:
            error_msg = f"Error getting weather for {location}: {str(e)}"
            logger.error(error_msg)
            
            # Crear un documento con información de fallback
            fallback_content = (
                f"No pude obtener información meteorológica en tiempo real para {location}. "
                "Considera consultar un servicio meteorológico como AccuWeather o weather.com para obtener datos actuales."
            )
            
            return CompanyDocument(
                id=f"weather_fallback_{datetime.now().timestamp()}",
                title=f"Weather information unavailable for {location}",
                content=fallback_content,
                document_type="fallback",
                source="system_fallback",
                metadata={"error": str(e), "location": location, "timestamp": datetime.now().isoformat()}
            )
    
    def get_news(self, topic: str, limit: int = 3) -> CompanyDocument:
        """Get latest news on a topic.
        
        Args:
            topic: News topic to search for
            limit: Maximum number of articles
            
        Returns:
            CompanyDocument with news articles
        """
        try:
            if not hasattr(self, "news_api_key"):
                return self._create_error_document("News API tool not available")
                
            url = f"https://newsapi.org/v2/everything?q={topic}&apiKey={self.news_api_key}&pageSize={limit}"
            response = requests.get(url)
            
            if response.status_code != 200:
                return self._create_error_document(f"News API error: {response.text}")
                
            data = response.json()
            articles = data.get("articles", [])
            
            if not articles:
                return self._create_error_document(f"No news found for topic: {topic}")
                
            content = "Recent News Articles:\n\n"
            for i, article in enumerate(articles[:limit], 1):
                content += f"{i}. {article.get('title', 'No title')}\n"
                content += f"Source: {article.get('source', {}).get('name', 'Unknown')}\n"
                content += f"Date: {article.get('publishedAt', 'Unknown date')}\n"
                content += f"Summary: {article.get('description', 'No description')}\n\n"
            
            return CompanyDocument(
                id=f"news_{datetime.now().timestamp()}",
                title=f"News about {topic}",
                content=content,
                document_type="external_api",
                source="newsapi",
                metadata={"topic": topic, "timestamp": datetime.now().isoformat()}
            )
        except Exception as e:
            logger.error(f"Error getting news: {e}")
            return self._create_error_document(f"Error getting news: {str(e)}")
    
    def _create_error_document(self, error_message: str) -> CompanyDocument:
        """Create an error document.
        
        Args:
            error_message: Error message
            
        Returns:
            CompanyDocument with error information
        """
        return CompanyDocument(
            id=f"error_{datetime.now().timestamp()}",
            title="External Knowledge Error",
            content=f"Error accessing external knowledge: {error_message}",
            document_type="error",
            source="external_knowledge_service",
            metadata={"error": error_message, "timestamp": datetime.now().isoformat()}
        ) 