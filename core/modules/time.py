"""
Time module for Edgar AI
Returns current time information
"""
import datetime

module_mode = False  # Single response module

def process(input_text: str, context: dict) -> str:
    """Process time request"""
    now = datetime.datetime.now()
    
    if "time" in input_text.lower():
        return f"the current time is {now.strftime('%I:%M %p')}"
    elif "date" in input_text.lower():
        return f"today's date is {now.strftime('%B %d, %Y')}"
    else:
        return f"The current date and time is {now.strftime('%B %d, %Y at %I:%M %p')}"