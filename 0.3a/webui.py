from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3
import os
import hashlib
import secrets
from datetime import datetime, timedelta
import re

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
    return render_template('chat/chat.html', colors=COLORS, user=user_info)

@app.route('/logout')
def logout():
    """Log out user"""
    # Delete remember me token if exists
    remember_token = request.cookies.get('remember_token')
    if remember_token:
        delete_remember_remember_token(remember_token)
    
    session.clear()
    response = redirect(url_for('index'))
    response.set_cookie('remember_token', '', expires=0)
    return response

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
    # Initialize database
    init_db()
    
    # Create directories if they don't exist
    os.makedirs('webui/static/images', exist_ok=True)
    os.makedirs('webui/login', exist_ok=True)
    os.makedirs('webui/chat', exist_ok=True)
    
    # Run Flask app
    app.run(host='0.0.0.0', port=5000, debug=False)