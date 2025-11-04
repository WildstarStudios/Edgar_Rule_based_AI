import json
import re
import string
import os
import random
import time
import threading
from typing import List, Dict, Tuple, Optional
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
            'last_detailed_topic': None,
            'available_follow_ups': {},
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
        
        self.load_data()
    
    def load_data(self):
        """Load QA pairs from JSON database file"""
        try:
            if os.path.exists(self.database_file):
                with open(self.database_file, 'r', encoding='utf-8') as f:
                    self.qa_pairs = json.load(f)
                print(f"📚 Loaded {len(self.qa_pairs)} question-answer pairs from {self.database_file}")
            else:
                print(f"⚠️ Database file {self.database_file} not found. Starting with empty database.")
                self.qa_pairs = []
        except Exception as e:
            print(f"❌ Error loading database: {e}")
            self.qa_pairs = []
    
    def save_data(self):
        """Save QA pairs to JSON database file"""
        try:
            with open(self.database_file, 'w', encoding='utf-8') as f:
                json.dump(self.qa_pairs, f, indent=2, ensure_ascii=False)
            print(f"💾 Saved {len(self.qa_pairs)} QA pairs to {self.database_file}")
        except Exception as e:
            print(f"❌ Error saving database: {e}")
    
    def add_qa_pair(self, qa_pair: dict):
        """Add a new QA pair to the database"""
        self.qa_pairs.append(qa_pair)
        self.save_data()
    
    def remove_qa_pair(self, question: str):
        """Remove a QA pair by question"""
        self.qa_pairs = [pair for pair in self.qa_pairs if pair['question'].lower() != question.lower()]
        self.save_data()

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
    
    # ===== IMPROVED MATCHING SYSTEM WITH MULTIPLE QUESTIONS SUPPORT =====
    
    def find_best_match(self, user_question: str) -> Optional[Tuple[dict, float, str]]:
        """Find best match with improved logic - supports multiple questions per answer set"""
        user_question_lower = user_question.lower().strip()
        
        # First check for exact matches in all question variations
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
            # Calculate similarity with all question variations
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
        """Calculate semantic similarity with multiple question support"""
        user_lower = user_question.lower()
        
        # Get all question variations for this QA pair
        questions = qa_pair.get('questions', [qa_pair['question']])
        db_keywords = qa_pair.get('keywords', [])
        
        best_similarity = 0.0
        
        for question in questions:
            db_lower = question.lower()
            
            # Multiple similarity measures for each question variation
            full_similarity = fuzz.token_set_ratio(user_lower, db_lower) / 100.0
            
            # Keyword matching
            keyword_score = 0.0
            if db_keywords:
                matches = sum(1 for keyword in db_keywords if keyword in user_lower)
                keyword_score = matches / len(db_keywords)
            
            # Combined score for this question variation
            combined_score = (full_similarity * 0.6 + keyword_score * 0.4)
            
            # Keep the best score across all question variations
            if combined_score > best_similarity:
                best_similarity = combined_score
        
        return min(best_similarity, 1.0)
    
    def find_exact_match(self, user_question: str) -> Optional[dict]:
        """Find exact matches in all question variations"""
        for qa_pair in self.qa_pairs:
            # Check all question variations for exact match
            questions = qa_pair.get('questions', [qa_pair['question']])
            for question in questions:
                if question.lower() == user_question:
                    return qa_pair
        return None
    
    def auto_correct_input(self, user_input: str) -> Tuple[str, List[Tuple[str, int]]]:
        """Auto-correct input with multiple question support"""
        user_lower = user_input.lower().strip()
        
        if len(user_lower) <= 3:
            return user_input, []
        
        # Check if input matches any question variation exactly
        for qa_pair in self.qa_pairs:
            questions = qa_pair.get('questions', [qa_pair['question']])
            for question in questions:
                if question.lower() == user_lower:
                    return user_input, []
        
        # Get all question variations for matching
        all_questions = []
        for pair in self.qa_pairs:
            questions = pair.get('questions', [pair['question']])
            all_questions.extend(questions)
        
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
        """Get a random answer from the available answers"""
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
