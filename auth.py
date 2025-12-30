"""
Authentication middleware and helpers for LLM Eval Playground.
Uses Supabase Auth for user management.
"""

import os
from typing import Optional, Dict, Any
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from dotenv import load_dotenv

load_dotenv()

# Supabase JWT configuration
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET", "")

# HTTP Bearer security scheme
security = HTTPBearer(auto_error=False)


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify a Supabase JWT token and return the payload.
    Returns None if token is invalid.
    """
    try:
        # Supabase uses HS256 algorithm
        payload = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated"
        )
        return payload
    except JWTError as e:
        print(f"JWT verification failed: {e}")
        return None


def get_user_id_from_token(token: str) -> Optional[str]:
    """Extract user ID from a verified token."""
    payload = verify_token(token)
    if payload:
        return payload.get("sub")
    return None


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Dict[str, Any]:
    """
    Dependency to get the current authenticated user from the request.
    Raises HTTPException 401 if not authenticated.
    """
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    token = credentials.credentials
    payload = verify_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return {
        "user_id": payload.get("sub"),
        "email": payload.get("email"),
        "role": payload.get("role", "authenticated")
    }


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[Dict[str, Any]]:
    """
    Dependency to optionally get the current user.
    Returns None if not authenticated (doesn't raise exception).
    """
    if not credentials:
        return None
    
    token = credentials.credentials
    payload = verify_token(token)
    
    if not payload:
        return None
    
    return {
        "user_id": payload.get("sub"),
        "email": payload.get("email"),
        "role": payload.get("role", "authenticated")
    }


# For development/demo mode without auth
# Default to demo mode if no JWT secret is configured
DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() == "true" or not SUPABASE_JWT_SECRET
DEMO_USER_ID = "00000000-0000-0000-0000-000000000001"  # Valid UUID format for demo user


async def get_current_user_or_demo(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Dict[str, Any]:
    """
    Get current user or return demo user if in demo mode.
    Useful for local development without auth setup.
    """
    if DEMO_MODE:
        return {
            "user_id": DEMO_USER_ID,
            "email": "demo@example.com",
            "role": "authenticated"
        }
    
    return await get_current_user(credentials)

