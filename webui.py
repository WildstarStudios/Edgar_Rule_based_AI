from flask import Flask, render_template, request, jsonify, session, Response
from ai_engine import AdvancedChatbot
import os
import json
import time
import threading
from datetime import datetime
import queue

app = Flask(__name__)
app.secret_key = 'edgar_ai_secret_key_2024'
app.config['SESSION_TYPE'] = 'filesystem'

# Global chatbot instance
chatbot = None
# Streaming queues for each session
stream_queues = {}

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
            # streaming_speed and other settings will be loaded from config.cfg automatically
        )
        return True
    except Exception as e:
        print(f"Error initializing chatbot: {e}")
        return False

@app.route('/')
def index():
    """Main chat interface"""
    # Generate a unique session ID for streaming
    session_id = str(time.time())
    session['stream_id'] = session_id
    stream_queues[session_id] = queue.Queue()
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
        
        # Get session ID for streaming
        session_id = session.get('stream_id')
        if not session_id:
            session_id = str(time.time())
            session['stream_id'] = session_id
            stream_queues[session_id] = queue.Queue()
        
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
                                callback=lambda text: stream_queues[session_id].put({
                                    'type': 'content',
                                    'text': text
                                })
                            )
                        else:
                            # Send complete response if streaming is disabled
                            stream_queues[session_id].put({
                                'type': 'content',
                                'text': answer
                            })
                        
                        # Send match information
                        group_name = 'Unknown'
                        if matched_group and isinstance(matched_group, dict):
                            group_name = matched_group.get('group_name', 'Unknown')
                        elif matched_group and isinstance(matched_group, str):
                            group_name = matched_group
                        
                        stream_queues[session_id].put({
                            'type': 'metadata',
                            'confidence': confidence,
                            'match_type': match_type,
                            'matched_group': group_name,
                            'corrections': corrections
                        })
                        
            except Exception as e:
                stream_queues[session_id].put({
                    'type': 'error',
                    'text': f'Error: {str(e)}'
                })
            finally:
                stream_queues[session_id].put({'type': 'end'})
        
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
    if not session_id or session_id not in stream_queues:
        return Response("No stream available", status=400)
    
    def generate():
        q = stream_queues[session_id]
        try:
            while True:
                message = q.get(timeout=30)  # 30 second timeout
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
            # Uses settings from config.cfg automatically
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

@app.route('/health')
def health_check():
    """Health check endpoint"""
    status = {
        'status': 'healthy' if chatbot else 'unhealthy',
        'chatbot_initialized': chatbot is not None,
        'current_model': chatbot.current_model if chatbot else None,
        'streaming_enabled': chatbot.streaming_speed > 0 if chatbot else False,
        'timestamp': datetime.now().isoformat()
    }
    return jsonify(status)

