from typing import Dict, Any, Optional
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """
    Mock authentication function for testing
    In production, this would validate JWT tokens
    """
    # For testing purposes, return a mock user
    return {
        "id": 1,
        "username": "test_user",
        "email": "test@example.com",
        "role": "admin",
        "company_id": 1
    }

async def get_current_active_user(current_user: Dict = Depends(get_current_user)) -> Dict[str, Any]:
    """Get current active user"""
    return current_user

def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify JWT token (mock implementation)
    """
    if token.startswith("Bearer "):
        token = token[7:]
    
    # Mock verification - in production, use proper JWT validation
    if token and len(token) > 10:
        return {
            "id": 1,
            "username": "test_user",
            "role": "admin"
        }
    return None
