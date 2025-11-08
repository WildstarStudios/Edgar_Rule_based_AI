import json
import re
import string
import os
import random
import time
import threading
from typing import List, Dict, Tuple, Optional, Callable
from fuzzywuzzy import fuzz, process
import nltk
from nltk.stem import PorterStemmer
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from collections import deque

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

class AdvancedChatbot:
    def __init__(self, database_file: str = "chatbot_database.json"):
        self.database_file = database_file
        self.qa_pairs = []
        self.stemmer = PorterStemmer()
        self.stop_words = set(stopwords.words('english'))
        
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
            'last_detailed_topic': None,  # Track what we last gave details about
            'available_follow_ups': {},   # Store available follow-up information
        }
        
        self.performance_stats = {
            'total_questions': 0,
            'successful_matches': 0,
            'low_confidence_matches': 0,
            'failed_matches': 0,
            'context_helps': 0,
            'semantic_rejections': 0,
            'follow_up_requests': 0,
        }
        
        self.load_enhanced_data_with_followups()
    
    def load_enhanced_data_with_followups(self):
        """Load data with comprehensive follow-up information"""
        self.qa_pairs = [
            # ===== GREETINGS & BASIC =====
            {
                "question": "hello",
                "answers": [
                    "Hello! How can I help you today?",
                    "Hi there! Nice to meet you!",
                    "Hey! I'm here to assist you!",
                ],
                "topic": "greeting",
                "priority": "high",
                "context_sensitive": False,
                "keywords": ["hello", "hi", "hey"],
                "follow_up_info": "I'm an advanced chatbot with context awareness, streaming responses, and intelligent matching. I can help with programming, AI, game development, and much more!"
            },
            {
                "question": "hi",
                "answers": [
                    "Hi! What can I do for you?",
                    "Hello there! How can I assist?",
                    "Hey! Ready to chat!",
                ],
                "topic": "greeting",
                "priority": "high",
                "context_sensitive": False,
                "keywords": ["hello", "hi", "hey"],
                "follow_up_info": "I specialize in technical topics like programming languages, AI concepts, and game development engines. Feel free to ask me anything in these areas!"
            },
            
            # ===== THANKS & COURTESY =====
            {
                "question": "thank you",
                "answers": [
                    "You're welcome! Happy to help!",
                    "My pleasure! Let me know if you need anything else!",
                    "You're welcome! Is there anything more I can assist with?",
                ],
                "topic": "thanks",
                "priority": "high",
                "context_sensitive": False,
                "keywords": ["thank", "thanks", "appreciate"],
                "follow_up_info": "I'm always here to help! I can provide detailed explanations, compare technologies, or help you learn new concepts. Just let me know what you're interested in!"
            },
            
            # ===== PROGRAMMING & TECH =====
            {
                "question": "Tell me about Python",
                "answers": [
                    "Python is a versatile programming language great for beginners and experts!",
                    "Python is known for its simplicity and extensive libraries!",
                    "Python's clean syntax makes it excellent for rapid development!",
                ],
                "topic": "programming",
                "priority": "medium",
                "context_sensitive": True,
                "keywords": ["python", "programming", "language"],
                "follow_up_info": """Python Details:
• Created by Guido van Rossum in 1991
• Used for: web development (Django, Flask), data science (Pandas, NumPy), AI/ML (TensorFlow, PyTorch)
• Key features: dynamic typing, automatic memory management, extensive standard library
• Popular in: scientific computing, automation, web development, and education"""
            },
            {
                "question": "What is Python?",
                "answers": [
                    "Python is a high-level programming language known for its readability and versatility!",
                    "Python is used for web development, data science, AI, and automation!",
                    "It's a popular language with a huge community and extensive libraries!",
                ],
                "topic": "programming",
                "priority": "medium",
                "context_sensitive": True,
                "keywords": ["python", "programming", "language"],
                "follow_up_info": """Python Applications:
• Web Development: Django, Flask, FastAPI
• Data Science: Pandas, NumPy, SciPy
• Machine Learning: TensorFlow, PyTorch, Scikit-learn
• Automation: Scripting, web scraping, DevOps
• Game Development: Pygame, Arcade
• Education: Beginner-friendly syntax and extensive learning resources"""
            },
            {
                "question": "What is machine learning?",
                "answers": [
                    "Machine learning enables computers to learn from data without explicit programming!",
                    "ML algorithms improve automatically through experience and data!",
                    "Machine learning powers modern AI applications and intelligent systems!",
                ],
                "topic": "ai",
                "priority": "medium",
                "context_sensitive": True,
                "keywords": ["machine", "learning", "ai", "algorithm"],
                "follow_up_info": """Machine Learning Types:
• Supervised Learning: Training with labeled data (classification, regression)
• Unsupervised Learning: Finding patterns in unlabeled data (clustering, dimensionality reduction)
• Reinforcement Learning: Learning through trial and error with rewards/punishments

Common Algorithms:
• Linear Regression, Decision Trees, Neural Networks
• K-Means Clustering, Principal Component Analysis
• Q-Learning, Deep Q-Networks

Applications: Recommendation systems, image recognition, natural language processing, autonomous vehicles"""
            },
            {
                "question": "What is Godot?",
                "answers": [
                    "Godot is a free, open-source game engine for 2D and 3D development!",
                    "Godot Engine is known for its flexible scene system and ease of use!",
                    "It's a popular game engine alternative with great community support!",
                ],
                "topic": "gaming",
                "priority": "medium",
                "context_sensitive": True,
                "keywords": ["godot", "game", "engine", "development"],
                "follow_up_info": """Godot Engine Features:
• Scene System: Flexible node-based architecture
• Scripting: GDScript (Python-like), C#, VisualScript
• 2D/3D: Built-in support for both 2D and 3D game development
• Export: Cross-platform to Windows, Mac, Linux, Android, iOS, Web
• Community: Active open-source community with extensive asset library

Advantages:
• Completely free and open-source (MIT license)
• No royalties or subscription fees
• Lightweight and fast
• Great for indie developers and prototyping"""
            },
            {
                "question": "What is artificial intelligence?",
                "answers": [
                    "AI is the simulation of human intelligence in machines!",
                    "Artificial intelligence enables machines to think, learn, and reason!",
                    "AI includes machine learning, natural language processing, and computer vision!",
                ],
                "topic": "ai",
                "priority": "medium",
                "context_sensitive": True,
                "keywords": ["artificial", "intelligence", "ai", "machine"],
                "follow_up_info": """AI Branches:
• Machine Learning: Algorithms that learn from data
• Natural Language Processing: Understanding and generating human language
• Computer Vision: Interpreting and understanding visual information
• Robotics: Intelligent control of physical systems
• Expert Systems: Rule-based decision making

Current Applications:
• Virtual assistants (Siri, Alexa)
• Image and speech recognition
• Autonomous vehicles
• Medical diagnosis systems
• Game AI and procedural content generation"""
            },
            
            # ===== ADDITIONAL TOPICS =====
            {
                "question": "What is Blender?",
                "answers": [
                    "Blender is a free and open-source 3D creation suite!",
                    "Blender is used for 3D modeling, animation, visual effects, and more!",
                    "It's a powerful alternative to commercial 3D software packages!",
                ],
                "topic": "creative",
                "priority": "medium",
                "context_sensitive": True,
                "keywords": ["blender", "3d", "modeling", "animation"],
                "follow_up_info": """Blender Features:
• 3D Modeling: Polygon modeling, sculpting, retopology
• Animation: Character animation, rigging, shape keys
• Rendering: Cycles (ray-tracing) and Eevee (real-time) renderers
• VFX: Compositing, motion tracking, simulation
• Game Development: Game engine (though deprecated in newer versions)

Advantages:
• Completely free and open-source
• Active development and large community
• All-in-one solution for 3D pipeline
• Used in professional studios and indie projects alike"""
            },
            {
                "question": "What is Wildstar Studios?",
                "answers": [
                    "Wildstar Studios appears to be a game development studio!",
                    "I believe Wildstar Studios works on game development projects!",
                    "It seems to be a studio in the gaming industry!",
                ],
                "topic": "gaming",
                "priority": "low",
                "context_sensitive": True,
                "keywords": ["wildstar", "studios", "game", "development"],
                "follow_up_info": """About Game Development Studios:
• Game studios range from small indie teams to large AAA companies
• They typically handle: game design, programming, art, sound, and marketing
• Common roles: Game designers, programmers, artists, producers, QA testers
• Development phases: Pre-production, production, testing, launch, post-launch support

For specific information about Wildstar Studios, you might want to check their official website or recent game releases, as my information might not be current."""
            },
            
            # ===== FALLBACK =====
            {
                "question": "how are you",
                "answers": [
                    "I'm functioning well, thank you! How are you?",
                    "I'm doing great! Ready to help you!",
                    "I'm running smoothly! What can I help with?",
                ],
                "topic": "greeting",
                "priority": "low",
                "context_sensitive": False,
                "keywords": ["how", "are", "you"],
                "follow_up_info": "As an AI, I don't have feelings, but I'm optimized for conversation and context awareness. I'm always learning and improving to provide better assistance!"
            },
        ]
        
        print(f"📚 Loaded {len(self.qa_pairs)} enhanced question-answer pairs with follow-up information!")
    
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
        
        # Find the best matching QA pair for this subject
        best_match = None
        best_score = 0.0
        
        for qa_pair in self.qa_pairs:
            # Calculate similarity with the subject
            score = self.calculate_subject_similarity(subject, qa_pair)
            if score > best_score and score > 0.3:  # Reasonable threshold
                best_score = score
                best_match = qa_pair
        
        if best_match and best_match.get('follow_up_info'):
            self.conversation_context['last_detailed_topic'] = best_match['question']
            return best_match['follow_up_info']
        else:
            # No specific information found, but try to be helpful
            return f"I don't have detailed information about '{subject}' specifically. I can tell you about programming languages, game engines, AI concepts, or other technical topics!"
    
    def handle_context_follow_up(self) -> Optional[str]:
        """Handle general tell me more using conversation context"""
        self.performance_stats['follow_up_requests'] += 1
        
        # Priority 1: Last successful match
        last_match = self.conversation_context.get('last_successful_match')
        if last_match and last_match.get('follow_up_info'):
            self.conversation_context['last_detailed_topic'] = last_match['question']
            return last_match['follow_up_info']
        
        # Priority 2: Current topic
        current_topic = self.conversation_context.get('current_topic')
        if current_topic:
            # Find a QA pair matching the current topic
            for qa_pair in self.qa_pairs:
                if (qa_pair.get('topic') == current_topic and 
                    qa_pair.get('follow_up_info')):
                    self.conversation_context['last_detailed_topic'] = qa_pair['question']
                    return qa_pair['follow_up_info']
        
        # Priority 3: Recent subjects
        if self.conversation_context['recent_subjects']:
            recent_subject = self.conversation_context['recent_subjects'][-1]
            for qa_pair in self.qa_pairs:
                if (recent_subject.lower() in qa_pair['question'].lower() and 
                    qa_pair.get('follow_up_info')):
                    self.conversation_context['last_detailed_topic'] = qa_pair['question']
                    return qa_pair['follow_up_info']
        
        # Fallback
        return "I'd be happy to provide more details! Could you be more specific about what you'd like to learn more about? For example, you could say 'tell me more about Python' or 'tell me more about game development'."
    
    def calculate_subject_similarity(self, subject: str, qa_pair: dict) -> float:
        """Calculate how well a subject matches a QA pair"""
        subject_lower = subject.lower()
        qa_question_lower = qa_pair['question'].lower()
        qa_keywords = [kw.lower() for kw in qa_pair.get('keywords', [])]
        
        scores = []
        
        # Check direct keyword matches
        for keyword in qa_keywords:
            if keyword in subject_lower:
                scores.append(1.0)
            elif fuzz.partial_ratio(keyword, subject_lower) > 80:
                scores.append(0.8)
        
        # Check question content
        if any(keyword in subject_lower for keyword in qa_keywords):
            scores.append(0.9)
        
        # Check fuzzy matching with the question
        question_similarity = fuzz.partial_ratio(subject_lower, qa_question_lower) / 100.0
        scores.append(question_similarity * 0.7)
        
        return max(scores) if scores else 0.0
    
    # ===== ENHANCED CONTEXT SYSTEM =====
    
    def update_conversation_context(self, user_input: str, bot_response: str, matched_qa: dict = None, confidence: float = 0.0):
        """Enhanced context tracking"""
        # Add to conversation history
        self.conversation_context['conversation_history'].append({
            'user': user_input,
            'bot': bot_response,
            'timestamp': time.time(),
            'confidence': confidence,
            'matched_topic': matched_qa.get('topic') if matched_qa else None
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
        if matched_qa and confidence >= self.MATCHING_CONFIG['SIMILARITY_THRESHOLDS']['medium_confidence']:
            # Store the entire QA pair for follow-up information
            self.conversation_context['last_successful_match'] = matched_qa
            self.performance_stats['successful_matches'] += 1
            
            # Store available follow-up if exists
            if matched_qa.get('follow_up_info'):
                self.conversation_context['available_follow_ups'][matched_qa['question']] = matched_qa['follow_up_info']
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
        """Extract meaningful entities"""
        entities = []
        text_lower = text.lower()
        words = word_tokenize(text_lower)
        
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
        
        topic_patterns = {
            'greeting': {'keywords': ['hello', 'hi', 'hey', 'greetings'], 'weight': 2.0},
            'thanks': {'keywords': ['thank', 'thanks', 'appreciate', 'grateful'], 'weight': 2.0},
            'programming': {'keywords': ['python', 'programming', 'code', 'developer'], 'weight': 1.2},
            'ai': {'keywords': ['machine learning', 'artificial intelligence', 'ai', 'neural network'], 'weight': 1.2},
            'gaming': {'keywords': ['godot', 'game', 'gaming', 'engine', 'blender'], 'weight': 1.2},
            'creative': {'keywords': ['blender', '3d', 'animation', 'modeling'], 'weight': 1.2},
        }
        
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
        
        # First check for exact matches
        exact_match = self.find_exact_match(user_question_lower)
        if exact_match:
            return exact_match, 1.0, "exact"
        
        # Check for tell me more patterns first
        tell_me_response = self.handle_tell_me_more(user_question)
        if tell_me_response and "tell me more" in user_question_lower:
            # Create a temporary QA pair for the follow-up response
            temp_qa = {
                "question": user_question,
                "answers": [tell_me_response],
                "topic": "follow_up",
                "follow_up_info": tell_me_response
            }
            return temp_qa, 0.9, "follow_up"
        
        # Then proceed with normal matching
        best_match = None
        best_score = 0.0
        best_match_type = "semantic"
        
        for qa_pair in self.qa_pairs:
            base_score = self.calculate_semantic_similarity(user_question, qa_pair)
            
            if base_score > best_score and base_score >= self.MATCHING_CONFIG['SIMILARITY_THRESHOLDS']['min_acceptable']:
                best_score = base_score
                best_match = qa_pair
        
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
    
    def calculate_semantic_similarity(self, user_question: str, qa_pair: dict) -> float:
        """Calculate semantic similarity"""
        user_lower = user_question.lower()
        db_lower = qa_pair['question'].lower()
        db_keywords = qa_pair.get('keywords', [])
        
        # Multiple similarity measures
        full_similarity = fuzz.token_set_ratio(user_lower, db_lower) / 100.0
        
        # Keyword matching
        keyword_score = 0.0
        if db_keywords:
            matches = sum(1 for keyword in db_keywords if keyword in user_lower)
            keyword_score = matches / len(db_keywords)
        
        # Combined score
        combined_score = (full_similarity * 0.6 + keyword_score * 0.4)
        
        return min(combined_score, 1.0)
    
    def find_exact_match(self, user_question: str) -> Optional[dict]:
        """Find exact matches"""
        for qa_pair in self.qa_pairs:
            if qa_pair['question'].lower() == user_question:
                return qa_pair
        return None
    
    def auto_correct_input(self, user_input: str) -> Tuple[str, List[Tuple[str, int]]]:
        """Auto-correct input"""
        user_lower = user_input.lower().strip()
        
        if len(user_lower) <= 3 or any(qa['question'].lower() == user_lower for qa in self.qa_pairs):
            return user_input, []
        
        existing_questions = [pair['question'] for pair in self.qa_pairs]
        matches = process.extract(user_input, existing_questions, 
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
                qa_pair, confidence, match_type = match_result
                answer = self.get_random_answer(qa_pair['answers'])
                
                # Add follow-up suggestion for relevant matches
                if (qa_pair.get('follow_up_info') and 
                    match_type in ['exact', 'high_confidence'] and
                    random.random() < 0.4):
                    answer += " Would you like to know more about this?"
                
                responses.append((question, answer, confidence, corrections, qa_pair['question'], match_type))
                self.update_conversation_context(question, answer, qa_pair, confidence)
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
            topic_guidance = {
                'programming': "I can help with programming topics like Python!",
                'ai': "I know about AI, machine learning, and related technologies!",
                'gaming': "I can tell you about game development and engines like Godot!",
            }
            if current_topic in topic_guidance:
                base_responses.append(topic_guidance[current_topic])
        
        return random.choice(base_responses)
    
    def get_random_answer(self, answers: List[str]) -> str:
        return random.choice(answers) if answers else "I don't have an answer for that."
    
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
        
        print(f"\n📊 Performance Statistics:")
        print(f"   Total questions: {total}")
        print(f"   Success rate: {success_rate:.1%}")
        print(f"   Follow-up requests: {self.performance_stats['follow_up_requests']}")
        print(f"   Failed matches: {self.performance_stats['failed_matches']}")
    
    # ===== CHAT INTERFACE =====
    
    def chat(self):
        print("🤖 Enhanced Chatbot with Follow-up Support")
        print("Type 'quit' to exit, 'stats' for statistics, 'context' for current context")
        print("Type 'reset' to clear conversation context")
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
                
                elif user_input.lower() == 'reset':
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
                    }
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
        """Simplified response display without streaming"""
        for i, (original_question, answer, confidence, corrections, matched_question, match_type) in enumerate(responses, 1):
            print(f"\n--- Question {i} ---")
            print(f"📝 You asked: '{original_question}'")
            
            if corrections:
                best_correction, best_score = corrections[0]
                print(f"🔧 Auto-corrected to: '{best_correction}' (confidence: {best_score}%)")
            
            if answer:
                print(f"🤖 {answer}")
                
                if matched_question and confidence > 0 and match_type != "follow_up":
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
                    print(f"💡 {display_type}: '{matched_question}' (confidence: {confidence:.2f})")
                
                context_summary = self.get_context_summary()
                if context_summary:
                    print(f"🧠 {context_summary}")
            else:
                print("🤖 I don't know how to answer that yet.")

# Test the enhanced follow-up system
def test_follow_up_system():
    print("🧪 Testing Enhanced Follow-up System")
    print("=" * 60)
    
    chatbot = AdvancedChatbot()
    
    # Test scenarios for follow-up functionality
    test_cases = [
        "what is python",
        "tell me more",  # Should use context from previous question
        "tell me more about machine learning",  # Specific subject
        "what is godot",
        "tell me more about blender",  # Different specific subject
        "tell me more about Wildstar Studios",  # Another specific subject
    ]
    
    for test in test_cases:
        print(f"\nYou: {test}")
        responses = chatbot.process_multiple_questions(test)
        for response in responses:
            if response[1]:
                print(f"Bot: {response[1]}")
                if response[5] == "follow_up":
                    print("💡 📚 Follow-up information provided")
                else:
                    print(f"Match: {response[5]} (confidence: {response[2]:.2f})")
        print(f"Context: {chatbot.get_context_summary()}")
        time.sleep(0.5)
    
    print(f"\n✅ Test completed!")
    chatbot.show_statistics()

if __name__ == "__main__":
    test_follow_up_system()
    print("\n" + "=" * 60)
    print("Starting enhanced chatbot session with follow-up support...")
    print("=" * 60)
    
    chatbot = AdvancedChatbot()
    chatbot.chat()
