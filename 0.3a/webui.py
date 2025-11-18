from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3
import os
import hashlib
import secrets
from datetime import datetime, timedelta
import re
import json
from core.layer import create_streaming_layer

app = Flask(__name__, 
            static_folder='webui/static',
            template_folder='webui')
app.secret_key = 'your-secret-key-here-change-in-production'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

# Color scheme matching your Tkinter app
COLORS = {
    'bg_primary': '#0f0f23',
    'bg_secondary': '#1a1a2e', 
    'bg_tertiary': '#252547',
    'accent_primary': '#6c63ff',
    'accent_secondary': '#00d4ff',
    'accent_success': '#00ff88',
    'accent_warning': '#ffaa00',
    'accent_error': '#ff4d7d',
    'text_primary': '#ffffff',
    'text_secondary': '#b0b0d0',
    'text_tertiary': '#8080a0',
    'border': '#404080',
    'input_bg': '#2d2d5a',
    'input_bg_disabled': '#1a1a3a',
    'hover_primary': '#5750d3',
    'hover_secondary': '#35356a'
}

# Initialize streaming layer
streaming_layer = None

def init_db():
    """Initialize the SQLite database"""
    conn = sqlite3.connect('edgarai_users.db')
    c = conn.cursor()
    
    # Users table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            first_name TEXT,
            last_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            is_active BOOLEAN DEFAULT 1,
            subscription_type TEXT DEFAULT 'free'
        )
    ''')
    
    # Sessions table for remember me functionality
    c.execute('''
        CREATE TABLE IF NOT EXISTS user_sessions (
            session_id TEXT PRIMARY KEY,
            user_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Insert demo user if not exists
    demo_password = hash_password('demo123')
    c.execute('''
        INSERT OR IGNORE INTO users (username, email, password_hash, first_name, last_name) 
        VALUES (?, ?, ?, ?, ?)
    ''', ('demo', 'demo@edgarai.org', demo_password, 'Edgar', 'AI User'))
    
    conn.commit()
    conn.close()

def init_streaming_layer():
    """Initialize the streaming layer for the web interface"""
    global streaming_layer
    try:
        streaming_layer = create_streaming_layer(
            config_file="config.cfg",
            streaming_callback=None,  # We'll handle streaming differently for web
            thinking_callback=None,
            response_complete_callback=None,
            status_update_callback=None,
            error_callback=None
        )
        print("✅ Streaming layer initialized for web interface")
    except Exception as e:
        print(f"❌ Error initializing streaming layer: {e}")

def hash_password(password):
    """Hash a password for storing"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(stored_hash, provided_password):
    """Verify a stored password against one provided by user"""
    return stored_hash == hash_password(provided_password)

def is_valid_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def is_valid_username(username):
    """Validate username format"""
    pattern = r'^[a-zA-Z0-9_]{3,20}$'
    return re.match(pattern, username) is not None

def create_remember_me_token(user_id):
    """Create a remember me token"""
    token = secrets.token_urlsafe(32)
    expires = datetime.now() + timedelta(days=30)
    
    conn = sqlite3.connect('edgarai_users.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO user_sessions (session_id, user_id, expires_at)
        VALUES (?, ?, ?)
    ''', (token, user_id, expires))
    conn.commit()
    conn.close()
    
    return token

def validate_remember_me_token(token):
    """Validate remember me token and return user_id if valid"""
    conn = sqlite3.connect('edgarai_users.db')
    c = conn.cursor()
    
    c.execute('''
        SELECT user_id FROM user_sessions 
        WHERE session_id = ? AND expires_at > ?
    ''', (token, datetime.now()))
    
    result = c.fetchone()
    conn.close()
    
    return result[0] if result else None

def delete_remember_me_token(token):
    """Delete a remember me token"""
    conn = sqlite3.connect('edgarai_users.db')
    c = conn.cursor()
    c.execute('DELETE FROM user_sessions WHERE session_id = ?', (token,))
    conn.commit()
    conn.close()

@app.route('/')
def index():
    """Main login page"""
    # Check if user is already logged in
    if 'user_id' in session:
        return redirect(url_for('chat'))
    
    # Check for remember me token
    remember_token = request.cookies.get('remember_token')
    if remember_token:
        user_id = validate_remember_me_token(remember_token)
        if user_id:
            session['user_id'] = user_id
            update_last_login(user_id)
            return redirect(url_for('chat'))
    
    return render_template('login/login.html', colors=COLORS, error=None)

@app.route('/login', methods=['POST'])
def login():
    """Handle login form submission"""
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    remember_me = request.form.get('remember_me') == 'on'
    
    # Input validation
    if not username or not password:
        return render_template('login/login.html', colors=COLORS, 
                                   error="Please fill in all fields")
    
    # Authenticate user
    user = authenticate_user(username, password)
    
    if user:
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['first_name'] = user['first_name']
        
        update_last_login(user['id'])
        
        response = redirect(url_for('chat'))
        
        # Set remember me cookie if requested
        if remember_me:
            token = create_remember_me_token(user['id'])
            response.set_cookie('remember_token', token, max_age=30*24*60*60)  # 30 days
        
        return response
    else:
        return render_template('login/login.html', colors=COLORS, 
                                   error="Invalid username or password")

@app.route('/register', methods=['POST'])
def register():
    """Handle user registration"""
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    confirm_password = request.form.get('confirm_password', '')
    
    # Input validation
    if not all([username, password, confirm_password]):
        return render_template('login/login.html', colors=COLORS, 
                                   error="Please fill in all required fields")
    
    if password != confirm_password:
        return render_template('login/login.html', colors=COLORS, 
                                   error="Passwords do not match")
    
    if len(password) < 6:
        return render_template('login/login.html', colors=COLORS, 
                                   error="Password must be at least 6 characters")
    
    if not is_valid_username(username):
        return render_template('login/login.html', colors=COLORS, 
                                   error="Username must be 3-20 characters (letters, numbers, _)")
    
    # Check if username already exists
    if user_exists(username, username):
        return render_template('login/login.html', colors=COLORS, 
                                   error="Username already exists")
    
    # Create new user with placeholder email
    email = f"{username}@edgarai.org"
    if create_user(username, email, password, "", ""):
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('index'))
    else:
        return render_template('login/login.html', colors=COLORS, 
                                   error="Registration failed. Please try again.")

@app.route('/chat')
def chat():
    """Chat interface (replaces dashboard)"""
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    user_info = get_user_info(session['user_id'])
    
    # Get streaming layer status
    chat_status = {}
    if streaming_layer:
        try:
            config = streaming_layer.get_configuration()
            chat_status = {
                'current_model': config['current_model'],
                'qa_groups_count': config['qa_groups_count'],
                'active_modules_count': config['active_modules_count'],
                'available_modules': config['available_modules'][:5]  # First 5 modules
            }
        except Exception as e:
            print(f"Error getting chat status: {e}")
            chat_status = {'current_model': 'Unknown', 'qa_groups_count': 0}
    
    return render_template('chat/chat.html', colors=COLORS, user=user_info, chat_status=chat_status)

@app.route('/logout')
def logout():
    """Log out user"""
    # Delete remember me token if exists
    remember_token = request.cookies.get('remember_token')
    if remember_token:
        delete_remember_me_token(remember_token)
    
    session.clear()
    response = redirect(url_for('index'))
    response.set_cookie('remember_token', '', expires=0)
    return response

# API Routes for Chat Functionality
@app.route('/api/chat', methods=['POST'])
def api_chat():
    """API endpoint for chat messages that uses the streaming layer"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'})
    
    data = request.get_json()
    user_message = data.get('message', '').strip()
    
    if not user_message:
        return jsonify({'success': False, 'error': 'Empty message'})
    
    try:
        if not streaming_layer:
            return jsonify({
                'success': True,
                'response': "I'm currently initializing. Please try again in a moment.",
                'context': 'System Initializing',
                'module_info': None
            })
        
        # Process the message through the streaming layer
        responses = streaming_layer.process_message(user_message)
        
        # Get context summary
        context = streaming_layer.get_context_summary()
        
        # Handle responses
        if responses:
            # Use the first response
            response_data = responses[0]
            
            # Handle different response formats
            if len(response_data) == 6:
                # AI Engine format: (original_question, answer, confidence, corrections, matched_group, match_type)
                original_question, answer, confidence, corrections, matched_group, match_type = response_data
                response_text = answer
                
                # Create module info
                if matched_group:
                    module_info = f"AI Engine: {matched_group} ({match_type}, confidence: {confidence:.2f})"
                else:
                    module_info = f"AI Engine ({match_type}, confidence: {confidence:.2f})"
                    
            elif len(response_data) == 3:
                # Module routing format: (answer, confidence, source)
                answer, confidence, source = response_data
                response_text = answer
                module_info = source
                
            else:
                # Unknown format
                response_text = str(response_data[0]) if response_data else "I received your message."
                module_info = "Unknown response format"
                
        else:
            # No responses - use fallback
            response_text = "I'm not sure how to respond to that. Could you try rephrasing your question?"
            module_info = "No matching response found"
        
        return jsonify({
            'success': True,
            'response': response_text,
            'context': context,
            'module_info': module_info
        })
        
    except Exception as e:
        print(f"Error processing chat message: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'response': "I'm experiencing technical difficulties. Please try again later."
        })

