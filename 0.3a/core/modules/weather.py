"""
Weather Module for Edgar AI Assistant
Handles weather-related queries with Open-Meteo API and summary responses.
"""

import time
import requests
from typing import Optional, Callable
try:
    from fuzzywuzzy import process as fuzzy_process, fuzz
    FUZZY_AVAILABLE = True
except ImportError:
    FUZZY_AVAILABLE = False
    print("⚠️  fuzzywuzzy not installed. Install with: pip install fuzzywuzzy python-levenshtein")

class WeatherModule:
    def __init__(self):
        self.name = "Weather Module"
        self.version = "1.2"  # Updated version
        self.open_meteo_base = "https://api.open-meteo.com/v1"
        
        # Expanded city to coordinates mapping for common locations
        self.city_coordinates = {
            # North America
            "new york": {"lat": 40.7128, "lon": -74.0060},
            "los angeles": {"lat": 34.0522, "lon": -118.2437},
            "chicago": {"lat": 41.8781, "lon": -87.6298},
            "miami": {"lat": 25.7617, "lon": -80.1918},
            "toronto": {"lat": 43.6532, "lon": -79.3832},
            "vancouver": {"lat": 49.2827, "lon": -123.1207},
            "seattle": {"lat": 47.6062, "lon": -122.3321},
            "san francisco": {"lat": 37.7749, "lon": -122.4194},
            "las vegas": {"lat": 36.1699, "lon": -115.1398},
            "phoenix": {"lat": 33.4484, "lon": -112.0740},
            "houston": {"lat": 29.7604, "lon": -95.3698},
            "dallas": {"lat": 32.7767, "lon": -96.7970},
            "atlanta": {"lat": 33.7490, "lon": -84.3880},
            "boston": {"lat": 42.3601, "lon": -71.0589},
            "washington": {"lat": 38.9072, "lon": -77.0369},
            "philadelphia": {"lat": 39.9526, "lon": -75.1652},
            "detroit": {"lat": 42.3314, "lon": -83.0458},
            "montreal": {"lat": 45.5017, "lon": -73.5673},
            "calgary": {"lat": 51.0447, "lon": -114.0719},
            "texas": {"lat": 31.9686, "lon": 99.9018},
            "new york city": {"lat": 40.7128, "lon": -74.0060},
            "nyc": {"lat": 40.7128, "lon": -74.0060},
            "la": {"lat": 34.0522, "lon": -118.2437},
            "sf": {"lat": 37.7749, "lon": -122.4194},
            
            # Europe
            "london": {"lat": 51.5074, "lon": -0.1278},
            "paris": {"lat": 48.8566, "lon": 2.3522},
            "berlin": {"lat": 52.5200, "lon": 13.4050},
            "rome": {"lat": 41.9028, "lon": 12.4964},
            "madrid": {"lat": 40.4168, "lon": -3.7038},
            "barcelona": {"lat": 41.3851, "lon": 2.1734},
            "amsterdam": {"lat": 52.3676, "lon": 4.9041},
            "brussels": {"lat": 50.8503, "lon": 4.3517},
            "vienna": {"lat": 48.2082, "lon": 16.3738},
            "prague": {"lat": 50.0755, "lon": 14.4378},
            "budapest": {"lat": 47.4979, "lon": 19.0402},
            "warsaw": {"lat": 52.2297, "lon": 21.0122},
            "lisbon": {"lat": 38.7223, "lon": -9.1393},
            "dublin": {"lat": 53.3498, "lon": -6.2603},
            "edinburgh": {"lat": 55.9533, "lon": -3.1883},
            "manchester": {"lat": 53.4808, "lon": -2.2426},
            "milan": {"lat": 45.4642, "lon": 9.1900},
            "athens": {"lat": 37.9838, "lon": 23.7275},
            "stockholm": {"lat": 59.3293, "lon": 18.0686},
            "oslo": {"lat": 59.9139, "lon": 10.7522},
            "copenhagen": {"lat": 55.6761, "lon": 12.5683},
            "helsinki": {"lat": 60.1699, "lon": 24.9384},
            
            # Asia
            "tokyo": {"lat": 35.6762, "lon": 139.6503},
            "beijing": {"lat": 39.9042, "lon": 116.4074},
            "shanghai": {"lat": 31.2304, "lon": 121.4737},
            "hong kong": {"lat": 22.3193, "lon": 114.1694},
            "singapore": {"lat": 1.3521, "lon": 103.8198},
            "seoul": {"lat": 37.5665, "lon": 126.9780},
            "bangkok": {"lat": 13.7563, "lon": 100.5018},
            "mumbai": {"lat": 19.0760, "lon": 72.8777},
            "delhi": {"lat": 28.7041, "lon": 77.1025},
            "dubai": {"lat": 25.2048, "lon": 55.2708},
            "istanbul": {"lat": 41.0082, "lon": 28.9784},
            "taipei": {"lat": 25.0330, "lon": 121.5654},
            "manila": {"lat": 14.5995, "lon": 120.9842},
            "jakarta": {"lat": 6.2088, "lon": 106.8456},
            "kuala lumpur": {"lat": 3.1390, "lon": 101.6869},
            
            # Australia & Oceania
            "sydney": {"lat": -33.8688, "lon": 151.2093},
            "melbourne": {"lat": -37.8136, "lon": 144.9631},
            "brisbane": {"lat": -27.4698, "lon": 153.0251},
            "perth": {"lat": -31.9505, "lon": 115.8605},
            "auckland": {"lat": -36.8485, "lon": 174.7633},
            "wellington": {"lat": -41.2865, "lon": 174.7762},
            
            # South America
            "sao paulo": {"lat": -23.5505, "lon": -46.6333},
            "rio de janeiro": {"lat": -22.9068, "lon": -43.1729},
            "buenos aires": {"lat": -34.6037, "lon": -58.3816},
            "lima": {"lat": -12.0464, "lon": -77.0428},
            "bogota": {"lat": 4.7110, "lon": -74.0721},
            "santiago": {"lat": -33.4489, "lon": -70.6693},
            
            # Africa
            "cairo": {"lat": 30.0444, "lon": 31.2357},
            "cape town": {"lat": -33.9249, "lon": 18.4241},
            "nairobi": {"lat": -1.2921, "lon": 36.8219},
            "lagos": {"lat": 6.5244, "lon": 3.3792},
            "johannesburg": {"lat": -26.2041, "lon": 28.0473},
            "casablanca": {"lat": 33.5731, "lon": -7.5898}
        }

    def fuzzy_match_city(self, user_input: str) -> Optional[tuple]:
        """
        Use fuzzy matching to find the best city match from user input.
        Returns (city_name, confidence_score, coordinates) or None if no good match.
        """
        if not FUZZY_AVAILABLE:
            return None
            
        # Extract potential location words (2-3 word phrases)
        words = user_input.lower().split()
        potential_queries = []
        
        # Create n-grams of 1, 2, and 3 words
        for n in [3, 2, 1]:
            for i in range(len(words) - n + 1):
                phrase = " ".join(words[i:i+n])
                potential_queries.append(phrase)
        
        # Try to match each potential query
        best_match = None
        best_score = 0
        
        for query in potential_queries:
            # Skip very common words that aren't locations
            if query in ["the", "a", "in", "at", "for", "weather", "forecast", "today", "tomorrow", "what's", "what", "is", "the", "like"]:
                continue
                
            matches = fuzzy_process.extract(query, self.city_coordinates.keys(), limit=1)
            if matches:
                city, score = matches[0]
                if score > best_score and score > 70:  # Threshold for acceptable match
                    best_match = (city, score, self.city_coordinates[city])
                    best_score = score
        
        return best_match if best_match else None

    def get_current_location_coordinates(self) -> dict:
        """
        Get approximate coordinates based on IP geolocation.
        Uses a free, fast service without API keys.
        """
        try:
            response = requests.get('http://ip-api.com/json/', timeout=3)
            if response.status_code == 200:
                data = response.json()
                if data['status'] == 'success':
                    print(f"📍 Detected location: {data['city']}, {data['country']}")
                    return {
                        "lat": data['lat'],
                        "lon": data['lon'],
                        "city": data['city'],
                        "country": data['country']
                    }
        except Exception as e:
            print(f"❌ Error getting location from IP: {e}")
        
        # Fallback to a default location
        print("📍 Using fallback location: New York, United States")
        return {"lat": 40.7128, "lon": -74.0060, "city": "New York", "country": "United States"}

    def extract_location(self, user_input: str) -> tuple:
        """
        Extract location from user input using both exact and fuzzy matching.
        Returns (location_type, location_name, coordinates)
        """
        user_input = user_input.lower().strip()
        
        # Skip if it's clearly a general weather query
        general_queries = [
            "weather", "forecast", "temperature", "how hot", "how cold", 
            "what's the weather", "what is the weather", "how's the weather",
            "how is the weather", "weather today", "weather now"
        ]
        
        is_general_query = any(query in user_input for query in general_queries)
        has_location_keyword = any(keyword in user_input for keyword in ["in ", "at ", "for "])
        
        # If it's a general query without location keywords, use current location
        if is_general_query and not has_location_keyword:
            current_location = self.get_current_location_coordinates()
            location_name = f"{current_location['city']}, {current_location['country']}"
            return "current", location_name, current_location
        
        # First, try exact matching for common cities
        for city, coords in self.city_coordinates.items():
            if city in user_input:
                print(f"📍 Exact match found: {city.title()}")
                return "specified", city.title(), coords
        
        # Try fuzzy matching if exact match fails
        fuzzy_result = self.fuzzy_match_city(user_input)
        if fuzzy_result:
            city, confidence, coords = fuzzy_result
            print(f"📍 Fuzzy matched '{city}' with {confidence}% confidence")
            return "specified", city.title(), coords
        
        # Check for location patterns as fallback
        location_patterns = ["in ", "at ", "for "]
        for pattern in location_patterns:
            if pattern in user_input:
                start_idx = user_input.find(pattern) + len(pattern)
                remaining_text = user_input[start_idx:].strip()
                
                # Try exact match on remaining text
                for city, coords in self.city_coordinates.items():
                    if city in remaining_text:
                        print(f"📍 Pattern match found: {city.title()}")
                        return "specified", city.title(), coords
                
                # Try fuzzy match on remaining text
                fuzzy_result = self.fuzzy_match_city(remaining_text)
                if fuzzy_result:
                    city, confidence, coords = fuzzy_result
                    print(f"📍 Fuzzy matched '{city}' with {confidence}% confidence")
                    return "specified", city.title(), coords
        
        # No location specified - use current location with better messaging
        print("📍 No location specified, using current location")
        current_location = self.get_current_location_coordinates()
        location_name = f"{current_location['city']}, {current_location['country']}"
        return "current", location_name, current_location

    def get_weather_summary(self, coordinates: dict, location_name: str, location_type: str) -> str:
        """
        Get weather summary from Open-Meteo API.
        """
        try:
            # Open-Meteo API call for current weather
            url = f"{self.open_meteo_base}/forecast"
            params = {
                'latitude': coordinates['lat'],
                'longitude': coordinates['lon'],
                'current_weather': 'true',
                'temperature_unit': 'fahrenheit',
                'wind_speed_unit': 'mph',
                'precipitation_unit': 'inch',
                'timezone': 'auto'
            }
            
            response = requests.get(url, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                current = data['current_weather']
                
                # Convert weather code to description
                weather_desc = self._get_weather_description(current['weathercode'])
                temperature = int(current['temperature'])
                wind_speed = int(current['windspeed'])
                
                # Create summary based on weather conditions
                summary = self._create_weather_summary(
                    location_name, location_type, temperature, 
                    weather_desc, wind_speed
                )
                
                return summary
            else:
                return f"Sorry, I couldn't fetch weather data for {location_name} right now."
                
        except Exception as e:
            print(f"❌ Error fetching weather data: {e}")
            return f"Unable to get weather information for {location_name}. Please try again later."

    def _get_weather_description(self, weather_code: int) -> str:
        """Convert Open-Meteo weather code to human-readable description"""
        weather_codes = {
            0: "clear sky",
            1: "mainly clear", 
            2: "partly cloudy",
            3: "overcast",
            45: "foggy",
            48: "depositing rime fog",
            51: "light drizzle",
            53: "moderate drizzle",
            55: "dense drizzle",
            56: "light freezing drizzle",
            57: "dense freezing drizzle",
            61: "slight rain",
            63: "moderate rain",
            65: "heavy rain",
            66: "light freezing rain",
            67: "heavy freezing rain",
            71: "slight snow fall",
            73: "moderate snow fall",
            75: "heavy snow fall",
            77: "snow grains",
            80: "slight rain showers",
            81: "moderate rain showers",
            82: "violent rain showers",
            85: "slight snow showers",
            86: "heavy snow showers",
            95: "thunderstorm",
            96: "thunderstorm with slight hail",
            99: "thunderstorm with heavy hail"
        }
        return weather_codes.get(weather_code, "unknown conditions")

    def _create_weather_summary(self, location: str, location_type: str, 
                              temp: int, condition: str, wind_speed: int) -> str:
        """Create a natural language weather summary"""
        
        # Location context - improved messaging
        if location_type == "current":
            location_context = f"Here's your current weather in {location}"
        else:
            location_context = f"Here's the current weather in {location}"
        
        # Temperature context
        if temp >= 80:
            temp_context = f"it's quite warm at {temp}°F"
        elif temp >= 65:
            temp_context = f"it's pleasant at {temp}°F"
        elif temp >= 50:
            temp_context = f"it's cool at {temp}°F"
        elif temp >= 32:
            temp_context = f"it's chilly at {temp}°F"
        else:
            temp_context = f"it's cold at {temp}°F"
        
        # Condition context
        if "rain" in condition:
            condition_context = f"with {condition}. You might want an umbrella! ☔ "
        elif "snow" in condition:
            condition_context = f"with {condition}. Perfect for staying cozy! ❄️ "
        elif "clear" in condition or "sun" in condition:
            condition_context = f"with {condition}. Great weather to be outside! ☀️ "
        elif "cloud" in condition:
            condition_context = f"with {condition}. Not too bad for going out! ⛅ "
        elif "thunder" in condition:
            condition_context = f"with {condition}. Best to stay indoors! ⚡ "
        elif "fog" in condition:
            condition_context = f"with {condition}. Drive carefully if you're out! 🌫️ "
        else:
            condition_context = f"with {condition}."
        
        # Wind context
        if wind_speed > 20:
            wind_context = "It's quite windy out there!"
        elif wind_speed > 10:
            wind_context = "There's a gentle breeze."
        else:
            wind_context = "The air is fairly calm."
        
        # Combine everything with proper spacing
        return f"{location_context}, {temp_context} {condition_context} {wind_context}"

    def process_query(self, user_input: str, streaming_callback: Optional[Callable] = None) -> str:
        """
        Process weather query - only returns the summary, doesn't stream it.
        """
        try:
            # Extract location
            location_type, location_name, coordinates = self.extract_location(user_input)
            
            # Get weather summary
            weather_summary = self.get_weather_summary(coordinates, location_name, location_type)
            
            # Just return the summary - let the main GUI handle streaming
            return weather_summary
            
        except Exception as e:
            error_msg = f"Sorry, I encountered an issue getting weather information. Please try again."
            print(f"❌ Weather module error: {e}")
            return error_msg


# Factory function for module creation
def create_weather_module():
    """Create and return a WeatherModule instance"""
    return WeatherModule()


# Main processing function (required interface for module system)
def process(user_input: str, streaming_callback: Optional[Callable] = None) -> str:
    """
    Main processing function for weather module.
    This is the function called by the routing system.
    """
    module = WeatherModule()
    
    # Just return the summary - streaming is handled by main GUI
    return module.process_query(user_input)