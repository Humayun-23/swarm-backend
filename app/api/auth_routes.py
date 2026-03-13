"""
Authentication Routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.database.models import User
from app.schemas.user_schema import (
    UserCreate,
    UserResponse,
    UserLogin,
    Token
)
from app.services.auth_service import (
    get_password_hash,
    authenticate_user,
    create_access_token,
    get_user_by_email,
    get_user_by_username
)
from app.dependencies import get_current_active_user
from app.utils.logger import logger


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user
    
    Args:
        user_data: User registration data
        db: Database session
        
    Returns:
        Created user
    """
    # Check if email already exists
    existing_user = await get_user_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if username already exists
    existing_username = await get_user_by_username(db, user_data.username)
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    
    new_user = User(
        email=user_data.email,
        username=user_data.username,
        full_name=user_data.full_name,
        hashed_password=hashed_password
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    logger.info(f"New user registered: {new_user.username}")
    
    return new_user


@router.post("/login", response_model=Token)
async def login(
    login_data: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """
    Login user and return access token
    
    Args:
        login_data: Login credentials
        db: Database session
        
    Returns:
        Access token
    """
    # Authenticate user
    user = await authenticate_user(db, login_data.username, login_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token = create_access_token(
        data={"sub": str(user.id), "username": user.username}
    )
    
    logger.info(f"User logged in: {user.username}")
    
    return Token(access_token=access_token, token_type="bearer")


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current user information
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User information
    """
    return current_user


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_active_user)):
    """
    Logout user (client-side token removal)
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Success message
    """
    logger.info(f"User logged out: {current_user.username}")
    
    return {"message": "Successfully logged out"}