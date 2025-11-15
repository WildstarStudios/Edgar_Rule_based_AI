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
        self.auto_start_chat = kwargs.get('auto_start_chat', 
                                        self.config.getboolean('ai_engine', 'auto_start_chat', fallback=True))
        self.answer_confidence_requirement = kwargs.get('answer_confidence_requirement',
                                                      self.config.getfloat('ai_engine', 'answer_confidence_requirement', fallback=0.85))
        
        # Streaming is now handled by the layer - we don't need streaming callbacks here
        self.streaming_api = kwargs.get('streaming_api', None)
        
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
        
        # Initialize with proper context reset
        self.reset_conversation_context()
        
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
            success = self.load_model_data()
            if not success and self.available_models:
                # Try to load the first available model if current fails
                self.current_model = self.available_models[0]
                self.load_model_data()
            
            if self.auto_start_chat or __name__ == "__main__":
                self.chat()
        else:
            print("❌ No models available. Please create a model first using the training GUI.")

    def reset_conversation_context(self):
        """Completely reset conversation context including tree navigation"""
        self.conversation_context = {
            'current_topic': None,
            'previous_topics': deque(maxlen=5),
            'mentioned_entities': deque(maxlen=10),
            'user_preferences': {},
            'conversation_history': deque(maxlen=6),
            'current_goal': None,
            'last_successful_match': None,
            'conversation_mood': 'neutral',
            'topic_consistency_score': 1.0,
            'recent_subjects': deque(maxlen=3),
            'last_detailed_topic': None,
            'available_follow_ups': {},
            
            # TREE NAVIGATION SYSTEM - FULLY RESET
            'active_tree': None,
            'current_branch': None,
            'branch_path': [],
            'available_branches': [],
            'tree_start_time': None,
            'tree_messages': 0,
        }
    
    def load_configuration(self) -> configparser.ConfigParser:
        """Load configuration from file"""
        config = configparser.ConfigParser()
        
        defaults = {
            'ai_engine': {
                'enable_model_selection': 'False',
                'auto_start_chat': 'True',
                'answer_confidence_requirement': '0.85'
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
        self.config.set('ai_engine', 'auto_start_chat', str(self.auto_start_chat))
        self.config.set('ai_engine', 'answer_confidence_requirement', str(self.answer_confidence_requirement))
        
        with open(self.config_file, 'w') as f:
            self.config.write(f)
        print(f"✅ Configuration saved to {self.config_file}")
    
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
            return False
        
        model_path = os.path.join(self.models_folder, f"{self.current_model}.json")
        try:
            with open(model_path, 'r', encoding='utf-8') as f:
                model_data = json.load(f)
            
            self.qa_groups = model_data.get('qa_groups', [])
            print(f"✅ Loaded {len(self.qa_groups)} QA groups from '{self.current_model}'")
            return True
            
        except FileNotFoundError:
            print(f"❌ Model file not found: {model_path}")
            self.qa_groups = []
            return False
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing model JSON: {e}")
            self.qa_groups = []
            return False
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            self.qa_groups = []
            return False
    
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
        print(f"🌳 Entered tree: {group.get('group_name', 'Unknown')}")
    
    def exit_tree(self):
        """Exit the current follow-up tree"""
        if self.is_in_tree():
            tree_name = self.conversation_context['active_tree'].get('group_name', 'Unknown')
            self.conversation_context['active_tree'] = None
            self.conversation_context['current_branch'] = None
            self.conversation_context['branch_path'] = []
            self.conversation_context['available_branches'] = []
            self.performance_stats['tree_exits'] += 1
            print(f"🌳 Exited tree: {tree_name}")
    
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
    
    # ===== STREAMING VIA LAYER API =====
    
    def stream_text_via_api(self, text: str, prefix: str = "") -> str:
        """Stream text using the layer API if available, otherwise print directly"""
        if self.streaming_api:
            return self.streaming_api.stream_text(text, prefix)
        else:
            # Fallback for standalone mode
            full_text = f"{prefix}{text}"
            print(full_text)
            return full_text
    
    def stream_thinking_via_api(self, text: str):
        """Stream thinking indicator via API"""
        if self.streaming_api:
            self.streaming_api.stream_thinking(text)
        else:
            print(f"THINKING: {text}")
    
    def set_confidence_requirement(self, requirement: float):
        """Set the minimum confidence requirement for answers (0.0 to 1.0, 0.0 = disabled)"""
        if requirement < 0.0 or requirement > 1.0:
            print("❌ Confidence requirement must be between 0.0 and 1.0")
            return
        
        self.answer_confidence_requirement = requirement
        status = "disabled" if requirement == 0.0 else f"set to {requirement:.2f}"
        print(f"🎯 Answer confidence requirement {status}")
        self.save_configuration()
    
    # ===== ENHANCED MATCHING SYSTEM =====
    
    def find_best_match(self, user_question: str) -> Optional[Tuple[dict, float, str]]:
        """Find best match with tree awareness"""
        user_question_lower = user_question.lower().strip()
        
        # Normal matching - REMOVED OLD "TELL ME MORE" SYSTEM
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
    
    # ===== OPTIMIZED QUESTION PROCESSING =====
    
    def process_multiple_questions(self, user_input: str) -> List[Tuple]:
        """Process input with tree navigation support"""
        questions = self.split_questions(user_input)
        responses = []
        
        for question in questions:
            if not question.strip():
                continue
                
            # FIRST: Handle tree navigation if we're in a tree
            if self.is_in_tree():
                # Check for navigation commands
                nav_response = self.handle_tree_navigation_commands(question)
                if nav_response:
                    responses.append((question, nav_response, 0.9, [], "Tree Navigation", "navigation"))
                    self.update_conversation_context(question, nav_response, None, 0.9)
                    continue
                
                # Try to match available branches
                branch_match = self.find_branch_match(question)
                if branch_match:
                    branch, confidence = branch_match
                    
                    # Check confidence requirement
                    if self.answer_confidence_requirement > 0 and confidence < self.answer_confidence_requirement:
                        self.performance_stats['confidence_rejections'] += 1
                        unknown_response = self.handle_unknown_question(question)
                        responses.append((question, unknown_response, 0.0, [], None, "confidence_rejection"))
                        self.update_conversation_context(question, unknown_response, None, 0.0)
                    else:
                        # Navigate to this branch
                        self.navigate_to_branch(branch)
                        answer = branch.get('answer', '')
                        responses.append((question, answer, confidence, [], 
                                        self.conversation_context['active_tree'].get('group_name', 'Unknown'), 
                                        "tree_branch"))
                        self.update_conversation_context(question, answer, 
                                                       self.conversation_context['active_tree'], confidence)
                    
                    # Check if we should exit tree
                    if self.should_exit_tree(question, True):
                        self.exit_tree()
                    
                    continue
                else:
                    # No branch match - check if we should exit tree
                    if self.should_exit_tree(question, False):
                        self.exit_tree()
                        # Continue with normal processing below
            
            # SECOND: Proceed with normal matching
            corrected_question, corrections = self.auto_correct_input(question)
            match_result = self.find_best_match(corrected_question)
            
            if match_result:
                group, confidence, match_type = match_result
                answer = self.get_random_answer(group.get('answers', []))
                
                responses.append((question, answer, confidence, corrections, group.get('group_name', 'Unknown'), match_type))
                self.update_conversation_context(question, answer, group, confidence)
                
                # ENTER TREE if this group has follow-ups and we're not already in a tree
                if group.get('follow_ups') and not self.is_in_tree():
                    self.enter_tree(group)
                
            else:
                unknown_response = self.handle_unknown_question(question)
                responses.append((question, unknown_response, 0.0, corrections, None, "unknown"))
                self.update_conversation_context(question, unknown_response, None, 0.0)
        
        return responses
    
    def split_questions(self, text: str) -> List[str]:
        """Split multiple questions"""
        sentences = re.split(r'[.!?]+', text)
        questions = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            if any(sep in sentence.lower() for sep in [' and ', ' then ', ' also ']):
                parts = re.split(r'\s+and\s+|\s+then\s+|\s+also\s+', sentence, flags=re.IGNORECASE)
                for part in parts:
                    part = part.strip()
                    if part and len(part) > 2:
                        questions.append(part)
            else:
                questions.append(sentence)
        
        return questions if questions else [text]
    
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
        
        # Extract entities
        entities = self.extract_meaningful_entities(user_input)
        for entity in entities:
            if entity not in self.conversation_context['mentioned_entities']:
                self.conversation_context['mentioned_entities'].append(entity)
        
        # Update topic
        new_topic = self.detect_topic(user_input)
        if new_topic and new_topic != self.conversation_context['current_topic']:
            self.conversation_context['previous_topics'].append(self.conversation_context['current_topic'])
            self.conversation_context['current_topic'] = new_topic
        
        # Track successful matches
        if matched_group and confidence >= self.MATCHING_CONFIG['SIMILARITY_THRESHOLDS']['medium_confidence']:
            self.conversation_context['last_successful_match'] = matched_group
            self.performance_stats['successful_matches'] += 1
        elif confidence > 0:
            self.performance_stats['successful_matches'] += 1
        else:
            self.performance_stats['failed_matches'] += 1
        
        self.performance_stats['total_questions'] += 1
    
    def extract_meaningful_entities(self, text: str) -> List[str]:
        """Extract meaningful entities"""
        entities = []
        words = re.findall(r'\b\w+\b', text.lower())
        
        for word in words:
            if (len(word) >= 4 and
                word not in ['what', 'how', 'where', 'when', 'why', 'who', 'which', 
                           'tell', 'explain', 'about', 'thank', 'thanks', 'hello', 'hi']):
                entities.append(word)
        
        return entities
    
    def detect_topic(self, text: str) -> str:
        """Detect topic from text"""
        text_lower = text.lower()
        
        topic_patterns = {
            'greeting': ['hello', 'hi', 'hey', 'greetings'],
            'thanks': ['thank', 'thanks', 'appreciate'],
        }
        
        for topic, keywords in topic_patterns.items():
            if any(keyword in text_lower for keyword in keywords):
                return topic
        
        return self.conversation_context['current_topic'] or 'general'
    
    def get_context_summary(self) -> str:
        """Get context summary"""
        summary = []
        
        if self.conversation_context['current_topic']:
            summary.append(f"Topic: {self.conversation_context['current_topic']}")
        
        if self.conversation_context['mentioned_entities']:
            entities = list(self.conversation_context['mentioned_entities'])[-2:]
            summary.append(f"Recent: {', '.join(entities)}")
        
        if self.is_in_tree():
            tree_pos = self.get_current_tree_position()
            summary.append(f"🌳 {tree_pos}")
        
        return " | ".join(summary) if summary else "Minimal context"
    
    def show_statistics(self):
        """Show statistics"""
        total = self.performance_stats['total_questions']
        if total == 0:
            print("No questions processed yet.")
            return
        
        success_rate = self.performance_stats['successful_matches'] / total
        
        print(f"\n📊 Performance Statistics:")
        print(f"   Total questions: {total}")
        print(f"   Success rate: {success_rate:.1%}")
        print(f"   Tree entries: {self.performance_stats['tree_entries']}")
        print(f"   Tree navigations: {self.performance_stats['tree_navigations']}")
        print(f"   Tree exits: {self.performance_stats['tree_exits']}")
        print(f"   Confidence rejections: {self.performance_stats['confidence_rejections']}")
        print(f"   Groups in model: {len(self.qa_groups)}")
        print(f"   Answer confidence requirement: {self.answer_confidence_requirement:.2f} ({'enabled' if self.answer_confidence_requirement > 0 else 'disabled'})")
    
    # ===== CHAT INTERFACE =====
    
    def chat(self):
        if not self.qa_groups:
            print("❌ No model loaded. Cannot start chat.")
            return
        
        print(f"\n🤖 {self.current_model} - Enhanced Chatbot with Tree Navigation")
        print("Type 'quit' to exit, 'stats' for statistics, 'context' for current context")
        print("Type 'reset' to clear conversation context")
        print("Type 'confidence <value>' to set minimum confidence requirement (0.0-1.0, 0.0 = disabled)")
        print(f"✨ Answer confidence requirement: {self.answer_confidence_requirement:.2f} ({'enabled' if self.answer_confidence_requirement > 0 else 'disabled'})")
        print("✨ NEW: Natural tree navigation - say 'go back', 'what are my options', etc.")
        print("-" * 60)
        
        while True:
            try:
                user_input = input("\nYou: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['quit', 'exit', 'bye']:
                    print("🤖 Goodbye! Thanks for chatting!")
                    break
                
                elif user_input.lower() == 'context':
                    print(f"🧠 Current Context: {self.get_context_summary()}")
                    continue
                
                elif user_input.lower() == 'stats':
                    self.show_statistics()
                    continue
                
                elif user_input.lower().startswith('confidence'):
                    parts = user_input.split()
                    if len(parts) == 2:
                        try:
                            requirement = float(parts[1])
                            self.set_confidence_requirement(requirement)
                        except ValueError:
                            print("❌ Please enter a valid number between 0.0 and 1.0")
                    else:
                        print("Usage: confidence <value> (0.0-1.0, 0.0 = disabled)")
                    continue
                
                elif user_input.lower() == 'reset':
                    self.reset_conversation_context()
                    print("🔄 Conversation context reset!")
                    continue
                
                responses = self.process_multiple_questions(user_input)
                self.display_responses(responses)
                
            except KeyboardInterrupt:
                print("\n🤖 Chatbot session ended.")
                break
            except Exception as e:
                print(f"🤖 Error: {e}")
    
    def display_responses(self, responses: List[Tuple]):
        """Display responses - streaming is handled by layer in GUI mode"""
        for i, (original_question, answer, confidence, corrections, matched_group, match_type) in enumerate(responses, 1):
            print(f"\n--- Question {i} ---")
            print(f"📝 You asked: '{original_question}'")
            
            if corrections:
                best_correction, best_score = corrections[0]
                print(f"🔧 Auto-corrected to: '{best_correction}' (confidence: {best_score}%)")
            
            if answer:
                if match_type == "confidence_rejection":
                    print("❌ Confidence too low - treating as unknown question")
                    self.stream_text_via_api(answer, "🤖 ")
                else:
                    self.stream_text_via_api(answer, "🤖 ")
                
                if matched_group and confidence > 0 and match_type != "confidence_rejection":
                    match_type_display = {
                        "exact": "🎯 Exact match",
                        "high_confidence": "✅ High confidence", 
                        "medium_confidence": "⚠️  Medium confidence",
                        "low_confidence": "🔍 Low confidence",
                        "semantic": "🧠 Semantic match",
                        "follow_up": "🔄 Follow-up",
                        "tree_branch": "🌳 Tree branch",
                        "navigation": "🧭 Navigation",
                        "unknown": "❓ Unknown"
                    }
                    display_type = match_type_display.get(match_type, match_type)
                    
                    match_info = f"{display_type} from group '{matched_group}' (confidence: {confidence:.2f})"
                    self.stream_text_via_api(match_info, "💡 ")
                
                context_summary = self.get_context_summary()
                if context_summary:
                    self.stream_text_via_api(context_summary, "🧠 ")
            else:
                print("🤖 I don't know how to answer that yet.")

# Main execution
def main():
    print("🤖 Edgar AI Engine - Starting...")
    print("=" * 50)
    
    if not os.path.exists("models"):
        print("❌ 'models' folder not found. Please run the training GUI first to create models.")
        return
    
    chatbot = AdvancedChatbot(auto_start_chat=True)

if __name__ == "__main__":
    main()