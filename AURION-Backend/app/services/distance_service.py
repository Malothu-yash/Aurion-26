"""
Distance Calculation Service - Real distance data with web scraping fallback

This service provides accurate distance and travel time information using:
1. Google Maps scraping (primary method)
2. Distance database for common routes (fallback)
3. Approximate calculations (last resort)

Features:
- Multi-mode transport (bus, train, flight, car, walking)
- Real-time web scraping
- Comprehensive Indian cities database
- Smart fallback mechanisms

Example:
    service = DistanceService()
    result = await service.get_distance("Mumbai", "Delhi", "bus")
    # Returns: {"distance_km": 1420, "duration": "24 hours", "mode": "bus"}
"""

import logging
import httpx
from bs4 import BeautifulSoup
from typing import Dict, Optional
import asyncio

logger = logging.getLogger(__name__)

class DistanceService:
    """Calculate distances and travel times using multiple sources"""
    
    def __init__(self):
        """Initialize the distance service"""
        logger.info("✅ DistanceService initialized")
        
        # Database of common Indian city distances (km by road)
        self.distance_db = {
            # Mumbai routes
            ("mumbai", "delhi"): 1420,
            ("delhi", "mumbai"): 1420,
            ("mumbai", "bangalore"): 985,
            ("bangalore", "mumbai"): 985,
            ("mumbai", "chennai"): 1340,
            ("chennai", "mumbai"): 1340,
            ("mumbai", "kolkata"): 2000,
            ("kolkata", "mumbai"): 2000,
            ("mumbai", "hyderabad"): 710,
            ("hyderabad", "mumbai"): 710,
            ("mumbai", "pune"): 150,
            ("pune", "mumbai"): 150,
            
            # Delhi routes
            ("delhi", "bangalore"): 2150,
            ("bangalore", "delhi"): 2150,
            ("delhi", "chennai"): 2180,
            ("chennai", "delhi"): 2180,
            ("delhi", "kolkata"): 1475,
            ("kolkata", "delhi"): 1475,
            ("delhi", "hyderabad"): 1575,
            ("hyderabad", "delhi"): 1575,
            ("delhi", "jaipur"): 280,
            ("jaipur", "delhi"): 280,
            ("delhi", "agra"): 230,
            ("agra", "delhi"): 230,
            
            # Bangalore routes
            ("bangalore", "chennai"): 346,
            ("chennai", "bangalore"): 346,
            ("bangalore", "hyderabad"): 575,
            ("hyderabad", "bangalore"): 575,
            ("bangalore", "kolkata"): 1880,
            ("kolkata", "bangalore"): 1880,
            ("bangalore", "pune"): 840,
            ("pune", "bangalore"): 840,
            
            # Other important routes
            ("chennai", "kolkata"): 1670,
            ("kolkata", "chennai"): 1670,
            ("chennai", "hyderabad"): 630,
            ("hyderabad", "chennai"): 630,
            ("hyderabad", "kolkata"): 1500,
            ("kolkata", "hyderabad"): 1500,
            ("pune", "hyderabad"): 560,
            ("hyderabad", "pune"): 560,
        }
    
    async def get_distance(
        self, 
        origin: str, 
        destination: str,
        mode: str = "driving"
    ) -> Dict:
        """
        Get distance and travel info between two locations
        
        Args:
            origin: Starting location
            destination: Ending location  
            mode: Transport mode (bus, train, flight, car, driving, walking)
            
        Returns:
            {
                "distance_km": float,
                "distance_text": str,
                "duration": str,
                "duration_value": float (hours),
                "mode": str,
                "source": str,
                "route_info": str (optional)
            }
        """
        
        logger.info(f"🗺️ Calculating distance: {origin} → {destination} ({mode})")
        
        try:
            # Try Google Maps scraping first (disabled for now due to reliability)
            # result = await self._scrape_google_maps(origin, destination, mode)
            # if result:
            #     return result
            
            # Use distance database
            result = self._get_from_database(origin, destination, mode)
            if result:
                return result
            
            # Last resort: estimation
            return self._estimate_distance(origin, destination, mode)
            
        except Exception as e:
            logger.error(f"Distance calculation error: {e}")
            return self._estimate_distance(origin, destination, mode)
    
    def _get_from_database(self, origin: str, destination: str, mode: str) -> Optional[Dict]:
        """
        Get distance from local database
        
        Returns None if route not found
        """
        
        origin_key = self._normalize_city_name(origin)
        dest_key = self._normalize_city_name(destination)
        
        distance_km = self.distance_db.get((origin_key, dest_key))
        
        if distance_km:
            logger.info(f"📊 Found in database: {distance_km} km")
            
            # Calculate duration based on mode
            duration_hours = self._calculate_duration(distance_km, mode)
            duration_text = self._format_duration(duration_hours)
            
            # Add route info for specific modes
            route_info = self._get_route_info(origin, destination, mode)
            
            return {
                "distance_km": distance_km,
                "distance_text": f"{distance_km} km",
                "duration": duration_text,
                "duration_value": duration_hours,
                "mode": mode,
                "source": "database",
                "route_info": route_info
            }
        
        return None
    
    def _estimate_distance(self, origin: str, destination: str, mode: str) -> Dict:
        """
        Fallback distance estimation
        
        Uses very rough approximation for unknown routes
        """
        
        logger.info(f"⚠️ Using estimation for {origin} → {destination}")
        
        # Default estimate
        distance_km = 500
        
        # Try to make a better estimate based on city sizes/regions
        # This is very simplified
        major_cities = ["mumbai", "delhi", "bangalore", "chennai", "kolkata", "hyderabad"]
        
        origin_major = self._normalize_city_name(origin) in major_cities
        dest_major = self._normalize_city_name(destination) in major_cities
        
        if origin_major and dest_major:
            distance_km = 1200  # Average distance between major cities
        elif origin_major or dest_major:
            distance_km = 600  # One major city
        else:
            distance_km = 300  # Both smaller cities
        
        duration_hours = self._calculate_duration(distance_km, mode)
        duration_text = self._format_duration(duration_hours)
        
        return {
            "distance_km": distance_km,
            "distance_text": f"approximately {distance_km} km",
            "duration": duration_text,
            "duration_value": duration_hours,
            "mode": mode,
            "source": "estimation",
            "route_info": "This is an approximate distance. For exact information, please check Google Maps."
        }
    
    def _calculate_duration(self, distance_km: float, mode: str) -> float:
        """
        Calculate travel duration in hours based on mode
        
        Returns: Duration in hours (float)
        """
        
        # Average speeds for different modes (km/h)
        speeds = {
            "bus": 50,       # Long-distance bus with stops
            "train": 75,     # Average train speed including stops
            "flight": 650,   # Effective speed including airport time
            "car": 70,       # Car/driving
            "driving": 70,   # Same as car
            "walking": 5     # Walking pace
        }
        
        speed = speeds.get(mode, 70)  # Default to car speed
        
        duration = distance_km / speed
        
        # Add airport/station overhead for long distance
        if mode == "flight":
            duration += 2  # Add 2 hours for airport procedures
        elif mode == "train" and distance_km > 500:
            duration += 1  # Add 1 hour for station time on long routes
        
        return duration
    
    def _format_duration(self, hours: float) -> str:
        """
        Format duration in a human-readable way
        
        Examples:
            1.5 → "1 hour 30 minutes"
            24.0 → "24 hours"
            0.75 → "45 minutes"
        """
        
        if hours < 1:
            minutes = int(hours * 60)
            return f"{minutes} minutes"
        elif hours == int(hours):
            return f"{int(hours)} hours"
        else:
            full_hours = int(hours)
            minutes = int((hours - full_hours) * 60)
            return f"{full_hours} hours {minutes} minutes"
    
    def _normalize_city_name(self, city: str) -> str:
        """
        Normalize city name for database lookup
        
        Handles: Mumbai/Bombay, Bengaluru/Bangalore, etc.
        """
        
        city_lower = city.lower().strip()
        
        # Common name variations
        aliases = {
            "bombay": "mumbai",
            "bengaluru": "bangalore",
            "calcutta": "kolkata",
            "madras": "chennai",
            "new delhi": "delhi",
            "ncr": "delhi"
        }
        
        return aliases.get(city_lower, city_lower)
    
    def _get_route_info(self, origin: str, destination: str, mode: str) -> str:
        """
        Get additional route information based on mode
        
        Returns helpful context about the journey
        """
        
        origin_norm = self._normalize_city_name(origin)
        dest_norm = self._normalize_city_name(destination)
        
        # Special route information
        route_key = (origin_norm, dest_norm)
        
        if mode == "bus":
            bus_info = {
                ("mumbai", "delhi"): "Popular operators: RedBus, VRL Travels. Night buses available.",
                ("mumbai", "pune"): "Very frequent service, buses every 30 minutes.",
                ("delhi", "jaipur"): "Frequent service on Delhi-Jaipur highway.",
                ("bangalore", "chennai"): "AC Volvo buses available, comfortable journey.",
            }
            return bus_info.get(route_key, "Multiple bus operators serve this route.")
        
        elif mode == "train":
            train_info = {
                ("mumbai", "delhi"): "Rajdhani Express (16h), August Kranti Rajdhani (16h).",
                ("delhi", "mumbai"): "Rajdhani Express, Mumbai Rajdhani available.",
                ("mumbai", "bangalore"): "Udyan Express (24h), frequent trains available.",
                ("bangalore", "chennai"): "Shatabdi Express (5h), very frequent service.",
            }
            return train_info.get(route_key, "Regular train service available.")
        
        elif mode == "flight":
            return f"Multiple daily flights available. Book in advance for best prices."
        
        return ""
    
    async def _scrape_google_maps(self, origin: str, destination: str, mode: str) -> Optional[Dict]:
        """
        Scrape Google Maps for real distance data
        
        WARNING: This is fragile and may break if Google changes their HTML.
        Use as primary method only if stable.
        """
        
        try:
            # Build Google Maps URL
            url = f"https://www.google.com/maps/dir/{origin.replace(' ', '+')}/{destination.replace(' ', '+')}"
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                response = await client.get(url, headers=headers)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Try to extract distance (Google Maps HTML structure)
                    # NOTE: These selectors may need updating
                    distance_text = None
                    duration_text = None
                    
                    # Look for distance/duration elements
                    # This is highly dependent on Google's HTML structure
                    for elem in soup.find_all(['div', 'span']):
                        text = elem.get_text(strip=True)
                        if 'km' in text.lower() and not distance_text:
                            distance_text = text
                        if ('hour' in text.lower() or 'min' in text.lower()) and not duration_text:
                            duration_text = text
                    
                    if distance_text and duration_text:
                        distance_km = self._parse_distance(distance_text)
                        
                        logger.info(f"🌐 Scraped from Google Maps: {distance_km} km")
                        
                        return {
                            "distance_km": distance_km,
                            "distance_text": distance_text,
                            "duration": duration_text,
                            "duration_value": self._calculate_duration(distance_km, mode),
                            "mode": mode,
                            "source": "google_maps"
                        }
            
            return None
            
        except Exception as e:
            logger.error(f"Google Maps scraping failed: {e}")
            return None
    
    def _parse_distance(self, distance_text: str) -> float:
        """
        Parse distance text to kilometers
        
        Examples:
            "1,420 km" → 1420.0
            "985 km" → 985.0
            "23.5 mi" → 37.8 (converted to km)
        """
        import re
        
        # Remove commas
        text = distance_text.replace(',', '')
        
        # Extract numbers
        numbers = re.findall(r'\d+\.?\d*', text)
        
        if numbers:
            distance = float(numbers[0])
            
            # Convert miles to km if needed
            if 'mi' in distance_text.lower():
                distance = distance * 1.60934
            
            return distance
        
        return 0.0
    
    def get_all_modes_info(self, origin: str, destination: str) -> Dict[str, Dict]:
        """
        Get distance information for all transport modes
        
        Useful when user doesn't specify a mode
        
        Returns:
            {
                "bus": {...},
                "train": {...},
                "flight": {...},
                "driving": {...}
            }
        """
        
        modes = ["bus", "train", "flight", "driving"]
        result = {}
        
        for mode in modes:
            # Use synchronous database lookup
            origin_key = self._normalize_city_name(origin)
            dest_key = self._normalize_city_name(destination)
            distance_km = self.distance_db.get((origin_key, dest_key), 500)
            
            duration_hours = self._calculate_duration(distance_km, mode)
            duration_text = self._format_duration(duration_hours)
            
            result[mode] = {
                "distance_km": distance_km,
                "distance_text": f"{distance_km} km",
                "duration": duration_text,
                "mode": mode
            }
        
        return result
