import json
import os

class Database:
    def __init__(self, users_file='users.json'):
        self.users_file = users_file
        self.users = self.load_users()
    
    def load_users(self):
        """Load users from JSON file"""
        if os.path.exists(self.users_file):
            try:
                with open(self.users_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                print(f"Note: {self.users_file} is corrupted or empty. Creating new user database.")
                return {}
        else:
            print(f"Note: {self.users_file} not found. Creating new user database.")
            return {}
    
    def save_users(self):
        """Save users to JSON file"""
        try:
            with open(self.users_file, 'w') as f:
                json.dump(self.users, f, indent=2)
            return True
        except IOError:
            print(f"Error: Could not save to {self.users_file}")
            return False
    
    def user_exists(self, email):
        """Check if user exists"""
        return email in self.users
    
    def get_user(self, email):
        """Get user by email"""
        return self.users.get(email)
    
    def save_user(self, user_data):
        """Save new user"""
        email = user_data['email']
        if email not in self.users:
            self.users[email] = user_data
            return self.save_users()
        return False
    
    def update_user(self, user_data):
        """Update existing user"""
        email = user_data['email']
        self.users[email] = user_data
        return self.save_users()