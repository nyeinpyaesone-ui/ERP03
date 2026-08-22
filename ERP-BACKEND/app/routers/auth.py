from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, field_validator, ConfigDict
from datetime import datetime, timezone
from typing import Optional

from app.database import get_db
from app.models import User
from app.auth import (
    verify_password, get_password_hash, create_access_token,
    get_current_user, require_admin
)
from app.services.activity_log import log_activity
from app.services.security_utils import validate_password_strength, constant_time_compare

router = APIRouter()

# Cache dummy password hash at module level to avoid recomputation on every login attempt
# This prevents unnecessary CPU load during brute force attacks
_DUMMY_PASSWORD_HASH = get_password_hash("dummy_password_for_timing")

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: str = "user"
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """
        Validate that a password meets the required strength criteria.
        
        Parameters:
            v (str): Password value to validate.
        
        Returns:
            str: The validated password.
        
        Raises:
            ValueError: If the password does not meet the strength requirements.
        """
        is_valid, error_msg = validate_password_strength(v)
        if not is_valid:
            raise ValueError(error_msg)
        return v

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class UserUpdate(BaseModel):
    """Whitelisted fields for user updates to prevent mass assignment."""
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None
    # Note: 'role' is intentionally excluded to prevent privilege escalation

@router.post("/register", response_model=UserResponse)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user account.
    
    Parameters:
    	user_data (UserCreate): User details and password for the account.
    	db (Session): Database session used to create and persist the user.
    
    Returns:
    	User: The newly registered user.
    
    Raises:
    	HTTPException: If an account with the provided email already exists.
    """
    existing = db.query(User).filter(User.email == user_data.email).first()
    if existing:
        # Use generic message to prevent user enumeration
        raise HTTPException(status_code=400, detail="Registration failed")

    user = User(
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        role=user_data.role
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    log_activity(db, user_id=user.id, action="user_registered", entity_type="user", entity_id=user.id)
    return user

@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Authenticate a user and create an access token.
    
    Parameters:
        form_data (OAuth2PasswordRequestForm): Form containing the user's username and password.
    
    Returns:
        dict: Access token, token type, and authenticated user information.
    
    Raises:
        HTTPException: With status code 401 when the credentials are invalid.
    """
    user = db.query(User).filter(User.email == form_data.username).first()
    
    # Use constant-time comparison to prevent timing attacks
    # Always perform password check even if user doesn't exist
    password_valid = False
    
    if user:
        password_valid = verify_password(form_data.password, user.hashed_password)
    else:
        # Perform dummy verification to maintain constant time
        verify_password(form_data.password, _DUMMY_PASSWORD_HASH)
    
    if not user or not password_valid:
        # Generic error message to prevent user enumeration
        raise HTTPException(status_code=401, detail="Invalid credentials")

    user.last_login = datetime.now(timezone.utc)
    db.commit()

    token = create_access_token({"sub": str(user.id), "role": user.role})
    log_activity(db, user_id=user.id, action="user_login", entity_type="user", entity_id=user.id)

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user
    }

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.get("/users", response_model=list[UserResponse])
def list_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    List users with pagination.
    
    Parameters:
    	skip (int): Number of users to skip before collecting results.
    	limit (int): Maximum number of users to return.
    
    Returns:
    	list[User]: The requested page of users.
    """
    return db.query(User).offset(skip).limit(limit).all()

@router.put("/users/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Update a user's full name, email address, or active status.
    
    Parameters:
        user_data (UserUpdate): Fields to apply to the user.
    
    Returns:
        UserResponse: The updated user.
    
    Raises:
        HTTPException: If the specified user does not exist.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Only update fields that are provided and whitelisted
    update_data = user_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if hasattr(user, key) and key != "id":
            setattr(user, key, value)

    db.commit()
    db.refresh(user)
    log_activity(db, user_id=current_user.id, action="user_updated", entity_type="user", entity_id=user.id)
    return user

