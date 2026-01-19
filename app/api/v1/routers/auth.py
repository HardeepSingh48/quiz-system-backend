"""Authentication router"""

from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.auth import UserRegister, UserLogin, TokenResponse, RefreshTokenRequest, UserResponse
from app.services.auth_service import AuthService
from app.api.v1.deps import get_auth_service, get_current_user
from app.db.base import User
from app.core.config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Register a new user
    
    SECURITY: Role is ALWAYS 'user' - admins must be created via seed script
    
    Args:
        user_data: User registration data (without role)
        auth_service: Authentication service
        
    Returns:
        Created user with role='user'
    """
    user = await auth_service.register(
        email=user_data.email,
        username=user_data.username,
        password=user_data.password
    )
    return user


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: UserLogin,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Login user and return JWT tokens
    
    Args:
        credentials: Login credentials
        auth_service: Authentication service
        
    Returns:
        Access and refresh tokens
    """
    access_token, refresh_token, expires_in = await auth_service.login(
        email=credentials.email,
        password=credentials.password
    )
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=expires_in
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    token_request: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Refresh access token using refresh token (with rotation)
    
    Args:
        token_request: Refresh token
        auth_service: Authentication service
        
    Returns:
        New access and refresh tokens
    """
    access_token, refresh_token, expires_in = await auth_service.refresh_tokens(
        refresh_token=token_request.refresh_token
    )
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=expires_in
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Logout user by revoking all refresh tokens
    
    Args:
        current_user: Current authenticated user
        auth_service: Authentication service
    """
    await auth_service.logout(current_user.id)
    return None


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get current user information
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User information
    """
    return current_user
