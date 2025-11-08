import json
import re
import string
import os
import random
import time
import threading
import sys
from typing import List, Dict, Tuple, Optional, Callable
from fuzzywuzzy import fuzz, process
from collections import deque

# Optional NLTK imports with fallbacks
try:
    import nltk
    from nltk.stem import PorterStemmer
    from nltk.tokenize import word_tokenize
    from nltk.corpus import stopwords
    
    # Download required NLTK data with error handling
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        try:
            nltk.download('punkt', quiet=True)
        except:
            print("⚠️  Could not download NLTK punkt data. Using fallback tokenizer.")
    
    try:
        nltk.data.find('corpora/stopwords')
    except LookupError:
        try:
            nltk.download('stopwords', quiet=True)
        except:
            print("⚠️  Could not download NLTK stopwords. Using minimal stopwords list.")
    
    # Initialize NLTK components with fallbacks
    try:
        stemmer = PorterStemmer()
        nltk_stopwords = set(stopwords.words('english'))
        NLTK_AVAILABLE = True
    except:
        stemmer = None
        nltk_stopwords = set(['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'])
        NLTK_AVAILABLE = False
        
except ImportError:
    print("⚠️  NLTK not available. Using simplified text processing.")
    NLTK_AVAILABLE = False
    stemmer = None
    nltk_stopwords = set(['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'])

