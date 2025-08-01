# cli.py
from auth import signup, login
from db import save_password, fetch_passwords, delete_password
from crypto_utils import generate_password

def main():
    print("🟢 Welcome to CLI Password Manager")

    email = input("Enter your email: ")
    password = input("Enter your login password: ")

    action = input("Signup or Login? (s/l): ").lower()
    if action == 's':
        user_id = signup(email, password)
    else:
        user_id = login(email)

    if not user_id:
        print("[!] Exiting due to login/signup failure.")
        return

    master_password = input("Enter your master password (used for encryption): ")

    while True:
        print("\n🔘 Choose an option:")
        print("1. Add new password")
        print("2. View all saved passwords")
        print("3. Delete a password")
        print("4. Generate strong password")
        print("5. Exit")

        choice = input("Enter choice: ")

        if choice == "1":
            platform = input("Platform (e.g., facebook): ").lower()
            username = input("Username: ")
            pw = input("Password (or leave blank to auto-generate): ")

            if not pw:
                pw = generate_password(length=16)
                print(f"[Suggested Password]: {pw}")

            save_password(user_id, platform, username, pw, master_password)

        elif choice == "2":
            fetch_passwords(user_id, master_password)

        elif choice == "3":
            platform = input("Enter platform name to delete: ").lower()
            delete_password(user_id, platform)

        elif choice == "4":
            pw = generate_password(length=20)
            print(f"[Suggested Password]: {pw}")

        elif choice == "5":
            print("👋 Exiting. Stay secure!")
            break

        else:
            print("[!] Invalid choice. Try again.")

if __name__ == "__main__":
    main()
