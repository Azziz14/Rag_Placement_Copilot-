"""Authentication service interacting with Supabase Auth.
"""

from typing import Dict, Any, Optional
import jwt
from supabase import create_client, Client

from app.core.config import settings

# Initialize Supabase client
# In fallback modes where settings are default placeholders, we handle errors gracefully
supabase_client: Optional[Client] = None
try:
    if settings.SUPABASE_URL and settings.SUPABASE_KEY and "your-project" not in settings.SUPABASE_URL:
        supabase_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
except Exception:
    # Fail silently or log in development, will fallback to dummy/offline behavior
    pass


class AuthService:
    """Service to handle user registration, login, and token verification."""

    @staticmethod
    def get_client() -> Client:
        """Helper to get or initialize Supabase client dynamically."""
        global supabase_client
        if supabase_client is None:
            supabase_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        return supabase_client

    def sign_up(self, email: str, password: str, full_name: Optional[str] = None) -> Dict[str, Any]:
        """Registers a new user in Supabase auth system."""
        client = self.get_client()
        options = {}
        if full_name:
            options["data"] = {"full_name": full_name}

        response = client.auth.sign_up({
            "email": email,
            "password": password,
            "options": options
        })
        return response

    def sign_in(self, email: str, password: str) -> Dict[str, Any]:
        """Logs in a user in Supabase auth system."""
        client = self.get_client()
        response = client.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        return response

    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verifies Supabase JWT token.
        
        Attempts local signature verification first, falling back to Supabase API check.
        """
        # 1. Attempt offline decode using SUPABASE_JWT_SECRET
        if settings.SUPABASE_JWT_SECRET and "your-jwt-secret" not in settings.SUPABASE_JWT_SECRET:
            try:
                payload = jwt.decode(
                    token,
                    settings.SUPABASE_JWT_SECRET,
                    algorithms=["HS256"],
                    audience="authenticated"
                )
                return payload
            except jwt.ExpiredSignatureError:
                raise ValueError("Token has expired")
            except jwt.InvalidTokenError:
                # Fallback to API verification in case of secret mismatch/local testing
                pass

        # 2. Fallback to API verification via Supabase Client
        try:
            client = self.get_client()
            user_response = client.auth.get_user(token)
            if not user_response or not user_response.user:
                raise ValueError("Invalid user token from Supabase Auth")
            
            user = user_response.user
            # Structure return dict similar to JWT payload
            return {
                "sub": user.id,
                "email": user.email,
                "user_metadata": user.user_metadata or {}
            }
        except Exception as e:
            raise ValueError(f"Token verification failed: {str(e)}")


auth_service = AuthService()
