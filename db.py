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

def save_password(user_id: str, platform: str, username: str, password: str, master_password: str, vault_id: str = None, url: str = "", notes: str = ""):
    """Encrypt and save a password entry for a user in a specific vault."""
    try:
        encrypted_pw = encrypt(password, master_password)
        
        # If no vault_id provided, use default vault
        if not vault_id:
            vault_id = get_or_create_default_vault(user_id)
            
        doc_ref = db.collection("users").document(user_id).collection("vaults").document(vault_id).collection("passwords").document(platform)
        
        # Check if password already exists to preserve created_at
        existing_doc = doc_ref.get()
        existing_created_at = None
        if existing_doc.exists:
            existing_data = existing_doc.to_dict()
            existing_created_at = existing_data.get('created_at')
        
        doc_ref.set({
            "platform": platform,
            "username": username,
            "password": encrypted_pw,
            "url": url,
            "notes": notes,
            "updated_at": datetime.utcnow(),
            "created_at": existing_created_at or datetime.utcnow()
        })
        
        # Update vault's last updated time
        vault_ref = db.collection("users").document(user_id).collection("vaults").document(vault_id)
        vault_ref.update({"updated_at": datetime.utcnow()})
        
        print(f"[✓] Password saved for {platform} in vault {vault_id}")
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

def fetch_passwords_for_gui(user_id: str, master_password: str, vault_id: str = None):
    """Retrieve and decrypt all passwords for a user from a specific vault - GUI version that returns data instead of printing."""
    try:
        # If no vault_id provided, use default vault
        if not vault_id:
            vault_id = get_or_create_default_vault(user_id)
        
        # Use the proper vault structure
        return get_vault_passwords(user_id, vault_id, master_password)
        
    except Exception as e:
        print(f"[!] Failed to fetch passwords: {e}")
        raise e

def delete_password(user_id: str, platform: str, vault_id: str = None):
    """Delete a specific password entry for a platform in a vault."""
    try:
        # If no vault_id provided, try both old and new structure
        if not vault_id:
            # Try old structure first (backwards compatibility)
            old_doc_ref = db.collection("users").document(user_id).collection("passwords").document(platform)
            if old_doc_ref.get().exists:
                old_doc_ref.delete()
                print(f"[✓] Deleted password for {platform} (old structure)")
                return
            
            # Try default vault
            vault_id = get_or_create_default_vault(user_id)
            
        doc_ref = db.collection("users").document(user_id).collection("vaults").document(vault_id).collection("passwords").document(platform)
        doc_ref.delete()
        
        # Update vault's last updated time
        vault_ref = db.collection("users").document(user_id).collection("vaults").document(vault_id)
        vault_ref.update({"updated_at": datetime.utcnow()})
        
        print(f"[✓] Deleted password for {platform} from vault {vault_id}")
    except Exception as e:
        print(f"[!] Failed to delete password: {e}")
        raise e

# ===== VAULT MANAGEMENT FUNCTIONS =====

def get_or_create_default_vault(user_id: str):
    """Get or create a default vault for a user."""
    try:
        vault_id = "default"
        vault_ref = db.collection("users").document(user_id).collection("vaults").document(vault_id)
        vault_doc = vault_ref.get()
        
        if not vault_doc.exists:
            # Create default vault
            vault_ref.set({
                "id": vault_id,
                "name": "My Vault",
                "description": "Default password vault",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            })
            print(f"[✓] Created default vault for user {user_id}")
            
        return vault_id
    except Exception as e:
        print(f"[!] Failed to get/create default vault: {e}")
        raise e

def create_vault(user_id: str, name: str, description: str = ""):
    """Create a new vault for a user."""
    try:
        # Generate vault ID
        import secrets
        vault_id = secrets.token_urlsafe(16)
        
        # Check if vault name already exists
        existing_vaults = get_vaults(user_id)
        if any(v["name"].lower() == name.lower() for v in existing_vaults):
            raise ValueError("A vault with this name already exists")
        
        vault_ref = db.collection("users").document(user_id).collection("vaults").document(vault_id)
        vault_ref.set({
            "id": vault_id,
            "name": name,
            "description": description,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })
        
        print(f"[✓] Created vault '{name}' with ID {vault_id}")
        return vault_id
    except Exception as e:
        print(f"[!] Failed to create vault: {e}")
        raise e

