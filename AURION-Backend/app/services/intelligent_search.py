# app/services/intelligent_search.py
"""
Intelligent Search Service - Multi-source web scraping with fallbacks
Handles: Live data, local searches, general information with smart routing
"""

import logging
import asyncio
from typing import Dict, Any, Optional, List
import aiohttp
from bs4 import BeautifulSoup
import json

from app.core.config import settings

logger = logging.getLogger(__name__)


class IntelligentSearchService:
    """
    Smart search service with multiple fallback sources:
    1. Google Custom Search API (primary)
    2. SerpAPI (fallback 1)
    3. ZenSerp (fallback 2)
    4. Direct web scraping (fallback 3)
    """
    
    def __init__(self):
        self.google_api_key = settings.GOOGLE_API_KEY
        self.google_cx = settings.GOOGLE_SEARCH_CX_ID
        self.serpapi_key = settings.SERPAPI_KEY
        self.zenserp_key = settings.ZENSERP_API_KEY
        self.weather_api_key = settings.WEATHER_API_KEY
        
        # Search method priority
        self.search_methods = []
        
        # Add available methods in priority order
        if self.google_api_key and self.google_cx:
            self.search_methods.append(self._google_search)
        if self.serpapi_key:
            self.search_methods.append(self._serpapi_search)
        if self.zenserp_key:
            self.search_methods.append(self._zenserp_search)
        
        # Always add direct scraping as final fallback
        self.search_methods.append(self._direct_scrape)
        
        logger.info(f"✅ IntelligentSearchService initialized with {len(self.search_methods)} search methods")
    
    async def search(
        self, 
        query: str, 
        search_type: str = 'general',
        location: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Main search entry point - routes to appropriate search method
        
        Args:
            query: Search query
            search_type: 'live', 'local', 'informational'
            location: Optional location context
        
        Returns:
            Search results with formatted output
        """
        
        logger.info(f"🔍 Search request: '{query}' (type: {search_type}, location: {location})")
        
        # Route based on search type
        if search_type == 'live':
            return await self.search_live_data(query, location)
        elif search_type == 'local':
            return await self.search_local(query, location)
        else:
            return await self.search_information(query, location)
    
    async def search_live_data(self, query: str, location: Optional[str] = None) -> Dict[str, Any]:
        """
        Search for live/real-time data (weather, stocks, cricket, news)
        Automatically detects data type and uses specialized methods
        """
        query_lower = query.lower()
        
        # Weather queries
        if any(word in query_lower for word in ['weather', 'temperature', 'forecast', 'climate']):
            return await self._fetch_weather(query, location)
        
        # Stock/crypto queries
        elif any(word in query_lower for word in ['stock', 'share', 'price', 'crypto', 'bitcoin']):
            result = await self._general_web_search(query, location, limit=3)
            if result.get('success'):
                result['type'] = 'stock_data'
            return result
        
        # Sports scores
        elif any(word in query_lower for word in ['score', 'match', 'cricket', 'football', 'game', 'ipl', 'fifa']):
            result = await self._general_web_search(query, location, limit=3)
            if result.get('success'):
                result['type'] = 'sports_score'
            return result
        
        # News queries
        elif any(word in query_lower for word in ['news', 'latest', 'today', 'current']):
            result = await self._general_web_search(query, location, limit=5)
            if result.get('success'):
                result['type'] = 'news'
            return result
        
        # General live search
        else:
            return await self._general_web_search(query, location)
    
    async def search_local(self, query: str, location: Optional[str] = None) -> Dict[str, Any]:
        """
        Search for local businesses/places (restaurants, shops, services)
        Uses location-aware search
        """
        if not location:
            return {
                'success': False,
                'error': 'Location required for local search',
                'message': 'Please specify a location'
            }
        
        # Enhance query with location
        full_query = f"{query} in {location}"
        logger.info(f"📍 Local search: {full_query}")
        
        result = await self._general_web_search(full_query, location, limit=5)
        if result.get('success'):
            result['type'] = 'local_business'
            result['location'] = location
        
        return result
    
    async def search_information(self, query: str, location: Optional[str] = None) -> Dict[str, Any]:
        """
        Search for general information (facts, how-to, explanations)
        """
        result = await self._general_web_search(query, location)
        if result.get('success'):
            result['type'] = 'information'
        return result
    
    # ========== SPECIALIZED SEARCH METHODS ==========
    
    async def _fetch_weather(self, query: str, location: Optional[str] = None) -> Dict[str, Any]:
        """Fetch weather data using OpenWeatherMap API"""
        
        # Extract location from query if not provided
        if not location:
            location = self._extract_location_from_query(query)
        
        if not location:
            return {
                'success': False,
                'error': 'Could not determine location for weather query',
                'message': 'Please specify a location (e.g., "weather in Mumbai")'
            }
        
        logger.info(f"🌤️ Fetching weather for: {location}")
        
        # Try OpenWeatherMap API if key available
        if self.weather_api_key:
            try:
                url = "https://api.openweathermap.org/data/2.5/weather"
                params = {
                    'q': location,
                    'appid': self.weather_api_key,
                    'units': 'metric'
                }
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                        if response.status == 200:
                            data = await response.json()
                            return {
                                'success': True,
                                'type': 'weather',
                                'source': 'OpenWeatherMap API',
                                'data': {
                                    'location': data['name'],
                                    'temperature': data['main']['temp'],
                                    'feels_like': data['main']['feels_like'],
                                    'humidity': data['main']['humidity'],
                                    'description': data['weather'][0]['description'],
                                    'wind_speed': data['wind']['speed']
                                },
                                'formatted': self._format_weather(data)
                            }
            except Exception as e:
                logger.error(f"Weather API error: {e}")
        
        # Fallback to web scraping
        logger.info(f"☁️ Weather API unavailable, using web search fallback")
        result = await self._general_web_search(f"weather in {location}", limit=2)
        if result.get('success'):
            result['type'] = 'weather'
        return result
    
    # ========== GENERAL WEB SEARCH METHODS ==========
    
    async def _general_web_search(
        self, 
        query: str, 
        location: Optional[str] = None,
        limit: int = 3
    ) -> Dict[str, Any]:
        """
        Intelligent web search with multiple fallbacks
        Tries each search method in priority order
        """
        
        logger.info(f"🔍 Starting search with {len(self.search_methods)} available methods")
        
        for i, search_method in enumerate(self.search_methods, 1):
            try:
                logger.info(f"🔄 Attempt {i}/{len(self.search_methods)}: {search_method.__name__}")
                result = await search_method(query, location, limit)
                if result.get('success'):
                    logger.info(f"✅ Search successful with {search_method.__name__}")
                    return result
                else:
                    logger.warning(f"⚠️ {search_method.__name__} returned no success")
            except Exception as e:
                logger.warning(f"⚠️ {search_method.__name__} failed: {e}")
                continue
        
        # All methods failed
        logger.error(f"❌ All {len(self.search_methods)} search methods failed for query: {query}")
        return {
            'success': False,
            'error': 'All search methods failed',
            'message': 'Unable to fetch search results. Please try again or rephrase your query.',
            'formatted': "I couldn't find any search results for that query. Could you try rephrasing it or being more specific?"
        }
    
    async def _google_search(
        self, 
        query: str, 
        location: Optional[str] = None,
        limit: int = 3
    ) -> Dict[str, Any]:
        """Google Custom Search API (primary)"""
        
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            'key': self.google_api_key,
            'cx': self.google_cx,
            'q': query,
            'num': min(limit, 10)  # Google max is 10
        }
        
        if location:
            params['gl'] = self._get_country_code(location)
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('items'):
                        return {
                            'success': True,
                            'source': 'Google Custom Search',
                            'data': data['items'],
                            'formatted': self._format_search_results(data['items'])
                        }
        
        raise Exception("Google search returned no results")
    
    async def _serpapi_search(
        self, 
        query: str, 
        location: Optional[str] = None,
        limit: int = 3
    ) -> Dict[str, Any]:
        """SerpAPI (fallback 1)"""
        
        url = "https://serpapi.com/search"
        params = {
            'api_key': self.serpapi_key,
            'q': query,
            'num': limit,
            'engine': 'google'
        }
        
        if location:
            params['location'] = location
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('organic_results'):
                        return {
                            'success': True,
                            'source': 'SerpAPI',
                            'data': data['organic_results'],
                            'formatted': self._format_serp_results(data['organic_results'])
                        }
        
        raise Exception("SerpAPI returned no results")
    
    async def _zenserp_search(
        self, 
        query: str, 
        location: Optional[str] = None,
        limit: int = 3
    ) -> Dict[str, Any]:
        """ZenSerp API (fallback 2)"""
        
        url = "https://app.zenserp.com/api/v2/search"
        params = {
            'apikey': self.zenserp_key,
            'q': query,
            'num': limit
        }
        
        if location:
            params['location'] = location
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('organic'):
                        return {
                            'success': True,
                            'source': 'ZenSerp',
                            'data': data['organic'],
                            'formatted': self._format_zenserp_results(data['organic'])
                        }
        
        raise Exception("ZenSerp returned no results")
    
    async def _direct_scrape(
        self, 
        query: str, 
        location: Optional[str] = None,
        limit: int = 3
    ) -> Dict[str, Any]:
        """Direct web scraping using DuckDuckGo (fallback 3 - always works)"""
        
        # Use DuckDuckGo HTML (no API key needed)
        search_query = query.replace(' ', '+')
        search_url = f"https://html.duckduckgo.com/html/?q={search_query}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(search_url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    results = []
                    for result in soup.select('.result')[:limit]:
                        title_elem = result.select_one('.result__title')
                        snippet_elem = result.select_one('.result__snippet')
                        url_elem = result.select_one('.result__url')
                        
                        if title_elem:
                            results.append({
                                'title': title_elem.get_text(strip=True),
                                'snippet': snippet_elem.get_text(strip=True) if snippet_elem else '',
                                'link': url_elem.get_text(strip=True) if url_elem else ''
                            })
                    
                    if results:
                        return {
                            'success': True,
                            'source': 'DuckDuckGo Scrape',
                            'data': results,
                            'formatted': self._format_scraped_results(results)
                        }
        
        raise Exception("Direct scraping failed")
    
    # ========== FORMATTING HELPERS ==========
    
    def _format_weather(self, data: Dict) -> str:
        """Format weather data for display"""
        return f"""🌤️ **Weather in {data['name']}**

🌡️ **Temperature:** {data['main']['temp']}°C (feels like {data['main']['feels_like']}°C)
💧 **Humidity:** {data['main']['humidity']}%
💨 **Wind:** {data['wind']['speed']} m/s
☁️ **Conditions:** {data['weather'][0]['description'].title()}"""
    
    def _format_search_results(self, results: List[Dict]) -> str:
        """Format Google search results"""
        formatted = "🔍 **Search Results:**\n\n"
        for i, item in enumerate(results, 1):
            formatted += f"**{i}. {item.get('title')}**\n"
            formatted += f"{item.get('snippet', '')}\n"
            formatted += f"🔗 {item.get('link')}\n\n"
        return formatted
    
    def _format_serp_results(self, results: List[Dict]) -> str:
        """Format SerpAPI results"""
        formatted = "🔍 **Search Results:**\n\n"
        for i, item in enumerate(results, 1):
            formatted += f"**{i}. {item.get('title')}**\n"
            formatted += f"{item.get('snippet', '')}\n"
            formatted += f"🔗 {item.get('link')}\n\n"
        return formatted
    
    def _format_zenserp_results(self, results: List[Dict]) -> str:
        """Format ZenSerp results"""
        return self._format_search_results(results)
    
    def _format_scraped_results(self, results: List[Dict]) -> str:
        """Format scraped results"""
        formatted = "🔍 **Search Results:**\n\n"
        for i, item in enumerate(results, 1):
            formatted += f"**{i}. {item.get('title')}**\n"
            if item.get('snippet'):
                formatted += f"{item['snippet']}\n"
            if item.get('link'):
                formatted += f"🔗 {item['link']}\n"
            formatted += "\n"
        return formatted
    
    # ========== UTILITY HELPERS ==========
    
    def _extract_location_from_query(self, query: str) -> Optional[str]:
        """Extract location from query using simple patterns"""
        query_lower = query.lower()
        
        # Common patterns: "weather in Mumbai", "Mumbai weather"
        if ' in ' in query_lower:
            parts = query_lower.split(' in ')
            if len(parts) > 1:
                return parts[1].strip().title()
        
        # Check for city names
        common_cities = {
            'mumbai': 'Mumbai',
            'delhi': 'Delhi', 
            'bangalore': 'Bangalore',
            'bengaluru': 'Bangalore',
            'hyderabad': 'Hyderabad',
            'hyd': 'Hyderabad',
            'chennai': 'Chennai',
            'kolkata': 'Kolkata',
            'pune': 'Pune',
            'ahmedabad': 'Ahmedabad',
            'jaipur': 'Jaipur',
            'blr': 'Bangalore',
            'blore': 'Bangalore'
        }
        
        for abbrev, full_name in common_cities.items():
            if abbrev in query_lower:
                return full_name
        
        return None
    
    def _get_country_code(self, location: str) -> str:
        """Get country code from location"""
        location_lower = location.lower()
        
        # Indian cities
        indian_cities = ['mumbai', 'delhi', 'bangalore', 'hyderabad', 'chennai', 
                        'kolkata', 'pune', 'ahmedabad', 'jaipur', 'surat']
        
        if any(city in location_lower for city in indian_cities):
            return 'in'  # India
        
        return 'us'  # Default to US


# Create singleton instance
intelligent_search = IntelligentSearchService()
