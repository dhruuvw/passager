# db.py
import firebase_admin
from firebase_admin import credentials, firestore
from crypto_utils import encrypt, decrypt
from datetime import datetime

# Initialize Firestore
if not firebase_admin._apps:
    cred = credentials.Certificate("firebase_config.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()

def save_password(user_id: str, platform: str, username: str, password: str, master_password: str):
    """Encrypt and save a password entry for a user."""
    try:
        encrypted_pw = encrypt(password, master_password)
        doc_ref = db.collection("users").document(user_id).collection("passwords").document(platform)
        doc_ref.set({
            "platform": platform,
            "username": username,
            "password": encrypted_pw,
            "updated_at": datetime.utcnow()
        }, merge=True)
        print(f"[✓] Password saved for {platform}")
    except Exception as e:
        print(f"[!] Failed to save password: {e}")
        raise e

def fetch_passwords(user_id: str, master_password: str):
    """Retrieve and decrypt all passwords for a user."""
    try:
        docs = db.collection("users").document(user_id).collection("passwords").stream()
        print("\n[🔐] Saved Passwords:")
        
        passwords = []
        for doc in docs:
            data = doc.to_dict()
            try:
                decrypted_pw = decrypt(data["password"], master_password)
                password_entry = {
                    "platform": data['platform'],
                    "username": data['username'],
                    "password": decrypted_pw,
                    "error": None
                }
                passwords.append(password_entry)
                print(f"- Platform: {data['platform']}")
                print(f"  Username: {data['username']}")
                print(f"  Password: {decrypted_pw}")
            except Exception as decrypt_error:
                password_entry = {
                    "platform": data['platform'],
                    "username": data.get('username', 'N/A'),
                    "password": None,
                    "error": "Incorrect master password"
                }
                passwords.append(password_entry)
                print(f"- Platform: {data['platform']} (⚠️ Incorrect master password)")
        
        return passwords
        
    except Exception as e:
        print(f"[!] Failed to fetch passwords: {e}")
        raise e

def fetch_passwords_for_gui(user_id: str, master_password: str):
    """Retrieve and decrypt all passwords for a user - GUI version that returns data instead of printing."""
    try:
        docs = db.collection("users").document(user_id).collection("passwords").stream()
        
        passwords = []
        for doc in docs:
            data = doc.to_dict()
            try:
                decrypted_pw = decrypt(data["password"], master_password)
                password_entry = {
                    "platform": data['platform'],
                    "username": data['username'],
                    "password": decrypted_pw,
                    "error": None
                }
                passwords.append(password_entry)
            except Exception as decrypt_error:
                password_entry = {
                    "platform": data['platform'],
                    "username": data.get('username', 'N/A'),
                    "password": None,
                    "error": "Incorrect master password"
                }
                passwords.append(password_entry)
        
        return passwords
        
    except Exception as e:
        print(f"[!] Failed to fetch passwords: {e}")
        raise e

def delete_password(user_id: str, platform: str):
    """Delete a specific password entry for a platform."""
    try:
        doc_ref = db.collection("users").document(user_id).collection("passwords").document(platform)
        doc_ref.delete()
        print(f"[✓] Deleted password for {platform}")
    except Exception as e:
        print(f"[!] Failed to delete password: {e}")
        raise e