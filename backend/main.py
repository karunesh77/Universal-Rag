# =====================================================
# RAG System - Backend Main File
# Ye file aapke application ka dil hai
# =====================================================

# STEP 1: Zaruri libraries import karo
# FastAPI - ye ek framework hai jo web server banata hai
# jaise Express (Node.js mein) ya Flask (Python mein)
from fastapi import FastAPI

# CORS - ye security ke liye use hota hai
# taaki frontend (React) se backend ko requests bhej sake
from fastapi.middleware.cors import CORSMiddleware

# python-dotenv - .env file se variables padne ke liye
# .env file mein API keys, passwords, etc store hote hain
from dotenv import load_dotenv

# OS - operating system ke saath kaam karne ke liye
# jaise environment variables read karna
import os

# Database initialization - tables create karne ke liye
from backend.database import init_db

# Routes - API endpoints
from backend.routes.auth import router as auth_router
from backend.routes.documents import router as documents_router
from backend.routes.queries import router as queries_router

# Load karo .env file ko (agar exist kare)
load_dotenv()

# =====================================================
# STEP 2: FastAPI Application banao
# =====================================================
# FastAPI - ye ek object banata hai jo aapka pura application handle karega
# Jab koi user browser mein request karega to ye object answer dega
app = FastAPI(
    title="Universal RAG System API",  # API ka naam
    description="A comprehensive Retrieval Augmented Generation system",  # Description
    version="1.0.0"  # Version number
)

# =====================================================
# STEP 3: CORS Configuration - Security Setup
# =====================================================
# CORS = Cross-Origin Resource Sharing
# Matlab: Frontend (React) aur Backend (FastAPI) alag ports par hote hain
# CORS kehta hai: "Hey, React ko permission do mere saath baat karne ka"

# Environment variables se origins le (agar nahi to default set karo)
origins = os.getenv("CORS_ORIGINS", "").split(",")

# Agar CORS_ORIGINS variable nahi hai to ye default values use karo
if not origins or origins == [""]:
    origins = [
        "http://localhost:3000",   # Frontend ka default port (Vite)
        "http://localhost:5173"    # Alternative Vite port
    ]

# Ab CORS middleware add karo
# Middleware = ek layer jo har request/response ke beech mein aata hai
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,           # Kaunse websites ko access dena hai
    allow_credentials=True,          # Cookies/credentials allow karo
    allow_methods=["*"],             # Saare HTTP methods allow karo (GET, POST, etc)
    allow_headers=["*"],             # Saare headers allow karo
)

# =====================================================
# STEP 3.6: INCLUDE ROUTERS - API Routes
# =====================================================
# Router = Related endpoints ka group
# include_router = Router ko app mein add karna

# Authentication routes
# /auth/register, /auth/login, /auth/me
app.include_router(auth_router)

# Document routes
# /documents/upload, /documents/, /documents/{id}, /documents/{id}/process
app.include_router(documents_router)

# Query routes (RAG)
# /queries/ask, /queries/, /queries/{id}, /queries/{id}/bookmark
app.include_router(queries_router)

# =====================================================
# STEP 3.7: STARTUP EVENT - Database Initialize
# =====================================================
# Jab app start hota hai, database tables create karna
# @app.on_event("startup") = jab server start ho

@app.on_event("startup")
async def startup_event():
    """
    App startup par run hone wala function
    Database ko initialize karta hai (tables create karta hai)

    Startup flow:
    1. FastAPI server start hota hai
    2. Ye function automatically call hota hai
    3. Database tables create hote hain
    4. Ab API requests handle karne ready
    """
    try:
        init_db()
        print("[OK] Database initialization completed!")
    except Exception as e:
        print(f"[ERROR] Database initialization failed: {str(e)}")
        raise e

# =====================================================
# STEP 4: API Endpoints banao
# =====================================================
# Endpoint = ek URL address jahan par user request kar sakta hai
# Jaise: GET /health, POST /upload, etc

# Endpoint 1: Root endpoint (Welcome message)
@app.get("/")  # GET request ke liye
async def root():  # async = non-blocking (alag request ke liye wait nahi karna padega)
    """
    Ye endpoint jab user "/" visit kare to kya response de
    """
    return {
        "message": "Welcome to Universal RAG System API",
        "version": "1.0.0",
        "docs": "/docs"  # Swagger documentation ka link
    }

# Endpoint 2: Health check endpoint
@app.get("/health")  # GET request ke liye
async def health_check():
    """
    Ye endpoint check karta hai ki backend sahi chal raha hai ya nahi
    Frontend har 30 sec baad is endpoint ko call kar sakta hai
    """
    return {
        "status": "healthy",  # Sab theek hai!
        "version": "1.0.0"
    }

# =====================================================
# STEP 5: Main Block - Ye jab directly file run ho
# =====================================================
if __name__ == "__main__":
    # Uvicorn = ASGI server (ye actual web server hai)
    # Jaise Apache ya Nginx par ye Python mein
    import uvicorn

    uvicorn.run(
        "main:app",  # Kaunsi file aur app object run karna
        host=os.getenv("BACKEND_HOST", "0.0.0.0"),  # Sab network interfaces se accessible
        port=int(os.getenv("BACKEND_PORT", 8000)),  # Port number (default 8000)
        reload=os.getenv("ENVIRONMENT") == "development"  # Auto-reload karo jab file change ho
    )