def create_html_template():
    """Create the HTML template with improved text box sizing"""
    html_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Edgar AI Assistant</title>
    <style>
        :root {
            --bg-primary: #0f0f23;
            --bg-secondary: #1a1a2e;
            --bg-tertiary: #252547;
            --accent-primary: #6c63ff;
            --accent-secondary: #00d4ff;
            --accent-success: #00ff88;
            --accent-warning: #ffaa00;
            --accent-error: #ff4d7d;
            --text-primary: #ffffff;
            --text-secondary: #b0b0d0;
            --text-tertiary: #8080a0;
            --border: #404080;
            --input-bg: #2d2d5a;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            height: 100vh;
            overflow: hidden;
        }
        
        .container {
            display: flex;
            height: 100vh;
        }
        
        /* Sidebar */
        .sidebar {
            width: 280px;
            background: var(--bg-secondary);
            padding: 20px;
            display: flex;
            flex-direction: column;
            border-right: 1px solid var(--border);
        }
        
        .logo {
            text-align: center;
            margin-bottom: 30px;
        }
        
        .logo h1 {
            font-size: 24px;
            margin-bottom: 5px;
            color: var(--accent-primary);
        }
        
        .logo p {
            color: var(--text-secondary);
            font-size: 14px;
        }
        
        .controls {
            flex: 1;
        }
        
        .control-btn {
            width: 100%;
            padding: 12px 15px;
            margin-bottom: 10px;
            background: var(--bg-tertiary);
            color: var(--text-primary);
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            text-align: left;
            transition: all 0.3s ease;
        }
        
        .control-btn:hover {
            background: var(--accent-primary);
            transform: translateX(5px);
        }
        
        .status {
            margin-top: auto;
            padding: 15px;
            background: var(--bg-tertiary);
            border-radius: 8px;
            font-size: 12px;
        }
        
        .status h3 {
            color: var(--text-secondary);
            margin-bottom: 5px;
        }
        
        /* Main Content */
        .main-content {
            flex: 1;
            display: flex;
            flex-direction: column;
            padding: 20px;
        }
        
        .chat-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 1px solid var(--border);
        }
        
        .model-info {
            display: flex;
            align-items: center;
            gap: 15px;
        }
        
        .model-select {
            background: var(--input-bg);
            color: var(--text-primary);
            border: 1px solid var(--border);
            border-radius: 6px;
            padding: 8px 12px;
            font-size: 14px;
        }
        
        .streaming-indicator {
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 12px;
            color: var(--accent-success);
        }
        
        .streaming-dot {
            width: 8px;
            height: 8px;
            background: var(--accent-success);
            border-radius: 50%;
            animation: pulse 1.5s infinite;
        }
        
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
        
        /* Chat Display */
        .chat-display {
            flex: 1;
            background: var(--bg-primary);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 20px;
            overflow-y: auto;
            margin-bottom: 20px;
            display: flex;
            flex-direction: column;
        }
        
        .message {
            margin-bottom: 15px;
            padding: 12px 16px;
            border-radius: 12px;
            max-width: 85%;
            word-wrap: break-word;
            position: relative;
        }
        
        .user-message {
            background: var(--accent-primary);
            margin-left: auto;
            text-align: right;
            align-self: flex-end;
        }
        
        .bot-message {
            background: var(--bg-tertiary);
            margin-right: auto;
            align-self: flex-start;
        }
        
        .message-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 6px;
            font-size: 11px;
            color: var(--text-secondary);
        }
        
        .message-content {
            line-height: 1.4;
            font-size: 14px;
            min-height: 20px;
        }
        
        .message-meta {
            font-size: 10px;
            color: var(--text-tertiary);
            margin-top: 6px;
            line-height: 1.2;
        }
        
        .system-message {
            text-align: center;
            color: var(--text-secondary);
            font-style: italic;
            margin: 10px 0;
            align-self: center;
            background: var(--bg-secondary);
            padding: 10px 15px;
            border-radius: 8px;
            max-width: 80%;
        }
        
        .error-message {
            background: var(--accent-error);
            color: white;
            padding: 10px 15px;
            border-radius: 6px;
            margin: 10px 0;
            align-self: center;
            max-width: 80%;
        }
        
        .typing-indicator {
            display: inline-flex;
            align-items: center;
            gap: 4px;
            padding: 6px 10px;
            background: var(--bg-tertiary);
            border-radius: 12px;
            font-style: italic;
            color: var(--text-secondary);
            font-size: 12px;
        }
        
        .typing-dot {
            width: 4px;
            height: 4px;
            background: var(--text-secondary);
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
            30% { transform: translateY(-4px); }
        }
        
        /* Input Area */
        .input-area {
            display: flex;
            gap: 10px;
            align-items: flex-end;
        }
        
        .input-container {
            flex: 1;
            display: flex;
            flex-direction: column;
        }
        
        .user-input {
            background: var(--input-bg);
            color: var(--text-primary);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 12px 15px;
            font-size: 14px;
            resize: none;
            min-height: 50px;
            max-height: 120px;
            font-family: inherit;
            line-height: 1.4;
        }
        
        .user-input:focus {
            outline: none;
            border-color: var(--accent-primary);
        }
        
        /* Auto-resize textarea */
        .auto-resize {
            overflow: hidden;
            transition: height 0.2s;
        }
        
        .quick-actions {
            display: flex;
            gap: 8px;
            margin-top: 10px;
            flex-wrap: wrap;
        }
        
        .quick-btn {
            background: var(--bg-tertiary);
            color: var(--text-primary);
            border: none;
            border-radius: 16px;
            padding: 6px 12px;
            font-size: 11px;
            cursor: pointer;
            transition: background 0.3s ease;
        }
        
        .quick-btn:hover {
            background: var(--accent-primary);
        }
        
        .send-btn {
            background: var(--accent-primary);
            color: var(--text-primary);
            border: none;
            border-radius: 12px;
            padding: 12px 20px;
            font-size: 13px;
            font-weight: bold;
            cursor: pointer;
            transition: background 0.3s ease;
            height: 50px;
            min-width: 80px;
        }
        
        .send-btn:hover:not(:disabled) {
            background: var(--hover-primary);
        }
        
        .send-btn:disabled {
            background: var(--text-tertiary);
            cursor: not-allowed;
        }
        
        /* Scrollbar */
        ::-webkit-scrollbar {
            width: 8px;
        }
        
        ::-webkit-scrollbar-track {
            background: var(--bg-secondary);
        }
        
        ::-webkit-scrollbar-thumb {
            background: var(--accent-primary);
            border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: var(--hover-primary);
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Sidebar -->
        <div class="sidebar">
            <div class="logo">
                <h1>Edgar AI</h1>
                <p>Your Personal Assistant</p>
            </div>
            
            <div class="controls">
                <button class="control-btn" onclick="showContext()">Show Context</button>
                <button class="control-btn" onclick="showStats()">Statistics</button>
                <button class="control-btn" onclick="resetChat()">Reset Chat</button>
                <button class="control-btn" onclick="showHelp()">Help</button>
            </div>
            
            <div class="status">
                <h3>Status</h3>
                <div id="status-message">Ready to assist</div>
                <div class="streaming-indicator" id="streaming-indicator" style="display: none;">
                    <div class="streaming-dot"></div>
                    <span>Streaming</span>
                </div>
                <div id="context-info" style="margin-top: 8px; font-size: 11px; color: var(--text-tertiary);"></div>
            </div>
        </div>
        
        <!-- Main Content -->
        <div class="main-content">
            <div class="chat-header">
                <div class="model-info">
                    <h2>Chat Interface</h2>
                    <select id="model-select" class="model-select" onchange="switchModel()">
                        <option value="">Loading models...</option>
                    </select>
                </div>
                <div id="connection-status" style="color: var(--accent-success);">Connected</div>
            </div>
            
            <!-- Chat Display -->
            <div class="chat-display" id="chat-display">
                <div class="system-message">
                    Welcome to Edgar AI Assistant!<br>
                    I'm here to help with programming, AI concepts, and much more.
                </div>
            </div>
            
            <!-- Input Area -->
            <div class="input-area">
                <div class="input-container">
                    <textarea 
                        id="user-input" 
                        class="user-input auto-resize" 
                        placeholder="Type your message here... (Press Enter to send, Shift+Enter for new line)"
                        onkeydown="handleKeydown(event)"
                        oninput="autoResize(this)"
                    ></textarea>
                    
                    <div class="quick-actions">
                        <button class="quick-btn" onclick="quickAction('tell me more')">Tell me more</button>
                        <button class="quick-btn" onclick="quickAction('what is Python?')">About Python</button>
                        <button class="quick-btn" onclick="quickAction('explain AI')">Explain AI</button>
                        <button class="quick-btn" onclick="quickAction('help')">Help</button>
                    </div>
                </div>
                
                <button id="send-btn" class="send-btn" onclick="sendMessage()">
                    Send
                </button>
            </div>
        </div>
    </div>

    <script>
        let currentModel = '';
        let currentBotMessage = null;
        let eventSource = null;
        let isStreaming = false;
        
        // Initialize the interface
        document.addEventListener('DOMContentLoaded', function() {
            loadModels();
            updateContextInfo();
            
            // Update context info every 30 seconds
            setInterval(updateContextInfo, 30000);
        });
        
        // Auto-resize textarea
        function autoResize(textarea) {
            textarea.style.height = 'auto';
            textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
        }
        
        // Load available models
        async function loadModels() {
            try {
                const response = await fetch('/api/models');
                const data = await response.json();
                
                const select = document.getElementById('model-select');
                select.innerHTML = '';
                
                if (data.models && data.models.length > 0) {
                    data.models.forEach(model => {
                        const option = document.createElement('option');
                        option.value = model.name;
                        option.textContent = `${model.name} (${model.qa_groups} groups)`;
                        select.appendChild(option);
                    });
                    currentModel = data.models[0].name;
                } else {
                    const option = document.createElement('option');
                    option.value = '';
                    option.textContent = 'No models available';
                    select.appendChild(option);
                }
            } catch (error) {
                console.error('Error loading models:', error);
            }
        }
        
        // Switch model
        async function switchModel() {
            const select = document.getElementById('model-select');
            const modelName = select.value;
            
            if (!modelName) return;
            
            try {
                const response = await fetch('/api/switch_model', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ model_name: modelName })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    currentModel = modelName;
                    addSystemMessage(`Switched to model: ${modelName}`);
                    updateStatus('Model switched successfully');
                } else {
                    addSystemMessage(`Error: ${data.error}`, true);
                }
            } catch (error) {
                console.error('Error switching model:', error);
                addSystemMessage('Error switching model', true);
            }
        }
        
        // Handle keyboard input
        function handleKeydown(event) {
            if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                sendMessage();
            }
        }
        
        // Send message
        async function sendMessage() {
            const input = document.getElementById('user-input');
            const message = input.value.trim();
            
            if (!message) return;
            
            // Disable input and show loading
            input.disabled = true;
            document.getElementById('send-btn').disabled = true;
            updateStatus('Processing your message...');
            
            // Add user message to chat
            addUserMessage(message);
            input.value = '';
            input.style.height = 'auto'; // Reset height
            
            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ message: message })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    if (data.streaming) {
                        // Start streaming
                        startStreaming();
                    } else {
                        // Non-streaming fallback
                        setTimeout(() => {
                            addSystemMessage('Streaming not available, using standard response');
                            updateStatus('Ready to assist');
                            input.disabled = false;
                            document.getElementById('send-btn').disabled = false;
                            input.focus();
                        }, 1000);
                    }
                } else {
                    addSystemMessage(`Error: ${data.error}`, true);
                    updateStatus('Error occurred');
                    input.disabled = false;
                    document.getElementById('send-btn').disabled = false;
                    input.focus();
                }
            } catch (error) {
                console.error('Error sending message:', error);
                addSystemMessage('Network error: Could not send message', true);
                updateStatus('Connection error');
                input.disabled = false;
                document.getElementById('send-btn').disabled = false;
                input.focus();
            }
        }
        
        // Start streaming response
        function startStreaming() {
            isStreaming = true;
            document.getElementById('streaming-indicator').style.display = 'flex';
            
            // Create new bot message
            currentBotMessage = createBotMessage();
            
            // Start Server-Sent Events connection
            eventSource = new EventSource('/api/stream');
            
            eventSource.onmessage = function(event) {
                const data = JSON.parse(event.data);
                
                switch (data.type) {
                    case 'content':
                        // Append streaming text
                        appendToBotMessage(data.text);
                        break;
                        
                    case 'metadata':
                        // Add metadata to the message
                        addMessageMetadata(data);
                        break;
                        
                    case 'end':
                        // Streaming complete
                        endStreaming();
                        break;
                        
                    case 'error':
                        addSystemMessage(data.text, true);
                        endStreaming();
                        break;
                        
                    case 'timeout':
                        addSystemMessage('Streaming timeout', true);
                        endStreaming();
                        break;
                }
            };
            
            eventSource.onerror = function(event) {
                console.error('Stream error:', event);
                addSystemMessage('Streaming error', true);
                endStreaming();
            };
        }
        
        // End streaming
        function endStreaming() {
            isStreaming = false;
            document.getElementById('streaming-indicator').style.display = 'none';
            
            if (eventSource) {
                eventSource.close();
                eventSource = null;
            }
            
            // Re-enable input
            const input = document.getElementById('user-input');
            input.disabled = false;
            document.getElementById('send-btn').disabled = false;
            input.focus();
            
            updateStatus('Ready to assist');
            updateContextInfo();
        }
        
        // Create a new bot message for streaming
        function createBotMessage() {
            const chatDisplay = document.getElementById('chat-display');
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message bot-message';
            
            const timestamp = new Date().toLocaleTimeString();
            
            messageDiv.innerHTML = `
                <div class="message-header">
                    <strong>Edgar</strong>
                    <span>${timestamp}</span>
                </div>
                <div class="message-content">
                    <div class="typing-indicator" id="typing-indicator">
                        <div class="typing-dot"></div>
                        <div class="typing-dot"></div>
                        <div class="typing-dot"></div>
                    </div>
                    <span id="streaming-content"></span>
                </div>
                <div class="message-meta" id="message-meta"></div>
            `;
            
            chatDisplay.appendChild(messageDiv);
            chatDisplay.scrollTop = chatDisplay.scrollHeight;
            
            return messageDiv;
        }
        
        // Append text to streaming message
        function appendToBotMessage(text) {
            if (!currentBotMessage) return;
            
            const contentElement = currentBotMessage.querySelector('#streaming-content');
            const typingIndicator = currentBotMessage.querySelector('#typing-indicator');
            
            if (typingIndicator) {
                typingIndicator.style.display = 'none';
            }
            
            contentElement.textContent += text;
            
            // Auto-scroll to bottom
            const chatDisplay = document.getElementById('chat-display');
            chatDisplay.scrollTop = chatDisplay.scrollHeight;
        }
        
        // Add metadata to the current message
        function addMessageMetadata(metadata) {
            if (!currentBotMessage) return;
            
            const metaElement = currentBotMessage.querySelector('#message-meta');
            
            let metaInfo = '';
            if (metadata.confidence > 0) {
                const matchType = getMatchTypeDisplay(metadata.match_type);
                metaInfo += `<div>${matchType} (confidence: ${metadata.confidence.toFixed(2)})</div>`;
            }
            
            if (metadata.corrections && metadata.corrections.length > 0) {
                const bestCorrection = metadata.corrections[0];
                metaInfo += `<div>Auto-corrected from original (confidence: ${bestCorrection[1]}%)</div>`;
            }
            
            metaElement.innerHTML = metaInfo;
        }
        
        // Quick actions
        function quickAction(action) {
            if (action === 'help') {
                showHelp();
            } else {
                const input = document.getElementById('user-input');
                input.value = action;
                autoResize(input); // Resize for the new content
                sendMessage();
            }
        }
        
        // Add user message to chat
        function addUserMessage(message) {
            const chatDisplay = document.getElementById('chat-display');
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message user-message';
            
            const timestamp = new Date().toLocaleTimeString();
            
            messageDiv.innerHTML = `
                <div class="message-header">
                    <strong>You</strong>
                    <span>${timestamp}</span>
                </div>
                <div class="message-content">${escapeHtml(message)}</div>
            `;
            
            chatDisplay.appendChild(messageDiv);
            chatDisplay.scrollTop = chatDisplay.scrollHeight;
        }
        
        // Add system message
        function addSystemMessage(message, isError = false) {
            const chatDisplay = document.getElementById('chat-display');
            const messageDiv = document.createElement('div');
            messageDiv.className = isError ? 'error-message' : 'system-message';
            messageDiv.textContent = message;
            chatDisplay.appendChild(messageDiv);
            chatDisplay.scrollTop = chatDisplay.scrollHeight;
        }
        
        // Update status
        function updateStatus(message) {
            document.getElementById('status-message').textContent = message;
        }
        
        // Update context info
        async function updateContextInfo() {
            try {
                const response = await fetch('/api/context');
                const data = await response.json();
                
                if (data.context && data.context !== 'Minimal context') {
                    document.getElementById('context-info').textContent = data.context;
                } else {
                    document.getElementById('context-info').textContent = 'No active context';
                }
            } catch (error) {
                console.error('Error updating context:', error);
            }
        }
        
        // Show context
        async function showContext() {
            try {
                const response = await fetch('/api/context');
                const data = await response.json();
                
                let contextInfo = 'Current Context:\\n';
                contextInfo += `• ${data.context}\\n`;
                if (data.current_topic) {
                    contextInfo += `• Current topic: ${data.current_topic}\\n`;
                }
                if (data.mentioned_entities && data.mentioned_entities.length > 0) {
                    contextInfo += `• Recent entities: ${data.mentioned_entities.slice(-3).join(', ')}\\n`;
                }
                contextInfo += `• Conversation length: ${data.conversation_length} messages`;
                
                alert(contextInfo);
            } catch (error) {
                console.error('Error getting context:', error);
                alert('Error getting context information');
            }
        }
        
        // Show statistics
        async function showStats() {
            try {
                const response = await fetch('/api/stats');
                const data = await response.json();
                
                let statsInfo = 'Chatbot Statistics:\\n';
                statsInfo += `• Total questions: ${data.total_questions}\\n`;
                statsInfo += `• Success rate: ${(data.success_rate * 100).toFixed(1)}%\\n`;
                statsInfo += `• Successful matches: ${data.successful_matches}\\n`;
                statsInfo += `• Failed matches: ${data.failed_matches}\\n`;
                statsInfo += `• Follow-up requests: ${data.follow_up_requests}\\n`;
                statsInfo += `• Context assists: ${data.context_helps}\\n`;
                statsInfo += `• Streaming: ${data.streaming_speed > 0 ? 'Enabled (' + data.streaming_speed + ' WPM)' : 'Disabled'}`;
                
                alert(statsInfo);
            } catch (error) {
                console.error('Error getting stats:', error);
                alert('Error getting statistics');
            }
        }
        
        // Reset chat
        async function resetChat() {
            if (confirm('Start a new conversation? Current context will be cleared.')) {
                try {
                    const response = await fetch('/api/reset');
                    const data = await response.json();
                    
                    if (data.success) {
                        const chatDisplay = document.getElementById('chat-display');
                        chatDisplay.innerHTML = `
                            <div class="system-message">
                                New conversation started!<br>
                                How can I assist you today?
                            </div>
                        `;
                        updateStatus('New chat started');
                        updateContextInfo();
                    }
                } catch (error) {
                    console.error('Error resetting chat:', error);
                    alert('Error resetting conversation');
                }
            }
        }
        
        // Show help
        function showHelp() {
            const helpText = `Edgar AI Assistant - Help

Quick Commands:
• 'tell me more' - Get detailed information
• 'tell me more about [topic]' - Specific details
• Ask about programming, AI, game development

Features:
• Context-aware conversations
• Intelligent question matching
• Detailed follow-up information
• Real-time text streaming
• Conversation statistics
• Multiple model support

Tips:
• Use the quick action buttons for common questions
• The assistant maintains context across messages
• Press Enter to send messages quickly
• Streaming settings are configured in config.cfg`;

            alert(helpText);
        }
        
        // Utility functions
        function escapeHtml(unsafe) {
            return unsafe
                .replace(/&/g, "&amp;")
                .replace(/</g, "&lt;")
                .replace(/>/g, "&gt;")
                .replace(/"/g, "&quot;")
                .replace(/'/g, "&#039;");
        }
        
        function getMatchTypeDisplay(matchType) {
            const types = {
                'exact': 'Exact match',
                'high_confidence': 'High confidence',
                'medium_confidence': 'Medium confidence', 
                'low_confidence': 'Low confidence',
                'semantic': 'Semantic match',
                'follow_up': 'Follow-up information',
                'unknown': 'Unknown question'
            };
            return types[matchType] || matchType;
        }
    </script>
</body>
</html>'''
    
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    
    # Write the template with UTF-8 encoding
    with open('templates/index.html', 'w', encoding='utf-8') as f:
        f.write(html_content)

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
    
    # Run the Flask app
    app.run(
        host='0.0.0.0', 
        port=5000, 
        debug=False, 
        use_reloader=False  # Disable reloader as requested
    )