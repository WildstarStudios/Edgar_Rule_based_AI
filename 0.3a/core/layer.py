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
import configparser
from typing import Callable, Optional, Dict, Any, List, Tuple
from difflib import SequenceMatcher
from fuzzywuzzy import fuzz, process

# Import AI engine
try:
    from .ai_engine import AdvancedChatbot
except ImportError:
    from ai_engine import AdvancedChatbot

class StreamingLayer:
    """
    Handles streaming communication between GUI and AI engine.
    Manages text streaming, callbacks, and state synchronization.
    """
    
    def __init__(self, config_file: str = "config.cfg", **kwargs):
        self.config_file = config_file
        
        # Load configuration
        self.config = self.load_configuration()
        
        # Streaming configuration from config
        self.streaming_speed = self.config.getint('ai_engine', 'streaming_speed', fallback=10000)
        self.additional_info_speed = self.config.getint('ai_engine', 'additional_info_speed', fallback=10000)
        self.letter_streaming = self.config.getboolean('ai_engine', 'letter_streaming', fallback=False)
        self.speed_limit = self.config.getboolean('ai_engine', 'speed_limit', fallback=True)
        
        # Strict routing threshold - FIXED: Only use this, not JSON threshold
        self.ROUTING_THRESHOLD = 0.75  # Fixed threshold for all routing
        
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
        
        # Initialize AI engine WITHOUT streaming callbacks
        # We'll handle all streaming in this layer
        self.ai_engine = AdvancedChatbot(
            config_file=config_file,
            auto_start_chat=False,
            streaming_callback=None,  # We handle streaming in layer
            thinking_callback=None,   # We handle thinking in layer
            response_complete_callback=None  # We handle completion in layer
        )
        
        # Routing configuration
        self.routing_config = None
        self.routing_file = "resources/route.json"
        self.load_routing_config()
        
        # API state for modules
        self.api_connections = {}
        
        print("✅ Streaming Layer initialized with complete streaming control")
        print(f"   Routing threshold: {self.ROUTING_THRESHOLD}")
        print(f"   Streaming speed: {self.streaming_speed} WPM")
        print(f"   Letter streaming: {self.letter_streaming}")
    
    def load_configuration(self) -> configparser.ConfigParser:
        """Load configuration from file"""
        config = configparser.ConfigParser()
        
        defaults = {
            'ai_engine': {
                'streaming_speed': '10000',
                'additional_info_speed': '10000',
                'letter_streaming': 'False',
                'speed_limit': 'True'
            }
        }
        
        for section, options in defaults.items():
            if not config.has_section(section):
                config.add_section(section)
            for key, value in options.items():
                config.set(section, key, value)
        
        if os.path.exists(self.config_file):
            config.read(self.config_file)
            print(f"✅ Loaded configuration from {self.config_file}")
        else:
            with open(self.config_file, 'w') as f:
                config.write(f)
            print(f"✅ Created default configuration file: {self.config_file}")
        
        return config
    
    def save_configuration(self):
        """Save current configuration to file"""
        self.config.set('ai_engine', 'streaming_speed', str(self.streaming_speed))
        self.config.set('ai_engine', 'additional_info_speed', str(self.additional_info_speed))
        self.config.set('ai_engine', 'letter_streaming', str(self.letter_streaming))
        self.config.set('ai_engine', 'speed_limit', str(self.speed_limit))
        
        with open(self.config_file, 'w') as f:
            self.config.write(f)
        print(f"✅ Configuration saved to {self.config_file}")
    
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
    
    def _calculate_fuzzy_containment_confidence(self, user_input: str, group_questions: List[str], 
                                              word_limit_enabled: bool, max_words: int, penalty_per_word: float) -> float:
        """
        Calculate confidence based on fuzzy containment matching with word limit penalties.
        
        Uses fuzzywuzzy to handle misspellings while maintaining strict word limits.
        
        Returns 1.0 if there's a perfect fuzzy containment match within word limits.
        Returns lower confidence if word limits are exceeded.
        Returns 0.0 if no fuzzy containment match.
        """
        user_input_lower = user_input.lower().strip()
        user_word_count = len(user_input_lower.split())
        
        # Check for fuzzy containment in any of the group's questions
        for question in group_questions:
            question_lower = question.lower().strip()
            
            # Use fuzzy partial ratio to handle misspellings and partial matches
            # Partial ratio is good for handling strings that are similar but not identical
            fuzzy_score = fuzz.partial_ratio(question_lower, user_input_lower)
            
            # Also check token set ratio for word order flexibility
            token_set_score = fuzz.token_set_ratio(question_lower, user_input_lower)
            
            # Use the higher of the two scores
            best_fuzzy_score = max(fuzzy_score, token_set_score)
            
            # High threshold for fuzzy matching (80% similarity)
            if best_fuzzy_score >= 80:
                # Perfect fuzzy match - starts with 1.0 confidence
                base_confidence = 1.0
                
                # Apply word limit penalty if enabled and user input exceeds max words
                if word_limit_enabled and user_word_count > max_words:
                    extra_words = user_word_count - max_words
                    penalty = extra_words * penalty_per_word
                    base_confidence = max(0.0, base_confidence - penalty)
                
                return base_confidence
        
        # No fuzzy containment match found
        return 0.0
    
    def _find_best_route(self, user_input: str) -> Tuple[Optional[Dict], float]:
        """
        Find the best matching routing group for user input using fuzzy containment matching.
        Returns (routing_group, confidence_score)
        Uses strict word limit penalties with fuzzy matching for misspellings.
        """
        if not self.routing_config or not self.routing_config.get('routing_groups'):
            return None, 0.0
        
        best_match = None
        best_confidence = 0.0
        
        for group in self.routing_config['routing_groups']:
            word_limit_enabled = group.get('word_limit_enabled', False)
            max_words = group.get('max_words', 10)  # Default to 10 if not specified
            penalty_per_word = group.get('penalty_per_word', 0.1)  # Default 10% penalty per extra word
            
            confidence = self._calculate_fuzzy_containment_confidence(
                user_input=user_input,
                group_questions=group.get('questions', []),
                word_limit_enabled=word_limit_enabled,
                max_words=max_words,
                penalty_per_word=penalty_per_word
            )
            
            # FIXED: Only use the fixed ROUTING_THRESHOLD, not JSON threshold
            if confidence >= self.ROUTING_THRESHOLD and confidence > best_confidence:
                best_confidence = confidence
                best_match = group
        
        return best_match, best_confidence
    
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
            
            # Create API connection for the module
            api_connection = StreamingAPI(self, module_name)
            
            # Call the module's process function with API connection
            if hasattr(module, 'process'):
                result = module.process(user_input, api_connection)
                
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
            self.stream_text(f"Error: Module '{module_name}' not found.\n")
            return [(f"Error: Module '{module_name}' not found or cannot be loaded.", 0.0, "Module Error")]
        except Exception as e:
            error_msg = f"Error executing module '{module_name}': {str(e)}"
            print(f"❌ {error_msg}")
            self.stream_text(f"Error executing module: {str(e)}\n")
            return [(f"Error executing module: {str(e)}", 0.0, "Module Error")]
    
    # ===== STREAMING API METHODS =====
    
    def stream_text(self, text: str, prefix: str = "", wpm: int = None, 
                   callback: Callable = None) -> str:
        """
        Stream text with adjustable speed.
        This is the main streaming method used by everything.
        """
        if wpm is None:
            wpm = self.streaming_speed
        
        # Use the callback if provided, otherwise use the layer's callback
        target_callback = callback if callback else self.streaming_callback
        
        if not self.speed_limit:
            wpm = 0
            
        if wpm == 0 or not target_callback:
            # No streaming, just return full text
            full_text = f"{prefix}{text}"
            if target_callback:
                target_callback(full_text)
            return full_text
        
        return self._stream_with_delays(text, prefix, wpm, target_callback)
    
    def _stream_with_delays(self, text: str, prefix: str, wpm: int, callback: Callable) -> str:
        """Stream text with proper delays based on configuration"""
        words_per_second = wpm / 60.0
        delay_per_word = 1.0 / words_per_second if words_per_second > 0 else 0
        
        if self.letter_streaming:
            return self._stream_letters(text, prefix, delay_per_word, callback)
        else:
            return self._stream_words(text, prefix, delay_per_word, callback)
    
    def _stream_words(self, text: str, prefix: str, delay_per_word: float, callback: Callable) -> str:
        """Stream text word by word with preserved formatting"""
        # Use regex to split while preserving all whitespace
        tokens = re.findall(r'\S+\s*', text)
        
        full_output = prefix
        callback(prefix)
        
        for token in tokens:
            # Output the token (word + its following whitespace)
            full_output += token
            callback(token)
            
            # Calculate dynamic delay based on token characteristics
            base_delay = delay_per_word
            
            # Longer pauses for punctuation
            if token.rstrip().endswith(('.', '!', '?')):
                base_delay *= 1.8
            elif token.rstrip().endswith((',', ';', ':')):
                base_delay *= 1.3
            
            # Check for newlines in the whitespace part
            if '\n' in token:
                # Count newlines for longer pauses
                newline_count = token.count('\n')
                base_delay *= (1.5 + (newline_count * 0.5))
            
            time.sleep(base_delay)
        
        # Always end with newline if not already there
        if not full_output.endswith('\n'):
            callback('\n')
            full_output += '\n'
            
        return full_output
    
    def _stream_letters(self, text: str, prefix: str, delay_per_word: float, callback: Callable) -> str:
        """Stream text letter by letter with preserved formatting"""
        # Convert word delay to letter delay (approx 5 letters per word)
        delay_per_letter = delay_per_word / 5.0
        
        full_output = prefix
        callback(prefix)
        
        for char in text:
            full_output += char
            callback(char)
            
            # Dynamic delays based on character type
            if char in '.!?':
                time.sleep(delay_per_letter * 3)
            elif char in ',;:':
                time.sleep(delay_per_letter * 2)
            elif char == ' ':
                time.sleep(delay_per_letter * 1.5)
            elif char == '\n':
                time.sleep(delay_per_letter * 4)  # Longer pause for newlines
            else:
                time.sleep(delay_per_letter)
        
        callback('\n')
        return full_output + '\n'
    
    def stream_thinking(self, text: str):
        """Stream thinking indicator"""
        if self.thinking_callback:
            self.thinking_callback(text)
    
    def stream_status(self, status: str):
        """Stream status update"""
        if self.status_update_callback:
            self.status_update_callback(status)
    
    def stream_error(self, error: str):
        """Stream error message"""
        if self.error_callback:
            self.error_callback(error)
    
    def complete_response(self):
        """Signal that response is complete"""
        if self.response_complete_callback:
            self.response_complete_callback()
    
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
            
            if route_match and route_match.get('engine') != "None" and confidence >= self.ROUTING_THRESHOLD:
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
                    return routed_responses
                else:
                    return []
                
            else:
                # No route found or route is "None", use AI engine
                if route_match and confidence < self.ROUTING_THRESHOLD:
                    self._update_status(f"Routing confidence too low ({confidence:.2f} < {self.ROUTING_THRESHOLD}), using AI engine")
                elif route_match:
                    self._update_status(f"No module specified, using AI engine (confidence: {confidence:.2f})")
                else:
                    self._update_status("No route found, using AI engine")
                
                # Process through AI engine
                responses = self.ai_engine.process_multiple_questions(user_input)
                
                # Convert AI engine responses to use our streaming
                processed_responses = []
                for response in responses:
                    if len(response) == 6:
                        original_question, answer, confidence, corrections, matched_group, match_type = response
                        processed_responses.append(response)
                    else:
                        # Handle different response formats
                        processed_responses.append(response)
                
                return processed_responses
            
        except Exception as e:
            error_msg = f"Error processing message: {str(e)}"
            self._handle_error(error_msg)
            self._update_status("Error occurred")
            return []
    
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
        self.save_configuration()
    
    def set_additional_info_speed(self, wpm: int):
        """Set additional info streaming speed"""
        self.additional_info_speed = max(0, wpm)
        self.save_configuration()
    
    def toggle_letter_streaming(self):
        """Toggle between word and letter streaming"""
        self.letter_streaming = not self.letter_streaming
        self.save_configuration()
    
    def set_confidence_requirement(self, requirement: float):
        """Set minimum confidence requirement for answers"""
        self.ai_engine.set_confidence_requirement(requirement)
    
    def toggle_speed_limit(self):
        """Toggle speed limiting on/off"""
        self.speed_limit = not self.speed_limit
        self.save_configuration()
    
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
            'available_modules': self.get_available_modules(),
            'routing_threshold': self.ROUTING_THRESHOLD
        }
    
    def stop_streaming(self):
        """Stop any ongoing streaming"""
        self.should_stop_streaming = True
        if self.streaming_thread and self.streaming_thread.is_alive():
            self.streaming_thread.join(timeout=1.0)
        self.should_stop_streaming = False
    
    def is_processing(self) -> bool:
        """Check if AI engine is currently processing"""
        return self.is_streaming
    
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
            'meets_threshold': confidence >= self.ROUTING_THRESHOLD,
            'threshold': self.ROUTING_THRESHOLD,
            'route_group': None,
            'module': None,
            'word_count': len(user_input.split())
        }
        
        if route_match:
            result['route_group'] = route_match['group_name']
            result['module'] = route_match['engine']
            result['word_limit_enabled'] = route_match.get('word_limit_enabled', False)
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


class StreamingAPI:
    """
    API class that modules use to communicate with the streaming layer.
    This provides a clean interface for modules to stream text, send status updates, etc.
    """
    
    def __init__(self, layer: StreamingLayer, module_name: str):
        self.layer = layer
        self.module_name = module_name
    
    def stream_text(self, text: str, prefix: str = "", wpm: int = None) -> str:
        """Stream text through the layer"""
        return self.layer.stream_text(text, prefix, wpm)
    
    def stream_thinking(self, text: str):
        """Stream thinking indicator"""
        self.layer.stream_thinking(text)
    
    def stream_status(self, status: str):
        """Stream status update"""
        self.layer.stream_status(status)
    
    def stream_error(self, error: str):
        """Stream error message"""
        self.layer.stream_error(error)
    
    def complete_response(self):
        """Signal that response is complete"""
        self.layer.complete_response()
    
    def get_config(self) -> Dict[str, Any]:
        """Get current configuration"""
        return self.layer.get_configuration()
    
    def get_module_name(self) -> str:
        """Get the name of the current module"""
        return self.module_name


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