def get_vaults(user_id: str):
    """Get all vaults for a user."""
    try:
        vaults_ref = db.collection("users").document(user_id).collection("vaults")
        vault_docs = vaults_ref.stream()
        
        vaults = []
        for doc in vault_docs:
            vault_data = doc.to_dict()
            vault_data["id"] = doc.id
            
            # Count passwords in this vault
            passwords_ref = db.collection("users").document(user_id).collection("vaults").document(doc.id).collection("passwords")
            password_count = len(list(passwords_ref.stream()))
            vault_data["password_count"] = password_count
            
            vaults.append(vault_data)
        
        # Sort by created date
        vaults.sort(key=lambda x: x.get("created_at", datetime.min), reverse=False)
        return vaults
    except Exception as e:
        print(f"[!] Failed to get vaults: {e}")
        raise e

def delete_vault(user_id: str, vault_id: str):
    """Delete a vault and all its passwords."""
    try:
        # Don't allow deleting default vault
        if vault_id == "default":
            raise ValueError("Cannot delete default vault")
            
        # Delete all passwords in the vault
        passwords_ref = db.collection("users").document(user_id).collection("vaults").document(vault_id).collection("passwords")
        password_docs = passwords_ref.stream()
        for password_doc in password_docs:
            password_doc.reference.delete()
        
        # Delete the vault
        vault_ref = db.collection("users").document(user_id).collection("vaults").document(vault_id)
        vault_ref.delete()
        
        print(f"[✓] Deleted vault {vault_id} and all its passwords")
    except Exception as e:
        print(f"[!] Failed to delete vault: {e}")
        raise e

def get_vault_passwords(user_id: str, vault_id: str, master_password: str):
    """Get all passwords from a specific vault."""
    try:
        passwords_ref = db.collection("users").document(user_id).collection("vaults").document(vault_id).collection("passwords")
        password_docs = passwords_ref.stream()
        
        passwords = []
        for doc in password_docs:
            data = doc.to_dict()
            try:
                decrypted_pw = decrypt(data["password"], master_password)
                password_entry = {
                    "id": doc.id,
                    "platform": data['platform'],
                    "username": data['username'],
                    "password": decrypted_pw,
                    "url": data.get('url', ''),
                    "notes": data.get('notes', ''),
                    "created_at": data.get('created_at'),
                    "updated_at": data.get('updated_at'),
                    "error": None
                }
                passwords.append(password_entry)
            except Exception as decrypt_error:
                password_entry = {
                    "id": doc.id,
                    "platform": data['platform'],
                    "username": data.get('username', 'N/A'),
                    "password": None,
                    "url": data.get('url', ''),
                    "notes": data.get('notes', ''),
                    "created_at": data.get('created_at'),
                    "updated_at": data.get('updated_at'),
                    "error": "Incorrect master password"
                }
                passwords.append(password_entry)
        
        return passwords
    except Exception as e:
        print(f"[!] Failed to get vault passwords: {e}")
        raise e

def migrate_existing_passwords(user_id: str):
    """Migrate existing passwords from old structure to default vault."""
    try:
        # Check if user has passwords in old structure
        old_passwords_ref = db.collection("users").document(user_id).collection("passwords")
        old_password_docs = list(old_passwords_ref.stream())
        
        if not old_password_docs:
            print(f"[i] No old passwords to migrate for user {user_id}")
            return
            
        # Get or create default vault
        default_vault_id = get_or_create_default_vault(user_id)
        
        # Move passwords to default vault
        migrated_count = 0
        for doc in old_password_docs:
            password_data = doc.to_dict()
            
            # Add missing fields for new structure
            password_data.update({
                "url": password_data.get("url", ""),
                "notes": password_data.get("notes", ""),
                "created_at": password_data.get("created_at", datetime.utcnow())
            })
            
            # Create in new structure
            new_doc_ref = db.collection("users").document(user_id).collection("vaults").document(default_vault_id).collection("passwords").document(doc.id)
            new_doc_ref.set(password_data)
            
            # Delete from old structure
            doc.reference.delete()
            migrated_count += 1
        
        print(f"[✓] Migrated {migrated_count} passwords to default vault for user {user_id}")
        return migrated_count
    except Exception as e:
        print(f"[!] Failed to migrate passwords: {e}")
        raise e
