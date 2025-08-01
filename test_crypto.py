from crypto_utils import encrypt, decrypt, generate_password

master_password = "myMasterPassword123"  # Ask user for this ideally

# Test encryption/decryption
plain = "MySecretPassword!"
encrypted = encrypt(plain, master_password)
print("Encrypted:", encrypted)

decrypted = decrypt(encrypted, master_password)
print("Decrypted:", decrypted)

# Test password generator
print("Suggested password:", generate_password(length=20))