@app.route('/api/reset_chat', methods=['POST'])
def api_reset_chat():
    """API endpoint to reset the chat conversation"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'})
    
    try:
        if streaming_layer:
            streaming_layer.reset_conversation()
            return jsonify({'success': True, 'message': 'Chat conversation reset'})
        else:
            return jsonify({'success': False, 'error': 'Streaming layer not initialized'})
    except Exception as e:
        print(f"Error resetting chat: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'})

@app.route('/api/chat_status')
def api_chat_status():
    """API endpoint to get chat status and statistics"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'})
    
    try:
        if streaming_layer:
            config = streaming_layer.get_configuration()
            stats = streaming_layer.get_statistics()
            
            return jsonify({
                'success': True,
                'current_model': config['current_model'],
                'qa_groups_count': config['qa_groups_count'],
                'active_modules': streaming_layer.get_active_modules(),
                'available_modules': config['available_modules'],
                'statistics': stats,
                'configuration': {
                    'streaming_speed': config['streaming_speed'],
                    'letter_streaming': config['letter_streaming'],
                    'confidence_requirement': config['confidence_requirement'],
                    'routing_threshold': config['routing_threshold']
                }
            })
        else:
            return jsonify({
                'success': True,
                'current_model': 'Unknown',
                'active_modules': [],
                'statistics': {},
                'configuration': {}
            })
    except Exception as e:
        print(f"Error getting chat status: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'})

@app.route('/api/change_model', methods=['POST'])
def api_change_model():
    """API endpoint to change the current model"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'})
    
    data = request.get_json()
    model_name = data.get('model_name', '').strip()
    
    if not model_name:
        return jsonify({'success': False, 'error': 'No model name provided'})
    
    try:
        if streaming_layer:
            success = streaming_layer.change_model(model_name)
            if success:
                return jsonify({
                    'success': True,
                    'message': f'Model changed to {model_name}',
                    'current_model': model_name
                })
            else:
                return jsonify({'success': False, 'error': 'Failed to change model'})
        else:
            return jsonify({'success': False, 'error': 'Streaming layer not initialized'})
    except Exception as e:
        print(f"Error changing model: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'})

@app.route('/api/refresh_models', methods=['POST'])
def api_refresh_models():
    """API endpoint to refresh available models"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'})
    
    try:
        if streaming_layer:
            available_models = streaming_layer.refresh_models()
            return jsonify({
                'success': True,
                'available_models': available_models,
                'message': f'Found {len(available_models)} models'
            })
        else:
            return jsonify({'success': False, 'error': 'Streaming layer not initialized'})
    except Exception as e:
        print(f"Error refreshing models: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'})

# Utility routes
@app.route('/api/check_username')
def check_username():
    """API endpoint to check if username is available"""
    username = request.args.get('username', '').strip()
    if not username:
        return jsonify({'available': False})
    
    conn = sqlite3.connect('edgarai_users.db')
    c = conn.cursor()
    c.execute('SELECT id FROM users WHERE username = ?', (username,))
    result = c.fetchone()
    conn.close()
    
    return jsonify({'available': result is None})

@app.route('/api/check_password_strength')
def check_password_strength():
    """API endpoint to check password strength"""
    password = request.args.get('password', '')
    if not password:
        return jsonify({'score': 0, 'feedback': ''})
    
    score = 0
    feedback = []
    
    # Length check
    if len(password) >= 8:
        score += 1
    else:
        feedback.append("Use at least 8 characters")
    
    # Complexity checks
    if re.search(r'[A-Z]', password):
        score += 1
    else:
        feedback.append("Include uppercase letters")
    
    if re.search(r'[a-z]', password):
        score += 1
    else:
        feedback.append("Include lowercase letters")
    
    if re.search(r'[0-9]', password):
        score += 1
    else:
        feedback.append("Include numbers")
    
    if re.search(r'[^A-Za-z0-9]', password):
        score += 1
    else:
        feedback.append("Include special characters")
    
    return jsonify({
        'score': score,
        'feedback': feedback[:2] if feedback else ["Strong password!"]
    })

# Database helper functions
def authenticate_user(username, password):
    """Authenticate user credentials"""
    conn = sqlite3.connect('edgarai_users.db')
    c = conn.cursor()
    
    c.execute('''
        SELECT id, username, password_hash, first_name, last_name 
        FROM users 
        WHERE (username = ? OR email = ?) AND is_active = 1
    ''', (username, username))
    
    user = c.fetchone()
    conn.close()
    
    if user and verify_password(user[2], password):
        return {
            'id': user[0],
            'username': user[1],
            'first_name': user[3],
            'last_name': user[4]
        }
    return None

def user_exists(username, email):
    """Check if username or email already exists"""
    conn = sqlite3.connect('edgarai_users.db')
    c = conn.cursor()
    c.execute('SELECT id FROM users WHERE username = ? OR email = ?', (username, email))
    result = c.fetchone()
    conn.close()
    return result is not None

def create_user(username, email, password, first_name, last_name):
    """Create a new user"""
    try:
        password_hash = hash_password(password)
        conn = sqlite3.connect('edgarai_users.db')
        c = conn.cursor()
        c.execute('''
            INSERT INTO users (username, email, password_hash, first_name, last_name)
            VALUES (?, ?, ?, ?, ?)
        ''', (username, email, password_hash, first_name, last_name))
        conn.commit()
        conn.close()
        return True
    except:
        return False

def update_last_login(user_id):
    """Update user's last login timestamp"""
    conn = sqlite3.connect('edgarai_users.db')
    c = conn.cursor()
    c.execute('UPDATE users SET last_login = ? WHERE id = ?', (datetime.now(), user_id))
    conn.commit()
    conn.close()

def get_user_info(user_id):
    """Get user information"""
    conn = sqlite3.connect('edgarai_users.db')
    c = conn.cursor()
    c.execute('''
        SELECT username, email, first_name, last_name, created_at, last_login, subscription_type
        FROM users WHERE id = ?
    ''', (user_id,))
    user = c.fetchone()
    conn.close()
    
    return {
        'username': user[0],
        'email': user[1],
        'first_name': user[2],
        'last_name': user[3],
        'created_at': user[4],
        'last_login': user[5],
        'subscription_type': user[6]
    }

if __name__ == '__main__':
    # Initialize database and streaming layer
    init_db()
    init_streaming_layer()
    
    # Create directories if they don't exist
    os.makedirs('webui/static/images', exist_ok=True)
    os.makedirs('webui/login', exist_ok=True)
    os.makedirs('webui/chat', exist_ok=True)
    
    # Run Flask app
    app.run(host='0.0.0.0', port=5000, debug=False)