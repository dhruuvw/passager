from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
from datetime import datetime, timedelta
import logging
import os
from functools import wraps
import secrets

# Import our modules
import auth
from db import save_password, fetch_passwords_for_gui, delete_password
from crypto_utils import generate_password

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', secrets.token_hex(32))
CORS(app)

# Rate limiter setup
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["100 per minute"],
    storage_uri="memory://"
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('auth.log'),
        logging.StreamHandler()
    ]
)

# Track login attempts
login_attempts = {}

def log_failed_attempt(email, ip):
    logging.warning(f"FAILED LOGIN | Email: {email} | IP: {ip}")

def log_security_event(event_type, email, ip, details=""):
    logging.info(f"SECURITY EVENT | Type: {event_type} | Email: {email} | IP: {ip} | Details: {details}")

def is_locked_out(email):
    entry = login_attempts.get(email)
    if entry and 'locked_until' in entry:
        if datetime.now() < entry['locked_until']:
            return True, entry['locked_until']
        else:
            del login_attempts[email]
    return False, None

def require_login(f):
    """Decorator to require login for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def validate_request_data(required_fields):
    """Decorator to validate required fields in request JSON"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            data = request.get_json()
            if not data:
                return jsonify({"status": "error", "message": "No JSON data provided"}), 400
            
            missing_fields = [field for field in required_fields if not data.get(field)]
            if missing_fields:
                return jsonify({
                    "status": "error", 
                    "message": f"Missing required fields: {', '.join(missing_fields)}"
                }), 400
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({"status": "error", "message": "Rate limit exceeded. Please try again later."}), 429

# ========== WEB ROUTES ==========

@app.route('/')
def index():
    """Landing page"""
    return render_template('landing.html')

@app.route('/login')
def login():
    """Login page"""
    return render_template('login.html')

@app.route('/signup')
def signup():
    """Signup page"""
    return render_template('signup.html')

@app.route('/vault')
@require_login
def vault():
    """Main vault page"""
    return render_template('vault.html', user_id=session['user_id'][:8] + '...')

@app.route('/logout')
def logout():
    """Logout and clear session"""
    session.clear()
    flash('You have been logged out successfully', 'info')
    return redirect(url_for('login'))

# ========== API ROUTES ==========

@app.route('/api/signup', methods=['POST'])
@limiter.limit("3 per minute")
@validate_request_data(['email', 'password'])
def signup_api():
    data = request.get_json()
    email = data.get("email").strip().lower()
    password = data.get("password")
    client_ip = request.remote_addr

    try:
        uid = auth.signup(email, password)
        if uid:
            log_security_event("SIGNUP_SUCCESS", email, client_ip, f"UID: {uid}")
            return jsonify({"status": "success", "uid": uid, "message": "Account created! Please verify your email."}), 201
        else:
            log_security_event("SIGNUP_FAILED", email, client_ip, "Invalid credentials or user exists")
            return jsonify({"status": "error", "message": "Signup failed. Check password requirements."}), 400
    except Exception as e:
        logging.error(f"Signup error for {email}: {str(e)}")
        return jsonify({"status": "error", "message": "Internal server error"}), 500

@app.route('/api/login', methods=['POST'])
@limiter.limit("5 per minute")
@validate_request_data(['email', 'password'])
def login_api():
    data = request.get_json()
    client_ip = request.remote_addr
    email = data.get("email").strip().lower()
    password = data.get("password")

    # Lockout check
    locked, until = is_locked_out(email)
    if locked:
        log_security_event("LOGIN_BLOCKED", email, client_ip, f"Account locked until {until}")
        return jsonify({
            "status": "locked", 
            "message": f"Account locked. Try again after {until.strftime('%H:%M:%S')}"
        }), 423

    try:
        uid = auth.login_with_rest_api(email, password)

        if uid:
            # Clear failed attempts on successful login
            login_attempts.pop(email, None)
            log_security_event("LOGIN_SUCCESS", email, client_ip, f"UID: {uid}")
            
            # Set session
            session['user_id'] = uid
            session['email'] = email
            
            return jsonify({"status": "success", "uid": uid}), 200
        else:
            # Handle failed login
            log_failed_attempt(email, client_ip)
            entry = login_attempts.get(email, {"count": 0})
            entry["count"] += 1
            entry["last"] = datetime.now()
            
            if entry["count"] >= 5:
                entry["locked_until"] = datetime.now() + timedelta(minutes=5)
                log_security_event("ACCOUNT_LOCKED", email, client_ip, f"Locked until: {entry['locked_until']}")
            
            login_attempts[email] = entry
            return jsonify({"status": "error", "message": "Invalid email or password"}), 401
            
    except Exception as e:
        logging.error(f"Login error for {email}: {str(e)}")
        return jsonify({"status": "error", "message": "Internal server error"}), 500

