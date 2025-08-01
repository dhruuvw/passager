import os
import base64
import random
import string

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding, hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# === ENCRYPTION / DECRYPTION SECTION ===

def derive_key(password: str, salt: bytes) -> bytes:
    """Derive a secure AES key from master password and salt using PBKDF2."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100_000,
        backend=default_backend()
    )
    return kdf.derive(password.encode())

def encrypt(plain_text: str, password: str) -> str:
    """Encrypt text using AES-CBC with a key derived from the password."""
    salt = os.urandom(16)
    key = derive_key(password, salt)

    iv = os.urandom(16)
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()

    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(plain_text.encode()) + padder.finalize()

    encrypted = encryptor.update(padded_data) + encryptor.finalize()

    # Combine salt + iv + encrypted and base64 encode
    encrypted_blob = salt + iv + encrypted
    return base64.b64encode(encrypted_blob).decode()

def decrypt(encrypted_text: str, password: str) -> str:
    """Decrypt the AES-encrypted base64 string using the master password."""
    encrypted_data = base64.b64decode(encrypted_text)

    salt = encrypted_data[:16]
    iv = encrypted_data[16:32]
    ciphertext = encrypted_data[32:]

    key = derive_key(password, salt)

    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()

    decrypted_padded = decryptor.update(ciphertext) + decryptor.finalize()

    unpadder = padding.PKCS7(128).unpadder()
    decrypted = unpadder.update(decrypted_padded) + unpadder.finalize()

    return decrypted.decode()

# === PASSWORD GENERATOR SECTION ===

def generate_password(length=16, use_upper=True, use_digits=True, use_symbols=True) -> str:
    """Generate a secure password with selected character sets."""
    lowercase = string.ascii_lowercase
    uppercase = string.ascii_uppercase if use_upper else ''
    digits = string.digits if use_digits else ''
    symbols = string.punctuation if use_symbols else ''

    all_chars = lowercase + uppercase + digits + symbols
    if not all_chars:
        raise ValueError("At least one character type must be selected.")

    # Ensure at least one of each type
    password = []
    if use_upper:
        password.append(random.choice(uppercase))
    if use_digits:
        password.append(random.choice(digits))
    if use_symbols:
        password.append(random.choice(symbols))
    password.append(random.choice(lowercase))  # always at least one lowercase

    remaining = length - len(password)
    password += random.choices(all_chars, k=remaining)
    random.shuffle(password)

    return ''.join(password)
def generate_key():
    """Generate a secure AES key and save it to a file."""
    key = os.urandom(32)
    with open("key.key", "wb") as f:
        f.write(key)
    print("[🔑] Encryption key generated and saved!")

def load_key():
    """Load the AES key from the key file."""
    try:
        with open("key.key", "rb") as f:
            return f.read()
    except FileNotFoundError:
        print("[❌] Key file not found! Run generate_key() first.")
        return None
