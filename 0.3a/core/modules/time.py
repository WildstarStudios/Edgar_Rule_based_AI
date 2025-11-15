"""
Time Module for Edgar AI Assistant
Handles time-related queries with summary responses.
"""

import datetime
from typing import Optional
try:
    from fuzzywuzzy import process as fuzzy_process, fuzz
    FUZZY_AVAILABLE = True
except ImportError:
    FUZZY_AVAILABLE = False
    print("⚠️  fuzzywuzzy not installed. Install with: pip install fuzzywuzzy python-levenshtein")

class TimeModule:
    def __init__(self):
        self.name = "Time Module"
        self.version = "1.1"  # Updated version
        
        # Expanded time zone mappings for global locations
        self.timezone_mapping = {
            # North America
            "new york": "America/New_York",
            "los angeles": "America/Los_Angeles", 
            "chicago": "America/Chicago",
            "denver": "America/Denver",
            "phoenix": "America/Phoenix",
            "seattle": "America/Los_Angeles",  # Same as LA
            "san francisco": "America/Los_Angeles",
            "miami": "America/New_York",  # Same as NY
            "atlanta": "America/New_York",
            "washington": "America/New_York",
            "boston": "America/New_York",
            "toronto": "America/Toronto",
            "vancouver": "America/Vancouver",
            "montreal": "America/Toronto",  # Same as Toronto
            "new york city": "America/New_York",
            "nyc": "America/New_York",
            "la": "America/Los_Angeles",
            "sf": "America/Los_Angeles",
            "dc": "America/New_York",
            
            # Europe
            "london": "Europe/London",
            "paris": "Europe/Paris",
            "berlin": "Europe/Berlin",
            "rome": "Europe/Rome",
            "madrid": "Europe/Madrid",
            "barcelona": "Europe/Madrid",
            "amsterdam": "Europe/Amsterdam",
            "brussels": "Europe/Brussels",
            "vienna": "Europe/Vienna",
            "prague": "Europe/Prague",
            "budapest": "Europe/Budapest",
            "warsaw": "Europe/Warsaw",
            "lisbon": "Europe/Lisbon",
            "dublin": "Europe/Dublin",
            "edinburgh": "Europe/London",  # Same as London
            "manchester": "Europe/London",
            "milan": "Europe/Rome",  # Same as Rome
            "athens": "Europe/Athens",
            "stockholm": "Europe/Stockholm",
            "oslo": "Europe/Oslo",
            "copenhagen": "Europe/Copenhagen",
            "helsinki": "Europe/Helsinki",
            
            # Asia
            "tokyo": "Asia/Tokyo",
            "beijing": "Asia/Shanghai",
            "shanghai": "Asia/Shanghai",
            "hong kong": "Asia/Hong_Kong",
            "singapore": "Asia/Singapore",
            "seoul": "Asia/Seoul",
            "bangkok": "Asia/Bangkok",
            "mumbai": "Asia/Kolkata",
            "delhi": "Asia/Kolkata",
            "dubai": "Asia/Dubai",
            "istanbul": "Europe/Istanbul",
            "taipei": "Asia/Taipei",
            "manila": "Asia/Manila",
            "jakarta": "Asia/Jakarta",
            "kuala lumpur": "Asia/Kuala_Lumpur",
            
            # Australia & Oceania
            "sydney": "Australia/Sydney",
            "melbourne": "Australia/Melbourne",
            "brisbane": "Australia/Brisbane",
            "perth": "Australia/Perth",
            "auckland": "Pacific/Auckland",
            "wellington": "Pacific/Auckland",  # Same as Auckland
            
            # South America
            "sao paulo": "America/Sao_Paulo",
            "rio de janeiro": "America/Sao_Paulo",  # Same as Sao Paulo
            "buenos aires": "America/Argentina/Buenos_Aires",
            "lima": "America/Lima",
            "bogota": "America/Bogota",
            "santiago": "America/Santiago",
            
            # Africa
            "cairo": "Africa/Cairo",
            "cape town": "Africa/Johannesburg",  # Same as Johannesburg
            "nairobi": "Africa/Nairobi",
            "lagos": "Africa/Lagos",
            "johannesburg": "Africa/Johannesburg",
            "casablanca": "Africa/Casablanca",
            
            # Timezone aliases
            "est": "America/New_York",
            "eastern": "America/New_York",
            "cst": "America/Chicago", 
            "central": "America/Chicago",
            "mst": "America/Denver",
            "mountain": "America/Denver",
            "pst": "America/Los_Angeles",
            "pacific": "America/Los_Angeles",
            "akst": "America/Anchorage",
            "alaska": "America/Anchorage",
            "hst": "Pacific/Honolulu",
            "hawaii": "Pacific/Honolulu",
            "gmt": "Europe/London",
            "utc": "UTC",
            "zulu": "UTC"
        }

    def fuzzy_match_location(self, user_input: str) -> Optional[tuple]:
        """
        Use fuzzy matching to find the best location match from user input.
        Returns (location_name, confidence_score, timezone_key) or None if no good match.
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
            if query in ["the", "a", "in", "at", "for", "time", "what", "is", "current", "now"]:
                continue
                
            matches = fuzzy_process.extract(query, self.timezone_mapping.keys(), limit=1)
            if matches:
                location, score = matches[0]
                if score > best_score and score > 75:  # Threshold for acceptable match
                    best_match = (location, score, self.timezone_mapping[location])
                    best_score = score
        
        return best_match if best_match else None

    def extract_location(self, user_input: str) -> tuple:
        """
        Extract location from user input using both exact and fuzzy matching.
        Returns (location_type, location_name, timezone_key)
        """
        user_input = user_input.lower()
        
        # Skip if it's clearly a general time query
        general_queries = [
            "time", "what time", "current time", "what's the time", "what is the time",
            "time now", "what time is it", "tell me the time"
        ]
        
        is_general_query = any(query in user_input for query in general_queries)
        has_location_keyword = any(keyword in user_input for keyword in ["in ", "at ", "for "])
        
        # If it's a general time query without location keywords, use local time
        if is_general_query and not has_location_keyword:
            return "local", "your location", None
        
        # First, try exact matching for common locations
        for location, timezone_key in self.timezone_mapping.items():
            if location in user_input:
                print(f"📍 Time module exact match found: {location.title()}")
                return "specified", location.title(), timezone_key
        
        # Try fuzzy matching if exact match fails
        fuzzy_result = self.fuzzy_match_location(user_input)
        if fuzzy_result:
            location, confidence, timezone_key = fuzzy_result
            print(f"📍 Time module fuzzy matched '{location}' with {confidence}% confidence")
            return "specified", location.title(), timezone_key
        
        # Check for location patterns as fallback
        location_patterns = ["in ", "at ", "for "]
        for pattern in location_patterns:
            if pattern in user_input:
                start_idx = user_input.find(pattern) + len(pattern)
                remaining_text = user_input[start_idx:].strip()
                
                # Try exact match on remaining text
                for location, timezone_key in self.timezone_mapping.items():
                    if location in remaining_text:
                        print(f"📍 Time module pattern match found: {location.title()}")
                        return "specified", location.title(), timezone_key
                
                # Try fuzzy match on remaining text
                fuzzy_result = self.fuzzy_match_location(remaining_text)
                if fuzzy_result:
                    location, confidence, timezone_key = fuzzy_result
                    print(f"📍 Time module fuzzy matched '{location}' with {confidence}% confidence")
                    return "specified", location.title(), timezone_key
        
        # No location specified - use local time with better messaging
        print("📍 No location specified, using local time")
        return "local", "your location", None

    def get_time_summary(self, location_type: str, location_name: str, timezone_key: str) -> str:
        """
        Get time summary for the specified location.
        """
        try:
            if location_type == "specified":
                # Get time for specified location
                import pytz
                tz = pytz.timezone(timezone_key)
                current_time = datetime.datetime.now(tz)
                
                # Create natural language summary
                summary = self._create_time_summary(current_time, location_name, "specified")
            else:
                # Get local time
                current_time = datetime.datetime.now()
                summary = self._create_time_summary(current_time, location_name, "local")
            
            return summary
            
        except Exception as e:
            print(f"❌ Error getting time data: {e}")
            return f"Unable to get time information for {location_name}. Please try again."

    def _create_time_summary(self, current_time: datetime.datetime, location: str, location_type: str) -> str:
        """Create a natural language time summary"""
        
        # Format time components
        day_name = current_time.strftime('%A')
        month_name = current_time.strftime('%B')
        day_number = current_time.day
        year = current_time.year
        time_12hr = current_time.strftime('%I:%M %p').lstrip('0')  # Remove leading zero
        time_24hr = current_time.strftime('%H:%M')
        
        # Get time of day context
        hour = current_time.hour
        if 5 <= hour < 12:
            time_of_day = "morning"
        elif 12 <= hour < 17:
            time_of_day = "afternoon"
        elif 17 <= hour < 21:
            time_of_day = "evening"
        else:
            time_of_day = "night"
        
        # Create location context
        if location_type == "specified":
            location_context = f"in {location}"
        else:
            location_context = "for your location"
        
        # Get timezone info if available
        timezone_info = ""
        try:
            if hasattr(current_time, 'tzinfo') and current_time.tzinfo:
                tz_name = current_time.tzinfo.tzname(current_time)
                if tz_name:
                    timezone_info = f" ({tz_name})"
        except:
            pass
        
        # Create the summary
        summary = f"🕐 It's {time_of_day} {location_context}. The current time is {time_12hr}{timezone_info} ({time_24hr} in 24-hour format). Today is {day_name}, {month_name} {self._get_ordinal(day_number)}, {year}."
        
        return summary

    def _get_ordinal(self, n: int) -> str:
        """Convert number to ordinal (1st, 2nd, 3rd, etc.)"""
        if 11 <= (n % 100) <= 13:
            suffix = 'th'
        else:
            suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
        return f"{n}{suffix}"

    def process(self, user_input: str, api) -> str:
        """
        Process time query using the streaming API.
        Returns the time summary string.
        """
        try:
            # Use API to stream thinking indicator
            api.stream_thinking("🕐 Checking the current time...")
            
            # Extract location information
            location_type, location_name, timezone_key = self.extract_location(user_input)
            
            # Get time summary
            time_summary = self.get_time_summary(location_type, location_name, timezone_key)
            
            # Return the summary - the layer will handle streaming
            return time_summary
            
        except Exception as e:
            error_msg = f"Sorry, I encountered an issue getting time information. Please try again."
            print(f"❌ Time module error: {e}")
            return error_msg


# Factory function for module creation
def create_time_module():
    """Create and return a TimeModule instance"""
    return TimeModule()


# Main processing function (required interface for module system)
def process(user_input: str, api) -> str:
    """
    Main processing function for time module.
    This is the function called by the routing system.
    """
    module = TimeModule()
    
    # Process using the API and return summary
    return module.process(user_input, api)