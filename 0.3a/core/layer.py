"""
Streaming Layer for Edgar AI Assistant

This module acts as an intermediary between the GUI and AI engine,
handling all streaming functionality and communication.
"""

import time
import re
import threading
from typing import Callable, Optional, Dict, Any, List, Tuple
from .ai_engine import AdvancedChatbot

class StreamingLayer:
    """
    Handles streaming communication between GUI and AI engine.
    Manages text streaming, callbacks, and state synchronization.
    """
    
    def __init__(self, config_file: str = "config.cfg", **kwargs):
        self.config_file = config_file
        
        # Streaming state
        self.is_streaming = False
        self.current_stream_text = ""
        self.streaming_thread = None
        self.should_stop_streaming = False
        
        # Callbacks for GUI communication
        self.streaming_callback = kwargs.get('streaming_callback', None)
        self.thinking_callback = kwargs.get('thinking_callback', None)
        self.response_complete_callback = kwargs.get('response_complete_callback', None)
        self.status_update_callback = kwargs.get('status_update_callback', None)
        self.error_callback = kwargs.get('error_callback', None)
        
        # Initialize AI engine
        self.ai_engine = AdvancedChatbot(
            config_file=config_file,
            auto_start_chat=False,
            streaming_callback=self._handle_engine_streaming,
            thinking_callback=self._handle_engine_thinking,
            response_complete_callback=self._handle_engine_response_complete
        )
        
        # Streaming configuration
        self.streaming_speed = self.ai_engine.streaming_speed
        self.additional_info_speed = self.ai_engine.additional_info_speed
        self.letter_streaming = self.ai_engine.letter_streaming
        self.speed_limit = self.ai_engine.speed_limit
        
        print("✅ Streaming Layer initialized")
    
    def _handle_engine_streaming(self, text: str):
        """Handle streaming text from AI engine"""
        if self.streaming_callback:
            self.streaming_callback(text)
    
    def _handle_engine_thinking(self, text: str):
        """Handle thinking indicators from AI engine"""
        if self.thinking_callback:
            self.thinking_callback(text)
    
    def _handle_engine_response_complete(self):
        """Handle response completion from AI engine"""
        if self.response_complete_callback:
            self.response_complete_callback()
    
    def _update_status(self, status: str):
        """Update status through callback"""
        if self.status_update_callback:
            self.status_update_callback(status)
    
    def _handle_error(self, error: str):
        """Handle errors through callback"""
        if self.error_callback:
            self.error_callback(error)
    
    # ===== PUBLIC API FOR GUI =====
    
    def process_message(self, user_input: str) -> List[Tuple]:
        """
        Process user message through AI engine.
        Returns list of responses for the GUI to handle.
        """
        try:
            self._update_status("Processing your message...")
            
            # Process through AI engine
            responses = self.ai_engine.process_multiple_questions(user_input)
            
            self._update_status("Response ready")
            return responses
            
        except Exception as e:
            error_msg = f"Error processing message: {str(e)}"
            self._handle_error(error_msg)
            self._update_status("Error occurred")
            return []
    
    def stream_text(self, text: str, prefix: str = "", wpm: int = None, 
                   callback: Callable = None) -> str:
        """
        Stream text with adjustable speed.
        Can use either AI engine streaming or local streaming.
        """
        if wpm is None:
            wpm = self.streaming_speed
        
        # Use AI engine's streaming if no custom callback provided
        if callback is None and self.streaming_callback:
            return self.ai_engine.stream_text(text, prefix, wpm, self.streaming_callback)
        elif callback:
            return self.ai_engine.stream_text(text, prefix, wpm, callback)
        else:
            # Fallback to local streaming
            return self._local_stream_text(text, prefix, wpm)
    
    def _local_stream_text(self, text: str, prefix: str = "", wpm: int = None) -> str:
        """Local streaming implementation as fallback"""
        if wpm is None:
            wpm = self.streaming_speed
            
        if not self.speed_limit:
            wpm = 0
            
        if wpm == 0:
            full_text = f"{prefix}{text}"
            if self.streaming_callback:
                self.streaming_callback(full_text)
            return full_text
        
        words_per_second = wpm / 60.0
        delay_per_word = 1.0 / words_per_second if words_per_second > 0 else 0
        
        # Use regex to split while preserving all whitespace
        tokens = re.findall(r'\S+\s*', text)
        
        full_output = prefix
        if self.streaming_callback:
            self.streaming_callback(prefix)
        
        for token in tokens:
            full_output += token
            if self.streaming_callback:
                self.streaming_callback(token)
            
            # Calculate dynamic delay based on token characteristics
            base_delay = delay_per_word
            
            # Longer pauses for punctuation
            if token.rstrip().endswith(('.', '!', '?')):
                base_delay *= 1.8
            elif token.rstrip().endswith((',', ';', ':')):
                base_delay *= 1.3
            
            # Check for newlines in the whitespace part
            if '\n' in token:
                newline_count = token.count('\n')
                base_delay *= (1.5 + (newline_count * 0.5))
            
            time.sleep(base_delay)
        
        # Always end with newline if not already there
        if not full_output.endswith('\n'):
            if self.streaming_callback:
                self.streaming_callback('\n')
            full_output += '\n'
            
        return full_output
    
    def get_available_models(self) -> list:
        """Get list of available models"""
        return self.ai_engine.get_available_models()
    
    def change_model(self, model_name: str) -> bool:
        """Change the current AI model"""
        try:
            self._update_status(f"Loading {model_name}...")
            
            # Update AI engine model
            self.ai_engine.current_model = model_name
            success = self.ai_engine.load_model_data()
            
            if success:
                self._update_status(f"Model loaded: {model_name}")
                return True
            else:
                self._update_status("Model load failed")
                return False
                
        except Exception as e:
            error_msg = f"Error changing model: {str(e)}"
            self._handle_error(error_msg)
            self._update_status("Model change failed")
            return False
    
    def refresh_models(self) -> list:
        """Refresh the list of available models"""
        return self.ai_engine.get_available_models()
    
    def get_context_summary(self) -> str:
        """Get current conversation context summary"""
        return self.ai_engine.get_context_summary()
    
    def get_statistics(self) -> dict:
        """Get chatbot performance statistics"""
        return self.ai_engine.performance_stats
    
    def reset_conversation(self):
        """Reset conversation context"""
        self.ai_engine.reset_conversation_context()
        self._update_status("Conversation reset")
    
    def get_current_model(self) -> str:
        """Get current model name"""
        return getattr(self.ai_engine, 'current_model', 'Unknown')
    
    def get_qa_groups_count(self) -> int:
        """Get number of QA groups in current model"""
        return len(self.ai_engine.qa_groups) if hasattr(self.ai_engine, 'qa_groups') else 0
    
    # ===== CONFIGURATION METHODS =====
    
    def set_streaming_speed(self, wpm: int):
        """Set main response streaming speed"""
        self.streaming_speed = max(0, wpm)
        self.ai_engine.set_streaming_speed(wpm)
    
    def set_additional_info_speed(self, wpm: int):
        """Set additional info streaming speed"""
        self.additional_info_speed = max(0, wpm)
        self.ai_engine.set_additional_info_speed(wpm)
    
    def toggle_letter_streaming(self):
        """Toggle between word and letter streaming"""
        self.letter_streaming = not self.letter_streaming
        self.ai_engine.toggle_letter_streaming()
    
    def set_confidence_requirement(self, requirement: float):
        """Set minimum confidence requirement for answers"""
        self.ai_engine.set_confidence_requirement(requirement)
    
    def toggle_speed_limit(self):
        """Toggle speed limiting on/off"""
        self.speed_limit = not self.speed_limit
        self.ai_engine.toggle_speed_limit()
    
    def get_configuration(self) -> Dict[str, Any]:
        """Get current configuration"""
        return {
            'streaming_speed': self.streaming_speed,
            'additional_info_speed': self.additional_info_speed,
            'letter_streaming': self.letter_streaming,
            'speed_limit': self.speed_limit,
            'confidence_requirement': self.ai_engine.answer_confidence_requirement,
            'current_model': self.get_current_model(),
            'qa_groups_count': self.get_qa_groups_count()
        }
    
    def stop_streaming(self):
        """Stop any ongoing streaming"""
        self.should_stop_streaming = True
        if self.streaming_thread and self.streaming_thread.is_alive():
            self.streaming_thread.join(timeout=1.0)
        self.should_stop_streaming = False
    
    def is_processing(self) -> bool:
        """Check if AI engine is currently processing"""
        # You might want to add more sophisticated state tracking
        return self.is_streaming


# Factory function for easy creation
def create_streaming_layer(config_file: str = "config.cfg", **kwargs) -> StreamingLayer:
    """
    Create and return a new StreamingLayer instance.
    
    Args:
        config_file: Path to configuration file
        **kwargs: Additional arguments including callbacks:
            - streaming_callback: Callback for streaming text
            - thinking_callback: Callback for thinking indicators
            - response_complete_callback: Callback for response completion
            - status_update_callback: Callback for status updates
            - error_callback: Callback for errors
    
    Returns:
        StreamingLayer instance
    """
    return StreamingLayer(config_file, **kwargs)


# Test function for standalone testing
def test_streaming_layer():
    """Test the streaming layer independently"""
    print("🧪 Testing Streaming Layer...")
    
    def test_streaming_callback(text):
        print(f"STREAM: {text}", end='')
    
    def test_thinking_callback(text):
        print(f"THINKING: {text}")
    
    def test_status_callback(status):
        print(f"STATUS: {status}")
    
    layer = create_streaming_layer(
        streaming_callback=test_streaming_callback,
        thinking_callback=test_thinking_callback,
        status_update_callback=test_status_callback
    )
    
    print("✅ Streaming Layer test completed")
    return layer


if __name__ == "__main__":
    test_streaming_layer()