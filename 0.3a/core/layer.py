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
        
        # Word variants configuration
        self.WORD_VARIANTS_CONFIG = {
            'fuzzy_threshold': 80  # Fuzzy matching threshold for variants
        }
        
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
        
        # Word variants configuration
        self.word_variants = {}
        self.variants_file = "resources/word_variants.json"
        self.load_word_variants()
        
        # API state for modules
        self.api_connections = {}
        
        # Enhanced module system
        self.active_modules = []  # List of active module names with module_mode=True
        self.module_limit = 3     # Maximum active modules
        self.message_limit = 10   # Messages before unloading inactive modules
        self.module_message_counts = {}  # Track messages since last valid input per module
        self.module_usage_counts = {}    # Track total usage for LRU eviction
        
        # Module context for multi-turn conversations
        self.module_contexts = {}
        
        print("✅ Streaming Layer initialized with complete streaming control")
        print(f"   Routing threshold: {self.ROUTING_THRESHOLD}")
        print(f"   Streaming speed: {self.streaming_speed} WPM")
        print(f"   Letter streaming: {self.letter_streaming}")
        print(f"   Module limit: {self.module_limit}")
        print(f"   Message limit: {self.message_limit}")
        print(f"   Loaded {len(self.word_variants)} word variant sets")
    
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
    
    def load_word_variants(self):
        """Load word variants configuration from JSON file"""
        try:
            if os.path.exists(self.variants_file):
                with open(self.variants_file, 'r', encoding='utf-8') as f:
                    variants_config = json.load(f)
                
                # Convert list of variant sets to a dictionary for faster lookup
                self.word_variants = {}
                for variant_set in variants_config.get('word_variants', []):
                    base_word = variant_set.get('base_word', '').lower().strip()
                    variants = variant_set.get('variants', [])
                    
                    if base_word:
                        # Store both base word and all variants
                        self.word_variants[base_word] = {
                            'base': base_word,
                            'variants': [v.lower().strip() for v in variants] + [base_word]  # Include base word itself
                        }
                
                print(f"✅ Loaded {len(self.word_variants)} word variant sets")
            else:
                self.word_variants = {}
                print("⚠️  No word variants config found, using empty configuration")
        except Exception as e:
            print(f"❌ Error loading word variants: {e}")
            self.word_variants = {}
    
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
    
    # ===== ENHANCED WORD VARIANTS SYSTEM WITH FUZZY MATCHING =====
    
    def _get_base_word_with_fuzzy(self, word: str, threshold: int = None) -> Optional[str]:
        """Get base word using fuzzy matching on variants"""
        if not self.word_variants:
            return None
        
        if threshold is None:
            threshold = self.WORD_VARIANTS_CONFIG['fuzzy_threshold']
        
        clean_word = word.lower().strip()
        
        # First try exact match
        for base_word, variant_data in self.word_variants.items():
            if clean_word in variant_data['variants']:
                return base_word
        
        # Then try fuzzy match
        for base_word, variant_data in self.word_variants.items():
            for variant in variant_data['variants']:
                similarity = fuzz.ratio(clean_word, variant)
                if similarity >= threshold:
                    print(f"🔍 Fuzzy variant match: '{clean_word}' ~ '{variant}' ({similarity}%) → '{base_word}'")
                    return base_word
        
        return None
    
    def _expand_with_variants(self, text: str) -> str:
        """
        Expand text with word variants using fuzzy matching.
        Replaces words with their base forms and adds variant forms.
        """
        if not self.word_variants:
            return text
        
        words = text.lower().split()
        expanded_words = []
        
        for word in words:
            # Clean the word (remove punctuation)
            clean_word = re.sub(r'[^\w\s]', '', word)
            
            # Get base word using fuzzy matching
            base_word = self._get_base_word_with_fuzzy(clean_word)
            
            if base_word:
                # Add both the base word and the original variant
                expanded_words.append(base_word)
                expanded_words.append(clean_word)
            else:
                # If not found as variant, just add the original word
                expanded_words.append(clean_word)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_words = []
        for word in expanded_words:
            if word not in seen:
                seen.add(word)
                unique_words.append(word)
        
        return ' '.join(unique_words)
    
    def _normalize_with_variants(self, text: str) -> str:
        """
        Normalize text by replacing variants with their base words using fuzzy matching.
        This helps with consistent matching.
        """
        if not self.word_variants:
            return text.lower()
        
        words = text.lower().split()
        normalized_words = []
        
        for word in words:
            # Clean the word (remove punctuation)
            clean_word = re.sub(r'[^\w\s]', '', word)
            
            # Get base word using fuzzy matching
            base_word = self._get_base_word_with_fuzzy(clean_word)
            
            if base_word:
                normalized_words.append(base_word)
            else:
                # If not found as variant, keep the original word
                normalized_words.append(clean_word)
        
        return ' '.join(normalized_words)
    
    def _calculate_fuzzy_containment_confidence(self, user_input: str, group_questions: list, 
                                              word_limit_enabled: bool, max_words: int, penalty_per_word: float) -> float:
        """
        ENHANCED FUZZY MATCHING with word variants support and fuzzy variant matching.
        
        Uses word variants to improve matching accuracy by:
        1. Expanding user input with variant forms using fuzzy matching
        2. Normalizing both inputs to base word forms using fuzzy matching
        3. Applying strict matching rules
        """
        user_input_lower = user_input.lower().strip()
        user_word_count = len(user_input_lower.split())
        
        # CRITICAL: Minimum length requirement to prevent single character matches
        if len(user_input_lower) < 3:
            print(f"🔍 Input too short for routing: '{user_input_lower}' (length: {len(user_input_lower)})")
            return 0.0
        
        # ENHANCEMENT: Expand user input with word variants using fuzzy matching
        expanded_user_input = self._expand_with_variants(user_input_lower)
        print(f"🔍 Expanded user input with variants: '{user_input_lower}' -> '{expanded_user_input}'")
        
        # Check for fuzzy containment in any of the group's questions
        for question in group_questions:
            question_lower = question.lower().strip()
            
            # ENHANCEMENT: Expand question with word variants using fuzzy matching
            expanded_question = self._expand_with_variants(question_lower)
            
            # CRITICAL: Require user input to be substantial portion of target phrase
            min_required_length = len(question_lower) * 0.5  # At least 50% of target length
            if len(user_input_lower) < min_required_length:
                print(f"🔍 Input too short for '{question}': '{user_input_lower}' ({len(user_input_lower)} < {min_required_length:.1f})")
                continue
            
            # ENHANCEMENT: Use both original and expanded versions for matching
            original_token_set_score = fuzz.token_set_ratio(question_lower, user_input_lower)
            expanded_token_set_score = fuzz.token_set_ratio(expanded_question, expanded_user_input)
            
            # Use the higher of the two scores
            token_set_score = max(original_token_set_score, expanded_token_set_score)
            
            # CRITICAL: High threshold for fuzzy matching (90% similarity)
            if token_set_score >= 95:
                # Perfect fuzzy match - starts with 1.0 confidence
                base_confidence = 1.0
                
                # Apply word limit penalty ONLY if user input EXCEEDS max words
                if word_limit_enabled and user_word_count > max_words:
                    extra_words = user_word_count - max_words
                    penalty = extra_words * penalty_per_word
                    base_confidence = max(0.0, base_confidence - penalty)
                    print(f"🔍 Word limit penalty applied: -{penalty:.2f} for {extra_words} extra words")
                
                print(f"🔍 Matched '{question}' with confidence {base_confidence:.2f} (fuzzy score: {token_set_score})")
                return base_confidence
            else:
                print(f"🔍 Fuzzy score too low for '{question}': {token_set_score} < 90 (original: {original_token_set_score}, expanded: {expanded_token_set_score})")
        
        # No fuzzy containment match found
        return 0.0
    
    def _find_best_route(self, user_input: str) -> tuple:
        """
        Find the best matching routing group for user input using enhanced fuzzy matching with word variants.
        Returns (routing_group, confidence_score)
        """
        if not self.routing_config or not self.routing_config.get('routing_groups'):
            return None, 0.0
        
        best_match = None
        best_confidence = 0.0
        
        for group in self.routing_config['routing_groups']:
            word_limit_enabled = group.get('word_limit_enabled', False)
            max_words = group.get('max_words', 10)
            penalty_per_word = group.get('penalty_per_word', 0.1)
            
            confidence = self._calculate_fuzzy_containment_confidence(
                user_input=user_input,
                group_questions=group.get('questions', []),
                word_limit_enabled=word_limit_enabled,
                max_words=max_words,
                penalty_per_word=penalty_per_word
            )
            
            # FIXED: Only use the fixed ROUTING_THRESHOLD
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
    
    def _execute_module(self, module_name: str, user_input: str) -> list:
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
    
    def _is_valid_module_response(self, responses: list) -> bool:
        """
        STRICT MATCHING: Determine if module response indicates valid input handling.
        Now requires 1.0 confidence for valid responses.
        Returns True only if the module returns 1.0 confidence.
        """
        if not responses:
            return False
        
        # Check if any response has 1.0 confidence
        for response in responses:
            if len(response) >= 2 and isinstance(response[1], (int, float)):
                confidence = response[1]
                if confidence >= 1.0:  # STRICT: Must have 1.0 confidence
                    print(f"🔍 Module returned valid response with confidence: {confidence}")
                    return True
        
        # No response with 1.0 confidence found
        print(f"🔍 No valid module response found (all confidences below 1.0)")
        return False
    
    def _should_activate_module(self, module_name: str) -> bool:
        """Check if a module should be activated (has module_mode=True)"""
        try:
            module = __import__(f"core.modules.{module_name}", fromlist=[''])
            return getattr(module, 'module_mode', False)
        except (ImportError, AttributeError):
            return False
    
    def _get_least_used_module(self) -> str:
        """Get the least used module based on usage counts for eviction"""
        if not self.active_modules:
            return None
        
        if not self.module_usage_counts:
            return self.active_modules[0]
        
        # Find module with lowest usage count
        least_used = None
        min_usage = float('inf')
        
        for module_name in self.active_modules:
            usage = self.module_usage_counts.get(module_name, 0)
            if usage < min_usage:
                min_usage = usage
                least_used = module_name
        
        return least_used
    
    def _activate_module(self, module_name: str):
        """Activate a module with module_mode=True"""
        if module_name in self.active_modules:
            # Already active, just update usage
            self.module_usage_counts[module_name] = self.module_usage_counts.get(module_name, 0) + 1
            return
        
        # Check if we need to evict a module due to limit
        if len(self.active_modules) >= self.module_limit:
            least_used = self._get_least_used_module()
            if least_used:
                self._deactivate_module(least_used)
                print(f"🔄 Module limit reached, evicted least used module: {least_used}")
        
        # Activate the new module
        self.active_modules.append(module_name)
        self.module_message_counts[module_name] = 0
        self.module_usage_counts[module_name] = self.module_usage_counts.get(module_name, 0) + 1
        
        print(f"✅ Activated module: {module_name}")
        print(f"   Active modules: {self.active_modules}")
    
    def _deactivate_module(self, module_name: str):
        """Deactivate a module"""
        if module_name in self.active_modules:
            self.active_modules.remove(module_name)
        
        if module_name in self.module_message_counts:
            del self.module_message_counts[module_name]
        
        if module_name in self.module_contexts:
            del self.module_contexts[module_name]
        
        print(f"🔴 Deactivated module: {module_name}")
        print(f"   Active modules: {self.active_modules}")
    
    def _has_strict_matching(self, module_name: str) -> bool:
        """Check if a module has strict matching enabled"""
        try:
            module = __import__(f"core.modules.{module_name}", fromlist=[''])
            return getattr(module, 'strict_matching', False)
        except (ImportError, AttributeError):
            return False

    def _is_input_relevant_to_module(self, module_name: str, user_input: str) -> bool:
        """
        ENHANCED: Check if user input is relevant to a module with strict matching.
        Uses word variants with fuzzy matching to improve relevance detection.
        """
        try:
            module = __import__(f"core.modules.{module_name}", fromlist=[''])
            
            # Check if module defines expected patterns
            if hasattr(module, 'get_expected_patterns'):
                patterns = module.get_expected_patterns()
                
                # ENHANCEMENT: Use normalized input with fuzzy variants
                input_normalized = self._normalize_with_variants(user_input.lower())
                
                # Check for exact matches first
                for pattern in patterns:
                    pattern_lower = pattern.lower()
                    
                    # Check original input
                    if pattern_lower in input_normalized:
                        return True
                
                # Then check fuzzy matches with enhanced input
                for pattern in patterns:
                    pattern_lower = pattern.lower()
                    
                    # Use token set ratio for better semantic matching
                    similarity = fuzz.token_set_ratio(input_normalized, pattern_lower)
                    
                    if similarity >= 70:  # 70% similarity threshold
                        print(f"🔍 Fuzzy match: '{user_input}' ~ '{pattern}' ({similarity}%)")
                        return True
                
                return False
            
            # If module doesn't define patterns, assume all inputs are relevant
            return True
            
        except (ImportError, AttributeError):
            return True

    def _try_module_with_validation(self, module_name: str, user_input: str) -> list:
        """
        Try a module and validate if it can handle the input.
        Returns response if valid (confidence >= 1.0), None if module wants to pass to next.
        Uses STRICT matching for module_mode modules.
        """
        try:
            # Check if this module has strict matching enabled
            module_has_strict_matching = self._has_strict_matching(module_name)
            
            # If module has strict matching, check if input is relevant first
            if module_has_strict_matching:
                if not self._is_input_relevant_to_module(module_name, user_input):
                    print(f"🔍 Module '{module_name}' has strict matching - input not relevant")
                    # CRITICAL FIX: Increment message count for strict matching rejections
                    self.module_message_counts[module_name] = self.module_message_counts.get(module_name, 0) + 1
                    print(f"🔴 Module '{module_name}' strict match rejection, count: {self.module_message_counts[module_name]}")
                    
                    # CRITICAL FIX: Check message limit for strict matching rejections too
                    if self.module_message_counts[module_name] >= self.message_limit:
                        print(f"🔴 Module '{module_name}' reached message limit from strict matching, deactivating")
                        self._deactivate_module(module_name)
                    
                    return None
            
            # Execute module
            responses = self._execute_module(module_name, user_input)
            
            # Check if module returned valid response with 1.0 confidence
            if self._is_valid_module_response(responses):
                # Valid input - reset message count and update usage
                self.module_message_counts[module_name] = 0
                self.module_usage_counts[module_name] = self.module_usage_counts.get(module_name, 0) + 1
                
                # Check if module wants to deactivate itself
                if self._should_deactivate_module(module_name):
                    self._deactivate_module(module_name)
                    print(f"🔴 Module '{module_name}' deactivated itself")
                
                return responses
            else:
                # Invalid input - increment message count
                self.module_message_counts[module_name] = self.module_message_counts.get(module_name, 0) + 1
                print(f"🔴 Module '{module_name}' returned invalid response (confidence < 1.0), count: {self.module_message_counts[module_name]}")
                
                # Check if we should deactivate due to inactivity
                if self.module_message_counts[module_name] >= self.message_limit:
                    print(f"🔴 Module '{module_name}' reached message limit, deactivating")
                    self._deactivate_module(module_name)
                
                return None
                
        except Exception as e:
            # Module error - deactivate
            error_msg = f"Error in module '{module_name}': {str(e)}"
            print(f"❌ {error_msg}")
            self._deactivate_module(module_name)
            return None
    
    def _should_deactivate_module(self, module_name: str) -> bool:
        """Check if a module wants to deactivate itself (module_mode=False)"""
        try:
            module = __import__(f"core.modules.{module_name}", fromlist=[''])
            current_mode = getattr(module, 'module_mode', True)
            if not current_mode:
                print(f"🔍 Module '{module_name}' has module_mode=False, should deactivate")
            return not current_mode  # Return True if module_mode is False
        except (ImportError, AttributeError):
            return False
    
    def _process_through_active_modules(self, user_input: str) -> list:
        """
        Process input through ALL active modules in order.
        Returns first valid response found (with 1.0 confidence), or None if NO module handles it.
        """
        if not self.active_modules:
            return None
        
        print(f"🔄 Processing through {len(self.active_modules)} active modules: {self.active_modules}")
        
        # Try each active module in order until we find one with 1.0 confidence
        for module_name in self.active_modules[:]:  # Copy for safe iteration
            print(f"   Trying module: {module_name}")
            response = self._try_module_with_validation(module_name, user_input)
            
            if response is not None:
                print(f"   ✅ Module '{module_name}' handled the input with 1.0 confidence")
                return response
            else:
                print(f"   ❌ Module '{module_name}' passed on the input (confidence < 1.0)")
        
        print("🔴 No active module handled the input with 1.0 confidence, falling back to routing system")
        return None
    
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
    
    def process_message(self, user_input: str) -> list:
        """
        Process user message through enhanced module system with word variants:
        1. Try all active modules first (module_mode=True) - CASCADE through them
        2. If no active module handles it with 1.0 confidence, try routing system  
        3. If routing matches a module with module_mode=True, activate it
        4. Finally fall back to AI engine
        """
        try:
            self._update_status("Processing your message...")
            
            # Step 1: Try active modules first - CASCADE through them
            module_response = self._process_through_active_modules(user_input)
            if module_response is not None:
                self._update_status("Active module handled request")
                return module_response
            
            # Step 2: Try routing system with word variants enhancement
            route_match, confidence = self._find_best_route(user_input)
            
            if route_match and route_match.get('engine') != "None" and confidence >= self.ROUTING_THRESHOLD:
                # Route to specified module
                module_name = route_match['engine']
                self._update_status(f"Routing to module: {module_name} (confidence: {confidence:.2f})")
                
                # Check if this module should be activated
                if self._should_activate_module(module_name):
                    self._activate_module(module_name)
                
                # Execute the module
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
                # Step 3: Fall back to AI engine
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
        stats = self.ai_engine.performance_stats
        stats['active_modules'] = len(self.active_modules)
        stats['module_usage'] = self.module_usage_counts
        stats['module_message_counts'] = self.module_message_counts
        stats['word_variants_count'] = len(self.word_variants)
        return stats
    
    def reset_conversation(self):
        """Reset conversation context"""
        self.ai_engine.reset_conversation_context()
        # Clear module contexts but keep active modules
        self.module_contexts = {}
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
    
    def get_configuration(self) -> dict:
        """Get current configuration"""
        routing_stats = self.get_routing_stats()
        variants_stats = self.get_word_variants_stats()
        
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
            'active_modules_count': len(self.active_modules),
            'available_modules': self.get_available_modules(),
            'routing_threshold': self.ROUTING_THRESHOLD,
            'module_limit': self.module_limit,
            'message_limit': self.message_limit,
            'word_variants_count': variants_stats['total_sets'],
            'word_variants_total': variants_stats['total_variants'],
            'fuzzy_variants_threshold': self.WORD_VARIANTS_CONFIG['fuzzy_threshold']
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
    
    def get_routing_groups(self) -> list:
        """Get all routing groups"""
        return self.routing_config.get('routing_groups', []) if self.routing_config else []
    
    def add_routing_group(self, group_data: dict) -> bool:
        """Add a new routing group"""
        if not self.routing_config:
            self.routing_config = {"routing_groups": [], "available_engines": [], "version": "1.0"}
        
        self.routing_config['routing_groups'].append(group_data)
        
        # Update available engines
        engine = group_data.get('engine')
        if engine and engine != "None" and engine not in self.routing_config['available_engines']:
            self.routing_config['available_engines'].append(engine)
        
        return self.save_routing_config()
    
    def update_routing_group(self, index: int, group_data: dict) -> bool:
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
    
    def get_routing_stats(self) -> dict:
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
    
    def test_routing_match(self, user_input: str) -> dict:
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
    
    def get_available_modules(self) -> list:
        """Get list of available modules from core/modules folder"""
        modules_folder = "core/modules"
        modules = []
        
        if os.path.exists(modules_folder):
            for file in os.listdir(modules_folder):
                if file.endswith('.py') and not file.startswith('_'):
                    module_name = file[:-3]  # Remove .py extension
                    modules.append(module_name)
        
        return sorted(modules)
    
    def get_active_modules(self) -> list:
        """Get list of currently active modules"""
        return self.active_modules.copy()
    
    def deactivate_module(self, module_name: str) -> bool:
        """Manually deactivate a module"""
        if module_name in self.active_modules:
            self._deactivate_module(module_name)
            return True
        return False
    
    def set_module_limit(self, limit: int):
        """Set the maximum number of active modules"""
        self.module_limit = max(1, limit)  # At least 1 module
        print(f"✅ Module limit set to: {self.module_limit}")
        
        # Enforce new limit by deactivating excess modules
        while len(self.active_modules) > self.module_limit:
            least_used = self._get_least_used_module()
            if least_used:
                self._deactivate_module(least_used)
    
    def set_message_limit(self, limit: int):
        """Set the message limit for module deactivation"""
        self.message_limit = max(1, limit)  # At least 1 message
        print(f"✅ Message limit set to: {self.message_limit}")
    
    # ===== WORD VARIANTS METHODS =====
    
    def refresh_word_variants(self):
        """Reload word variants from file"""
        self.load_word_variants()
    
    def get_word_variants_stats(self) -> dict:
        """Get word variants statistics"""
        total_variants = sum(len(data['variants']) for data in self.word_variants.values())
        
        return {
            'total_sets': len(self.word_variants),
            'total_variants': total_variants,
            'base_words': list(self.word_variants.keys())
        }
    
    def test_word_variants_expansion(self, text: str) -> dict:
        """
        Test how word variants expand a given text.
        Useful for debugging and testing variant matching.
        """
        expanded = self._expand_with_variants(text)
        normalized = self._normalize_with_variants(text)
        
        return {
            'original': text,
            'expanded': expanded,
            'normalized': normalized,
            'words_processed': len(text.split()),
            'words_expanded': len(expanded.split()),
            'variants_applied': len(expanded.split()) - len(text.split())
        }


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
    
    def get_config(self) -> dict:
        """Get current configuration"""
        return self.layer.get_configuration()
    
    def get_module_name(self) -> str:
        """Get the name of the current module"""
        return self.module_name
    
    def get_module_context(self) -> dict:
        """Get context data for this module"""
        return self.layer.module_contexts.get(self.module_name, {})
    
    def set_module_context(self, context: dict):
        """Set context data for this module"""
        self.layer.module_contexts[self.module_name] = context
    
    def deactivate_self(self):
        """Allow module to deactivate itself"""
        self.layer._deactivate_module(self.module_name)


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