import json
import re
import os
import random
import time
import sys
import configparser
from typing import List, Dict, Tuple, Optional, Callable
from fuzzywuzzy import fuzz, process
from collections import deque
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_session import Session
import hashlib
import secrets
from datetime import datetime
import uuid

# ===== DATABASE SETUP =====
class SimpleUserDB:
    def __init__(self, db_file="users.json"):
        self.db_file = db_file
        self.users = self.load_users()
    
    def load_users(self):
        if os.path.exists(self.db_file):
            try:
                with open(self.db_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def save_users(self):
        with open(self.db_file, 'w') as f:
            json.dump(self.users, f, indent=2)
    
    def create_user(self, username, password):
        if username in self.users:
            return False, "Username already exists"
        
        # Hash password with salt
        salt = secrets.token_hex(16)
        password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        
        self.users[username] = {
            'password_hash': password_hash,
            'salt': salt,
            'created_at': datetime.now().isoformat(),
            'last_login': None
        }
        self.save_users()
        return True, "User created successfully"
    
    def verify_user(self, username, password):
        if username not in self.users:
            return False, "User not found"
        
        user_data = self.users[username]
        password_hash = hashlib.sha256((password + user_data['salt']).encode()).hexdigest()
        
        if password_hash == user_data['password_hash']:
            self.users[username]['last_login'] = datetime.now().isoformat()
            self.save_users()
            return True, "Login successful"
        return False, "Invalid password"

# ===== AI ENGINE (Your existing code) =====
class AdvancedChatbot:
    def __init__(self, model_name: str = None, config_file: str = "config.cfg", **kwargs):
        self.models_folder = "models"
        self.current_model = model_name
        self.config_file = config_file
        
        # Load configuration
        self.config = self.load_configuration()
        
        # Apply configuration with kwargs override
        self.enable_model_selection = kwargs.get('enable_model_selection', 
                                               self.config.getboolean('ai_engine', 'enable_model_selection', fallback=True))
        self.streaming_speed = kwargs.get('streaming_speed', 
                                        self.config.getint('ai_engine', 'streaming_speed', fallback=300))
        self.additional_info_speed = kwargs.get('additional_info_speed', 
                                              self.config.getint('ai_engine', 'additional_info_speed', fallback=150))
        self.letter_streaming = kwargs.get('letter_streaming', 
                                         self.config.getboolean('ai_engine', 'letter_streaming', fallback=False))
        self.auto_start_chat = kwargs.get('auto_start_chat', 
                                        self.config.getboolean('ai_engine', 'auto_start_chat', fallback=True))
        self.answer_confidence_requirement = kwargs.get('answer_confidence_requirement',
                                                      self.config.getfloat('ai_engine', 'answer_confidence_requirement', fallback=0.0))
        
        # Streaming callbacks for GUI integration
        self.streaming_callback = kwargs.get('streaming_callback', None)
        self.thinking_callback = kwargs.get('thinking_callback', None)
        self.response_complete_callback = kwargs.get('response_complete_callback', None)
        
        self.qa_groups = []
        
        # Enhanced configuration with same thresholds for all matching
        self.MATCHING_CONFIG = {
            'SIMILARITY_THRESHOLDS': {
                'exact_match': 0.95,
                'high_confidence': 0.75,
                'medium_confidence': 0.60,
                'low_confidence': 0.45,
                'min_acceptable': 0.35
            },
            'AUTO_CORRECTION': {
                'min_confidence': 90,
                'apply_threshold': 92,
                'semantic_check': True
            }
        }
        
        # Enhanced context system with tree navigation
        self.conversation_context = {
            'current_topic': None,
            'previous_topics': deque(maxlen=5),
            'mentioned_entities': deque(maxlen=10),
            'conversation_history': deque(maxlen=6),
            'last_successful_match': None,
            'recent_subjects': deque(maxlen=3),
            
            # ENHANCED TREE NAVIGATION SYSTEM
            'active_tree': None,           # Current QA group we're in a tree for
            'current_branch': None,        # Current branch in the tree
            'branch_path': [],             # Path taken through the tree [root_branch, child_branch, ...]
            'available_branches': [],      # Available branches at current level
            'tree_start_time': None,       # When we entered the tree
            'tree_messages': 0,            # How many messages in current tree
        }
        
        self.performance_stats = {
            'total_questions': 0,
            'successful_matches': 0,
            'failed_matches': 0,
            'follow_up_requests': 0,
            'tree_entries': 0,
            'tree_navigations': 0,
            'tree_exits': 0,
            'confidence_rejections': 0
        }
        
        # Load available models and select one
        self.available_models = self.get_available_models()
        
        if not self.current_model:
            if self.enable_model_selection and self.available_models:
                self.select_model()
            elif self.available_models:
                self.current_model = self.available_models[0]
                print(f"✅ Auto-selected model: {self.current_model}")
        
        if self.current_model:
            self.load_model_data()
        else:
            print("❌ No models available. Please create a model first using the training GUI.")
    
    def load_configuration(self) -> configparser.ConfigParser:
        """Load configuration from file"""
        config = configparser.ConfigParser()
        
        defaults = {
            'ai_engine': {
                'enable_model_selection': 'False',
                'streaming_speed': '300',
                'additional_info_speed': '150',
                'letter_streaming': 'False',
                'auto_start_chat': 'True',
                'answer_confidence_requirement': '0.0'
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
    
    def get_available_models(self) -> List[str]:
        """Get list of available models"""
        models = []
        if os.path.exists(self.models_folder):
            for file in os.listdir(self.models_folder):
                if file.endswith('.json'):
                    model_name = file[:-5]
                    models.append(model_name)
        return sorted(models)
    
    def select_model(self):
        """Let user select a model from available models"""
        if not self.available_models:
            print("❌ No models found in 'models' folder.")
            return
        
        print("\n🤖 Available AI Models:")
        print("=" * 40)
        for i, model_name in enumerate(self.available_models, 1):
            print(f"{i}. {model_name}")
        
        while True:
            try:
                choice = input(f"\nSelect model (1-{len(self.available_models)}): ").strip()
                if not choice:
                    continue
                
                choice_num = int(choice)
                if 1 <= choice_num <= len(self.available_models):
                    self.current_model = self.available_models[choice_num - 1]
                    print(f"✅ Selected model: {self.current_model}")
                    break
                else:
                    print(f"❌ Please enter a number between 1 and {len(self.available_models)}")
            except ValueError:
                print("❌ Please enter a valid number")
    
    def load_model_data(self):
        """Load data from the selected model"""
        if not self.current_model:
            print("❌ No model selected")
            return
        
        model_path = os.path.join(self.models_folder, f"{self.current_model}.json")
        try:
            with open(model_path, 'r') as f:
                model_data = json.load(f)
            
            self.qa_groups = model_data.get('qa_groups', [])
            print(f"✅ Loaded {len(self.qa_groups)} QA groups from '{self.current_model}'")
            
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            self.qa_groups = []
    
    # ===== ENHANCED TREE NAVIGATION SYSTEM =====
    
    def is_in_tree(self) -> bool:
        """Check if we're currently navigating a follow-up tree"""
        return self.conversation_context['active_tree'] is not None
    
    def enter_tree(self, group: dict):
        """Enter a follow-up tree from a root group"""
        if not group.get('follow_ups'):
            return
        
        self.conversation_context['active_tree'] = group
        self.conversation_context['current_branch'] = None
        self.conversation_context['branch_path'] = []
        self.conversation_context['available_branches'] = group['follow_ups']
        self.conversation_context['tree_start_time'] = time.time()
        self.conversation_context['tree_messages'] = 0
        
        self.performance_stats['tree_entries'] += 1
    
    def exit_tree(self):
        """Exit the current follow-up tree"""
        if self.is_in_tree():
            self.conversation_context['active_tree'] = None
            self.conversation_context['current_branch'] = None
            self.conversation_context['branch_path'] = []
            self.conversation_context['available_branches'] = []
            self.performance_stats['tree_exits'] += 1
    
    def navigate_to_branch(self, branch: dict):
        """Navigate to a specific branch in the tree"""
        if not self.is_in_tree():
            return
        
        # Add current branch to path if it exists
        if self.conversation_context['current_branch']:
            self.conversation_context['branch_path'].append(self.conversation_context['current_branch'])
        
        # Set new current branch and available branches
        self.conversation_context['current_branch'] = branch
        self.conversation_context['available_branches'] = branch.get('children', [])
        self.conversation_context['tree_messages'] += 1
        self.performance_stats['tree_navigations'] += 1
    
    def navigate_back(self) -> bool:
        """Navigate back one level in the tree. Returns True if successful."""
        if not self.is_in_tree() or not self.conversation_context['branch_path']:
            return False
        
        # Pop the last branch from path and set as current
        previous_branch = self.conversation_context['branch_path'].pop()
        self.conversation_context['current_branch'] = previous_branch
        
        # Update available branches - if we're back at root, use tree's follow_ups
        if not self.conversation_context['branch_path']:
            self.conversation_context['available_branches'] = self.conversation_context['active_tree']['follow_ups']
        else:
            self.conversation_context['available_branches'] = previous_branch.get('children', [])
        
        self.conversation_context['tree_messages'] += 1
        return True
    
    def get_current_tree_position(self) -> str:
        """Get human-readable current tree position"""
        if not self.is_in_tree():
            return ""
        
        path_names = []
        for branch in self.conversation_context['branch_path']:
            path_names.append(branch.get('branch_name', 'Unknown'))
        
        if self.conversation_context['current_branch']:
            path_names.append(self.conversation_context['current_branch'].get('branch_name', 'Unknown'))
        
        return " → ".join(path_names) if path_names else "Root"
    
    def find_branch_match(self, user_input: str) -> Optional[Tuple[dict, float]]:
        """Find the best matching branch in available branches"""
        if not self.conversation_context['available_branches']:
            return None
        
        user_lower = user_input.lower().strip()
        best_match = None
        best_score = 0.0
        
        for branch in self.conversation_context['available_branches']:
            branch_question = branch.get('question', '').lower().strip()
            if not branch_question:
                continue
            
            # Use same matching as normal chat (not stricter)
            similarity = fuzz.token_set_ratio(user_lower, branch_question) / 100.0
            
            if similarity > best_score and similarity >= self.MATCHING_CONFIG['SIMILARITY_THRESHOLDS']['min_acceptable']:
                best_score = similarity
                best_match = branch
        
        if best_match:
            return best_match, best_score
        
        return None
    
    def handle_tree_navigation_commands(self, user_input: str) -> Optional[str]:
        """Handle natural language tree navigation commands"""
        user_lower = user_input.lower().strip()
        
        # Back navigation patterns
        back_patterns = [
            r'go back',
            r'^back$',
            r'previous',
            r'return to',
            r'never mind',
            r'not that',
            r'go back to',
            r'take me back'
        ]
        
        for pattern in back_patterns:
            if re.search(pattern, user_lower):
                if self.navigate_back():
                    current_pos = self.get_current_tree_position()
                    return f"Okay, going back to {current_pos}."
                else:
                    return "We're already at the beginning of this conversation."
        
        # Show options patterns
        options_patterns = [
            r'what are my options',
            r'what can i ask',
            r'what else',
            r'other options',
            r'show options',
            r'what are the choices'
        ]
        
        for pattern in options_patterns:
            if re.search(pattern, user_lower):
                return self.get_available_branches_text()
        
        return None
    
    def get_available_branches_text(self) -> str:
        """Get text describing available branches"""
        if not self.conversation_context['available_branches']:
            return "There are no more options at this level."
        
        branch_names = []
        for branch in self.conversation_context['available_branches']:
            name = branch.get('branch_name', 'Unknown')
            branch_names.append(name)
        
        return f"Available options: {', '.join(branch_names)}"
    
    def should_exit_tree(self, user_input: str, current_tree_match: bool) -> bool:
        """Determine if we should exit the tree based on user input"""
        if not self.is_in_tree():
            return False
        
        user_lower = user_input.lower().strip()
        
        # Explicit exit patterns
        exit_patterns = [
            r'^exit$',
            r'^quit$',
            r'stop',
            r'new topic',
            r'start over',
            r'main menu'
        ]
        
        for pattern in exit_patterns:
            if re.search(pattern, user_lower):
                return True
        
        # Exit if no match in tree and user seems to be changing topic
        if not current_tree_match:
            # Check if this might be a completely different question
            different_topic = self.is_different_topic(user_input)
            if different_topic:
                return True
        
        return False
    
    def is_different_topic(self, user_input: str) -> bool:
        """Check if user input seems to be about a completely different topic"""
        user_lower = user_input.lower()
        
        # If it matches any root group strongly, it's probably a new topic
        for group in self.qa_groups:
            for question in group.get('questions', []):
                similarity = fuzz.token_set_ratio(user_lower, question.lower()) / 100.0
                if similarity > 0.7:  # Strong match to a different root
                    return True
        
        return False
    
    # ===== STREAMING FUNCTIONALITY =====
    
    def stream_text(self, text: str, prefix: str = "🤖 ", wpm: int = None, callback: Callable = None):
        """Stream text word by word or letter by letter with adjustable speed"""
        if wpm is None:
            wpm = self.streaming_speed
            
        if wpm == 0:
            full_text = f"{prefix}{text}"
            if callback:
                callback(full_text)
            else:
                print(full_text)
            return full_text
        
        output_method = callback if callback else lambda x: print(x, end='', flush=True)
        
        if self.letter_streaming:
            return self._stream_letters(text, prefix, wpm, output_method)
        else:
            return self._stream_words(text, prefix, wpm, output_method)
    
    def _stream_words(self, text: str, prefix: str, wpm: int, output_method: Callable) -> str:
        """Stream text word by word"""
        words_per_second = wpm / 60.0
        delay_per_word = 1.0 / words_per_second if words_per_second > 0 else 0
        
        words = text.split()
        full_output = prefix
        output_method(prefix)
        
        for i, word in enumerate(words):
            if i > 0:
                full_output += ' '
                output_method(' ')
            
            full_output += word
            output_method(word)
            
            if word.endswith(('.', '!', '?')):
                time.sleep(delay_per_word * 1.5)
            elif word.endswith((',', ';', ':')):
                time.sleep(delay_per_word * 1.2)
            else:
                time.sleep(delay_per_word)
        
        output_method('\n')
        return full_output + '\n'
    
    def _stream_letters(self, text: str, prefix: str, wpm: int, output_method: Callable) -> str:
        """Stream text letter by letter"""
        lpm = wpm * 5
        letters_per_second = lpm / 60.0
        delay_per_letter = 1.0 / letters_per_second if letters_per_second > 0 else 0
        
        full_output = prefix
        output_method(prefix)
        
        for char in text:
            full_output += char
            output_method(char)
            
            if char in '.!?':
                time.sleep(delay_per_letter * 3)
            elif char in ',;:':
                time.sleep(delay_per_letter * 2)
            elif char == ' ':
                time.sleep(delay_per_letter * 1.5)
            else:
                time.sleep(delay_per_letter)
        
        output_method('\n')
        return full_output + '\n'
    
    # ===== ENHANCED MATCHING SYSTEM =====
    
    def find_best_match(self, user_question: str) -> Optional[Tuple[dict, float, str]]:
        """Find best match with tree awareness"""
        user_question_lower = user_question.lower().strip()
        
        # Check for tell me more patterns
        tell_me_response = self.handle_tell_me_more(user_question)
        if tell_me_response and any(pattern in user_question_lower for pattern in ['tell me more', 'more information', 'explain more']):
            temp_group = {
                "group_name": "Follow-up Information",
                "questions": [user_question],
                "answers": [tell_me_response],
                "topic": "follow_up"
            }
            return temp_group, 0.9, "follow_up"
        
        # Normal matching
        best_match = None
        best_score = 0.0
        best_match_type = "semantic"
        
        for group in self.qa_groups:
            for question in group.get('questions', []):
                base_score = self.calculate_semantic_similarity(user_question, question)
                
                if base_score > best_score and base_score >= self.MATCHING_CONFIG['SIMILARITY_THRESHOLDS']['min_acceptable']:
                    best_score = base_score
                    best_match = group
        
        if best_match:
            # Check confidence requirement
            if self.answer_confidence_requirement > 0 and best_score < self.answer_confidence_requirement:
                self.performance_stats['confidence_rejections'] += 1
                return None
            
            # Apply tiered confidence
            thresholds = self.MATCHING_CONFIG['SIMILARITY_THRESHOLDS']
            if best_score >= thresholds['exact_match']:
                match_type = "exact"
            elif best_score >= thresholds['high_confidence']:
                match_type = "high_confidence"
            elif best_score >= thresholds['medium_confidence']:
                match_type = "medium_confidence"
            elif best_score >= thresholds['low_confidence']:
                match_type = "low_confidence"
            else:
                match_type = "semantic"
            
            return best_match, best_score, match_type
        
        return None
    
    def calculate_semantic_similarity(self, user_question: str, db_question: str) -> float:
        """Calculate semantic similarity between user question and database question"""
        user_lower = user_question.lower()
        db_lower = db_question.lower()
        
        similarity = fuzz.token_set_ratio(user_lower, db_lower) / 100.0
        return min(similarity, 1.0)
    
    def auto_correct_input(self, user_input: str) -> Tuple[str, List[Tuple[str, int]]]:
        """Auto-correct input"""
        user_lower = user_input.lower().strip()
        
        if len(user_lower) <= 3:
            return user_input, []
        
        all_questions = []
        for group in self.qa_groups:
            all_questions.extend(group.get('questions', []))
        
        if any(q.lower() == user_lower for q in all_questions):
            return user_input, []
        
        matches = process.extract(user_input, all_questions, 
                                scorer=fuzz.partial_ratio, limit=5)
        
        good_matches = []
        for match, score in matches:
            if score >= self.MATCHING_CONFIG['AUTO_CORRECTION']['min_confidence']:
                if self.validate_semantic_match(user_input, match):
                    good_matches.append((match, score))
        
        if good_matches and good_matches[0][1] >= self.MATCHING_CONFIG['AUTO_CORRECTION']['apply_threshold']:
            return good_matches[0][0], good_matches
        
        return user_input, good_matches
    
    def validate_semantic_match(self, user_question: str, matched_question: str) -> bool:
        """Validate semantic match"""
        user_words = set(user_question.lower().split())
        matched_words = set(matched_question.lower().split())
        common_words = {'what', 'is', 'are', 'how', 'why', 'when', 'where', 'who', 'tell', 'me', 'about'}
        user_content = user_words - common_words
        matched_content = matched_words - common_words
        
        return bool(user_content.intersection(matched_content))
    
    # ===== ENHANCED QUESTION PROCESSING =====
    
    def process_question(self, user_input: str) -> Dict:
        """Process a single question and return response data for web"""
        # Handle tree navigation if we're in a tree
        if self.is_in_tree():
            # Check for navigation commands
            nav_response = self.handle_tree_navigation_commands(user_input)
            if nav_response:
                self.update_conversation_context(user_input, nav_response, None, 0.9)
                return {
                    'question': user_input,
                    'answer': nav_response,
                    'confidence': 0.9,
                    'corrections': [],
                    'matched_group': 'Tree Navigation',
                    'match_type': 'navigation',
                    'in_tree': True,
                    'tree_position': self.get_current_tree_position(),
                    'available_branches': self.get_available_branches_text()
                }
            
            # Try to match available branches
            branch_match = self.find_branch_match(user_input)
            if branch_match:
                branch, confidence = branch_match
                
                # Check confidence requirement
                if self.answer_confidence_requirement > 0 and confidence < self.answer_confidence_requirement:
                    self.performance_stats['confidence_rejections'] += 1
                    unknown_response = self.handle_unknown_question(user_input)
                    self.update_conversation_context(user_input, unknown_response, None, 0.0)
                    return {
                        'question': user_input,
                        'answer': unknown_response,
                        'confidence': 0.0,
                        'corrections': [],
                        'matched_group': None,
                        'match_type': 'confidence_rejection',
                        'in_tree': True,
                        'tree_position': self.get_current_tree_position(),
                        'available_branches': self.get_available_branches_text()
                    }
                else:
                    # Navigate to this branch
                    self.navigate_to_branch(branch)
                    answer = branch.get('answer', '')
                    self.update_conversation_context(user_input, answer, self.conversation_context['active_tree'], confidence)
                    
                    response_data = {
                        'question': user_input,
                        'answer': answer,
                        'confidence': confidence,
                        'corrections': [],
                        'matched_group': self.conversation_context['active_tree'].get('group_name', 'Unknown'),
                        'match_type': 'tree_branch',
                        'in_tree': True,
                        'tree_position': self.get_current_tree_position(),
                        'available_branches': self.get_available_branches_text()
                    }
                    
                    # Check if we should exit tree
                    if self.should_exit_tree(user_input, True):
                        self.exit_tree()
                        response_data['in_tree'] = False
                        response_data['tree_position'] = ""
                    
                    return response_data
            else:
                # No branch match - check if we should exit tree
                if self.should_exit_tree(user_input, False):
                    self.exit_tree()
        
        # Check for explicit "tell me more" patterns
        tell_me_response = self.handle_tell_me_more(user_input)
        if tell_me_response and any(pattern in user_input.lower() for pattern in ['tell me more', 'more information', 'explain more']):
            self.update_conversation_context(user_input, tell_me_response, None, 0.9)
            return {
                'question': user_input,
                'answer': tell_me_response,
                'confidence': 0.9,
                'corrections': [],
                'matched_group': "Follow-up Information",
                'match_type': 'follow_up',
                'in_tree': self.is_in_tree(),
                'tree_position': self.get_current_tree_position(),
                'available_branches': self.get_available_branches_text() if self.is_in_tree() else ""
            }
        
        # Proceed with normal matching
        corrected_question, corrections = self.auto_correct_input(user_input)
        match_result = self.find_best_match(corrected_question)
        
        if match_result:
            group, confidence, match_type = match_result
            answer = self.get_random_answer(group.get('answers', []))
            
            self.update_conversation_context(user_input, answer, group, confidence)
            
            response_data = {
                'question': user_input,
                'answer': answer,
                'confidence': confidence,
                'corrections': corrections,
                'matched_group': group.get('group_name', 'Unknown'),
                'match_type': match_type,
                'in_tree': self.is_in_tree(),
                'tree_position': self.get_current_tree_position(),
                'available_branches': self.get_available_branches_text() if self.is_in_tree() else ""
            }
            
            # ENTER TREE if this group has follow-ups and we're not already in a tree
            if group.get('follow_ups') and not self.is_in_tree():
                self.enter_tree(group)
                response_data['in_tree'] = True
                response_data['tree_position'] = self.get_current_tree_position()
                response_data['available_branches'] = self.get_available_branches_text()
            
            return response_data
        else:
            unknown_response = self.handle_unknown_question(user_input)
            self.update_conversation_context(user_input, unknown_response, None, 0.0)
            return {
                'question': user_input,
                'answer': unknown_response,
                'confidence': 0.0,
                'corrections': corrections,
                'matched_group': None,
                'match_type': 'unknown',
                'in_tree': self.is_in_tree(),
                'tree_position': self.get_current_tree_position(),
                'available_branches': self.get_available_branches_text() if self.is_in_tree() else ""
            }
    
    def handle_unknown_question(self, question: str) -> str:
        """Handle unknown questions"""
        base_responses = [
            "I'm not sure about that yet. Could you ask something else?",
            "I don't have information about that currently.",
            "That's beyond my knowledge at the moment.",
        ]
        
        return random.choice(base_responses)
    
    def get_random_answer(self, answers: List[str]) -> str:
        return random.choice(answers) if answers else "I don't have an answer for that."
    
    def handle_tell_me_more(self, user_input: str) -> Optional[str]:
        """Handle tell me more requests"""
        self.performance_stats['follow_up_requests'] += 1
        return "I'd be happy to provide more details! Could you be more specific about what you'd like to learn more about?"
    
    # ===== CONTEXT SYSTEM =====
    
    def update_conversation_context(self, user_input: str, bot_response: str, matched_group: dict = None, confidence: float = 0.0):
        """Update conversation context"""
        self.conversation_context['conversation_history'].append({
            'user': user_input,
            'bot': bot_response,
            'timestamp': time.time(),
            'confidence': confidence,
            'matched_topic': matched_group.get('topic') if matched_group else None,
        })
        
        # Track successful matches
        if matched_group and confidence >= self.MATCHING_CONFIG['SIMILARITY_THRESHOLDS']['medium_confidence']:
            self.conversation_context['last_successful_match'] = matched_group
            self.performance_stats['successful_matches'] += 1
        elif confidence > 0:
            self.performance_stats['successful_matches'] += 1
        else:
            self.performance_stats['failed_matches'] += 1
        
        self.performance_stats['total_questions'] += 1
    
    def reset_conversation(self):
        """Reset conversation context"""
        self.conversation_context.update({
            'current_topic': None,
            'previous_topics': deque(maxlen=5),
            'mentioned_entities': deque(maxlen=10),
            'conversation_history': deque(maxlen=6),
            'last_successful_match': None,
            'recent_subjects': deque(maxlen=3),
            'active_tree': None,
            'current_branch': None,
            'branch_path': [],
            'available_branches': [],
            'tree_start_time': None,
            'tree_messages': 0,
        })

# ===== FLASK WEB APPLICATION =====
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here-change-in-production'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = './flask_session'
Session(app)

# Initialize database and AI
user_db = SimpleUserDB()

# Store chatbot instances per user session
def get_user_chatbot():
    if 'chatbot' not in session:
        session['chatbot'] = AdvancedChatbot(auto_start_chat=False, web_mode=True)
    return session['chatbot']

# ===== ROUTES =====
@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('chat'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        success, message = user_db.verify_user(username, password)
        if success:
            session['username'] = username
            # Initialize a new chatbot for this session
            session['chatbot'] = AdvancedChatbot(auto_start_chat=False, web_mode=True)
            return redirect(url_for('chat'))
        else:
            return render_template('login.html', error=message)
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if password != confirm_password:
            return render_template('register.html', error="Passwords do not match")
        
        if len(password) < 4:
            return render_template('register.html', error="Password must be at least 4 characters")
        
        success, message = user_db.create_user(username, password)
        if success:
            return redirect(url_for('login'))
        else:
            return render_template('register.html', error=message)
    
    return render_template('register.html')

@app.route('/chat')
def chat():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    chatbot = get_user_chatbot()
    return render_template('chat.html', 
                         username=session['username'],
                         model_name=chatbot.current_model or "No Model")

@app.route('/send_message', methods=['POST'])
def send_message():
    if 'username' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user_input = request.json.get('message', '').strip()
    if not user_input:
        return jsonify({'error': 'Empty message'}), 400
    
    chatbot = get_user_chatbot()
    response_data = chatbot.process_question(user_input)
    
    return jsonify(response_data)

@app.route('/reset_chat', methods=['POST'])
def reset_chat():
    if 'username' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    chatbot = get_user_chatbot()
    chatbot.reset_conversation()
    
    return jsonify({'success': True})

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ===== HTML TEMPLATES =====
@app.route('/templates/<template_name>')
def serve_template(template_name):
    if template_name == 'login.html':
        return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Login - Edgar AI</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        
        .login-container {
            background: white;
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            width: 100%;
            max-width: 400px;
        }
        
        .logo {
            text-align: center;
            margin-bottom: 30px;
        }
        
        .logo h1 {
            color: #333;
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .logo p {
            color: #666;
            font-size: 1.1em;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        label {
            display: block;
            margin-bottom: 8px;
            color: #333;
            font-weight: 500;
        }
        
        input[type="text"],
        input[type="password"] {
            width: 100%;
            padding: 15px;
            border: 2px solid #e1e5e9;
            border-radius: 10px;
            font-size: 16px;
            transition: border-color 0.3s;
        }
        
        input[type="text"]:focus,
        input[type="password"]:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .btn {
            width: 100%;
            padding: 15px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s;
        }
        
        .btn:hover {
            transform: translateY(-2px);
        }
        
        .btn-secondary {
            background: #6c757d;
            margin-top: 10px;
        }
        
        .error {
            background: #fee;
            border: 1px solid #f5c6cb;
            color: #721c24;
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 20px;
            text-align: center;
        }
        
        .links {
            text-align: center;
            margin-top: 20px;
        }
        
        .links a {
            color: #667eea;
            text-decoration: none;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="logo">
            <h1>🤖 Edgar AI</h1>
            <p>Intelligent Chat Assistant</p>
        </div>
        
        {% if error %}
        <div class="error">{{ error }}</div>
        {% endif %}
        
        <form method="POST">
            <div class="form-group">
                <label for="username">Username</label>
                <input type="text" id="username" name="username" required>
            </div>
            
            <div class="form-group">
                <label for="password">Password</label>
                <input type="password" id="password" name="password" required>
            </div>
            
            <button type="submit" class="btn">Login</button>
        </form>
        
        <div class="links">
            <p>Don't have an account? <a href="{{ url_for('register') }}">Register here</a></p>
        </div>
    </div>
</body>
</html>
        '''
    elif template_name == 'register.html':
        return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Register - Edgar AI</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        
        .register-container {
            background: white;
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            width: 100%;
            max-width: 400px;
        }
        
        .logo {
            text-align: center;
            margin-bottom: 30px;
        }
        
        .logo h1 {
            color: #333;
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .logo p {
            color: #666;
            font-size: 1.1em;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        label {
            display: block;
            margin-bottom: 8px;
            color: #333;
            font-weight: 500;
        }
        
        input[type="text"],
        input[type="password"] {
            width: 100%;
            padding: 15px;
            border: 2px solid #e1e5e9;
            border-radius: 10px;
            font-size: 16px;
            transition: border-color 0.3s;
        }
        
        input[type="text"]:focus,
        input[type="password"]:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .btn {
            width: 100%;
            padding: 15px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s;
        }
        
        .btn:hover {
            transform: translateY(-2px);
        }
        
        .btn-secondary {
            background: #6c757d;
            margin-top: 10px;
        }
        
        .error {
            background: #fee;
            border: 1px solid #f5c6cb;
            color: #721c24;
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 20px;
            text-align: center;
        }
        
        .links {
            text-align: center;
            margin-top: 20px;
        }
        
        .links a {
            color: #667eea;
            text-decoration: none;
        }
    </style>
</head>
<body>
    <div class="register-container">
        <div class="logo">
            <h1>🤖 Edgar AI</h1>
            <p>Create Your Account</p>
        </div>
        
        {% if error %}
        <div class="error">{{ error }}</div>
        {% endif %}
        
        <form method="POST">
            <div class="form-group">
                <label for="username">Username</label>
                <input type="text" id="username" name="username" required>
            </div>
            
            <div class="form-group">
                <label for="password">Password</label>
                <input type="password" id="password" name="password" required>
            </div>
            
            <div class="form-group">
                <label for="confirm_password">Confirm Password</label>
                <input type="password" id="confirm_password" name="confirm_password" required>
            </div>
            
            <button type="submit" class="btn">Register</button>
        </form>
        
        <div class="links">
            <p>Already have an account? <a href="{{ url_for('login') }}">Login here</a></p>
        </div>
    </div>
</body>
</html>
        '''
    elif template_name == 'chat.html':
        return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Chat - Edgar AI</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f5f5;
            height: 100vh;
            overflow: hidden;
        }
        
        .chat-container {
            display: flex;
            flex-direction: column;
            height: 100vh;
            max-width: 800px;
            margin: 0 auto;
            background: white;
            box-shadow: 0 0 20px rgba(0,0,0,0.1);
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .header-info h1 {
            font-size: 1.5em;
            margin-bottom: 5px;
        }
        
        .header-info p {
            opacity: 0.9;
            font-size: 0.9em;
        }
        
        .header-actions {
            display: flex;
            gap: 10px;
        }
        
        .btn {
            padding: 8px 16px;
            background: rgba(255,255,255,0.2);
            color: white;
            border: none;
            border-radius: 20px;
            cursor: pointer;
            font-size: 0.9em;
            transition: background 0.3s;
        }
        
        .btn:hover {
            background: rgba(255,255,255,0.3);
        }
        
        .chat-messages {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            background: #f8f9fa;
        }
        
        .message {
            margin-bottom: 20px;
            animation: fadeIn 0.3s ease-in;
        }
        
        .user-message {
            text-align: right;
        }
        
        .bot-message {
            text-align: left;
        }
        
        .message-bubble {
            display: inline-block;
            max-width: 70%;
            padding: 12px 16px;
            border-radius: 18px;
            word-wrap: break-word;
        }
        
        .user-message .message-bubble {
            background: #667eea;
            color: white;
            border-bottom-right-radius: 4px;
        }
        
        .bot-message .message-bubble {
            background: white;
            color: #333;
            border: 1px solid #e1e5e9;
            border-bottom-left-radius: 4px;
        }
        
        .message-info {
            font-size: 0.8em;
            color: #666;
            margin-top: 5px;
            padding: 0 10px;
        }
        
        .tree-info {
            background: #e7f3ff;
            border: 1px solid #b3d9ff;
            border-radius: 10px;
            padding: 10px;
            margin: 10px 0;
            font-size: 0.9em;
        }
        
        .input-container {
            padding: 20px;
            background: white;
            border-top: 1px solid #e1e5e9;
        }
        
        .input-group {
            display: flex;
            gap: 10px;
        }
        
        .message-input {
            flex: 1;
            padding: 15px;
            border: 2px solid #e1e5e9;
            border-radius: 25px;
            font-size: 16px;
            outline: none;
            transition: border-color 0.3s;
        }
        
        .message-input:focus {
            border-color: #667eea;
        }
        
        .send-btn {
            padding: 15px 25px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 25px;
            cursor: pointer;
            font-size: 16px;
            transition: background 0.3s;
        }
        
        .send-btn:hover {
            background: #5a6fd8;
        }
        
        .send-btn:disabled {
            background: #ccc;
            cursor: not-allowed;
        }
        
        .typing-indicator {
            display: none;
            padding: 10px 16px;
            background: white;
            border: 1px solid #e1e5e9;
            border-radius: 18px;
            border-bottom-left-radius: 4px;
            max-width: 70%;
        }
        
        .typing-dots {
            display: flex;
            gap: 4px;
        }
        
        .typing-dot {
            width: 8px;
            height: 8px;
            background: #999;
            border-radius: 50%;
            animation: typing 1.4s infinite;
        }
        
        .typing-dot:nth-child(2) {
            animation-delay: 0.2s;
        }
        
        .typing-dot:nth-child(3) {
            animation-delay: 0.4s;
        }
        
        @keyframes typing {
            0%, 60%, 100% { transform: translateY(0); }
            30% { transform: translateY(-10px); }
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .streaming-text {
            display: inline;
        }
        
        /* Mobile optimizations */
        @media (max-width: 768px) {
            .chat-container {
                height: 100vh;
                border-radius: 0;
            }
            
            .header {
                padding: 15px;
            }
            
            .header-info h1 {
                font-size: 1.3em;
            }
            
            .message-bubble {
                max-width: 85%;
            }
            
            .input-container {
                padding: 15px;
            }
        }
    </style>
</head>
<body>
    <div class="chat-container">
        <div class="header">
            <div class="header-info">
                <h1>🤖 Edgar AI</h1>
                <p>Welcome, {{ username }} | Model: {{ model_name }}</p>
            </div>
            <div class="header-actions">
                <button class="btn" onclick="resetChat()">New Chat</button>
                <button class="btn" onclick="logout()">Logout</button>
            </div>
        </div>
        
        <div class="chat-messages" id="chatMessages">
            <div class="message bot-message">
                <div class="message-bubble">
                    Hello! I'm Edgar AI. How can I help you today?
                </div>
                <div class="message-info">Just now</div>
            </div>
        </div>
        
        <div class="typing-indicator" id="typingIndicator">
            <div class="typing-dots">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        </div>
        
        <div class="input-container">
            <div class="input-group">
                <input type="text" class="message-input" id="messageInput" 
                       placeholder="Type your message..." autocomplete="off">
                <button class="send-btn" id="sendBtn" onclick="sendMessage()">Send</button>
            </div>
        </div>
    </div>

    <script>
        let isStreaming = false;
        
        function addMessage(message, isUser = false) {
            const chatMessages = document.getElementById('chatMessages');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${isUser ? 'user-message' : 'bot-message'}`;
            
            const bubble = document.createElement('div');
            bubble.className = 'message-bubble';
            
            if (isUser) {
                bubble.textContent = message;
            } else {
                bubble.innerHTML = `<div class="streaming-text">${message}</div>`;
            }
            
            messageDiv.appendChild(bubble);
            
            const info = document.createElement('div');
            info.className = 'message-info';
            info.textContent = 'Just now';
            messageDiv.appendChild(info);
            
            chatMessages.appendChild(messageDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;
            
            return bubble;
        }
        
        function showTyping() {
            document.getElementById('typingIndicator').style.display = 'inline-block';
            document.getElementById('chatMessages').scrollTop = document.getElementById('chatMessages').scrollHeight;
        }
        
        function hideTyping() {
            document.getElementById('typingIndicator').style.display = 'none';
        }
        
        function streamText(element, text, speed = 30) {
            return new Promise((resolve) => {
                let i = 0;
                element.innerHTML = '';
                
                function typeChar() {
                    if (i < text.length) {
                        element.innerHTML += text.charAt(i);
                        i++;
                        setTimeout(typeChar, speed);
                    } else {
                        resolve();
                    }
                }
                
                typeChar();
            });
        }
        
        async function sendMessage() {
            const input = document.getElementById('messageInput');
            const message = input.value.trim();
            
            if (!message || isStreaming) return;
            
            input.value = '';
            document.getElementById('sendBtn').disabled = true;
            isStreaming = true;
            
            // Add user message
            addMessage(message, true);
            
            // Show typing indicator
            showTyping();
            
            try {
                const response = await fetch('/send_message', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ message: message })
                });
                
                const data = await response.json();
                hideTyping();
                
                if (response.ok) {
                    // Add bot message with streaming effect
                    const bubble = addMessage('', false);
                    const streamingElement = bubble.querySelector('.streaming-text');
                    
                    await streamText(streamingElement, data.answer);
                    
                    // Show additional info if available
                    if (data.in_tree && data.tree_position) {
                        const treeInfo = document.createElement('div');
                        treeInfo.className = 'tree-info';
                        treeInfo.innerHTML = `
                            <strong>🌳 ${data.tree_position}</strong>
                            ${data.available_branches ? '<br>' + data.available_branches : ''}
                        `;
                        bubble.parentNode.appendChild(treeInfo);
                    }
                    
                    if (data.match_type && data.match_type !== 'unknown') {
                        const matchInfo = document.createElement('div');
                        matchInfo.className = 'message-info';
                        matchInfo.textContent = `Confidence: ${(data.confidence * 100).toFixed(1)}% | ${data.matched_group}`;
                        bubble.parentNode.appendChild(matchInfo);
                    }
                    
                } else {
                    addMessage('Sorry, there was an error processing your message.', false);
                }
            } catch (error) {
                hideTyping();
                addMessage('Sorry, there was a connection error.', false);
                console.error('Error:', error);
            } finally {
                document.getElementById('sendBtn').disabled = false;
                isStreaming = false;
                input.focus();
            }
        }
        
        function resetChat() {
            if (confirm('Start a new conversation? This will clear the current chat history.')) {
                fetch('/reset_chat', { method: 'POST' })
                    .then(() => {
                        const chatMessages = document.getElementById('chatMessages');
                        chatMessages.innerHTML = `
                            <div class="message bot-message">
                                <div class="message-bubble">
                                    Hello! I'm Edgar AI. How can I help you today?
                                </div>
                                <div class="message-info">Just now</div>
                            </div>
                        `;
                    });
            }
        }
        
        function logout() {
            window.location.href = '/logout';
        }
        
        // Event listeners
        document.getElementById('messageInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
        
        // Focus input on load
        document.getElementById('messageInput').focus();
    </script>
</body>
</html>
        '''
    return "Template not found", 404

# ===== MAIN EXECUTION =====
if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('models', exist_ok=True)
    os.makedirs('flask_session', exist_ok=True)
    
    print("🤖 Edgar AI Web Interface Starting...")
    print("=" * 50)
    print("📱 Access the application at: http://localhost:5000")
    print("🔐 Default: Register a new account to get started")
    
    app.run(host='0.0.0.0', port=5000, debug=False)
