# =====================================================
# AUTHENTICATION ROUTES
# =====================================================
# Ye file user registration aur login handle karta hai
# Password hashing, JWT tokens, security - sab yahan
# =====================================================

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta
import os

# Local imports
from backend.database import get_db
from backend.models import User
from backend.schemas import UserCreate, UserLogin, UserResponse, Token
from backend.utils.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_token
)
from backend.dependencies import get_current_user

# =====================================================
# ROUTER SETUP
# =====================================================
# Router = Group of related routes
# prefix = "/auth" matlab sab routes /auth/... se start honge
# tags = Swagger docs mein grouping ke liye

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
    responses={404: {"description": "Not found"}}
)

# =====================================================
# ROUTE 1: USER REGISTRATION
# =====================================================

@router.post("/register", response_model=UserResponse)
async def register(
    user_data: UserCreate,  # Frontend se request
    db: Session = Depends(get_db)  # Database session
):
    """
    New User Registration

    Frontend se user data aata hai:
    - Email (unique hona chahiye)
    - Name
    - Password (hashed hoga database mein)

    Response:
    - User info (password nahi)

    Errors:
    - 400: Email already exists
    - 422: Invalid data
    """

    try:
        # Pehle check karo agar email pehle se exist karta hai
        existing_user = db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            # Email already exists error
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Password hash karo (plaintext kabhi store nahi karte!)
        # hash_password = ek function jo password ko encrypted form mein convert karta hai
        # Even hum password dekh nahi sakte database mein (one-way encryption)
        hashed_password = hash_password(user_data.password)

        # Naya user create karo
        new_user = User(
            email=user_data.email,
            name=user_data.name,
            password_hash=hashed_password,
            created_at=datetime.utcnow()
        )

        # Database mein add karo
        db.add(new_user)
        db.commit()  # Changes save karo
        db.refresh(new_user)  # Fresh data pull karo

        # Success response return karo
        return new_user

    except IntegrityError:
        # Database integrity error (duplicate key, etc)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Registration failed. Email might already exist."
        )

    except Exception as e:
        # Koi unexpected error
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration error: {str(e)}"
        )


# =====================================================
# ROUTE 2: USER LOGIN
# =====================================================

@router.post("/login", response_model=Token)
async def login(
    login_data: UserLogin,  # Email aur password
    db: Session = Depends(get_db)
):
    """
    User Login

    Frontend se email aur password aata hai

    Process:
    1. Email se user dhundho database mein
    2. Password verify karo (hash compare)
    3. JWT token generate karo
    4. Token return karo

    JWT Token = Security token
    - Frontend store karta hai
    - Har request mein bhejta hai
    - Backend verify karta hai
    - Token expire hota hai (security)

    Errors:
    - 401: Invalid email/password
    """

    # Email se user dhundo
    user = db.query(User).filter(User.email == login_data.email).first()

    # Agar user nahi milya ya password galat hai
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Password verify karo (hash compare)
    # verify_password = ek function jo plaintext password ko hash se compare karta hai
    if not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Password sahi hai! JWT token generate karo
    access_token = create_access_token(
        data={"sub": str(user.id)}  # Token mein user ID store karo
    )

    # Last login time update karo
    user.last_login = datetime.utcnow()
    db.commit()

    # Token return karo
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }


# =====================================================
# ROUTE 3: GET CURRENT USER
# =====================================================

@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user)
):
    """
    Get Current User Info

    Frontend token bhejta hai → Backend current user return karta hai

    Protected endpoint - Token mandatory hai!

    Usage:
    ──────
    Header: Authorization: Bearer <token>
    Response: User info

    Errors:
    - 401: Token missing/invalid
    """
    return current_user


# =====================================================
# DOCUMENTATION COMMENTS
# =====================================================
"""
AUTHENTICATION FLOW:

1. REGISTRATION:
   ───────────────
   Frontend                          Backend
      │                                │
      ├─ POST /auth/register ────────→ │
      │  {email, name, password}      │
      │                                ├─ Email check karo
      │                                ├─ Password hash karo
      │                                ├─ User create karo
      │                                │
      │  ← {user_info}               │
      │                                │

2. LOGIN:
   ───────
   Frontend                          Backend
      │                                │
      ├─ POST /auth/login ───────────→ │
      │  {email, password}            │
      │                                ├─ Email find karo
      │                                ├─ Password verify karo
      │                                ├─ JWT token generate karo
      │                                │
      │  ← {access_token, user}      │
      │                                │

3. PROTECTED REQUESTS:
   ────────────────────
   Frontend                          Backend
      │                                │
      ├─ GET /auth/me ───────────────→ │
      │  Header: Authorization: Bearer │
      │  <token>                       │
      │                                ├─ Token verify karo
      │                                ├─ User ID extract karo
      │                                ├─ User fetch karo
      │                                │
      │  ← {user_info}               │
      │                                │


PASSWORD HASHING:

Plain Password:  "MyPassword123"
                    ↓ (hash function)
Hashed Password: "$2b$12$N9qo8uLOickgxxx..."
                    (one-way encryption)

Database mein hashed password store hota hai
Jab login hota hai:
- Entered password: "MyPassword123"
- Hash karo: "$2b$12$N9qo8uLOickgxxx..."
- Database ke hash se compare karo
- Match = Login successful!


JWT TOKEN:

Token mein kya hota hai:
- User ID (encrypted)
- Issue time
- Expiration time
- Signature

Token lifetime: 1 hour (configurable)
Jab expire hota hai → Refresh token use karna padta hai


SECURITY CHECKLIST:
✓ Password hashing (plaintext nahi)
✓ JWT tokens (session-based nahi)
✓ Token expiration
✓ HTTPS recommended (production mein)
✓ Rate limiting (brute force protection)
"""