class AdvancedChatbot:
    def __init__(self, model_name: str = None, enable_model_selection: bool = True, 
                 streaming_speed: int = 0, additional_info_speed: int = 0,
                 run_tests_at_startup: bool = False, letter_streaming: bool = False):
        self.models_folder = "models"
        self.current_model = model_name
        self.enable_model_selection = enable_model_selection
        self.streaming_speed = streaming_speed  # Words per minute (0 = off) - for main responses only
        self.additional_info_speed = additional_info_speed  # Words per minute (0 = off) - for match info and context
        self.run_tests_at_startup = run_tests_at_startup
        self.letter_streaming = letter_streaming  # NEW: Letter-by-letter streaming mode
        self.qa_groups = []
        self.stemmer = stemmer
        self.stop_words = nltk_stopwords
        self.nltk_available = NLTK_AVAILABLE
        
        # Enhanced configuration
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
        
        # Enhanced context system with follow-up tracking
        self.conversation_context = {
            'current_topic': None,
            'previous_topics': deque(maxlen=5),
            'mentioned_entities': deque(maxlen=15),
            'user_preferences': {},
            'conversation_history': deque(maxlen=8),
            'current_goal': None,
            'last_successful_match': None,
            'conversation_mood': 'neutral',
            'topic_consistency_score': 1.0,
            'recent_subjects': deque(maxlen=5),
            'last_detailed_topic': None,
            'available_follow_ups': {},
            'current_group_index': 0,
            'used_questions': set(),
            'used_answers': set(),
            'current_question_index': 0,
            'current_answer_index': 0
        }
        
        self.performance_stats = {
            'total_questions': 0,
            'successful_matches': 0,
            'low_confidence_matches': 0,
            'failed_matches': 0,
            'context_helps': 0,
            'semantic_rejections': 0,
            'follow_up_requests': 0,
            'groups_tested': 0,
            'questions_tested': 0,
            'answers_tested': 0
        }
        
        # Load available models and select one
        self.available_models = self.get_available_models()
        
        if not self.current_model:
            if self.enable_model_selection and self.available_models:
                self.select_model()
            elif self.available_models:
                # Auto-select first model
                self.current_model = self.available_models[0]
                print(f"✅ Auto-selected model: {self.current_model}")
        
        if self.current_model:
            self.load_model_data()
            
            # NEW: Run tests at startup if configured
            if self.run_tests_at_startup:
                print("\n" + "="*60)
                print("🧪 STARTUP TESTING MODE ACTIVATED")
                print("="*60)
                self.run_systematic_test()
                print("\n" + "="*60)
                print("🧪 STARTUP TESTING COMPLETE - Starting chat session...")
                print("="*60)
            
            # Auto-start chat session after model selection
            self.chat()
        else:
            print("❌ No models available. Please create a model first using the training GUI.")
    
    def get_available_models(self) -> List[str]:
        """Get list of available models"""
        models = []
        if os.path.exists(self.models_folder):
            for file in os.listdir(self.models_folder):
                if file.endswith('.json'):
                    model_name = file[:-5]  # Remove .json extension
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
            
            # Initialize testing state
            self.initialize_testing_state()
            
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            self.qa_groups = []
    
    def initialize_testing_state(self):
        """Initialize state for systematic testing"""
        self.conversation_context['current_group_index'] = 0
        self.conversation_context['used_questions'] = set()
        self.conversation_context['used_answers'] = set()
        self.conversation_context['current_question_index'] = 0
        self.conversation_context['current_answer_index'] = 0
        
        # Reset performance stats for testing
        self.performance_stats.update({
            'groups_tested': 0,
            'questions_tested': 0,
            'answers_tested': 0
        })
    
    # ===== ENHANCED STREAMING FUNCTIONALITY =====
    
    def stream_text(self, text: str, prefix: str = "🤖 ", wpm: int = None):
        """Stream text word by word or letter by letter with adjustable speed"""
        if wpm is None:
            wpm = self.streaming_speed
            
        if wpm == 0:
            # Streaming disabled - print immediately
            print(f"{prefix}{text}")
            return
        
        if self.letter_streaming:
            # NEW: Letter-by-letter streaming mode
            self._stream_letters(text, prefix, wpm)
        else:
            # Word-by-word streaming mode
            self._stream_words(text, prefix, wpm)
    
    def _stream_words(self, text: str, prefix: str, wpm: int):
        """Stream text word by word"""
        # Calculate delay between words based on words per minute
        words_per_second = wpm / 60.0
        delay_per_word = 1.0 / words_per_second if words_per_second > 0 else 0
        
        words = text.split()
        sys.stdout.write(prefix)
        sys.stdout.flush()
        
        for i, word in enumerate(words):
            # Add space before word (except first word)
            if i > 0:
                sys.stdout.write(' ')
            
            sys.stdout.write(word)
            sys.stdout.flush()
            
            # Add punctuation pauses
            if word.endswith(('.', '!', '?')):
                time.sleep(delay_per_word * 1.5)  # Longer pause at sentence end
            elif word.endswith((',', ';', ':')):
                time.sleep(delay_per_word * 1.2)  # Slightly longer pause at clauses
            else:
                time.sleep(delay_per_word)
        
        print()  # New line at the end
    
    def _stream_letters(self, text: str, prefix: str, wpm: int):
        """NEW: Stream text letter by letter"""
        # Convert words per minute to letters per minute
        # Average English word length is ~4.7 letters, so we'll use 5 for calculation
        lpm = wpm * 5
        letters_per_second = lpm / 60.0
        delay_per_letter = 1.0 / letters_per_second if letters_per_second > 0 else 0
        
        sys.stdout.write(prefix)
        sys.stdout.flush()
        
        for char in text:
            sys.stdout.write(char)
            sys.stdout.flush()
            
            # Slightly longer pauses for punctuation and spaces
            if char in '.!?':
                time.sleep(delay_per_letter * 3)
            elif char in ',;:':
                time.sleep(delay_per_letter * 2)
            elif char == ' ':
                time.sleep(delay_per_letter * 1.5)
            else:
                time.sleep(delay_per_letter)
        
        print()  # New line at the end
    
    def set_streaming_speed(self, wpm: int):
        """Set main response streaming speed in words per minute (0 = off)"""
        self.streaming_speed = max(0, wpm)
        mode = "letters" if self.letter_streaming else "words"
        status = "disabled" if wpm == 0 else f"set to {wpm} WPM ({mode})"
        print(f"📝 Main response streaming {status}")
    
    def set_additional_info_speed(self, wpm: int):
        """Set additional info streaming speed in words per minute (0 = off)"""
        self.additional_info_speed = max(0, wpm)
        mode = "letters" if self.letter_streaming else "words"
        status = "disabled" if wpm == 0 else f"set to {wpm} WPM ({mode})"
        print(f"📝 Additional info streaming {status}")
    
    def toggle_letter_streaming(self):
        """NEW: Toggle between word and letter streaming modes"""
        self.letter_streaming = not self.letter_streaming
        mode = "LETTER-BY-LETTER" if self.letter_streaming else "WORD-BY-WORD"
        print(f"📝 Streaming mode changed to: {mode}")
    
    # ===== ENHANCED "TELL ME MORE" FUNCTIONALITY =====
    
    def handle_tell_me_more(self, user_input: str) -> Optional[str]:
        """Enhanced tell me more handling with subject extraction"""
        user_input_lower = user_input.lower().strip()
        
        # Patterns for tell me more requests
        tell_me_patterns = [
            r'tell me more(?:\s+about\s+(.+))?',
            r'more information(?:\s+about\s+(.+))?',
            r'explain more(?:\s+about\s+(.+))?',
            r'go deeper(?:\s+about\s+(.+))?',
            r'elaborate(?:\s+on\s+(.+))?',
            r'what else(?:\s+about\s+(.+))?',
            r'give me details(?:\s+about\s+(.+))?',
        ]
        
        extracted_subject = None
        for pattern in tell_me_patterns:
            match = re.search(pattern, user_input_lower)
            if match:
                if match.group(1):  # Has a specific subject
                    extracted_subject = match.group(1).strip()
                break
        
        # Handle the request
        if extracted_subject:
            # User asked about a specific subject
            return self.handle_specific_follow_up(extracted_subject)
        else:
            # User asked generally - use context
            return self.handle_context_follow_up()
    
    def handle_specific_follow_up(self, subject: str) -> Optional[str]:
        """Handle tell me more about [specific subject]"""
        self.performance_stats['follow_up_requests'] += 1
        
        # Find the best matching QA group for this subject
        best_match = None
        best_score = 0.0
        
        for group in self.qa_groups:
            # Calculate similarity with the subject
            score = self.calculate_subject_similarity(subject, group)
            if score > best_score and score > 0.3:  # Reasonable threshold
                best_score = score
                best_match = group
        
        if best_match and best_match.get('follow_ups'):
            follow_up_info = self.extract_follow_up_info(best_match['follow_ups'])
            if follow_up_info:
                self.conversation_context['last_detailed_topic'] = best_match.get('group_name', 'Unknown')
                return follow_up_info
        
        # No specific information found, but try to be helpful
        return f"I don't have detailed information about '{subject}' specifically. I can tell you about {self.get_available_topics()}!"
    
    def extract_follow_up_info(self, follow_ups: List) -> str:
        """Extract follow-up information from the tree structure"""
        if not follow_ups:
            return ""
        
        info_parts = []
        for follow_up in follow_ups:
            branch_name = follow_up.get('branch_name', 'Unknown')
            question = follow_up.get('question', '')
            answer = follow_up.get('answer', '')
            
            if answer:  # Only include if there's actual content
                info_parts.append(f"• {branch_name}: {answer}")
            
            # Recursively get children
            children_info = self.extract_follow_up_info(follow_up.get('children', []))
            if children_info:
                # Indent child information for better readability
                indented_children = '\n'.join(f"  {line}" for line in children_info.split('\n'))
                info_parts.append(indented_children)
        
        return "\n".join(info_parts) if info_parts else ""
    
    def handle_context_follow_up(self) -> Optional[str]:
        """Handle general tell me more using conversation context"""
        self.performance_stats['follow_up_requests'] += 1
        
        # Priority 1: Last successful match
        last_match = self.conversation_context.get('last_successful_match')
        if last_match and last_match.get('follow_ups'):
            follow_up_info = self.extract_follow_up_info(last_match['follow_ups'])
            if follow_up_info:
                self.conversation_context['last_detailed_topic'] = last_match.get('group_name', 'Unknown')
                return follow_up_info
        
        # Priority 2: Current topic
        current_topic = self.conversation_context.get('current_topic')
        if current_topic:
            # Find a QA group matching the current topic
            for group in self.qa_groups:
                if (group.get('topic') == current_topic and 
                    group.get('follow_ups')):
                    follow_up_info = self.extract_follow_up_info(group['follow_ups'])
                    if follow_up_info:
                        self.conversation_context['last_detailed_topic'] = group.get('group_name', 'Unknown')
                        return follow_up_info
        
        # Fallback
        return "I'd be happy to provide more details! Could you be more specific about what you'd like to learn more about?"
    
    def calculate_subject_similarity(self, subject: str, group: dict) -> float:
        """Calculate how well a subject matches a QA group"""
        subject_lower = subject.lower()
        group_name_lower = group.get('group_name', '').lower()
        group_desc_lower = group.get('group_description', '').lower()
        group_topic = group.get('topic', '').lower()
        
        scores = []
        
        # Check group name
        if group_name_lower and subject_lower in group_name_lower:
            scores.append(0.9)
        
        # Check group description
        if group_desc_lower and subject_lower in group_desc_lower:
            scores.append(0.7)
        
        # Check topic
        if group_topic and subject_lower in group_topic:
            scores.append(0.8)
        
        # Check questions in the group
        for question in group.get('questions', []):
            if subject_lower in question.lower():
                scores.append(0.6)
                break
        
        return max(scores) if scores else 0.0
    
    def get_available_topics(self) -> str:
        """Get string of available topics"""
        topics = set()
        for group in self.qa_groups:
            topic = group.get('topic')
            if topic:
                topics.add(topic)
        return ", ".join(sorted(topics)) if topics else "various topics"
    
    # ===== ENHANCED CONTEXT SYSTEM =====
    
    def update_conversation_context(self, user_input: str, bot_response: str, matched_group: dict = None, confidence: float = 0.0):
        """Enhanced context tracking"""
        # Add to conversation history
        self.conversation_context['conversation_history'].append({
            'user': user_input,
            'bot': bot_response,
            'timestamp': time.time(),
            'confidence': confidence,
            'matched_topic': matched_group.get('topic') if matched_group else None
        })
        
        # Extract and track meaningful entities
        entities = self.extract_meaningful_entities(user_input)
        for entity in entities:
            if entity not in self.conversation_context['mentioned_entities']:
                self.conversation_context['mentioned_entities'].append(entity)
        
        # Extract and track subjects
        subject = self.extract_subject(user_input)
        if subject and subject not in self.conversation_context['recent_subjects']:
            self.conversation_context['recent_subjects'].append(subject)
        
        # Update current topic
        new_topic = self.detect_topic_with_confidence(user_input)
        self.update_topic_consistency(new_topic)
        
        # Track successful matches
        if matched_group and confidence >= self.MATCHING_CONFIG['SIMILARITY_THRESHOLDS']['medium_confidence']:
            self.conversation_context['last_successful_match'] = matched_group
            self.performance_stats['successful_matches'] += 1
        elif confidence > 0:
            self.performance_stats['low_confidence_matches'] += 1
        else:
            self.performance_stats['failed_matches'] += 1
        
        self.performance_stats['total_questions'] += 1
    
    def extract_subject(self, text: str) -> Optional[str]:
        """Extract the main subject from a question"""
        text_lower = text.lower().strip()
        
        patterns = [
            r'what is (.+?)\??$',
            r'what are (.+?)\??$', 
            r'who is (.+?)\??$',
            r'where is (.+?)\??$',
            r'when is (.+?)\??$',
            r'why is (.+?)\??$',
            r'how does (.+?)\??$',
            r'tell me about (.+?)\??$',
            r'explain (.+?)\??$',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text_lower)
            if match:
                subject = match.group(1).strip()
                subject = re.sub(r'^(the|a|an)\s+', '', subject)
                return subject if len(subject) >= 2 else None
        
        return None
    
    def extract_meaningful_entities(self, text: str) -> List[str]:
        """Extract meaningful entities with NLTK fallback"""
        entities = []
        text_lower = text.lower()
        
        try:
            if self.nltk_available:
                # Try using NLTK tokenizer
                words = word_tokenize(text_lower)
            else:
                # Fallback: simple space-based tokenization with punctuation removal
                words = re.findall(r'\b\w+\b', text_lower)
        except Exception as e:
            # Ultimate fallback
            words = re.findall(r'\b\w+\b', text_lower)
        
        for word in words:
            if (len(word) >= 4 and
                word not in self.stop_words and 
                word.isalpha() and
                word not in ['what', 'how', 'where', 'when', 'why', 'who', 'which', 
                           'tell', 'explain', 'about', 'thank', 'thanks', 'hello', 'hi']):
                entities.append(word)
        
        return entities
    
    def detect_topic_with_confidence(self, text: str) -> str:
        """Detect topic with confidence scoring"""
        text_lower = text.lower()
        
        # Extract topics from actual groups
        topic_patterns = {}
        for group in self.qa_groups:
            topic = group.get('topic')
            if topic and topic not in topic_patterns:
                topic_patterns[topic] = {
                    'keywords': [topic.lower()],
                    'weight': 1.2
                }
        
        # Add default patterns
        default_patterns = {
            'greeting': {'keywords': ['hello', 'hi', 'hey', 'greetings'], 'weight': 2.0},
            'thanks': {'keywords': ['thank', 'thanks', 'appreciate', 'grateful'], 'weight': 2.0},
        }
        
        for topic, pattern in default_patterns.items():
            if topic not in topic_patterns:
                topic_patterns[topic] = pattern
        
        topic_scores = {}
        for topic, pattern in topic_patterns.items():
            score = sum(1 for keyword in pattern['keywords'] if keyword in text_lower)
            if score > 0:
                topic_scores[topic] = score * pattern['weight']
        
        if topic_scores:
            best_topic = max(topic_scores.items(), key=lambda x: x[1])[0]
            if topic_scores[best_topic] >= 1.0:
                if best_topic != self.conversation_context['current_topic']:
                    self.conversation_context['previous_topics'].append(self.conversation_context['current_topic'])
                self.conversation_context['current_topic'] = best_topic
                return best_topic
        
        return self.conversation_context['current_topic'] or 'general'
    
    def update_topic_consistency(self, new_topic: str):
        """Track topic consistency"""
        if not self.conversation_context['conversation_history']:
            self.conversation_context['topic_consistency_score'] = 1.0
            return
        
        recent_topics = []
        for exchange in list(self.conversation_context['conversation_history'])[-3:]:
            if exchange.get('matched_topic'):
                recent_topics.append(exchange['matched_topic'])
        
        if recent_topics:
            same_topic_count = sum(1 for topic in recent_topics if topic == new_topic)
            consistency = same_topic_count / len(recent_topics)
            self.conversation_context['topic_consistency_score'] = (
                self.conversation_context['topic_consistency_score'] * 0.7 + consistency * 0.3
            )
    
    # ===== IMPROVED MATCHING SYSTEM =====
    
    def find_best_match(self, user_question: str) -> Optional[Tuple[dict, float, str]]:
        """Find best match with improved logic"""
        user_question_lower = user_question.lower().strip()
        
        # First check for tell me more patterns
        tell_me_response = self.handle_tell_me_more(user_question)
        if tell_me_response and any(pattern in user_question_lower for pattern in ['tell me more', 'more information', 'explain more']):
            # Create a temporary group for the follow-up response
            temp_group = {
                "group_name": "Follow-up Information",
                "questions": [user_question],
                "answers": [tell_me_response],
                "topic": "follow_up"
            }
            return temp_group, 0.9, "follow_up"
        
        # Then proceed with normal matching
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
        
        # Multiple similarity measures
        full_similarity = fuzz.token_set_ratio(user_lower, db_lower) / 100.0
        
        # Combined score
        return min(full_similarity, 1.0)
    
    def auto_correct_input(self, user_input: str) -> Tuple[str, List[Tuple[str, int]]]:
        """Auto-correct input"""
        user_lower = user_input.lower().strip()
        
        if len(user_lower) <= 3:
            return user_input, []
        
        # Get all questions from all groups
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
        user_subject = self.extract_subject(user_question)
        matched_subject = self.extract_subject(matched_question)
        
        if user_subject and matched_subject:
            subject_similarity = fuzz.token_set_ratio(user_subject, matched_subject) / 100.0
            if subject_similarity < 0.3:
                return False
        
        user_words = set(user_question.lower().split())
        matched_words = set(matched_question.lower().split())
        common_words = {'what', 'is', 'are', 'how', 'why', 'when', 'where', 'who', 'tell', 'me', 'about'}
        user_content = user_words - common_words
        matched_content = matched_words - common_words
        
        return bool(user_content.intersection(matched_content))
    
    # ===== QUESTION PROCESSING =====
    
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
    
    def process_multiple_questions(self, user_input: str) -> List[Tuple]:
        """Process input with enhanced follow-up support"""
        questions = self.split_questions(user_input)
        responses = []
        
        for question in questions:
            if not question.strip():
                continue
                
            corrected_question, corrections = self.auto_correct_input(question)
            match_result = self.find_best_match(corrected_question)
            
            if match_result:
                group, confidence, match_type = match_result
                answer = self.get_random_answer(group.get('answers', []))
                
                # Add follow-up suggestion for relevant matches
                if (group.get('follow_ups') and 
                    match_type in ['exact', 'high_confidence'] and
                    random.random() < 0.4):
                    answer += " Would you like to know more about this?"
                
                responses.append((question, answer, confidence, corrections, group.get('group_name', 'Unknown'), match_type))
                self.update_conversation_context(question, answer, group, confidence)
            else:
                unknown_response = self.handle_unknown_question(question)
                responses.append((question, unknown_response, 0.0, corrections, None, "unknown"))
                self.update_conversation_context(question, unknown_response, None, 0.0)
        
        return responses
    
    def handle_unknown_question(self, question: str) -> str:
        """Handle unknown questions"""
        subject = self.extract_subject(question)
        current_topic = self.conversation_context.get('current_topic')
        
        base_responses = [
            "I'm not sure about that yet. Could you ask something else?",
            "I don't have information about that currently.",
            "That's beyond my knowledge at the moment.",
        ]
        
        if subject:
            subject_responses = [
                f"I don't know about {subject} specifically.",
                f"I'm not familiar with {subject}.",
            ]
            base_responses = subject_responses + base_responses
        
        if current_topic:
            # Find available topics from groups
            available_topics = self.get_available_topics()
            base_responses.append(f"I can help with topics like: {available_topics}")
        
        return random.choice(base_responses)
    
    def get_random_answer(self, answers: List[str]) -> str:
        return random.choice(answers) if answers else "I don't have an answer for that."
    
    # ===== ENHANCED TESTING SYSTEM =====
    
    def get_current_testing_group(self) -> Optional[Dict]:
        """Get the current group being tested"""
        if not self.qa_groups:
            return None
        
        current_index = self.conversation_context['current_group_index']
        if current_index < len(self.qa_groups):
            return self.qa_groups[current_index]
        return None
    
    def get_next_question_variant(self) -> Optional[Tuple[str, str]]:
        """Get the next question variant to test from current group"""
        current_group = self.get_current_testing_group()
        if not current_group:
            return None
        
        questions = current_group.get('questions', [])
        if not questions:
            return None
        
        # Find next unused question
        for i, question in enumerate(questions):
            question_id = f"{self.conversation_context['current_group_index']}_{i}"
            if question_id not in self.conversation_context['used_questions']:
                self.conversation_context['current_question_index'] = i
                return question, question_id
        
        return None
    
    def get_next_answer_variant(self) -> Optional[str]:
        """Get the next answer variant to test from current group"""
        current_group = self.get_current_testing_group()
        if not current_group:
            return None
        
        answers = current_group.get('answers', [])
        if not answers:
            return None
        
        # Find next unused answer
        for i, answer in enumerate(answers):
            answer_id = f"{self.conversation_context['current_group_index']}_{i}"
            if answer_id not in self.conversation_context['used_answers']:
                self.conversation_context['current_answer_index'] = i
                return answer
        
        return None
    
    def mark_question_used(self, question_id: str):
        """Mark a question variant as used"""
        self.conversation_context['used_questions'].add(question_id)
        self.performance_stats['questions_tested'] += 1
    
    def mark_answer_used(self, answer_id: str):
        """Mark an answer variant as used"""
        self.conversation_context['used_answers'].add(answer_id)
        self.performance_stats['answers_tested'] += 1
    
    def move_to_next_group(self):
        """Move to the next group for testing"""
        current_group = self.get_current_testing_group()
        if current_group:
            self.performance_stats['groups_tested'] += 1
        
        self.conversation_context['current_group_index'] += 1
        self.conversation_context['used_questions'] = set()
        self.conversation_context['used_answers'] = set()
        self.conversation_context['current_question_index'] = 0
        self.conversation_context['current_answer_index'] = 0
    
    def is_group_completed(self) -> bool:
        """Check if all variants in current group have been tested"""
        current_group = self.get_current_testing_group()
        if not current_group:
            return True
        
        questions = current_group.get('questions', [])
        answers = current_group.get('answers', [])
        
        # Check if all questions and answers have been used
        all_questions_used = len(self.conversation_context['used_questions']) >= len(questions)
        all_answers_used = len(self.conversation_context['used_answers']) >= len(answers)
        
        return all_questions_used and all_answers_used
    
    def is_testing_complete(self) -> bool:
        """Check if all groups have been tested"""
        return self.conversation_context['current_group_index'] >= len(self.qa_groups)
    
    def get_testing_progress(self) -> Dict:
        """Get current testing progress"""
        if not self.qa_groups:
            return {'complete': True, 'progress': 0.0}
        
        total_groups = len(self.qa_groups)
        current_group_index = self.conversation_context['current_group_index']
        
        if current_group_index >= total_groups:
            return {'complete': True, 'progress': 1.0}
        
        current_group = self.qa_groups[current_group_index]
        questions = current_group.get('questions', [])
        answers = current_group.get('answers', [])
        
        questions_used = len(self.conversation_context['used_questions'])
        answers_used = len(self.conversation_context['used_answers'])
        
        group_progress = (questions_used + answers_used) / (len(questions) + len(answers)) if (questions and answers) else 1.0
        
        overall_progress = (current_group_index + min(group_progress, 1.0)) / total_groups
        
        return {
            'complete': False,
            'progress': overall_progress,
            'current_group': current_group_index + 1,
            'total_groups': total_groups,
            'current_group_name': current_group.get('group_name', f'Group {current_group_index + 1}'),
            'questions_tested': questions_used,
            'total_questions': len(questions),
            'answers_tested': answers_used,
            'total_answers': len(answers)
        }
    
    def run_systematic_test(self):
        """Run systematic test using all question and answer variants"""
        if not self.qa_groups:
            print("❌ No QA groups available for testing")
            return
        
        print(f"\n🧪 Starting Systematic Test for '{self.current_model}'")
        print("=" * 60)
        
        self.initialize_testing_state()
        test_results = []
        total_combinations = sum(len(group.get('questions', [])) * len(group.get('answers', [])) for group in self.qa_groups)
        current_combination = 0
        
        print(f"📊 Total question-answer combinations to test: {total_combinations}")
        
        while not self.is_testing_complete():
            progress = self.get_testing_progress()
            current_group = self.get_current_testing_group()
            
            if not current_group:
                break
            
            print(f"\n📋 Testing Group {progress['current_group']}/{progress['total_groups']}: {current_group.get('group_name', 'Unnamed Group')}")
            print(f"📊 Progress: {progress['progress']:.1%}")
            
            group_results = self.test_current_group()
            test_results.extend(group_results)
            
            # Update combination count
            current_combination += len(group_results)
            print(f"✅ Group completed: {len(group_results)} combinations tested")
            
            self.move_to_next_group()
        
        print(f"\n✅ Testing Complete!")
        print("=" * 60)
        self.show_test_results(test_results)
    
    def test_current_group(self) -> List[Dict]:
        """Test all variants in the current group"""
        results = []
        current_group = self.get_current_testing_group()
        
        while not self.is_group_completed():
            # Get next question variant
            question_result = self.get_next_question_variant()
            if not question_result:
                break
            
            question, question_id = question_result
            
            # Test this question with all answer variants
            answer_variants_tested = 0
            while True:
                answer = self.get_next_answer_variant()
                if not answer:
                    break
                
                # Test the combination
                result = self.test_question_answer_pair(question, answer, current_group)
                results.append(result)
                
                # Mark answer as used
                answer_id = f"{self.conversation_context['current_group_index']}_{self.conversation_context['current_answer_index']}"
                self.mark_answer_used(answer_id)
                answer_variants_tested += 1
                
                # NEW: Enhanced progress display showing the actual testing
                print(f"  🔍 Testing: '{question}'")
                print(f"  💬 Answer: '{answer[:80]}{'...' if len(answer) > 80 else ''}'")
                print(f"  ✅ Match confidence: {result['confidence']:.2f} - {'✓' if result['is_correct_match'] else '✗'}")
                print(f"  {'-'*40}")
            
            # Mark question as used
            self.mark_question_used(question_id)
        
        return results
    
    def test_question_answer_pair(self, question: str, answer: str, group: Dict) -> Dict:
        """Test a specific question-answer pair"""
        # Simulate the matching process
        match_result = self.find_best_match(question)
        confidence = 0.0
        match_type = "unknown"
        
        if match_result:
            matched_group, confidence, match_type = match_result
            # Check if it matched the correct group
            is_correct_match = matched_group.get('group_name') == group.get('group_name')
        else:
            is_correct_match = False
        
        return {
            'question': question,
            'answer': answer,
            'group': group.get('group_name'),
            'confidence': confidence,
            'match_type': match_type,
            'is_correct_match': is_correct_match,
            'timestamp': time.time()
        }
    
    def show_test_results(self, results: List[Dict]):
        """Display comprehensive test results"""
        if not results:
            print("No test results to display")
            return
        
        total_tests = len(results)
        successful_matches = sum(1 for r in results if r['is_correct_match'])
        average_confidence = sum(r['confidence'] for r in results) / total_tests if total_tests > 0 else 0
        
        print(f"📊 Test Results Summary:")
        print(f"   Total tests performed: {total_tests}")
        print(f"   Successful matches: {successful_matches}/{total_tests} ({successful_matches/total_tests:.1%})")
        print(f"   Average confidence: {average_confidence:.2f}")
        print(f"   Groups tested: {self.performance_stats['groups_tested']}")
        print(f"   Questions tested: {self.performance_stats['questions_tested']}")
        print(f"   Answers tested: {self.performance_stats['answers_tested']}")
        
        # Show match type distribution
        match_types = {}
        for result in results:
            match_type = result['match_type']
            match_types[match_type] = match_types.get(match_type, 0) + 1
        
        print(f"\n🎯 Match Type Distribution:")
        for match_type, count in match_types.items():
            percentage = count / total_tests
            print(f"   {match_type}: {count} ({percentage:.1%})")
        
        # Show low confidence matches
        low_confidence = [r for r in results if r['confidence'] < 0.5 and r['is_correct_match']]
        if low_confidence:
            print(f"\n⚠️  Low Confidence Correct Matches ({len(low_confidence)}):")
            for result in low_confidence[:5]:  # Show first 5
                print(f"   '{result['question']}' (confidence: {result['confidence']:.2f})")
    
    # ===== SIMPLIFIED UTILITY METHODS =====
    
    def get_context_summary(self) -> str:
        """Get context summary"""
        summary = []
        
        if self.conversation_context['current_topic']:
            consistency = self.conversation_context['topic_consistency_score']
            summary.append(f"Topic: {self.conversation_context['current_topic']} ({consistency:.1f})")
        
        if self.conversation_context['mentioned_entities']:
            entities = list(self.conversation_context['mentioned_entities'])[-3:]
            summary.append(f"Recent: {', '.join(entities)}")
        
        if self.conversation_context['last_detailed_topic']:
            summary.append(f"Last detailed: {self.conversation_context['last_detailed_topic'][:20]}...")
        
        return " | ".join(summary) if summary else "Minimal context"
    
    def show_statistics(self):
        """Show statistics"""
        total = self.performance_stats['total_questions']
        if total == 0:
            print("No questions processed yet.")
            return
        
        success_rate = self.performance_stats['successful_matches'] / total
        
        streaming_mode = "letters" if self.letter_streaming else "words"
        
        print(f"\n📊 Performance Statistics:")
        print(f"   Total questions: {total}")
        print(f"   Success rate: {success_rate:.1%}")
        print(f"   Follow-up requests: {self.performance_stats['follow_up_requests']}")
        print(f"   Failed matches: {self.performance_stats['failed_matches']}")
        print(f"   Groups in model: {len(self.qa_groups)}")
        print(f"   Main response streaming: {self.streaming_speed} WPM ({'enabled' if self.streaming_speed > 0 else 'disabled'}) - {streaming_mode} mode")
        print(f"   Additional info streaming: {self.additional_info_speed} WPM ({'enabled' if self.additional_info_speed > 0 else 'disabled'}) - {streaming_mode} mode")
    
    # ===== CHAT INTERFACE =====
    
    def chat(self):
        if not self.qa_groups:
            print("❌ No model loaded. Cannot start chat.")
            return
        
        streaming_mode = "LETTER-BY-LETTER" if self.letter_streaming else "WORD-BY-WORD"
        
        print(f"\n🤖 {self.current_model} - Enhanced Chatbot with Follow-up Support")
        print("Type 'quit' to exit, 'stats' for statistics, 'context' for current context")
        print("Type 'reset' to clear conversation context, 'test' to run systematic test")
        print("Type 'streaming <wpm>' to set main response streaming speed (0 = off)")
        print("Type 'additional_speed <wpm>' to set additional info streaming speed (0 = off)")
        print("Type 'letter_mode' to toggle between word and letter streaming")  # NEW
        print(f"✨ Main response streaming: {self.streaming_speed} WPM ({'enabled' if self.streaming_speed > 0 else 'disabled'}) - {streaming_mode}")
        print(f"✨ Additional info streaming: {self.additional_info_speed} WPM ({'enabled' if self.additional_info_speed > 0 else 'disabled'}) - {streaming_mode}")
        print("✨ NEW: Try 'tell me more' or 'tell me more about [subject]' for detailed information!")
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
                
                elif user_input.lower() == 'test':
                    self.run_systematic_test()
                    continue
                
                elif user_input.lower() == 'letter_mode':  # NEW
                    self.toggle_letter_streaming()
                    continue
                
                elif user_input.lower().startswith('streaming'):
                    # Handle streaming command for main responses
                    parts = user_input.split()
                    if len(parts) == 2:
                        try:
                            wpm = int(parts[1])
                            self.set_streaming_speed(wpm)
                        except ValueError:
                            print("❌ Please enter a valid number for WPM")
                    else:
                        print("Usage: streaming <wpm> (0 = off)")
                    continue
                
                elif user_input.lower().startswith('additional_speed'):
                    # Handle streaming command for additional info
                    parts = user_input.split()
                    if len(parts) == 2:
                        try:
                            wpm = int(parts[1])
                            self.set_additional_info_speed(wpm)
                        except ValueError:
                            print("❌ Please enter a valid number for WPM")
                    else:
                        print("Usage: additional_speed <wpm> (0 = off)")
                    continue
                
                elif user_input.lower() == 'reset':
                    # Preserve testing state but reset conversation context
                    self.conversation_context.update({
                        'current_topic': None,
                        'previous_topics': deque(maxlen=5),
                        'mentioned_entities': deque(maxlen=15),
                        'user_preferences': {},
                        'conversation_history': deque(maxlen=8),
                        'current_goal': None,
                        'last_successful_match': None,
                        'conversation_mood': 'neutral',
                        'topic_consistency_score': 1.0,
                        'recent_subjects': deque(maxlen=5),
                        'last_detailed_topic': None,
                        'available_follow_ups': {},
                    })
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
        """Display responses with separate streaming for main response and additional info"""
        for i, (original_question, answer, confidence, corrections, matched_group, match_type) in enumerate(responses, 1):
            print(f"\n--- Question {i} ---")
            print(f"📝 You asked: '{original_question}'")
            
            if corrections:
                best_correction, best_score = corrections[0]
                print(f"🔧 Auto-corrected to: '{best_correction}' (confidence: {best_score}%)")
            
            if answer:
                # Use main response streaming speed for the main answer
                self.stream_text(answer, "🤖 ", self.streaming_speed)
                
                if matched_group and confidence > 0 and match_type != "follow_up":
                    match_type_display = {
                        "exact": "🎯 Exact match",
                        "high_confidence": "✅ High confidence", 
                        "medium_confidence": "⚠️  Medium confidence",
                        "low_confidence": "🔍 Low confidence",
                        "semantic": "🧠 Semantic match",
                        "follow_up": "📚 Follow-up information",
                        "unknown": "❓ Unknown question"
                    }
                    display_type = match_type_display.get(match_type, match_type)
                    
                    # Use additional info streaming speed for match info
                    match_info = f"{display_type} from group '{matched_group}' (confidence: {confidence:.2f})"
                    self.stream_text(match_info, "💡 ", self.additional_info_speed)
                
                context_summary = self.get_context_summary()
                if context_summary:
                    # Use additional info streaming speed for context info
                    self.stream_text(context_summary, "🧠 ", self.additional_info_speed)
            else:
                print("🤖 I don't know how to answer that yet.")

# Main execution with configurable options
def main():
    print("🤖 Edgar AI Engine - Starting...")
    print("=" * 50)
    
    # Check if models folder exists
    if not os.path.exists("models"):
        print("❌ 'models' folder not found. Please run the training GUI first to create models.")
        return
    
    # NEW: Enhanced configuration options
    ENABLE_MODEL_SELECTION = False      # Set to False to auto-select first model
    STREAMING_SPEED = 500              # Words per minute for main responses (0 = off, try 150-300 for natural speed)
    ADDITIONAL_INFO_SPEED = 0           # Words per minute for additional info (0 = off)
    RUN_TESTS_AT_STARTUP = True         # NEW: Set to True to run tests automatically at startup
    LETTER_STREAMING = True            # NEW: Set to True for letter-by-letter streaming
    
    # Initialize chatbot with configuration
    chatbot = AdvancedChatbot(
        enable_model_selection=ENABLE_MODEL_SELECTION,
        streaming_speed=STREAMING_SPEED,
        additional_info_speed=ADDITIONAL_INFO_SPEED,
        run_tests_at_startup=RUN_TESTS_AT_STARTUP,      # NEW
        letter_streaming=LETTER_STREAMING               # NEW
    )

if __name__ == "__main__":
    main()