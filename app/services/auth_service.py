"""
Authentication Service
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database.models import User
from app.config import settings
from app.schemas.user_schema import TokenData

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify password against hash
    
    Args:
        plain_password: Plain text password
        hashed_password: Hashed password
        
    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash password
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password
    """
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT access token
    
    Args:
        data: Data to encode in token
        expires_delta: Token expiration time delta
        
    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    return encoded_jwt


def decode_access_token(token: str) -> Optional[TokenData]:
    """
    Decode JWT access token
    
    Args:
        token: JWT token
        
    Returns:
        TokenData if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        username: str = payload.get("username")
        
        if user_id is None:
            return None
        
        return TokenData(user_id=user_id, username=username)
    except JWTError:
        return None


async def authenticate_user(
    db: AsyncSession,
    username: str,
    password: str
) -> Optional[User]:
    """
    Authenticate user by username and password
    
    Args:
        db: Database session
        username: Username
        password: Password
        
    Returns:
        User if authenticated, None otherwise
    """
    result = await db.execute(
        select(User).where(User.username == username)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        return None
    
    if not verify_password(password, user.hashed_password):
        return None
    
    return user


async def get_user_by_id(db: AsyncSession, user_id: str) -> Optional[User]:
    """
    Get user by ID
    
    Args:
        db: Database session
        user_id: User ID
        
    Returns:
        User if found, None otherwise
    """
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    return result.scalar_one_or_none()


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """
    Get user by email
    
    Args:
        db: Database session
        email: Email address
        
    Returns:
        User if found, None otherwise
    """
    result = await db.execute(
        select(User).where(User.email == email)
    )
    return result.scalar_one_or_none()


async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
    """
    Get user by username
    
    Args:
        db: Database session
        username: Username
        
    Returns:
        User if found, None otherwise
    """
    result = await db.execute(
        select(User).where(User.username == username)
    )
    return result.scalar_one_or_none()