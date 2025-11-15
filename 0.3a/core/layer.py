"""
Streaming Layer for Edgar AI Assistant

This module acts as an intermediary between the GUI and AI engine,
handling all streaming functionality and communication.
"""

import time
import re
import threading
import json
import os
from typing import Callable, Optional, Dict, Any, List, Tuple
from difflib import SequenceMatcher
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
        
        # Routing configuration
        self.routing_config = None
        self.routing_file = "resources/route.json"
        self.load_routing_config()
        
        print("✅ Streaming Layer initialized with routing support")
    
    def load_routing_config(self):
        """Load routing configuration from JSON file"""
        try:
            if os.path.exists(self.routing_file):
                with open(self.routing_file, 'r', encoding='utf-8') as f:
                    self.routing_config = json.load(f)
                print(f"✅ Loaded {len(self.routing_config.get('routing_groups', []))} routing groups")
            else:
                self.routing_config = {"routing_groups": [], "available_engines": [], "version": "1.0"}
                print("⚠️  No routing config found, using empty configuration")
        except Exception as e:
            print(f"❌ Error loading routing config: {e}")
            self.routing_config = {"routing_groups": [], "available_engines": [], "version": "1.0"}
    
    def save_routing_config(self):
        """Save routing configuration to JSON file"""
        try:
            os.makedirs("resources", exist_ok=True)
            with open(self.routing_file, 'w', encoding='utf-8') as f:
                json.dump(self.routing_config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"❌ Error saving routing config: {e}")
            return False
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts using SequenceMatcher"""
        return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()
    
    def _find_best_route(self, user_input: str) -> Tuple[Optional[Dict], float]:
        """
        Find the best matching routing group for user input.
        Returns (routing_group, confidence_score)
        """
        if not self.routing_config or not self.routing_config.get('routing_groups'):
            return None, 0.0
        
        best_match = None
        best_confidence = 0.0
        
        for group in self.routing_config['routing_groups']:
            # Calculate confidence for each question in the group
            max_group_confidence = 0.0
            for question in group.get('questions', []):
                confidence = self._calculate_similarity(user_input, question)
                if confidence > max_group_confidence:
                    max_group_confidence = confidence
            
            # Apply word limit penalty if enabled
            if group.get('word_limit_enabled', False):
                word_count = len(user_input.split())
                max_words = group.get('max_words', 0)
                if word_count > max_words:
                    penalty = (word_count - max_words) * group.get('penalty_per_word', 0.02)
                    max_group_confidence = max(0.0, max_group_confidence - penalty)
            
            # Check if this group has the best confidence that meets threshold
            threshold = group.get('confidence_threshold', 0.6)
            if max_group_confidence >= threshold and max_group_confidence > best_confidence:
                best_confidence = max_group_confidence
                best_match = group
        
        return best_match, best_confidence
    
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
    
    def _execute_module(self, module_name: str, user_input: str) -> List[Tuple]:
        """
        Execute a module with the given user input.
        Returns responses in the same format as AI engine.
        """
        try:
            # Import and execute the module
            module_path = f"core.modules.{module_name}"
            module = __import__(module_path, fromlist=[''])
            
            # Call the module's process function with streaming callback
            if hasattr(module, 'process'):
                # Pass the streaming callback to the module for real-time streaming
                result = module.process(user_input, streaming_callback=self.streaming_callback)
                
                # Convert module result to standard response format
                if isinstance(result, str):
                    return [(result, 1.0, f"Module: {module_name}")]
                elif isinstance(result, list):
                    return result
                else:
                    return [(str(result), 1.0, f"Module: {module_name}")]
            else:
                return [("Module doesn't have a 'process' function", 0.0, f"Module: {module_name}")]
                
        except ImportError as e:
            error_msg = f"Could not import module '{module_name}': {str(e)}"
            print(f"❌ {error_msg}")
            if self.streaming_callback:
                self.streaming_callback(f"Error: Module '{module_name}' not found.\n")
            return [(f"Error: Module '{module_name}' not found or cannot be loaded.", 0.0, "Module Error")]
        except Exception as e:
            error_msg = f"Error executing module '{module_name}': {str(e)}"
            print(f"❌ {error_msg}")
            if self.streaming_callback:
                self.streaming_callback(f"Error executing module: {str(e)}\n")
            return [(f"Error executing module: {str(e)}", 0.0, "Module Error")]
    
    # ===== PUBLIC API FOR GUI =====
    
    def process_message(self, user_input: str) -> List[Tuple]:
        """
        Process user message through routing system or AI engine.
        Returns list of responses for the GUI to handle.
        """
        try:
            self._update_status("Processing your message...")
            
            # First, try to find a routing match
            route_match, confidence = self._find_best_route(user_input)
            
            if route_match and route_match.get('engine') != "None":
                # Route to specified module
                module_name = route_match['engine']
                self._update_status(f"Routing to module: {module_name} (confidence: {confidence:.2f})")
                
                responses = self._execute_module(module_name, user_input)
                
                # Add routing info to responses
                if responses:
                    routed_responses = []
                    for response in responses:
                        if len(response) == 3:
                            answer, conf, source = response
                            routed_responses.append((answer, conf, f"Routed: {source}"))
                        else:
                            routed_responses.append(response)
                    responses = routed_responses
                
            else:
                # No route found or route is "None", use AI engine
                if route_match:
                    self._update_status(f"No module specified, using AI engine (confidence: {confidence:.2f})")
                else:
                    self._update_status("No route found, using AI engine")
                
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
    
    # ===== ROUTING SYSTEM METHODS =====
    
    def get_routing_groups(self) -> List[Dict]:
        """Get all routing groups"""
        return self.routing_config.get('routing_groups', []) if self.routing_config else []
    
    def add_routing_group(self, group_data: Dict) -> bool:
        """Add a new routing group"""
        if not self.routing_config:
            self.routing_config = {"routing_groups": [], "available_engines": [], "version": "1.0"}
        
        self.routing_config['routing_groups'].append(group_data)
        
        # Update available engines
        engine = group_data.get('engine')
        if engine and engine != "None" and engine not in self.routing_config['available_engines']:
            self.routing_config['available_engines'].append(engine)
        
        return self.save_routing_config()
    
    def update_routing_group(self, index: int, group_data: Dict) -> bool:
        """Update an existing routing group"""
        if not self.routing_config or index >= len(self.routing_config['routing_groups']):
            return False
        
        self.routing_config['routing_groups'][index] = group_data
        
        # Rebuild available engines list
        engines = set()
        for group in self.routing_config['routing_groups']:
            engine = group.get('engine')
            if engine and engine != "None":
                engines.add(engine)
        
        self.routing_config['available_engines'] = list(engines)
        
        return self.save_routing_config()
    
    def delete_routing_group(self, index: int) -> bool:
        """Delete a routing group"""
        if not self.routing_config or index >= len(self.routing_config['routing_groups']):
            return False
        
        self.routing_config['routing_groups'].pop(index)
        
        # Rebuild available engines list
        engines = set()
        for group in self.routing_config['routing_groups']:
            engine = group.get('engine')
            if engine and engine != "None":
                engines.add(engine)
        
        self.routing_config['available_engines'] = list(engines)
        
        return self.save_routing_config()
    
    def refresh_routing_config(self):
        """Reload routing configuration from file"""
        self.load_routing_config()
    
    def get_routing_stats(self) -> Dict[str, Any]:
        """Get routing system statistics"""
        groups = self.get_routing_groups()
        total_questions = sum(len(group.get('questions', [])) for group in groups)
        active_modules = set(group.get('engine') for group in groups if group.get('engine') != "None")
        
        return {
            'total_groups': len(groups),
            'total_questions': total_questions,
            'active_modules': len(active_modules),
            'modules_list': list(active_modules)
        }
    
    def test_routing_match(self, user_input: str) -> Dict[str, Any]:
        """
        Test routing matching for a given input without executing.
        Useful for debugging and testing.
        """
        route_match, confidence = self._find_best_route(user_input)
        
        result = {
            'input': user_input,
            'matched': route_match is not None,
            'confidence': confidence,
            'route_group': None,
            'module': None
        }
        
        if route_match:
            result['route_group'] = route_match['group_name']
            result['module'] = route_match['engine']
            result['threshold'] = route_match.get('confidence_threshold', 0.6)
            result['word_limit_enabled'] = route_match.get('word_limit_enabled', False)
            
            if result['word_limit_enabled']:
                result['max_words'] = route_match.get('max_words', 0)
                result['penalty_per_word'] = route_match.get('penalty_per_word', 0.0)
        
        return result
    
    def get_available_modules(self) -> List[str]:
        """Get list of available modules from core/modules folder"""
        modules_folder = "core/modules"
        modules = []
        
        if os.path.exists(modules_folder):
            for file in os.listdir(modules_folder):
                if file.endswith('.py') and not file.startswith('_'):
                    module_name = file[:-3]  # Remove .py extension
                    modules.append(module_name)
        
        return sorted(modules)
    
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
        routing_stats = self.get_routing_stats()
        
        return {
            'streaming_speed': self.streaming_speed,
            'additional_info_speed': self.additional_info_speed,
            'letter_streaming': self.letter_streaming,
            'speed_limit': self.speed_limit,
            'confidence_requirement': self.ai_engine.answer_confidence_requirement,
            'current_model': self.get_current_model(),
            'qa_groups_count': self.get_qa_groups_count(),
            'routing_groups_count': routing_stats['total_groups'],
            'routing_questions_count': routing_stats['total_questions'],
            'active_modules_count': routing_stats['active_modules'],
            'available_modules': self.get_available_modules()
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
    print("🧪 Testing Streaming Layer with Routing...")
    
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
    
    # Test routing configuration
    print(f"Routing groups: {len(layer.get_routing_groups())}")
    print(f"Routing stats: {layer.get_routing_stats()}")
    print(f"Available modules: {layer.get_available_modules()}")
    
    # Test routing matching
    test_inputs = [
        "What's the weather like?",
        "What time is it?",
        "Tell me a joke"
    ]
    
    for test_input in test_inputs:
        match_result = layer.test_routing_match(test_input)
        print(f"Input: '{test_input}' -> {match_result}")
    
    print("✅ Streaming Layer test completed")
    return layer


if __name__ == "__main__":
    test_streaming_layer()