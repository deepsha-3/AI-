import hashlib
import os
import sqlite3
import re
import tkinter as tk
from tkinter import messagebox
import secrets
import string
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random

class AuthenticationManager:
    def __init__(self, db_name="users.db"):
        self.db_name = db_name
        self.init_db()
        # Email configuration for password reset
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        # These should be configured by user or in a config file
        self.email_sender = "your_email@gmail.com"  # Change this
        self.email_password = "your_app_password"   # Change this
    
    def init_db(self):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    salt TEXT NOT NULL,
                    skills TEXT DEFAULT '',
                    location TEXT DEFAULT '',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            # Add password reset tokens table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS password_reset_tokens (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT NOT NULL,
                    token TEXT NOT NULL,
                    expires_at TIMESTAMP DEFAULT (datetime('now', '+1 hour')),
                    used INTEGER DEFAULT 0,
                    FOREIGN KEY (email) REFERENCES users(email)
                )
            ''')
            conn.commit()
    
    def hash_password(self, password, salt=None):
        if salt is None:
            salt = os.urandom(32)
        password_hash = hashlib.pbkdf2_hmac(
            'sha256', password.encode('utf-8'), salt, 100000
        )
        return password_hash, salt
    
    def generate_reset_token(self):
        """Generate a secure random token for password reset"""
        return secrets.token_urlsafe(32)
    
    def create_password_reset_token(self, email):
        """Create a password reset token for the user"""
        if not self.email_exists(email):
            return False, "Email not registered"
        
        token = self.generate_reset_token()
        
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            # Invalidate any existing tokens
            cursor.execute(
                "UPDATE password_reset_tokens SET used = 1 WHERE email = ?",
                (email,)
            )
            # Insert new token
            cursor.execute(
                '''INSERT INTO password_reset_tokens (email, token) 
                   VALUES (?, ?)''',
                (email, token)
            )
            conn.commit()
        
        return True, token
    
    def verify_reset_token(self, email, token):
        """Verify if a reset token is valid"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute(
                '''SELECT email FROM password_reset_tokens 
                   WHERE email = ? AND token = ? AND used = 0 
                   AND expires_at > datetime('now')''',
                (email, token)
            )
            result = cursor.fetchone()
        
        return result is not None
    
    def use_reset_token(self, email, token):
        """Mark a reset token as used"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute(
                '''UPDATE password_reset_tokens SET used = 1 
                   WHERE email = ? AND token = ?''',
                (email, token)
            )
            conn.commit()
    
    def reset_password(self, email, token, new_password):
        """Reset user's password using valid token"""
        # Verify token
        if not self.verify_reset_token(email, token):
            return False, "Invalid or expired token"
        
        # Validate new password strength
        if not self.is_strong_password(new_password):
            return False, "Password must be at least 8 characters with uppercase, lowercase, number, and special character"
        
        # Hash new password
        password_hash, salt = self.hash_password(new_password)
        
        # Update password in database
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute(
                '''UPDATE users SET password_hash = ?, salt = ? 
                   WHERE email = ?''',
                (password_hash.hex(), salt.hex(), email)
            )
            # Mark token as used
            cursor.execute(
                '''UPDATE password_reset_tokens SET used = 1 
                   WHERE email = ? AND token = ?''',
                (email, token)
            )
            conn.commit()
        
        return True, "Password reset successful"
    
    def send_reset_email(self, email, token):
        """Send password reset email (simplified version)"""
        try:
            # For demo purposes, we'll show the token in a messagebox
            # In production, you would send an actual email
            reset_link = f"http://localhost:8000/reset-password?email={email}&token={token}"
            message = f"""
            Password Reset Request
            
            Someone requested a password reset for your account.
            
            Your reset token is: {token}
            
            Or click this link: {reset_link}
            
            This token will expire in 1 hour.
            
            If you didn't request this, please ignore this email.
            """
            
            # In a real application, you would send the email:
            # msg = MIMEMultipart()
            # msg['From'] = self.email_sender
            # msg['To'] = email
            # msg['Subject'] = "Password Reset Request - Job Matching Assistant"
            # msg.attach(MIMEText(message, 'plain'))
            # 
            # with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
            #     server.starttls()
            #     server.login(self.email_sender, self.email_password)
            #     server.send_message(msg)
            
            return True, message
        except Exception as e:
            return False, f"Failed to send email: {str(e)}"
    
    def register_user(self, username, email, password, skills="", location=""):
        # Check if email already exists
        if self.email_exists(email):
            return False, "Email already registered"
        
        # Validate email format
        if not self.is_valid_email(email):
            return False, "Invalid email format"
        
        # Validate password strength
        if not self.is_strong_password(password):
            return False, "Password must be at least 8 characters with uppercase, lowercase, number, and special character"
        
        # Hash the password
        password_hash, salt = self.hash_password(password)
        
        # Store user in database
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute(
                '''INSERT INTO users (username, email, password_hash, salt, skills, location) 
                   VALUES (?, ?, ?, ?, ?, ?)''',
                (username, email, password_hash.hex(), salt.hex(), 
                 json.dumps(skills), location)
            )
            conn.commit()
        
        return True, "User registered successfully"
    
    def verify_user(self, email, password):
        # Get user data from database
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute(
                '''SELECT password_hash, salt, username, skills, location 
                   FROM users WHERE email = ?''',
                (email,)
            )
            result = cursor.fetchone()
        
        if not result:
            return False, "User not found", None
        
        stored_hash_hex, salt_hex, username, skills_json, location = result
        stored_hash = bytes.fromhex(stored_hash_hex)
        salt = bytes.fromhex(salt_hex)
        
        # Parse skills from JSON
        skills = json.loads(skills_json) if skills_json else []
        
        # Hash the provided password with the stored salt
        provided_hash, _ = self.hash_password(password, salt)
        
        # Compare the hashes
        if provided_hash == stored_hash:
            user_data = {
                'username': username,
                'email': email,
                'skills': skills,
                'location': location
            }
            return True, "Login successful", user_data
        else:
            return False, "Invalid password", None
    
    def email_exists(self, email):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT id FROM users WHERE email = ?',
                (email,)
            )
            return cursor.fetchone() is not None
    
    def is_valid_email(self, email):
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def is_strong_password(self, password):
        if len(password) < 8:
            return False
        if not re.search(r'[A-Z]', password):
            return False
        if not re.search(r'[a-z]', password):
            return False
        if not re.search(r'[0-9]', password):
            return False
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False
        return True
    
    def update_user_profile(self, email, skills, location):
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    '''UPDATE users SET skills = ?, location = ? 
                       WHERE email = ?''',
                    (json.dumps(skills), location, email)
                )
                conn.commit()
            return True, "Profile updated successfully"
        except Exception as e:
            return False, f"Error updating profile: {str(e)}"


class AnimatedAuthWindow:
    def __init__(self, root, auth_manager, on_login_success):
        self.root = root
        self.auth_manager = auth_manager
        self.on_login_success = on_login_success
        
        self.center_window(1000, 600)
        
        # Animation variables
        self.animation_running = False
        self.current_hue = 0
        self.canvas = None
        
        self.setup_ui()
        
        # Start background animation
        self.animate_background()
    
    def center_window(self, width, height):
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        self.root.resizable(False, False)
    
    def setup_ui(self):
        self.root.title("Job Matching Assistant - Authentication")
        self.root.configure(bg="#0a1929")
        
        # Create canvas for animated background
        self.canvas = tk.Canvas(self.root, bg="#0a1929", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Main container
        self.main_container = tk.Frame(self.canvas, bg="#0a1929")
        self.main_container.place(relx=0.5, rely=0.5, anchor=tk.CENTER, width=800, height=500)
        
        # Create the animated panels
        self.create_panels()
        
        # Start with login form
        self.show_login_form()
    
    def create_panels(self):
        # Login form - initially visible
        self.login_frame = tk.Frame(self.main_container, bg="#ffffff", relief=tk.FLAT, bd=0)
        self.login_frame.place(relx=0, rely=0, relwidth=0.5, relheight=1)
        
        # Welcome panel: initially on the right side
        self.welcome_frame = tk.Frame(self.main_container, bg="#1e3a5f", relief=tk.FLAT, bd=0)
        self.welcome_frame.place(relx=0.5, rely=0, relwidth=0.5, relheight=1)
        
        # Create login form content
        self.create_login_form()
        
        # Create welcome panel content
        self.create_welcome_panel()
    
    def create_login_form(self):
        # Title with new color theme
        title_label = tk.Label(self.login_frame, text="Welcome Back!", 
                              font=("Arial", 24, "bold"), bg="#ffffff", fg="#1e3a5f")
        title_label.pack(pady=(40, 10))
        
        subtitle_label = tk.Label(self.login_frame, 
                                 text="Enter your credentials to access job matching", 
                                 font=("Arial", 10), bg="#ffffff", fg="#5d7a9e")
        subtitle_label.pack(pady=(0, 40))
        
        # Email field
        email_frame = tk.Frame(self.login_frame, bg="#ffffff")
        email_frame.pack(pady=10, padx=40, fill=tk.X)
        
        tk.Label(email_frame, text="Email", font=("Arial", 10, "bold"), 
                bg="#ffffff", fg="#1e3a5f").pack(anchor="w")
        
        self.login_email_var = tk.StringVar()
        email_entry = tk.Entry(email_frame, textvariable=self.login_email_var, 
                              font=("Arial", 12), bd=1, relief=tk.SOLID, 
                              highlightthickness=1, highlightcolor="#3d5a80", 
                              highlightbackground="#e8edf5")
        email_entry.pack(pady=5, fill=tk.X)
        
        # Password field with show/hide button
        password_frame = tk.Frame(self.login_frame, bg="#ffffff")
        password_frame.pack(pady=10, padx=40, fill=tk.X)
        
        tk.Label(password_frame, text="Password", font=("Arial", 10, "bold"), 
                bg="#ffffff", fg="#1e3a5f").pack(anchor="w")
        
        self.login_password_var = tk.StringVar()
        
        # Create a frame for password entry and button
        password_input_frame = tk.Frame(password_frame, bg="#ffffff")
        password_input_frame.pack(pady=5, fill=tk.X)
        
        # Password entry field
        self.login_password_entry = tk.Entry(password_input_frame, 
                                            textvariable=self.login_password_var, 
                                            font=("Arial", 12), show="•", bd=1, relief=tk.SOLID,
                                            highlightthickness=1, highlightcolor="#3d5a80", 
                                            highlightbackground="#e8edf5")
        self.login_password_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Show/hide password button
        self.login_show_password_btn = tk.Button(password_input_frame, text="👁", 
                                               font=("Arial", 10), bg="#e8edf5", fg="#1e3a5f",
                                               bd=1, relief=tk.SOLID, cursor="hand2",
                                               width=3, height=1)
        self.login_show_password_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        # Bind the button to toggle password visibility
        self.login_show_password_btn.config(
            command=lambda: self.toggle_password_visibility(self.login_password_entry, 
                                                           self.login_show_password_btn)
        )
        
        # Add keyboard shortcut (Ctrl+E to toggle password visibility)
        self.login_password_entry.bind('<Control-e>', 
            lambda e: self.toggle_password_visibility(self.login_password_entry, 
                                                     self.login_show_password_btn))
        self.login_password_entry.bind('<Control-E>', 
            lambda e: self.toggle_password_visibility(self.login_password_entry, 
                                                     self.login_show_password_btn))
        
        # Forgot password link
        forgot_frame = tk.Frame(self.login_frame, bg="#ffffff")
        forgot_frame.pack(pady=(5, 0), padx=40, fill=tk.X)
        
        forgot_btn = tk.Button(forgot_frame, text="Forgot Password?", 
                              font=("Arial", 9), bg="#ffffff", fg="#3d5a80", 
                              bd=0, cursor="hand2", command=self.show_forgot_password)
        forgot_btn.pack(anchor="e")
        
        # Login button with new color
        login_btn = tk.Button(self.login_frame, text="SIGN IN", 
                             font=("Arial", 12, "bold"), bg="#3d5a80", fg="white", 
                             width=20, height=2, bd=0, cursor="hand2", 
                             activebackground="#2d4a70", activeforeground="white",
                             command=self.login)
        login_btn.pack(pady=20)
        
        # Register prompt
        register_prompt = tk.Frame(self.login_frame, bg="#ffffff")
        register_prompt.pack(pady=10)
        
        tk.Label(register_prompt, text="Don't have an account?", font=("Arial", 9), 
                bg="#ffffff", fg="#5d7a9e").pack(side=tk.LEFT)
        
        tk.Button(register_prompt, text="Sign Up", font=("Arial", 9, "bold"), 
                 bg="#ffffff", fg="#3d5a80", bd=0, cursor="hand2",
                 command=self.show_register_form).pack(side=tk.LEFT, padx=5)
    
    def create_welcome_panel(self):
        # Title with new color theme
        title_label = tk.Label(self.welcome_frame, text="New Here?", 
                              font=("Arial", 24, "bold"), bg="#1e3a5f", fg="white")
        title_label.pack(pady=(120, 10))
        
        subtitle_label = tk.Label(self.welcome_frame, 
                                 text="Register to start matching with your dream jobs", 
                                 font=("Arial", 10), bg="#1e3a5f", fg="white")
        subtitle_label.pack(pady=(0, 30))
        
        # Register button with new color
        register_btn = tk.Button(self.welcome_frame, text="SIGN UP", 
                                font=("Arial", 12, "bold"), bg="#3d5a80", fg="white", 
                                width=20, height=2, bd=0, cursor="hand2",
                                activebackground="#2d4a70", activeforeground="white",
                                command=self.show_register_form)
        register_btn.pack(pady=20)
    
    def show_login_form(self):
        self.animate_panels(0)
        self.root.title("Job Matching Assistant - Sign In")
    
    def show_register_form(self):
        # First animate the panels to the left
        self.animate_panels(-0.5)
        
        # Then create the register form on the right side
        if hasattr(self, 'register_frame'):
            self.register_frame.destroy()
        
        self.register_frame = tk.Frame(self.main_container, bg="#ffffff", relief=tk.FLAT, bd=0)
        self.register_frame.place(relx=0.5, rely=0, relwidth=0.5, relheight=1)
        
        # Create register form content - USING A SCROLLABLE FRAME
        self.create_register_form_content()
        
        self.root.title("Job Matching Assistant - Sign Up")
    
    def show_forgot_password(self):
        """Show forgot password dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Forgot Password")
        dialog.geometry("400x300")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.configure(bg="#ffffff")
        
        # Center the dialog
        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - dialog.winfo_width()) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")
        
        # Content
        main_frame = tk.Frame(dialog, padx=20, pady=20, bg="#ffffff")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(main_frame, text="Reset Password", 
                font=("Arial", 16, "bold"), bg="#ffffff", fg="#1e3a5f").pack(pady=(0, 20))
        
        tk.Label(main_frame, text="Enter your email address to receive a reset link:", 
                font=("Arial", 10), bg="#ffffff", fg="#5d7a9e").pack(pady=(0, 20))
        
        # Email input
        email_var = tk.StringVar()
        tk.Label(main_frame, text="Email Address:", 
                font=("Arial", 10, "bold"), bg="#ffffff", fg="#1e3a5f").pack(anchor="w", pady=(5, 0))
        
        email_entry = tk.Entry(main_frame, textvariable=email_var, 
                              font=("Arial", 12), width=30,
                              highlightthickness=1, highlightcolor="#3d5a80")
        email_entry.pack(pady=(0, 20), fill=tk.X)
        
        # Status label
        status_label = tk.Label(main_frame, text="", 
                               font=("Arial", 9), bg="#ffffff", fg="#c44536")
        status_label.pack(pady=(0, 20))
        
        def send_reset_link():
            email = email_var.get().strip()
            if not email:
                status_label.config(text="Please enter your email address", fg="#c44536")
                return
            
            if not self.auth_manager.is_valid_email(email):
                status_label.config(text="Please enter a valid email address", fg="#c44536")
                return
            
            if not self.auth_manager.email_exists(email):
                status_label.config(text="Email not registered", fg="#c44536")
                return
            
            # Create reset token
            success, token = self.auth_manager.create_password_reset_token(email)
            
            if success:
                # Send reset email (for demo, show token in messagebox)
                email_sent, message = self.auth_manager.send_reset_email(email, token)
                
                if email_sent:
                    # Show token for demo purposes
                    show_token_dialog(email, token)
                else:
                    status_label.config(text=message, fg="#c44536")
            else:
                status_label.config(text=token, fg="#c44536")
        
        def show_token_dialog(email, token):
            """Show token dialog for demo purposes"""
            token_dialog = tk.Toplevel(dialog)
            token_dialog.title("Password Reset Token")
            token_dialog.geometry("500x400")
            token_dialog.resizable(False, False)
            token_dialog.transient(dialog)
            token_dialog.grab_set()
            token_dialog.configure(bg="#ffffff")
            
            # Center the dialog
            token_dialog.update_idletasks()
            x = dialog.winfo_x() + (dialog.winfo_width() - token_dialog.winfo_width()) // 2
            y = dialog.winfo_y() + (dialog.winfo_height() - token_dialog.winfo_height()) // 2
            token_dialog.geometry(f"+{x}+{y}")
            
            # Content
            token_frame = tk.Frame(token_dialog, padx=20, pady=20, bg="#ffffff")
            token_frame.pack(fill=tk.BOTH, expand=True)
            
            tk.Label(token_frame, text="Password Reset Token", 
                    font=("Arial", 16, "bold"), bg="#ffffff", fg="#1e3a5f").pack(pady=(0, 20))
            
            tk.Label(token_frame, text="For demo purposes, here is your reset token:", 
                    font=("Arial", 10), bg="#ffffff", fg="#5d7a9e").pack(pady=(0, 10))
            
            # Show token
            token_text = tk.Text(token_frame, height=4, width=50, wrap=tk.WORD,
                                font=("Courier", 10), bg="#f8f9fa", fg="#1e3a5f")
            token_text.pack(pady=10)
            token_text.insert(tk.END, token)
            token_text.config(state=tk.DISABLED)
            
            tk.Label(token_frame, text="Copy this token and use it to reset your password.", 
                    font=("Arial", 9), bg="#ffffff", fg="#5d7a9e").pack(pady=(0, 20))
            
            # Buttons
            button_frame = tk.Frame(token_frame, bg="#ffffff")
            button_frame.pack(fill=tk.X, pady=(10, 0))
            
            tk.Button(button_frame, text="Reset Password Now", 
                     command=lambda: self.show_reset_password(email, token, token_dialog),
                     bg="#3d5a80", fg="white", bd=0, padx=20).pack(side=tk.LEFT, padx=(0, 10))
            
            tk.Button(button_frame, text="Close", 
                     command=token_dialog.destroy,
                     bg="#95a5a6", fg="white", bd=0, padx=20).pack(side=tk.LEFT)
        
        # Buttons
        button_frame = tk.Frame(main_frame, bg="#ffffff")
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        tk.Button(button_frame, text="Send Reset Link", command=send_reset_link,
                 bg="#3d5a80", fg="white", bd=0, padx=20).pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Button(button_frame, text="Cancel", command=dialog.destroy,
                 bg="#95a5a6", fg="white", bd=0, padx=20).pack(side=tk.LEFT)
    
    def show_reset_password(self, email, token, parent_dialog=None):
        """Show reset password dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Reset Password")
        dialog.geometry("400x400")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.configure(bg="#ffffff")
        
        # Center the dialog
        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - dialog.winfo_width()) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")
        
        # Close parent dialog if provided
        if parent_dialog:
            parent_dialog.destroy()
        
        # Content
        main_frame = tk.Frame(dialog, padx=20, pady=20, bg="#ffffff")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(main_frame, text="Set New Password", 
                font=("Arial", 16, "bold"), bg="#ffffff", fg="#1e3a5f").pack(pady=(0, 20))
        
        tk.Label(main_frame, text=f"Reset password for: {email}", 
                font=("Arial", 10), bg="#ffffff", fg="#5d7a9e").pack(pady=(0, 20))
        
        # New Password
        new_password_var = tk.StringVar()
        tk.Label(main_frame, text="New Password:", 
                font=("Arial", 10, "bold"), bg="#ffffff", fg="#1e3a5f").pack(anchor="w", pady=(5, 0))
        
        new_password_entry = tk.Entry(main_frame, textvariable=new_password_var, 
                                     font=("Arial", 12), show="•", width=30,
                                     highlightthickness=1, highlightcolor="#3d5a80")
        new_password_entry.pack(pady=(0, 10), fill=tk.X)
        
        # Confirm Password
        confirm_password_var = tk.StringVar()
        tk.Label(main_frame, text="Confirm New Password:", 
                font=("Arial", 10, "bold"), bg="#ffffff", fg="#1e3a5f").pack(anchor="w", pady=(5, 0))
        
        confirm_password_entry = tk.Entry(main_frame, textvariable=confirm_password_var, 
                                         font=("Arial", 12), show="•", width=30,
                                         highlightthickness=1, highlightcolor="#3d5a80")
        confirm_password_entry.pack(pady=(0, 20), fill=tk.X)
        
        # Password requirements
        req_label = tk.Label(main_frame, 
                            text="Password must be at least 8 characters with uppercase, lowercase, number, and special character",
                            font=("Arial", 9), bg="#ffffff", fg="#5d7a9e", wraplength=350)
        req_label.pack(pady=(0, 20))
        
        # Status label
        status_label = tk.Label(main_frame, text="", 
                               font=("Arial", 9), bg="#ffffff", fg="#27ae60")
        status_label.pack(pady=(0, 20))
        
        def reset_password():
            new_password = new_password_var.get()
            confirm_password = confirm_password_var.get()
            
            if not new_password or not confirm_password:
                status_label.config(text="Please fill in all fields", fg="#c44536")
                return
            
            if new_password != confirm_password:
                status_label.config(text="Passwords do not match", fg="#c44536")
                return
            
            # Reset password
            success, message = self.auth_manager.reset_password(email, token, new_password)
            
            if success:
                status_label.config(text=message, fg="#27ae60")
                # Close dialog after success
                dialog.after(2000, dialog.destroy)
                messagebox.showinfo("Success", "Password reset successfully! You can now login with your new password.")
            else:
                status_label.config(text=message, fg="#c44536")
        
        # Buttons
        button_frame = tk.Frame(main_frame, bg="#ffffff")
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        tk.Button(button_frame, text="Reset Password", command=reset_password,
                 bg="#3d5a80", fg="white", bd=0, padx=20).pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Button(button_frame, text="Cancel", command=dialog.destroy,
                 bg="#95a5a6", fg="white", bd=0, padx=20).pack(side=tk.LEFT)
    
    def create_register_form_content(self):
        # Create a canvas and scrollbar for the register form
        self.register_canvas = tk.Canvas(self.register_frame, bg="#ffffff", highlightthickness=0)
        scrollbar = tk.Scrollbar(self.register_frame, orient="vertical", command=self.register_canvas.yview)
        scrollable_frame = tk.Frame(self.register_canvas, bg="#ffffff")
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: self.register_canvas.configure(scrollregion=self.register_canvas.bbox("all"))
        )
        
        self.register_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        self.register_canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack canvas and scrollbar
        self.register_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Title
        title_label = tk.Label(scrollable_frame, text="Create Account", 
                              font=("Arial", 24, "bold"), bg="#ffffff", fg="#1e3a5f")
        title_label.pack(pady=(40, 10))
        
        subtitle_label = tk.Label(scrollable_frame, 
                                 text="Fill in your details to get started", 
                                 font=("Arial", 10), bg="#ffffff", fg="#5d7a9e")
        subtitle_label.pack(pady=(0, 20))
        
        # Name field
        name_frame = tk.Frame(scrollable_frame, bg="#ffffff")
        name_frame.pack(pady=10, padx=40, fill=tk.X)
        
        tk.Label(name_frame, text="Username", font=("Arial", 10, "bold"), 
                bg="#ffffff", fg="#1e3a5f").pack(anchor="w")
        
        self.register_name_var = tk.StringVar()
        name_entry = tk.Entry(name_frame, textvariable=self.register_name_var, 
                             font=("Arial", 12), bd=1, relief=tk.SOLID, 
                             highlightthickness=1, highlightcolor="#3d5a80", 
                             highlightbackground="#e8edf5")
        name_entry.pack(pady=5, fill=tk.X)
        
        # Email field
        email_frame = tk.Frame(scrollable_frame, bg="#ffffff")
        email_frame.pack(pady=10, padx=40, fill=tk.X)
        
        tk.Label(email_frame, text="Email", font=("Arial", 10, "bold"), 
                bg="#ffffff", fg="#1e3a5f").pack(anchor="w")
        
        self.register_email_var = tk.StringVar()
        email_entry = tk.Entry(email_frame, textvariable=self.register_email_var, 
                              font=("Arial", 12), bd=1, relief=tk.SOLID, 
                              highlightthickness=1, highlightcolor="#3d5a80", 
                              highlightbackground="#e8edf5")
        email_entry.pack(pady=5, fill=tk.X)
        
        # Skills field
        skills_frame = tk.Frame(scrollable_frame, bg="#ffffff")
        skills_frame.pack(pady=10, padx=40, fill=tk.X)
        
        tk.Label(skills_frame, text="Skills (comma-separated)", font=("Arial", 10, "bold"), 
                bg="#ffffff", fg="#1e3a5f").pack(anchor="w")
        
        self.register_skills_var = tk.StringVar()
        skills_entry = tk.Entry(skills_frame, textvariable=self.register_skills_var, 
                               font=("Arial", 12), bd=1, relief=tk.SOLID,
                               highlightthickness=1, highlightcolor="#3d5a80", 
                               highlightbackground="#e8edf5")
        skills_entry.pack(pady=5, fill=tk.X)
        
        # Location field
        location_frame = tk.Frame(scrollable_frame, bg="#ffffff")
        location_frame.pack(pady=10, padx=40, fill=tk.X)
        
        tk.Label(location_frame, text="Location", font=("Arial", 10, "bold"), 
                bg="#ffffff", fg="#1e3a5f").pack(anchor="w")
        
        self.register_location_var = tk.StringVar()
        location_entry = tk.Entry(location_frame, textvariable=self.register_location_var, 
                                 font=("Arial", 12), bd=1, relief=tk.SOLID,
                                 highlightthickness=1, highlightcolor="#3d5a80", 
                                 highlightbackground="#e8edf5")
        location_entry.pack(pady=5, fill=tk.X)
        
        # Password field with show/hide button
        password_frame = tk.Frame(scrollable_frame, bg="#ffffff")
        password_frame.pack(pady=10, padx=40, fill=tk.X)
        
        tk.Label(password_frame, text="Password", font=("Arial", 10, "bold"), 
                bg="#ffffff", fg="#1e3a5f").pack(anchor="w")
        
        self.register_password_var = tk.StringVar()
        
        # Create a frame for password entry and button
        register_password_input_frame = tk.Frame(password_frame, bg="#ffffff")
        register_password_input_frame.pack(pady=5, fill=tk.X)
        
        # Password entry field
        self.register_password_entry = tk.Entry(register_password_input_frame, 
                                               textvariable=self.register_password_var, 
                                               font=("Arial", 12), show="•", bd=1, relief=tk.SOLID,
                                               highlightthickness=1, highlightcolor="#3d5a80", 
                                               highlightbackground="#e8edf5")
        self.register_password_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Show/hide password button
        self.register_show_password_btn = tk.Button(register_password_input_frame, text="👁", 
                                                  font=("Arial", 10), bg="#e8edf5", fg="#1e3a5f",
                                                  bd=1, relief=tk.SOLID, cursor="hand2",
                                                  width=3, height=1)
        self.register_show_password_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        # Bind the button to toggle password visibility
        self.register_show_password_btn.config(
            command=lambda: self.toggle_password_visibility(self.register_password_entry, 
                                                           self.register_show_password_btn)
        )
        
        # Add keyboard shortcut (Ctrl+E to toggle password visibility)
        self.register_password_entry.bind('<Control-e>', 
            lambda e: self.toggle_password_visibility(self.register_password_entry, 
                                                     self.register_show_password_btn))
        self.register_password_entry.bind('<Control-E>', 
            lambda e: self.toggle_password_visibility(self.register_password_entry, 
                                                     self.register_show_password_btn))
        
        # Password requirements label
        req_label = tk.Label(scrollable_frame, 
                            text="Password must be at least 8 characters with uppercase, lowercase, number, and special character",
                            font=("Arial", 9), bg="#ffffff", fg="#5d7a9e", wraplength=350)
        req_label.pack(pady=(0, 20), padx=40)
        
        # Register button with new color
        register_btn = tk.Button(scrollable_frame, text="SIGN UP", 
                                font=("Arial", 12, "bold"), bg="#3d5a80", fg="white", 
                                width=20, height=2, bd=0, cursor="hand2",
                                activebackground="#2d4a70", activeforeground="white",
                                command=self.register)
        register_btn.pack(pady=10)
        
        # Login prompt
        login_prompt = tk.Frame(scrollable_frame, bg="#ffffff")
        login_prompt.pack(pady=10)
        
        tk.Label(login_prompt, text="Already have an account?", font=("Arial", 9), 
                bg="#ffffff", fg="#5d7a9e").pack(side=tk.LEFT)
        
        tk.Button(login_prompt, text="Sign In", font=("Arial", 9, "bold"), 
                 bg="#ffffff", fg="#3d5a80", bd=0, cursor="hand2",
                 command=self.show_login_form).pack(side=tk.LEFT, padx=5)
        
        # Update the canvas scrollregion
        scrollable_frame.update_idletasks()
        self.register_canvas.config(scrollregion=self.register_canvas.bbox("all"))
        
        # Bind mouse wheel for scrolling
        self.register_canvas.bind_all("<MouseWheel>", self._on_mousewheel)
    
    def _on_mousewheel(self, event):
        self.register_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    def toggle_password_visibility(self, entry_widget, show_button):
        """Toggle password visibility between hidden and visible"""
        if entry_widget.cget('show') == '':
            entry_widget.config(show='•')  # Hide password
            show_button.config(text='👁')  # Show open eye icon
            show_button.config(bg='#e8edf5', fg='#1e3a5f')
        else:
            entry_widget.config(show='')   # Show password
            show_button.config(text='🙈')  # Show crossed eye icon
            show_button.config(bg='#3d5a80', fg='white')
    
    def animate_panels(self, target_relx):
        if self.animation_running:
            return
            
        self.animation_running = True
        current_relx = float(self.login_frame.place_info()["relx"])
        
        # Calculate step
        step = (target_relx - current_relx) / 15
        
        def move():
            nonlocal current_relx
            current_relx += step
            
            if (step > 0 and current_relx >= target_relx) or (step < 0 and current_relx <= target_relx):
                current_relx = target_relx
                self.login_frame.place(relx=current_relx, rely=0, relwidth=0.5, relheight=1)
                self.welcome_frame.place(relx=current_relx + 0.5, rely=0, relwidth=0.5, relheight=1)
                self.animation_running = False
                return
            
            self.login_frame.place(relx=current_relx, rely=0, relwidth=0.5, relheight=1)
            self.welcome_frame.place(relx=current_relx + 0.5, rely=0, relwidth=0.5, relheight=1)
            self.root.after(20, move)
        
        move()
    
    def animate_background(self):
        # Create a smooth color changing background
        self.current_hue = (self.current_hue + 0.5) % 360
        r, g, b = self.hsv_to_rgb(self.current_hue, 0.15, 0.15)
        color = f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"
        
        self.canvas.configure(bg=color)
        self.main_container.configure(bg=color)
        
        # Schedule the next animation frame
        self.root.after(50, self.animate_background)
    
    def hsv_to_rgb(self, h, s, v):
        # Convert HSV to RGB color
        h = h / 360.0
        if s == 0.0:
            return v, v, v
        
        i = int(h * 6)
        f = (h * 6) - i
        p = v * (1 - s)
        q = v * (1 - s * f)
        t = v * (1 - s * (1 - f))
        
        if i % 6 == 0:
            return v, t, p
        elif i % 6 == 1:
            return q, v, p
        elif i % 6 == 2:
            return p, v, t
        elif i % 6 == 3:
            return p, q, v
        elif i % 6 == 4:
            return t, p, v
        else:
            return v, p, q
    
    def login(self):
        """Handle login button click"""
        email = self.login_email_var.get().strip()
        password = self.login_password_var.get()
        
        if not email or not password:
            messagebox.showerror("Error", "Please enter both email and password")
            return
        
        success, message, user_data = self.auth_manager.verify_user(email, password)
        
        if success:
            messagebox.showinfo("Success", message)
            self.on_login_success(email, user_data)
        else:
            messagebox.showerror("Error", message)
    
    def register(self):
        """Handle register button click"""
        username = self.register_name_var.get().strip()
        email = self.register_email_var.get().strip()
        password = self.register_password_var.get()
        skills_str = self.register_skills_var.get().strip()
        location = self.register_location_var.get().strip()
        
        # Validate inputs
        if not all([username, email, password, location]):
            messagebox.showerror("Error", "Please fill in all required fields")
            return
        
        # Parse skills
        skills = [skill.strip() for skill in skills_str.split(',')] if skills_str else []
        
        # Register user
        success, message = self.auth_manager.register_user(
            username, email, password, skills, location
        )
        
        if success:
            messagebox.showinfo("Success", message)
            # Automatically log in the user after registration
            success, message, user_data = self.auth_manager.verify_user(email, password)
            if success:
                self.on_login_success(email, user_data)
        else:
            messagebox.showerror("Error", message)