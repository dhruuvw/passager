from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, 
    QTextEdit, QMessageBox, QLabel, QCheckBox, QSpinBox, QGroupBox
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont
from db import save_password, fetch_passwords_for_gui, delete_password
from crypto_utils import generate_password
import json
import pyperclip  # For copying passwords to clipboard

class VaultWindow(QWidget):
    def __init__(self, user_id, master_password):
        super().__init__()
        self.user_id = user_id
        self.master_password = master_password
        self.setWindowTitle(f"🔐 Password Vault - User: {self.user_id[:8]}...")
        self.setGeometry(500, 200, 800, 600)
        self.setStyleSheet("""
            QWidget {
                background-color: #f0f0f0;
                font-family: Arial, sans-serif;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QLineEdit {
                padding: 8px;
                border: 2px solid #ddd;
                border-radius: 4px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border-color: #4CAF50;
            }
            QTextEdit {
                border: 2px solid #ddd;
                border-radius: 4px;
                font-family: 'Courier New', monospace;
                font-size: 11px;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #ddd;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)

        self.init_ui()
        self.load_passwords_on_start()

    def init_ui(self):
        main_layout = QVBoxLayout()

        # Title
        title_label = QLabel("🔐 Password Vault")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        # Add Password Section
        add_group = QGroupBox("➕ Add New Password")
        add_layout = QVBoxLayout()

        self.platform_input = QLineEdit()
        self.platform_input.setPlaceholderText("Platform (e.g., Gmail, Facebook)")
        add_layout.addWidget(self.platform_input)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username or Email")
        add_layout.addWidget(self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)
        add_layout.addWidget(self.password_input)

        # Password visibility toggle
        password_layout = QHBoxLayout()
        self.show_password_checkbox = QCheckBox("Show Password")
        self.show_password_checkbox.stateChanged.connect(self.toggle_password_visibility)
        password_layout.addWidget(self.show_password_checkbox)
        password_layout.addStretch()
        add_layout.addLayout(password_layout)

        # Password Generator Section
        gen_group = QGroupBox("🔁 Password Generator")
        gen_layout = QVBoxLayout()

        # Generator controls
        gen_controls_layout = QHBoxLayout()
        
        gen_controls_layout.addWidget(QLabel("Length:"))
        self.length_spinbox = QSpinBox()
        self.length_spinbox.setRange(4, 128)
        self.length_spinbox.setValue(16)
        gen_controls_layout.addWidget(self.length_spinbox)

        self.use_uppercase_cb = QCheckBox("Uppercase")
        self.use_uppercase_cb.setChecked(True)
        gen_controls_layout.addWidget(self.use_uppercase_cb)

        self.use_digits_cb = QCheckBox("Digits")
        self.use_digits_cb.setChecked(True)
        gen_controls_layout.addWidget(self.use_digits_cb)

        self.use_symbols_cb = QCheckBox("Symbols")
        self.use_symbols_cb.setChecked(True)
        gen_controls_layout.addWidget(self.use_symbols_cb)

        gen_controls_layout.addStretch()
        gen_layout.addLayout(gen_controls_layout)

        # Generate button
        self.generate_btn = QPushButton("🎲 Generate Password")
        self.generate_btn.clicked.connect(self.generate_password_gui)
        gen_layout.addWidget(self.generate_btn)

        gen_group.setLayout(gen_layout)
        add_layout.addWidget(gen_group)

        # Action buttons
        button_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("💾 Save Password")
        self.save_btn.clicked.connect(self.save_password_gui)
        button_layout.addWidget(self.save_btn)

        self.clear_btn = QPushButton("🧹 Clear Form")
        self.clear_btn.clicked.connect(self.clear_form)
        button_layout.addWidget(self.clear_btn)

        add_layout.addLayout(button_layout)
        add_group.setLayout(add_layout)
        main_layout.addWidget(add_group)

        # View/Manage Passwords Section
        manage_group = QGroupBox("📂 Manage Passwords")
        manage_layout = QVBoxLayout()

        # Management buttons
        manage_button_layout = QHBoxLayout()
        
        self.view_btn = QPushButton("🔍 Refresh View")
        self.view_btn.clicked.connect(self.view_passwords)
        manage_button_layout.addWidget(self.view_btn)

        self.delete_btn = QPushButton("🗑️ Delete Selected")
        self.delete_btn.clicked.connect(self.handle_delete_password)
        manage_button_layout.addWidget(self.delete_btn)

        self.export_btn = QPushButton("📤 Export Passwords")
        self.export_btn.clicked.connect(self.export_passwords)
        manage_button_layout.addWidget(self.export_btn)

        manage_button_layout.addStretch()
        manage_layout.addLayout(manage_button_layout)

        # Results area
        self.result_area = QTextEdit()
        self.result_area.setReadOnly(True)
        self.result_area.setPlaceholderText("Your passwords will appear here...")
        self.result_area.setMinimumHeight(250)
        manage_layout.addWidget(self.result_area)

        manage_group.setLayout(manage_layout)
        main_layout.addWidget(manage_group)

        # Status bar
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: gray; font-size: 11px; padding: 5px;")
        main_layout.addWidget(self.status_label)

        self.setLayout(main_layout)

        # Auto-refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.auto_refresh)
        self.refresh_timer.start(30000)  # Refresh every 30 seconds

    def toggle_password_visibility(self, state):
        if state == Qt.Checked:
            self.password_input.setEchoMode(QLineEdit.Normal)
        else:
            self.password_input.setEchoMode(QLineEdit.Password)

    def set_status(self, message, duration=5000):
        self.status_label.setText(message)
        QTimer.singleShot(duration, lambda: self.status_label.setText("Ready"))

    def clear_form(self):
        self.platform_input.clear()
        self.username_input.clear()
        self.password_input.clear()
        self.show_password_checkbox.setChecked(False)
        self.set_status("Form cleared")

    def generate_password_gui(self):
        try:
            length = self.length_spinbox.value()
            use_upper = self.use_uppercase_cb.isChecked()
            use_digits = self.use_digits_cb.isChecked()
            use_symbols = self.use_symbols_cb.isChecked()

            if not any([use_upper, use_digits, use_symbols]):
                QMessageBox.warning(self, "Generator Error", "Please select at least one character type.")
                return

            generated = generate_password(length, use_upper, use_digits, use_symbols)
            self.password_input.setText(generated)
            
            # Copy to clipboard
            try:
                pyperclip.copy(generated)
                self.set_status(f"Password generated and copied to clipboard! (Length: {length})")
            except:
                self.set_status(f"Password generated! (Length: {length})")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate password: {e}")

    def save_password_gui(self):
        platform = self.platform_input.text().strip().lower()
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        if not platform or not username or not password:
            QMessageBox.warning(self, "Missing Fields", "Please fill in all fields.")
            return

        try:
            save_password(self.user_id, platform, username, password, self.master_password)
            QMessageBox.information(self, "Success", f"Password for '{platform}' saved successfully!")
            self.clear_form()
            self.view_passwords()  # Refresh the view
            self.set_status(f"Password saved for {platform}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save password: {e}")

    def load_passwords_on_start(self):
        """Load passwords when the window opens"""
        QTimer.singleShot(500, self.view_passwords)

    def view_passwords(self):
        try:
            self.result_area.clear()
            passwords = fetch_passwords_for_gui(self.user_id, self.master_password)

            if not passwords:
                self.result_area.setText("No passwords found.\n\nGet started by adding your first password above! 🚀")
                self.set_status("No passwords found")
                return

            output = f"🔐 Your Saved Passwords ({len(passwords)} total)\n"
            output += "=" * 60 + "\n\n"
            
            for i, p in enumerate(passwords, 1):
                if p.get("error"):
                    output += f"❌ {i}. Platform: {p['platform']}\n"
                    output += f"   Error: {p['error']}\n"
                    output += f"   Username: {p.get('username', 'N/A')}\n"
                else:
                    output += f"🌐 {i}. Platform: {p['platform'].title()}\n"
                    output += f"   👤 Username: {p['username']}\n"
                    output += f"   🔑 Password: {p['password']}\n"
                    output += f"   📋 [Click to copy: {p['password']}]\n"
                
                output += "-" * 50 + "\n\n"

            output += f"\n💡 Tip: To delete a password, enter the platform name above and click 'Delete Selected'"
            self.result_area.setText(output)
            self.set_status(f"Loaded {len(passwords)} passwords")

        except Exception as e:
            error_msg = f"Error loading passwords: {str(e)}"
            QMessageBox.critical(self, "Error", error_msg)
            self.result_area.setText(error_msg)
            self.set_status("Error loading passwords")

    def handle_delete_password(self):
        platform = self.platform_input.text().strip().lower()
        if not platform:
            QMessageBox.warning(self, "Missing Platform", "Enter the platform name to delete.")
            return

        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete the password for '{platform}'?\n\nThis action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                delete_password(self.user_id, platform)
                QMessageBox.information(self, "Success", f"Password for '{platform}' deleted successfully.")
                self.platform_input.clear()
                self.view_passwords()  # Refresh the view
                self.set_status(f"Password deleted for {platform}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Delete failed: {e}")

    def export_passwords(self):
        """Export passwords to a JSON file"""
        try:
            passwords = fetch_passwords_for_gui(self.user_id, self.master_password)
            if not passwords:
                QMessageBox.information(self, "No Data", "No passwords to export.")
                return

            from PyQt5.QtWidgets import QFileDialog
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Export Passwords", "passwords_export.json", "JSON Files (*.json)"
            )
            
            if file_path:
                # Remove any error entries before export
                clean_passwords = [p for p in passwords if not p.get("error")]
                
                with open(file_path, 'w') as f:
                    json.dump(clean_passwords, f, indent=2)
                
                QMessageBox.information(self, "Export Success", f"Passwords exported to:\n{file_path}")
                self.set_status(f"Exported {len(clean_passwords)} passwords")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export passwords: {e}")

    def auto_refresh(self):
        """Auto-refresh passwords periodically"""
        if self.isVisible():
            self.view_passwords()

    def closeEvent(self, event):
        """Handle window close event"""
        self.refresh_timer.stop()
        reply = QMessageBox.question(
            self, "Confirm Exit",
            "Are you sure you want to exit the Password Vault?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()