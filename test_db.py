from db import save_password, fetch_passwords, delete_password

# Paste the UID printed after signup/login
user_id = "A5vCV97g9KRoe2ajv3ngq6QNQBE2"   # ✅ Replace with your real Firebase UID

# Ask the user for master password used in encryption/decryption
master_password = "myMasterPassword123"  # Use the same as in test_crypto

# ---- TEST 1: Save a password ----
save_password(user_id, "instagram", "harnoor.insta", "igPass@456", master_password)

# ---- TEST 2: Fetch all passwords ----
fetch_passwords(user_id, master_password)

# ---- TEST 3: Delete a password (optional) ----
# delete_password(user_id, "instagram")
