from flask import Flask, render_template, request, jsonify, session, Response
from ai_engine import AdvancedChatbot
import os
import json
import time
import threading
from datetime import datetime
import queue
import uuid

app = Flask(__name__)
app.secret_key = 'edgar_ai_secret_key_2024'
app.config['SESSION_TYPE'] = 'filesystem'

# Global chatbot instance
chatbot = None
# Streaming queues for each session with cleanup mechanism
stream_queues = {}
# Session timeout (30 minutes)
SESSION_TIMEOUT = 1800

def initialize_chatbot():
    """Initialize the chatbot with the first available model"""
    global chatbot
    try:
        models_folder = "models"
        if not os.path.exists(models_folder):
            os.makedirs(models_folder)
            return False
            
        available_models = []
        if os.path.exists(models_folder):
            for file in os.listdir(models_folder):
                if file.endswith('.json'):
                    model_name = file[:-5]
                    available_models.append(model_name)
        
        if not available_models:
            return False
            
        # Use the first available model with settings from config.cfg
        chatbot = AdvancedChatbot(
            model_name=available_models[0],
            auto_start_chat=False
        )
        return True
    except Exception as e:
        print(f"Error initializing chatbot: {e}")
        return False

def cleanup_old_sessions():
    """Clean up old sessions that have timed out"""
    current_time = time.time()
    sessions_to_remove = []
    
    for session_id, queue_data in stream_queues.items():
        if 'last_activity' in queue_data:
            if current_time - queue_data['last_activity'] > SESSION_TIMEOUT:
                sessions_to_remove.append(session_id)
    
    for session_id in sessions_to_remove:
        if session_id in stream_queues:
            del stream_queues[session_id]

def get_or_create_session():
    """Get current session ID or create a new one"""
    if 'stream_id' not in session:
        session['stream_id'] = str(uuid.uuid4())
    
    session_id = session['stream_id']
    
    # Clean up old sessions periodically
    if len(stream_queues) > 10:  # Only clean up if we have many sessions
        cleanup_old_sessions()
    
    # Create queue if it doesn't exist
    if session_id not in stream_queues:
        stream_queues[session_id] = {
            'queue': queue.Queue(),
            'last_activity': time.time()
        }
    else:
        # Update activity timestamp
        stream_queues[session_id]['last_activity'] = time.time()
    
    return session_id

def get_session_queue(session_id):
    """Get queue for session ID, handling missing sessions gracefully"""
    if session_id in stream_queues:
        stream_queues[session_id]['last_activity'] = time.time()
        return stream_queues[session_id]['queue']
    return None

