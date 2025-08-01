# test_auth.py
from auth import signup, login

email = input("Enter email: ")
password = input("Enter password: ")

choice = input("Signup or Login? (s/l): ").lower()

if choice == "s":
    signup(email, password)
elif choice == "l":
    login(email)
else:
    print("Invalid choice.")
