# =====================================================
# DATABASE CONFIGURATION - Connection & Session Setup
# =====================================================
# Ye file FastAPI ko database ke saath connect karta hai
# SQLAlchemy engine aur session manage karta hai
# =====================================================

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# =====================================================
# STEP 1: DATABASE URL CONFIGURATION
# =====================================================
# Database URL format:
# postgresql://username:password@host:port/database_name

# .env file se DATABASE_URL padhna
DATABASE_URL = os.getenv("DATABASE_URL")

# Agar DATABASE_URL nahi hai to default use karo (Development ke liye)
if not DATABASE_URL:
    # Check if running on AWS Lambda (Lambda has writable /tmp only)
    if os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
        DATABASE_URL = "sqlite:////tmp/rag_system.db"
        print("Running on AWS Lambda: Using SQLite in /tmp/")
    else:
        DATABASE_URL = "sqlite:///./test.db"
        print("WARNING: DATABASE_URL not found in .env")
        print("Using SQLite for development: sqlite:///./test.db")
else:
    # Check karo agar PostgreSQL hai ya SQLite
    if "postgresql" in DATABASE_URL:
        print(f"Using PostgreSQL: {DATABASE_URL.split('@')[1]}")  # Server address show karo
    else:
        print(f"Using SQLite for development: {DATABASE_URL}")  # SQLite path show karo

# =====================================================
# STEP 2: CREATE DATABASE ENGINE
# =====================================================
# Engine = Database ke saath connection pool
# Connection pool = Kuch connections ready rakhte hain (reuse ke liye)

# SQLAlchemy engine create karo
_engine_kwargs = {}
if DATABASE_URL.startswith("sqlite"):
    _engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(
    DATABASE_URL,
    **_engine_kwargs,
    # echo=True,  # SQL queries print kare (debugging ke liye)
    # pool_pre_ping=True,  # Connection check kare query se pehle
    # pool_size=5,  # Kitne connections ready rakhne hain
    # max_overflow=10,  # Zyada connections banane ka permission
)

# Connection pool explanation:
# - Pool = Ready connections ki queue
# - Pre-ping = Connection active hai check karna
# - Size = Base connections
# - Overflow = Extra connections ager zarurat ho

# =====================================================
# STEP 3: CREATE SESSION FACTORY
# =====================================================
# SessionLocal = Session banane ke liye factory
# Har API request ko ek session chahiye

SessionLocal = sessionmaker(
    autocommit=False,  # Manually commit karna (auto nahi)
    autoflush=False,   # Manually flush karna (auto nahi)
    bind=engine        # Kaunse engine se connect karna
)

# =====================================================
# STEP 4: DATABASE DEPENDENCY (FastAPI ke liye)
# =====================================================
# Ye function FastAPI ke dependency injection mein use hota hai
# Har endpoint ko database session dena

_db_initialized = False

def ensure_tables():
    """Ensure tables exist - call before first DB usage"""
    global _db_initialized
    if not _db_initialized:
        from backend.models import Base
        Base.metadata.create_all(bind=engine)
        _db_initialized = True

def get_db() -> Session:
    """
    Database session provide karna FastAPI endpoints ko

    Ye function har API request ke liye ek session banata hai
    aur request khatam hone ke baad close karta hai

    Usage in FastAPI:
    ────────────────
    @app.get("/users")
    def get_users(db: Session = Depends(get_db)):
        return db.query(User).all()

    FastAPI automatically:
    1. get_db() call karega
    2. Session provide karega
    3. Route execute karega
    4. finally block mein session close karega
    """
    ensure_tables()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# =====================================================
# STEP 5: DATABASE INITIALIZATION
# =====================================================
# Base.metadata.create_all(engine)
# Ye line database mein sabhi tables create karega

def init_db():
    """
    Database mein tables create karna

    Ye function jab app start hota hai tab call karna
    Models se table structure define hote hain

    Usage:
    ──────
    # main.py mein:
    from backend.database import init_db

    @app.on_event("startup")
    def startup():
        init_db()
    """
    from backend.models import Base
    Base.metadata.create_all(bind=engine)
    print(f"Database initialized: {list(Base.metadata.tables.keys())}")

# =====================================================
# DATABASE EXPLANATION
# =====================================================
"""
SQLAlchemy Architecture:

┌──────────────────────────────────────┐
│      FastAPI Application             │
│                                      │
│  @app.get("/users")                  │
│  def get_users(db: Session = ...):   │ ← get_db() use
│      return db.query(User).all()     │
└──────────────┬───────────────────────┘
               │
               ↓ (Depends - Dependency Injection)
        ┌──────────────┐
        │  get_db()    │ ← SessionLocal banata hai
        └──────┬───────┘
               │
               ↓
        ┌──────────────┐
        │ SessionLocal │ ← Session factory
        │ (Configured) │
        └──────┬───────┘
               │
               ↓
        ┌──────────────┐
        │   Engine     │ ← Connection pool
        └──────┬───────┘
               │
               ↓
        ┌──────────────┐
        │  PostgreSQL  │ ← Actual Database
        │  (or SQLite) │
        └──────────────┘


Session Lifecycle:
──────────────────

1. Request aati hai
   ↓
2. FastAPI get_db() call karta hai
   ↓
3. SessionLocal se naya Session banata hai
   ↓
4. Database se connection pool mein se ek connection leta hai
   ↓
5. Endpoint ko Session deta hai
   ↓
6. Endpoint database queries karta hai
   ↓
7. Request complete hota hai
   ↓
8. finally block mein session.close() hota hai
   ↓
9. Connection pool mein connection wapas jata hai


Pool Concept:
─────────────

Connection Pool = Restaurant ki waiting line

Without Pool:
├─ Customer aata hai
├─ Chair laana padta hai (slow)
├─ Customer baithta hai
└─ Request handle hota hai

With Pool (5 chairs pre-made):
├─ Customer aata hai
├─ Ready chair mil jata hai (fast!)
├─ Customer baithta hai
└─ Request handle hota hai

Benefits:
- Faster response time
- Reduced overhead
- Better resource management
"""

# =====================================================
# DATABASE OPERATIONS CHEATSHEET
# =====================================================
"""
# Create:
──────
db.add(new_user)
db.commit()
db.refresh(new_user)

# Read:
──────
user = db.query(User).filter(User.id == 1).first()
users = db.query(User).all()

# Update:
────────
user = db.query(User).filter(User.id == 1).first()
user.name = "New Name"
db.commit()

# Delete:
────────
user = db.query(User).filter(User.id == 1).first()
db.delete(user)
db.commit()
"""