@app.route('/api/resend_verification', methods=['POST'])
@limiter.limit("2 per minute")
@validate_request_data(['email'])
def resend_verification_api():
    data = request.get_json()
    email = data.get("email").strip().lower()
    client_ip = request.remote_addr

    try:
        success = auth.resend_verification_email(email)
        if success:
            log_security_event("VERIFICATION_RESENT", email, client_ip)
            return jsonify({"status": "success", "message": "Verification email sent successfully!"}), 200
        else:
            return jsonify({"status": "error", "message": "Failed to send verification email"}), 400
    except Exception as e:
        logging.error(f"Resend verification error for {email}: {str(e)}")
        return jsonify({"status": "error", "message": "Internal server error"}), 500

@app.route('/api/save_password', methods=['POST'])
@limiter.limit("10 per minute")
@validate_request_data(['platform', 'username', 'password', 'master_password'])
def save_password_api():
    if 'user_id' not in session:
        return jsonify({"status": "error", "message": "Not authenticated"}), 401
        
    data = request.get_json()
    user_id = session['user_id']
    platform = data.get("platform").strip().lower()
    username = data.get("username").strip()
    password = data.get("password")
    master_password = data.get("master_password")
    client_ip = request.remote_addr

    try:
        save_password(user_id, platform, username, password, master_password)
        log_security_event("PASSWORD_SAVED", f"user_id:{user_id}", client_ip, f"Platform: {platform}")
        return jsonify({"status": "success", "message": f"Password saved for {platform}"}), 200
    except Exception as e:
        logging.error(f"Save password error for user {user_id}: {str(e)}")
        return jsonify({"status": "error", "message": "Failed to save password"}), 500

@app.route('/api/fetch_passwords', methods=['POST'])
@limiter.limit("10 per minute")
@validate_request_data(['master_password'])
def fetch_passwords_api():
    if 'user_id' not in session:
        return jsonify({"status": "error", "message": "Not authenticated"}), 401
        
    data = request.get_json()
    user_id = session['user_id']
    master_password = data.get("master_password")
    client_ip = request.remote_addr

    try:
        passwords = fetch_passwords_for_gui(user_id, master_password)
        log_security_event("PASSWORDS_FETCHED", f"user_id:{user_id}", client_ip, f"Count: {len(passwords)}")
        return jsonify({"status": "success", "passwords": passwords}), 200
    except Exception as e:
        logging.error(f"Fetch passwords error for user {user_id}: {str(e)}")
        return jsonify({"status": "error", "message": "Failed to fetch passwords"}), 500

@app.route('/api/delete_password', methods=['DELETE'])
@limiter.limit("10 per minute")
@validate_request_data(['platform'])
def delete_password_api():
    if 'user_id' not in session:
        return jsonify({"status": "error", "message": "Not authenticated"}), 401
        
    data = request.get_json()
    user_id = session['user_id']
    platform = data.get("platform").strip().lower()
    client_ip = request.remote_addr

    try:
        delete_password(user_id, platform)
        log_security_event("PASSWORD_DELETED", f"user_id:{user_id}", client_ip, f"Platform: {platform}")
        return jsonify({"status": "success", "message": f"Password deleted for {platform}"}), 200
    except Exception as e:
        logging.error(f"Delete password error for user {user_id}: {str(e)}")
        return jsonify({"status": "error", "message": "Failed to delete password"}), 500

@app.route('/api/generate_password', methods=['POST'])
@limiter.limit("20 per minute")
def generate_password_api():
    data = request.get_json() or {}
    length = data.get("length", 16)
    use_upper = data.get("use_upper", True)
    use_digits = data.get("use_digits", True)
    use_symbols = data.get("use_symbols", True)
    client_ip = request.remote_addr

    try:
        # Validate length
        if not isinstance(length, int) or length < 4 or length > 128:
            return jsonify({"status": "error", "message": "Length must be between 4 and 128"}), 400
        
        generated_password = generate_password(length, use_upper, use_digits, use_symbols)
        log_security_event("PASSWORD_GENERATED", "anonymous", client_ip, f"Length: {length}")
        return jsonify({"status": "success", "password": generated_password}), 200
    except Exception as e:
        logging.error(f"Generate password error: {str(e)}")
        return jsonify({"status": "error", "message": "Failed to generate password"}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0"
    }), 200

@app.route('/api/ping', methods=['GET'])
def ping():
    return jsonify({"status": "pong", "timestamp": datetime.now().isoformat()}), 200

if __name__ == '__main__':
    # Security headers
    @app.after_request
    def after_request(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        return response
    
    # Run with debug=False for production
    app.run(host='0.0.0.0', port=5051, debug=True)
