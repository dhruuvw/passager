import firebase_admin
from firebase_admin import auth, credentials
import smtplib
from email.message import EmailMessage
import time
import requests
from dotenv import load_dotenv
import os
import re  # for password strength check

load_dotenv()

# Initialize Firebase Admin SDK
if not firebase_admin._apps:
    cred = credentials.Certificate("firebase_config.json")
    firebase_admin.initialize_app(cred)

# Email sender details
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
APP_PASSWORD = os.getenv("APP_PASSWORD")
FIREBASE_API_KEY = os.getenv("FIREBASE_API_KEY")


def is_strong_password(password):
    """
    Enforce strong password:
    - Minimum 8 characters
    - At least 1 uppercase, 1 lowercase, 1 digit, 1 special character
    """
    return (
        len(password) >= 8 and
        re.search(r"[A-Z]", password) and
        re.search(r"[a-z]", password) and
        re.search(r"[0-9]", password) and
        re.search(r"[\W_]", password)  # special characters
    )


def send_email_verification(email, link):
    msg = EmailMessage()
    msg['Subject'] = 'Verify Your Email for Password Manager'
    msg['From'] = SENDER_EMAIL
    msg['To'] = email
    msg.set_content(f"Click the link below to verify your email:\n\n{link}")

    print(f"[i] Attempting to send verification email to {email}...")
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(SENDER_EMAIL, APP_PASSWORD)
            smtp.send_message(msg)
        print(f"[✓] Verification email sent to {email}")
    except smtplib.SMTPAuthenticationError:
        print("[!] SMTP Authentication failed: Check app password or email settings.")
    except Exception as e:
        print(f"[!] Failed to send email: {e}")


def signup(email, password):
    if not is_strong_password(password):
        print("[!] Weak password. Use at least 8 characters with uppercase, lowercase, number, and special character.")
        return None

    try:
        user = auth.create_user(email=email, password=password)
        print(f"[✓] User created: {user.uid}")

        # Send verification email
        try:
            link = auth.generate_email_verification_link(email)
            send_email_verification(email, link)
            print("[i] Please check your inbox and click the verification link.")
        except Exception as e:
            print(f"[!] Failed to send verification email: {e}")

        return user.uid

    except auth.EmailAlreadyExistsError:
        print("[!] An account already exists with this email.")
        try:
            user = auth.get_user_by_email(email)
            print(f"[i] Using existing account: {user.uid}")
            return user.uid
        except:
            return None
    except Exception as e:
        print(f"[!] Signup failed: {e}")
        return None


def login(email, password):
    try:
        user = auth.get_user_by_email(email)
        if not user.email_verified:
            print("[!] Login failed: Email not verified. Please verify your email first.")
            return None
        print(f"[✓] Login successful: {user.uid}")
        return user.uid
    except auth.UserNotFoundError:
        print("[!] Login failed: User not found")
        return None
    except Exception as e:
        print(f"[!] Login failed: {e}")
        return None


def login_with_rest_api(email, password):
    if not FIREBASE_API_KEY:
        print("[!] Firebase API key not found in environment variables")
        return login(email, password)

    FIREBASE_REST_URL = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}"
    payload = {
        "email": email,
        "password": password,
        "returnSecureToken": True
    }

    try:
        response = requests.post(FIREBASE_REST_URL, json=payload, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if not data.get('emailVerified', False):
                print("[!] REST API login failed: Email not verified")
                return {'error': 'unverified'}
            print(f"[✓] Logged in as UID: {data['localId']}")
            return data['localId']
        else:
            print("[!] REST API login failed, trying fallback method...")
            return login(email, password)
    except Exception as e:
        print(f"[!] REST API login failed: {e}")
        print("[i] Trying fallback login method...")
        return login(email, password)


def resend_verification_email(email):
    try:
        user = auth.get_user_by_email(email)
        if user.email_verified:
            print("[i] Email is already verified!")
            return True
        link = auth.generate_email_verification_link(email)
        send_email_verification(email, link)
        print("[✓] Verification email resent successfully!")
        return True
    except auth.UserNotFoundError:
        print("[!] User not found")
        return False
    except Exception as e:
        print(f"[!] Failed to resend verification email: {e}")
        return False
