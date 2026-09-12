from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, UserRole, Notification
from app.schemas import UserRegister, UserLogin, UserResponse, UserUpdate, Token
from app.auth import get_password_hash, verify_password, create_access_token, get_current_active_user
from app.config import settings

router = APIRouter(prefix="/api/users", tags=["Users & Authentication"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user_in: UserRegister, db: Session = Depends(get_db)):
    """Register a new user (Farmer, Equipment Owner, or Laborer)."""
    existing_user = db.query(User).filter(User.email == user_in.email.lower().strip()).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists"
        )
    
    hashed_pwd = get_password_hash(user_in.password)
    new_user = User(
        name=user_in.name.strip(),
        email=user_in.email.lower().strip(),
        password_hash=hashed_pwd,
        role=user_in.role.lower().strip(),
        phone=user_in.phone.strip() if user_in.phone else None,
        address=user_in.address.strip() if user_in.address else None,
        is_active=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Create welcome notification
    welcome_notif = Notification(
        user_id=new_user.id,
        message=f"Welcome to KhetSaathi, {new_user.name}! Your account has been created as {new_user.role.capitalize()}."
    )
    db.add(welcome_notif)
    db.commit()

    return new_user

@router.post("/login", response_model=Token)
def login_for_access_token(
    user_in: UserLogin,
    db: Session = Depends(get_db)
):
    """Authenticate user with email and password, returning JWT access token."""
    user = db.query(User).filter(User.email == user_in.email.lower().strip()).first()
    if not user or not verify_password(user_in.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated. Please contact support."
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role, "id": user.id},
        expires_delta=access_token_expires
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@router.get("/me", response_model=UserResponse)
def get_current_user_profile(current_user: User = Depends(get_current_active_user)):
    """Retrieve the profile of the currently authenticated user."""
    return current_user

@router.put("/me", response_model=UserResponse)
def update_current_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update profile information of the currently authenticated user."""
    if user_update.name is not None:
        current_user.name = user_update.name.strip()
    if user_update.phone is not None:
        current_user.phone = user_update.phone.strip()
    if user_update.address is not None:
        current_user.address = user_update.address.strip()

    db.commit()
    db.refresh(current_user)
    return current_user

@router.get("/{user_id}", response_model=UserResponse)
def get_user_by_id(user_id: int, db: Session = Depends(get_db)):
    """Retrieve public profile for a specific user ID."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user
