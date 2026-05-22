# =====================================================
# DEPENDENCIES - FastAPI Dependency Injection
# =====================================================
# Ye file shared dependencies define karta hai
# Jo multiple routes mein use hoti hain
#
# Dependency Injection kya hota hai?
# ─────────────────────────────────────
# Jaise:  @router.get("/profile")
#         def profile(user = Depends(get_current_user)):
#             return user
#
# Depends = FastAPI automatically function call karta hai
# get_current_user = Authentication check karta hai
# =====================================================

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import User
from backend.utils.security import decode_token

# =====================================================
# JWT TOKEN SCHEME SETUP
# =====================================================
# OAuth2PasswordBearer = Authorization header se token nikalna
#
# Jab user login karta hai:
# 1. Backend JWT token deta hai
# 2. Frontend token store karta hai (localStorage)
# 3. Har request mein header mein bhejta hai:
#    Authorization: Bearer eyJhbGciOiJIUzI1NiIsIn...
# 4. OAuth2PasswordBearer header padhta hai
# 5. Token nikalta hai
#
# tokenUrl = Login endpoint (docs mein link ke liye)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# =====================================================
# GET CURRENT USER - Main Auth Dependency
# =====================================================

def get_current_user(
    token: str = Depends(oauth2_scheme),  # Auto header se token nikalo
    db: Session = Depends(get_db)         # Database session
) -> User:
    """
    Protected routes ke liye current user fetch karna

    Ye function automatically:
    1. Authorization header se token nikalta hai
    2. JWT token decode karta hai
    3. User ID nikalta hai
    4. Database se user fetch karta hai
    5. User return karta hai (ya error throw karta hai)

    Kaise use karte hain:
    ─────────────────────
    from backend.dependencies import get_current_user

    @router.get("/my-documents")
    async def my_documents(
        current_user: User = Depends(get_current_user)
    ):
        # current_user = logged in user (auto)
        return {"name": current_user.name}

    Errors:
    ───────
    - 401: Token missing (header mein nahi diya)
    - 401: Token invalid (galat token)
    - 401: Token expired (1 ghante baad expire)
    - 401: User not found
    - 403: User inactive
    """

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # JWT token decode karo
        # Token mein user ID chhupa hua hota hai (encrypted)
        payload = decode_token(token)

        # Token se user ID nikalo
        # "sub" = subject (token kiske liye hai)
        user_id_str: str = payload.get("sub")

        if user_id_str is None:
            # Token mein user ID hi nahi!
            raise credentials_exception

        user_id = int(user_id_str)

    except ValueError:
        # int() conversion fail hua
        raise credentials_exception
    except HTTPException:
        # Already HTTPException hai, re-raise karo
        raise credentials_exception
    except Exception:
        # decode_token fail hua:
        # - Expired token (time limit khatam)
        # - Invalid signature (tampered token)
        # - Malformed token (galat format)
        raise credentials_exception

    # Database se user fetch karo by ID
    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive. Contact support."
        )

    return user


# =====================================================
# OPTIONAL: GET CURRENT USER (Token Optional)
# =====================================================
# Ye sirf tab use hota hai jab token optional ho
# (Public endpoints jo login users ke liye extra info dete hain)

def get_current_user_optional(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User | None:
    """
    Optional auth dependency

    Agar token hai → User return karo
    Agar token nahi hai → None return karo (error nahi)

    Useful for endpoints jo both:
    - Anonymous users handle kare
    - Logged in users ke liye extra data dena
    """
    try:
        return get_current_user(token=token, db=db)
    except HTTPException:
        return None
