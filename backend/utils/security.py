# =====================================================
# SECURITY UTILITIES
# =====================================================
# Password hashing, JWT tokens, encryption
# Production-ready security functions
# =====================================================

from datetime import datetime, timedelta, timezone
from typing import Optional
import os
from dotenv import load_dotenv

# JWT libraries
from jwt import encode, decode, ExpiredSignatureError, InvalidTokenError

# Password hashing - Direct bcrypt (no passlib complexity)
import bcrypt

load_dotenv()

# =====================================================
# JWT CONFIGURATION
# =====================================================
# Secret key = Signature ke liye (token ko verify karne ke liye)
# Ye key kisi ko nahi deना! (production mein random strong key use karo)

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"  # Token signing algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # Token 1 hour ke liye valid


# =====================================================
# FUNCTION 1: HASH PASSWORD
# =====================================================

def hash_password(password: str) -> str:
    """
    Bcrypt se password hash karo - simple, proven approach
    """
    # Bcrypt 72-byte limit ke liye truncate
    password_bytes = password.encode('utf-8')[:72]

    # Salt generate karke hash karo
    salt = bcrypt.gensalt(rounds=10)
    hashed = bcrypt.hashpw(password_bytes, salt)

    # Return as string
    return hashed.decode('utf-8')


# =====================================================
# FUNCTION 2: VERIFY PASSWORD
# =====================================================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Bcrypt se password verify karo
    """
    try:
        password_bytes = plain_password.encode('utf-8')[:72]
        hashed_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception as e:
        print(f"Password verification error: {str(e)}")
        return False


# =====================================================
# FUNCTION 3: CREATE JWT TOKEN
# =====================================================

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    JWT Access Token generate karo

    JWT Token structure:
    ─────────────────────
    Header:    {alg: "HS256", typ: "JWT"}
    Payload:   {sub: "user_id", exp: timestamp, iat: timestamp}
    Signature: HMACSHA256(header + payload, secret_key)

    Complete token:
    ─────────────────
    eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.
    eyJzdWIiOiIxIiwiZXhwIjoxNjMxNTI3NjAwfQ.
    NjU3OGU5MWQzNTU3OWYxNmU4ZTcwZTQ4NQ

    Usage:
    ──────
    token = create_access_token({"sub": "1"})
    # Frontend store karega localStorage/cookies mein
    # Har request mein bhejega

    Token lifetime:
    ────────────────
    Default: 1 hour
    Custom: Pass expires_delta parameter
    """

    to_encode = data.copy()  # Data ka copy banao (original modify nahi karna)

    # Expiration time set karo
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        # Default = 1 hour
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    # Token mein expiration time add karo
    to_encode.update({"exp": expire})

    # JWT token encode karo (sign karo)
    # encode = data + secret key se token banao
    encoded_jwt = encode(
        to_encode,           # Data (user info, expiration)
        SECRET_KEY,          # Secret key (signature ke liye)
        algorithm=ALGORITHM  # HS256 algorithm
    )

    return encoded_jwt


# =====================================================
# FUNCTION 4: DECODE & VERIFY JWT TOKEN
# =====================================================

def decode_token(token: str) -> dict:
    """
    JWT Token ko verify aur decode karo

    Process:
    ────────
    1. Token signature verify karo (SECRET_KEY se)
    2. Token expire hua ya nahi check karo
    3. Data extract karo (user ID, etc)

    Usage:
    ──────
    payload = decode_token(token)
    user_id = payload.get("sub")

    Errors:
    ───────
    - ExpiredSignatureError: Token expire ho gaya
    - InvalidTokenError: Token invalid hai (tampered with)
    """

    try:
        # Token decode karo
        # token = Frontend se aaya JWT token
        # SECRET_KEY = Signature verify karne ke liye
        # ALGORITHM = Kaunsa algorithm use hua
        payload = decode(
            token,           # JWT token
            SECRET_KEY,      # Secret key (verify karne ke liye)
            algorithms=[ALGORITHM]  # Allowed algorithms
        )

        # Payload successful decode hua
        # Isme "sub" (user ID) hona chahiye
        user_id: str = payload.get("sub")

        if user_id is None:
            raise InvalidTokenError("No subject in token")

        return payload

    except ExpiredSignatureError:
        # Token expire ho gaya
        # Frontend ko naya token lena padega
        print("Token has expired")
        raise ValueError("Token has expired")

    except InvalidTokenError as e:
        # Token invalid hai
        # Signature match nahi hua ya corrupted hai
        print(f"Invalid token: {str(e)}")
        raise ValueError(f"Invalid token: {str(e)}")

    except Exception as e:
        # Koi unexpected error
        print(f"Token verification error: {str(e)}")
        raise ValueError(f"Token verification failed: {str(e)}")


# =====================================================
# OPTIONAL: PASSWORD STRENGTH CHECK
# =====================================================

def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Password strength validation

    Checks:
    ──────
    ✓ Minimum 8 characters
    ✓ At least one uppercase letter
    ✓ At least one lowercase letter
    ✓ At least one digit
    ✓ At least one special character (optional)

    Returns:
    ───────
    (is_valid, message)
    """

    if len(password) < 8:
        return False, "Password must be at least 8 characters"

    if not any(char.isupper() for char in password):
        return False, "Password must contain at least one uppercase letter"

    if not any(char.islower() for char in password):
        return False, "Password must contain at least one lowercase letter"

    if not any(char.isdigit() for char in password):
        return False, "Password must contain at least one digit"

    return True, "Password is strong"


# =====================================================
# DOCUMENTATION: SECURITY FLOW
# =====================================================
"""
SECURITY IMPLEMENTATION:

1. REGISTRATION:
   ───────────────
   User enters: "MyPassword123"
                ↓ (hash_password)
   Database:   "$2b$12$N9qo8uLOickgxxx..."
   ✓ Plaintext password kabhi save nahi hota!


2. LOGIN:
   ───────
   User enters:    "MyPassword123"
   Database has:   "$2b$12$N9qo8uLOickgxxx..."
                ↓ (verify_password)
   Result:     True ✓
                ↓ (create_access_token)
   JWT Token:  "eyJhbGciOiJIUzI1NiIs..."
   Send to:    Frontend


3. PROTECTED REQUESTS:
   ────────────────────
   Frontend sends:
   Header: Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
                ↓ (decode_token)
   Backend verifies:
   - Signature valid?
   - Token expired?
   - User exists?
                ↓
   Grant access ✓


PASSWORD HASHING BENEFITS:
──────────────────────────
1. One-way: Hash se password nahi nikla ja sakta
2. Bcrypt slow: Brute force mein time lagega (security)
3. Salt included: Same password different hash har baar
4. Industry standard: Security researchers approve


JWT TOKEN BENEFITS:
────────────────────
1. Stateless: Server pe session store nahi karna
2. Secure: Signature se verify kar sakte ho
3. Expiring: Token expire hota hai (time-limited)
4. Mobile-friendly: Cookies ki zarurat nahi


SECURITY CHECKLIST:
────────────────────
✓ Password hashing (bcrypt)
✓ JWT tokens
✓ Token expiration
✓ HTTPS required (production)
✓ Secure cookies (httpOnly, secure flags)
✓ Rate limiting needed
✓ CORS configured
"""