@app.route('/')
def index():
    """Main chat interface"""
    # Always create a new session for the index route
    session.clear()
    session_id = get_or_create_session()
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat messages with streaming support"""
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({'error': 'Empty message'}), 400
        
        if not chatbot:
            return jsonify({'error': 'Chatbot not initialized'}), 500
        
        # Get or create session ID for streaming
        session_id = get_or_create_session()
        session_queue = get_session_queue(session_id)
        
        if not session_queue:
            return jsonify({'error': 'Session expired, please refresh the page'}), 400
        
        # Process the message in a separate thread for streaming
        def process_message():
            try:
                responses = chatbot.process_multiple_questions(user_message)
                
                for response in responses:
                    if len(response) >= 6:
                        original_question, answer, confidence, corrections, matched_group, match_type = response
                        
                        # Stream the response if streaming is enabled in config
                        if answer and chatbot.streaming_speed > 0:
                            # Use the chatbot's streaming functionality
                            chatbot.stream_text(
                                answer,
                                "",
                                chatbot.streaming_speed,
                                callback=lambda text: session_queue.put({
                                    'type': 'content',
                                    'text': text
                                })
                            )
                        else:
                            # Send complete response if streaming is disabled
                            session_queue.put({
                                'type': 'content',
                                'text': answer
                            })
                        
                        # Send match information
                        group_name = 'Unknown'
                        if matched_group and isinstance(matched_group, dict):
                            group_name = matched_group.get('group_name', 'Unknown')
                        elif matched_group and isinstance(matched_group, str):
                            group_name = matched_group
                        
                        session_queue.put({
                            'type': 'metadata',
                            'confidence': confidence,
                            'match_type': match_type,
                            'matched_group': group_name,
                            'corrections': corrections
                        })
                        
            except Exception as e:
                session_queue.put({
                    'type': 'error',
                    'text': f'Error: {str(e)}'
                })
            finally:
                session_queue.put({'type': 'end'})
        
        # Start processing in background thread
        threading.Thread(target=process_message, daemon=True).start()
        
        return jsonify({
            'success': True,
            'message': 'Processing started',
            'streaming': chatbot.streaming_speed > 0
        })
        
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/stream')
def stream():
    """Server-Sent Events endpoint for streaming responses"""
    session_id = session.get('stream_id')
    if not session_id:
        return Response("No session available", status=400)
    
    session_queue = get_session_queue(session_id)
    if not session_queue:
        return Response("Session expired or invalid", status=400)
    
    def generate():
        try:
            while True:
                message = session_queue.get(timeout=30)  # 30 second timeout
                if message['type'] == 'end':
                    yield f"data: {json.dumps({'type': 'end'})}\n\n"
                    break
                elif message['type'] == 'error':
                    yield f"data: {json.dumps({'type': 'error', 'text': message['text']})}\n\n"
                    break
                else:
                    yield f"data: {json.dumps(message)}\n\n"
        except queue.Empty:
            yield f"data: {json.dumps({'type': 'timeout'})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'text': str(e)})}\n\n"
    
    return Response(generate(), mimetype='text/event-stream')

@app.route('/api/context')
def get_context():
    """Get current conversation context"""
    if not chatbot:
        return jsonify({'error': 'Chatbot not initialized'}), 500
    
    try:
        context_summary = chatbot.get_context_summary()
        return jsonify({
            'context': context_summary,
            'current_topic': chatbot.conversation_context.get('current_topic'),
            'mentioned_entities': list(chatbot.conversation_context.get('mentioned_entities', [])),
            'conversation_length': len(chatbot.conversation_context.get('conversation_history', []))
        })
    except Exception as e:
        print(f"Error getting context: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats')
def get_stats():
    """Get chatbot statistics"""
    if not chatbot:
        return jsonify({'error': 'Chatbot not initialized'}), 500
    
    try:
        stats = chatbot.performance_stats
        total = stats['total_questions']
        success_rate = stats['successful_matches'] / total if total > 0 else 0
        
        return jsonify({
            'total_questions': total,
            'success_rate': success_rate,
            'successful_matches': stats['successful_matches'],
            'failed_matches': stats['failed_matches'],
            'follow_up_requests': stats['follow_up_requests'],
            'groups_tested': stats['groups_tested'],
            'context_helps': stats['context_helps'],
            'streaming_speed': chatbot.streaming_speed,
            'letter_streaming': chatbot.letter_streaming
        })
    except Exception as e:
        print(f"Error getting stats: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/models')
def get_models():
    """Get available models"""
    try:
        models_folder = "models"
        available_models = []
        
        if os.path.exists(models_folder):
            for file in os.listdir(models_folder):
                if file.endswith('.json'):
                    model_name = file[:-5]
                    model_path = os.path.join(models_folder, file)
                    
                    # Load model info
                    try:
                        with open(model_path, 'r') as f:
                            model_data = json.load(f)
                        
                        model_info = {
                            'name': model_name,
                            'description': model_data.get('description', 'No description'),
                            'author': model_data.get('author', 'Unknown'),
                            'version': model_data.get('version', '1.0.0'),
                            'qa_groups': len(model_data.get('qa_groups', [])),
                            'created_at': model_data.get('created_at', 'Unknown')
                        }
                        available_models.append(model_info)
                    except Exception as e:
                        print(f"Error loading model {model_name}: {e}")
        
        return jsonify({'models': available_models})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/switch_model', methods=['POST'])
def switch_model():
    """Switch to a different model"""
    try:
        data = request.get_json()
        model_name = data.get('model_name')
        
        if not model_name:
            return jsonify({'error': 'No model name provided'}), 400
        
        global chatbot
        chatbot = AdvancedChatbot(
            model_name=model_name,
            auto_start_chat=False
        )
        
        return jsonify({
            'success': True,
            'message': f'Switched to model: {model_name}'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/reset')
def reset_conversation():
    """Reset the conversation context"""
    if not chatbot:
        return jsonify({'error': 'Chatbot not initialized'}), 500
    
    try:
        # Reset conversation context but preserve testing state
        chatbot.conversation_context.update({
            'current_topic': None,
            'previous_topics': chatbot.conversation_context['previous_topics'],
            'mentioned_entities': chatbot.conversation_context['mentioned_entities'],
            'user_preferences': {},
            'conversation_history': chatbot.conversation_context['conversation_history'],
            'current_goal': None,
            'last_successful_match': None,
            'conversation_mood': 'neutral',
            'topic_consistency_score': 1.0,
            'recent_subjects': chatbot.conversation_context['recent_subjects'],
            'last_detailed_topic': None,
            'available_follow_ups': {},
        })
        
        return jsonify({'success': True, 'message': 'Conversation reset'})
    except Exception as e:
        print(f"Error resetting conversation: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/refresh_session')
def refresh_session():
    """Refresh the session - useful after server reboot"""
    session.clear()
    session_id = get_or_create_session()
    return jsonify({
        'success': True,
        'message': 'Session refreshed',
        'session_id': session_id
    })

@app.route('/health')
def health_check():
    """Health check endpoint"""
    status = {
        'status': 'healthy' if chatbot else 'unhealthy',
        'chatbot_initialized': chatbot is not None,
        'current_model': chatbot.current_model if chatbot else None,
        'streaming_enabled': chatbot.streaming_speed > 0 if chatbot else False,
        'active_sessions': len(stream_queues),
        'timestamp': datetime.now().isoformat()
    }
    return jsonify(status)

if __name__ == '__main__':
    # Initialize chatbot
    print("🤖 Initializing Edgar AI Chatbot...")
    if initialize_chatbot():
        print(f"✅ Chatbot initialized with model: {chatbot.current_model}")
        print(f"✅ Loaded {len(chatbot.qa_groups)} QA groups")
        print(f"✅ Streaming: {'Enabled (' + str(chatbot.streaming_speed) + ' WPM)' if chatbot.streaming_speed > 0 else 'Disabled'}")
        print(f"✅ Settings loaded from config.cfg")
    else:
        print("❌ No models found. Please create models using the training GUI first.")
        print("💡 Models should be placed in the 'models' folder as JSON files")
    
    # Create the HTML template
    create_html_template()
    
    print("🚀 Starting Edgar AI Web Server...")
    print("📧 Access the chat interface at: http://localhost:5000")
    print("⚡ Running with use_reloader=False")
    print("🔄 Session management: Enabled (auto-cleanup)")
    
    # Run the Flask app
    app.run(
        host='0.0.0.0', 
        port=5000, 
        debug=False, 
        use_reloader=False
    )