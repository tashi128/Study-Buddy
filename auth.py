"""
Authentication module for Study Buddy
Handles user registration, login, and session management
"""

import sqlite3
import hashlib
import hmac
import secrets
import re
from datetime import datetime
import streamlit as st


class AuthDB:
    """Database handler for authentication"""
    
    def __init__(self, db_path="database/study.db"):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Initialize authentication tables"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP
                )
            """)
            
            # Create sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    session_token TEXT UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            
            conn.commit()
            conn.close()
        except Exception as e:
            st.error(f"Database initialization error: {e}")
    
    def hash_password(self, password: str) -> str:
        """Hash password using PBKDF2"""
        salt = secrets.token_hex(16)
        hash_obj = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return f"{salt}${hash_obj.hex()}"
    
    def verify_password(self, password: str, hash_str: str) -> bool:
        """Verify password against hash"""
        try:
            salt, hash_hex = hash_str.split('$')
            hash_obj = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
            return hash_obj.hex() == hash_hex
        except:
            return False
    
    def email_exists(self, email: str) -> bool:
        """Check if email already exists"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE email = ?", (email.lower(),))
            result = cursor.fetchone()
            conn.close()
            return result is not None
        except:
            return False
    
    def register_user(self, name: str, email: str, password: str) -> dict:
        """Register new user"""
        try:
            # Validate inputs
            if not name or len(name) < 2:
                return {"success": False, "error": "Name must be at least 2 characters"}
            
            if not self._validate_email(email):
                return {"success": False, "error": "Invalid email format. Please enter a valid email address"}
            
            password_validation = self._validate_password_strength(password)
            if not password_validation["valid"]:
                return {"success": False, "error": password_validation["error"]}
            
            if self.email_exists(email):
                return {"success": False, "error": "Email already registered"}
            
            # Create user
            password_hash = self.hash_password(password)
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO users (name, email, password_hash)
                VALUES (?, ?, ?)
            """, (name, email.lower(), password_hash))
            
            user_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return {"success": True, "user_id": user_id, "message": "Registration successful!"}
        except Exception as e:
            return {"success": False, "error": f"Registration error: {str(e)}"}
    
    def login_user(self, email: str, password: str) -> dict:
        """Login user and create session"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT id, name, password_hash FROM users WHERE email = ?", (email.lower(),))
            user = cursor.fetchone()
            
            if not user or not self.verify_password(password, user[2]):
                return {"success": False, "error": "Invalid email or password"}
            
            user_id = user[0]
            
            # Update last login
            cursor.execute("UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?", (user_id,))
            
            # Create session token
            session_token = secrets.token_urlsafe(32)
            cursor.execute("""
                INSERT INTO sessions (user_id, session_token)
                VALUES (?, ?)
            """, (user_id, session_token))
            
            conn.commit()
            conn.close()
            
            return {
                "success": True,
                "user_id": user_id,
                "name": user[1],
                "session_token": session_token,
                "message": "Login successful!"
            }
        except Exception as e:
            return {"success": False, "error": f"Login error: {str(e)}"}

    def oauth_login_or_register(self, name: str, email: str) -> dict:
        """Login/register user via trusted OAuth provider and create a session."""
        try:
            if not self._validate_email(email):
                return {"success": False, "error": "Invalid email from OAuth provider"}

            display_name = (name or "").strip() or "Study Buddy User"
            email_lower = email.lower()

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT id, name FROM users WHERE email = ?", (email_lower,))
            user = cursor.fetchone()

            if user:
                user_id = user[0]
                user_name = user[1]
            else:
                # OAuth users do not need a local password; store a random one.
                random_password = secrets.token_urlsafe(24)
                password_hash = self.hash_password(random_password)
                cursor.execute("""
                    INSERT INTO users (name, email, password_hash)
                    VALUES (?, ?, ?)
                """, (display_name, email_lower, password_hash))
                user_id = cursor.lastrowid
                user_name = display_name

            cursor.execute("UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?", (user_id,))

            session_token = secrets.token_urlsafe(32)
            cursor.execute("""
                INSERT INTO sessions (user_id, session_token)
                VALUES (?, ?)
            """, (user_id, session_token))

            conn.commit()
            conn.close()

            return {
                "success": True,
                "user_id": user_id,
                "name": user_name,
                "session_token": session_token,
                "message": "OAuth login successful!"
            }
        except Exception as e:
            return {"success": False, "error": f"OAuth login error: {str(e)}"}
    
    def verify_session(self, session_token: str) -> dict:
        """Verify if session token is valid"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT u.id, u.name, u.email FROM sessions s
                JOIN users u ON s.user_id = u.id
                WHERE s.session_token = ?
            """, (session_token,))
            
            user = cursor.fetchone()
            conn.close()
            
            if user:
                return {"valid": True, "user_id": user[0], "name": user[1], "email": user[2]}
            return {"valid": False}
        except:
            return {"valid": False}
    
    def logout_user(self, session_token: str):
        """Logout user and remove session"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM sessions WHERE session_token = ?", (session_token,))
            conn.commit()
            conn.close()
        except:
            pass
    
    @staticmethod
    def _validate_email(email: str) -> bool:
        """Validate email format using RFC 5322 standard"""
        # More comprehensive email validation pattern
        pattern = r'^[a-zA-Z0-9.!#$%&\'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def _validate_password_strength(password: str) -> dict:
        """
        Validate password strength
        Requirements:
        - At least 8 characters
        - At least one uppercase letter (A-Z)
        - At least one lowercase letter (a-z)
        - At least one number (0-9)
        - At least one special character (!@#$%^&*)
        """
        errors = []
        
        if len(password) < 8:
            errors.append("at least 8 characters")
        
        if not re.search(r'[A-Z]', password):
            errors.append("at least one uppercase letter (A-Z)")
        
        if not re.search(r'[a-z]', password):
            errors.append("at least one lowercase letter (a-z)")
        
        if not re.search(r'[0-9]', password):
            errors.append("at least one number (0-9)")
        
        if not re.search(r'[!@#$%^&*()_\-+=\[\]{};:\'",.<>?/\\|`~]', password):
            errors.append("at least one special character (!@#$%^&* etc.)")
        
        if errors:
            error_message = "Password must contain: " + ", ".join(errors)
            return {"valid": False, "error": error_message}
        
        return {"valid": True, "error": ""}


# Initialize auth database
auth_db = AuthDB()


def init_auth_state():
    """Initialize authentication state"""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.user_id = None
        st.session_state.user_name = None
        st.session_state.user_email = None
        st.session_state.session_token = None
        st.session_state.is_guest = False
    elif "is_guest" not in st.session_state:
        st.session_state.is_guest = False
    
    # Check for existing session in cookies/storage
    if st.session_state.session_token:
        result = auth_db.verify_session(st.session_state.session_token)
        if not result["valid"]:
            st.session_state.authenticated = False
            st.session_state.session_token = None
            st.session_state.is_guest = False


def is_authenticated() -> bool:
    """Check if user is currently authenticated"""
    return st.session_state.get("authenticated", False)


def get_current_user() -> dict:
    """Get current authenticated user info"""
    return {
        "user_id": st.session_state.get("user_id"),
        "name": st.session_state.get("user_name"),
        "email": st.session_state.get("user_email"),
        "is_guest": st.session_state.get("is_guest", False)
    }


def start_guest_session():
    """Create a lightweight guest session without a persisted account."""
    st.session_state.authenticated = True
    st.session_state.user_id = "guest"
    st.session_state.user_name = "Guest User"
    st.session_state.user_email = "Guest mode"
    st.session_state.session_token = None
    st.session_state.is_guest = True


def logout():
    """Logout current user"""
    if st.session_state.session_token:
        auth_db.logout_user(st.session_state.session_token)
    
    st.session_state.authenticated = False
    st.session_state.user_id = None
    st.session_state.user_name = None
    st.session_state.user_email = None
    st.session_state.session_token = None
    st.session_state.is_guest = False
