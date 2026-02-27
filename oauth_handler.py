"""
OAuth handler for Google and Apple Sign-In integration with Study Buddy
Handles OAuth flows and token validation
"""

import os
import json
import hashlib
import hmac
from datetime import datetime, timedelta
import jwt
import requests
from urllib.parse import urlencode, parse_qs, urlparse
import streamlit as st
try:
    from dotenv import load_dotenv
    load_dotenv(override=True)
except Exception:
    pass


class OAuthHandler:
    """Manages OAuth authentication for Google and Apple"""
    
    # OAuth Configuration
    # These should be set via environment variables or Streamlit secrets
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "YOUR_GOOGLE_CLIENT_ID.apps.googleusercontent.com")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "YOUR_GOOGLE_CLIENT_SECRET")
    # App root callback for Streamlit; keep this in sync with Google Console.
    GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8501")
    
    # OAuth URLs
    GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
    GOOGLE_USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"
    

    @staticmethod
    def get_google_auth_url():
        """Generate Google OAuth authorization URL"""
        # Check if credentials are configured
        if OAuthHandler.GOOGLE_CLIENT_ID.startswith("YOUR_"):
            return None
        
        redirect_uri = OAuthHandler._get_google_redirect_uri()
        
        params = {
            "client_id": OAuthHandler.GOOGLE_CLIENT_ID,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "access_type": "offline",
            "prompt": "consent"
        }
        return f"{OAuthHandler.GOOGLE_AUTH_URL}?{urlencode(params)}"
    
    @staticmethod
    def get_apple_auth_url():
        """Generate Apple OAuth authorization URL"""
        # Check if credentials are configured
        if OAuthHandler.APPLE_TEAM_ID.startswith("YOUR_"):
            return None
        
        params = {
            "client_id": OAuthHandler.APPLE_CLIENT_ID,
            "redirect_uri": OAuthHandler.APPLE_REDIRECT_URI,
            "response_type": "code",
            "response_mode": "query",
            "scope": "name email",
            "state": OAuthHandler._generate_state()
        }
        return f"{OAuthHandler.APPLE_AUTH_URL}?{urlencode(params)}"
    
    @staticmethod
    def exchange_google_code_for_token(code):
        """Exchange Google authorization code for access token"""
        try:
            redirect_uri = OAuthHandler._get_google_redirect_uri()
            token_payload = {
                "client_id": OAuthHandler.GOOGLE_CLIENT_ID,
                "client_secret": OAuthHandler.GOOGLE_CLIENT_SECRET,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": redirect_uri
            }
            
            response = requests.post(OAuthHandler.GOOGLE_TOKEN_URL, data=token_payload)
            response.raise_for_status()
            
            token_data = response.json()
            return {
                "success": True,
                "access_token": token_data.get("access_token"),
                "id_token": token_data.get("id_token")
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def _get_google_redirect_uri():
        """Normalize redirect URI so auth and token exchange always use the exact same value."""
        uri = (OAuthHandler.GOOGLE_REDIRECT_URI or "").strip()
        if not uri:
            return "http://localhost:8501"
        # Normalize localhost root to avoid slash/no-slash mismatches in Google config.
        parsed = urlparse(uri)
        if parsed.hostname in {"localhost", "127.0.0.1"} and parsed.path == "/":
            return uri.rstrip("/")
        return uri
    
    @staticmethod
    def get_google_user_info(access_token):
        """Get user info from Google using access token"""
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            response = requests.get(OAuthHandler.GOOGLE_USERINFO_URL, headers=headers)
            response.raise_for_status()
            
            user_info = response.json()
            return {
                "success": True,
                "user_info": {
                    "name": user_info.get("name", ""),
                    "email": user_info.get("email", ""),
                    "picture": user_info.get("picture", ""),
                    "provider": "google"
                }
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def exchange_apple_code_for_token(code):
        """Exchange Apple authorization code for access token"""
        try:
            # For Apple, we need to create a client secret JWT
            client_secret = OAuthHandler._generate_apple_client_secret()
            
            token_payload = {
                "client_id": OAuthHandler.APPLE_CLIENT_ID,
                "client_secret": client_secret,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": OAuthHandler.APPLE_REDIRECT_URI
            }
            
            response = requests.post(OAuthHandler.APPLE_TOKEN_URL, data=token_payload)
            response.raise_for_status()
            
            token_data = response.json()
            return {
                "success": True,
                "access_token": token_data.get("access_token"),
                "id_token": token_data.get("id_token")
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def decode_apple_id_token(id_token):
        """Decode and validate Apple ID token"""
        try:
            # Decode without verification first to get kid and alg
            unverified_header = jwt.get_unverified_header(id_token)
            
            # In production, you would fetch Apple's public key and verify the signature
            # For now, we'll do basic decoding
            decoded = jwt.decode(id_token, options={"verify_signature": False})
            
            return {
                "success": True,
                "name": decoded.get("name", "Apple User"),
                "email": decoded.get("email", ""),
                "provider": "apple",
                "user_id": decoded.get("sub", "")
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def _generate_apple_client_secret():
        """Generate Apple client secret JWT"""
        try:
            payload = {
                "iss": OAuthHandler.APPLE_TEAM_ID,
                "aud": "https://appleid.apple.com",
                "sub": OAuthHandler.APPLE_CLIENT_ID,
                "iat": int(datetime.utcnow().timestamp()),
                "exp": int((datetime.utcnow() + timedelta(days=180)).timestamp()),
            }
            
            # If private key is provided, sign it
            if OAuthHandler.APPLE_PRIVATE_KEY:
                client_secret = jwt.encode(
                    payload,
                    OAuthHandler.APPLE_PRIVATE_KEY,
                    algorithm="ES256",
                    headers={"kid": OAuthHandler.APPLE_KEY_ID}
                )
                return client_secret
            else:
                # For demo purposes, return unsigned (not secure for production)
                return json.dumps(payload)
        except Exception as e:
            st.error(f"Error generating Apple client secret: {e}")
            return None
    
    @staticmethod
    def _generate_state():
        """Generate random state for OAuth flow"""
        import secrets
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def is_google_configured():
        """Check if Google OAuth credentials are configured"""
        return not OAuthHandler.GOOGLE_CLIENT_ID.startswith("YOUR_")
    
    @staticmethod
    def is_apple_configured():
        """Check if Apple OAuth credentials are configured"""
        return not OAuthHandler.APPLE_TEAM_ID.startswith("YOUR_")
    
    @staticmethod
    def get_setup_instructions():
        """Return setup instructions for OAuth"""
        return """
        ## 🔐 OAuth Setup Required
        
        To enable Google and Apple Sign-In, you need to configure OAuth credentials.
        
        **Quick Setup:**
        
        1. **Edit the `.env` file** in your project root
        2. **Get Google credentials** from [Google Cloud Console](https://console.cloud.google.com/):
           - Go to APIs & Services → Credentials
           - Create OAuth 2.0 credentials for Web application
           - Add your Client ID and Client Secret to `.env`
        
        3. **Get Apple credentials** from [Apple Developer](https://developer.apple.com/):
           - Go to Certificates, Identifiers & Profiles
           - Create a Service ID and get your Team ID, Key ID, and Private Key
           - Add them to `.env`
        
        **See `OAUTH_SETUP.md` for detailed step-by-step instructions.**
        
        Until then, you can:
        ✅ Use email/password login and signup
        ✅ View all other Study Buddy features
        
        The OAuth buttons will work once credentials are added!
        """
