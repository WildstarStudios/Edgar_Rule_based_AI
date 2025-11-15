"""
Time Module for Edgar AI Assistant
Handles time-related queries with streaming response.
"""

import datetime
import time as time_module
from typing import Optional, Callable

def process(user_input: str, streaming_callback: Optional[Callable] = None) -> str:
    """Process time queries with streaming"""
    current_time = datetime.datetime.now()
    
    response = (f"🕐 Current Date and Time:\n"
                f"• Date: {current_time.strftime('%A, %B %d, %Y')}\n"
                f"• Time: {current_time.strftime('%I:%M:%S %p')}\n"
                f"• Timezone: {current_time.astimezone().tzinfo}")
    
    if streaming_callback:
        # Stream the response with natural pacing
        lines = response.split('\n')
        for line in lines:
            if line.strip():
                words = line.split()
                for word in words:
                    streaming_callback(word + ' ')
                    time_module.sleep(0.03)
                streaming_callback('\n')
                time_module.sleep(0.1)
    else:
        return response
    
    return response