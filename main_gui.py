import sys
import requests
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLineEdit,
    QPushButton, QMessageBox, QLabel
)
from vault_window import VaultWindow


class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Password Manager - Login / Signup")
        self.setGeometry(600, 300, 400, 350)

        layout = QVBoxLayout()

        # Title
        title_label = QLabel("🔐 Password Manager")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        layout.addWidget(title_label)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Enter email")
        layout.addWidget(self.email_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter login password")
        self.password_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password_input)

        # Password strength label
        self.password_strength_label = QLabel("")
        self.password_strength_label.setStyleSheet("font-weight: bold; margin-left: 5px;")
        layout.addWidget(self.password_strength_label)

        # Connect password input change to strength checker
        self.password_input.textChanged.connect(self.check_password_strength)

        self.master_password_input = QLineEdit()
        self.master_password_input.setPlaceholderText("Enter master password (for encryption)")
        self.master_password_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.master_password_input)

        self.login_btn = QPushButton("Login")
        self.login_btn.clicked.connect(self.login_user)
        layout.addWidget(self.login_btn)

        self.signup_btn = QPushButton("Signup")
        self.signup_btn.clicked.connect(self.signup_user)
        layout.addWidget(self.signup_btn)

        self.resend_verification_btn = QPushButton("Resend Verification Email")
        self.resend_verification_btn.clicked.connect(self.resend_verification)
        layout.addWidget(self.resend_verification_btn)

        self.setLayout(layout)

    def check_password_strength(self):
        password = self.password_input.text()

        length = len(password)
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(not c.isalnum() for c in password)

        score = 0
        if length >= 8:
            score += 1
        if has_upper:
            score += 1
        if has_lower:
            score += 1
        if has_digit:
            score += 1
        if has_special:
            score += 1

        if score <= 2:
            strength = "Weak"
            color = "red"
        elif score == 3 or score == 4:
            strength = "Medium"
            color = "orange"
        else:
            strength = "Strong"
            color = "green"

        self.password_strength_label.setText(f"Password Strength: {strength}")
        self.password_strength_label.setStyleSheet(f"color: {color}; font-weight: bold; margin-left: 5px;")

    def login_user(self):
        email = self.email_input.text().strip()
        password = self.password_input.text().strip()
        master_password = self.master_password_input.text().strip()

        if not email or not password or not master_password:
            QMessageBox.warning(self, "Input Error", "Please enter email, password, and master password.")
            return

        try:
            response = requests.post(
                "http://localhost:5000/login",
                json={"email": email, "password": password},
                timeout=5
            )
            data = response.json()

            if response.status_code == 200:
                QMessageBox.information(self, "Success", "Login successful!")
                self.hide()
                self.vault_window = VaultWindow(data["uid"], master_password)
                self.vault_window.show()

            elif response.status_code == 403:
                QMessageBox.critical(self, "Account Locked", data["message"])

            else:
                QMessageBox.warning(self, "Login Failed", data.get("message", "Login failed."))

        except Exception as e:
            QMessageBox.critical(self, "Server Error", f"Could not connect to server:\n{str(e)}")

    def signup_user(self):
        email = self.email_input.text().strip()
        password = self.password_input.text().strip()
        master_password = self.master_password_input.text().strip()

        if not email or not password or not master_password:
            QMessageBox.warning(self, "Input Error", "Please enter email, password, and master password.")
            return

        try:
            response = requests.post(
                "http://localhost:5000/signup",
                json={"email": email, "password": password},
                timeout=5
            )
            data = response.json()

            if response.status_code == 200:
                QMessageBox.information(
                    self,
                    "Signup Successful",
                    "Account created!\n📧 Check your inbox for a verification email."
                )
                self.email_input.clear()
                self.password_input.clear()
                self.master_password_input.clear()
                self.password_strength_label.clear()
            else:
                QMessageBox.warning(self, "Signup Failed", data.get("message", "Signup failed."))

        except Exception as e:
            QMessageBox.critical(self, "Server Error", f"Could not connect to server:\n{str(e)}")

    def resend_verification(self):
        email = self.email_input.text().strip()

        if not email:
            QMessageBox.warning(self, "Missing Email", "Please enter your email address.")
            return

        try:
            response = requests.post(
                "http://localhost:5000/resend_verification",
                json={"email": email},
                timeout=5
            )
            data = response.json()

            if response.status_code == 200:
                QMessageBox.information(self, "Email Sent", data["message"])
            else:
                QMessageBox.warning(self, "Failed", data.get("message", "Failed to send email."))

        except Exception as e:
            QMessageBox.critical(self, "Server Error", f"Could not connect to server:\n{str(e)}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LoginWindow()
    window.show()
    sys.exit(app.exec_())
