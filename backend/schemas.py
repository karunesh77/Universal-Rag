# =====================================================
# PYDANTIC SCHEMAS - Request/Response Models
# =====================================================
# Ye file API requests/responses ko validate karta hai
# Frontend se data aata hai → Schema check karta hai → Accept/Reject
#
# Schema = Pydantic model
# Frontend se JSON aata hai → Python object mein convert
# Database se Python object → JSON mein convert karke response
# =====================================================

from pydantic import BaseModel, EmailStr, Field, validator
from datetime import datetime
from typing import Optional, List
from enum import Enum

# =====================================================
# ENUMS - Fixed Values
# =====================================================
# Ye values jo fixed hote hain (dropdown options jaisa)

class FileTypeEnum(str, Enum):
    """
    File types jo upload ho sakte hain
    """
    PDF = "pdf"
    DOCX = "docx"
    XLSX = "xlsx"
    PPTX = "pptx"
    TXT = "txt"

class ProcessingStatusEnum(str, Enum):
    """
    Document processing status
    """
    PENDING = "pending"        # Abhi process hona baaki hai
    PROCESSING = "processing"  # Process ho raha hai
    COMPLETED = "completed"    # Complete ho gaya
    FAILED = "failed"          # Process fail ho gaya


# =====================================================
# USER SCHEMAS
# =====================================================

class UserCreate(BaseModel):
    """
    User Registration - Frontend se request

    Frontend ye data bhejta hai jab naya user signup kare:
    {
        "email": "john@example.com",
        "name": "John Doe",
        "password": "SecurePass123!"
    }
    """

    # Email - Unique hona chahiye
    # EmailStr = Pydantic ke liye valid email format
    email: EmailStr = Field(
        ...,  # Required field
        description="User ka email address (unique)",
        example="john@example.com"
    )

    # User ka naam
    name: str = Field(
        ...,  # Required
        min_length=2,  # Kam se kam 2 characters
        max_length=255,  # Zyada se zyada 255 characters
        description="User ka full name",
        example="John Doe"
    )

    # Password
    password: str = Field(
        ...,  # Required
        min_length=8,  # Kam se kam 8 characters (security)
        description="User ka password (minimum 8 characters)",
        example="SecurePass123!"
    )

    # Validation - Password strong enough?
    @validator("password")
    def validate_password(cls, v):
        """
        Password validation:
        - Kam se kam ek uppercase letter
        - Kam se kam ek lowercase letter
        - Kam se kam ek number
        """
        if not any(char.isupper() for char in v):
            raise ValueError("Password mein kam se kam ek uppercase letter hona chahiye")
        if not any(char.islower() for char in v):
            raise ValueError("Password mein kam se kam ek lowercase letter hona chahiye")
        if not any(char.isdigit() for char in v):
            raise ValueError("Password mein kam se kam ek number hona chahiye")
        return v

    class Config:
        # Swagger docs mein example dikhane ke liye
        json_schema_extra = {
            "example": {
                "email": "john@example.com",
                "name": "John Doe",
                "password": "SecurePass123!"
            }
        }


class UserLogin(BaseModel):
    """
    User Login - Frontend se request

    Login karte time sirf email aur password chahiye
    """

    email: EmailStr = Field(
        ...,
        description="User ka email",
        example="john@example.com"
    )

    password: str = Field(
        ...,
        description="User ka password",
        example="SecurePass123!"
    )


class UserResponse(BaseModel):
    """
    User Response - Backend se response

    Backend user ke data return karta hai
    NOTE: Password kabhi return nahi karte! (Security!)
    """

    id: int = Field(description="User ka unique ID")
    email: str = Field(description="User ka email")
    name: str = Field(description="User ka naam")
    created_at: datetime = Field(description="Account banane ka time")
    last_login: Optional[datetime] = Field(description="Last login time")
    is_active: bool = Field(description="User active hai?")

    # Pydantic v2 config
    class Config:
        from_attributes = True  # Database model se convert karne ke liye


class UserListResponse(BaseModel):
    """
    Multiple Users Response
    """
    id: int
    email: str
    name: str
    created_at: datetime


# =====================================================
# DOCUMENT SCHEMAS
# =====================================================

class DocumentCreate(BaseModel):
    """
    Document Upload - Frontend se request

    File upload karte time sirf file info bhejte hain
    Actual file binary data multipart form-data se jata hai
    """

    filename: str = Field(
        ...,
        max_length=255,
        description="File ka naam",
        example="invoice.pdf"
    )

    file_type: FileTypeEnum = Field(
        ...,
        description="File ka type",
        example="pdf"
    )

    file_size: int = Field(
        ...,
        gt=0,  # Greater than 0
        le=52428800,  # 50MB tak
        description="File size in bytes",
        example=1024000
    )


class DocumentResponse(BaseModel):
    """
    Document Response - Backend se response

    Backend document ke details return karta hai
    """

    id: int = Field(description="Document ka unique ID")
    user_id: int = Field(description="Kaunse user ne upload kiya")
    filename: str = Field(description="File ka naam")
    file_type: str = Field(description="File ka type")
    file_size: int = Field(description="File size in bytes")
    created_at: datetime = Field(description="Upload time")
    is_processed: bool = Field(description="Kya embeddings generate ho gaye?")
    processing_status: str = Field(description="Processing status")
    processing_error: Optional[str] = Field(description="Koi error tha?")

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    """
    Multiple Documents Response
    """
    id: int
    filename: str
    file_type: str
    file_size: int
    created_at: datetime
    is_processed: bool
    processing_status: str


# =====================================================
# EMBEDDING SCHEMAS
# =====================================================

class EmbeddingResponse(BaseModel):
    """
    Embedding Response - Vector info

    Document ke chunks aur unke embeddings
    """

    id: int = Field(description="Embedding ka ID")
    document_id: int = Field(description="Kaunse document ka")
    chunk_index: int = Field(description="Chunk number")
    chunk_text: str = Field(description="Text ka piece")
    vector_id: Optional[str] = Field(description="Pinecone mein vector ka ID")
    created_at: datetime = Field(description="Creation time")

    class Config:
        from_attributes = True


# =====================================================
# QUERY/CHAT SCHEMAS
# =====================================================

class QueryCreate(BaseModel):
    """
    Query Create - Frontend se request

    User jab question pooche to ye schema use hota hai
    """

    question: str = Field(
        ...,
        min_length=5,  # Kam se kam 5 characters
        max_length=5000,  # Zyada se zyada 5000 characters
        description="User ka question",
        example="Invoice mein total amount kya hai?"
    )

    document_id: Optional[int] = Field(
        default=None,
        description="Agar specific document se pouch rahe ho"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "question": "Invoice mein total amount kya hai?",
                "document_id": 1
            }
        }


class QueryResponse(BaseModel):
    """
    Query Response - Backend se response

    Backend question ka answer return karta hai
    """

    id: int = Field(description="Query ka ID")
    user_id: int = Field(description="Kaunse user ne pocha")
    question: str = Field(description="User ka question")
    answer: str = Field(description="AI ka answer")
    context: Optional[str] = Field(description="Relevant text")
    confidence: float = Field(description="Answer ka confidence (0-100)")
    created_at: datetime = Field(description="Query time")
    is_bookmarked: bool = Field(description="Bookmark kiya hai?")

    class Config:
        from_attributes = True


class QueryListResponse(BaseModel):
    """
    Multiple Queries Response
    """
    id: int
    question: str
    answer: str
    confidence: float
    created_at: datetime
    is_bookmarked: bool


# =====================================================
# TOKEN SCHEMA (For Authentication)
# =====================================================

class Token(BaseModel):
    """
    JWT Token Response - Login successful

    Login successful hone ke baad ye return hota hai
    """

    access_token: str = Field(description="JWT token")
    token_type: str = Field(default="bearer", description="Token type")
    user: UserResponse = Field(description="User info")


# =====================================================
# ERROR RESPONSE SCHEMA
# =====================================================

class ErrorResponse(BaseModel):
    """
    Error Response - Kuch galat hua to ye return hota hai
    """

    detail: str = Field(description="Error message")
    error_code: Optional[str] = Field(description="Error code")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "detail": "Email already exists",
                "error_code": "EMAIL_EXISTS",
                "timestamp": "2024-05-09T10:30:00"
            }
        }


# =====================================================
# PAGINATION SCHEMA
# =====================================================

class PaginationResponse(BaseModel):
    """
    Paginated Response - Bahut sare items ke liye

    Agar users 100 hain to pagination se 10-10 karte hain
    """

    total: int = Field(description="Total items")
    page: int = Field(description="Current page")
    page_size: int = Field(description="Items per page")
    pages: int = Field(description="Total pages")
    items: List = Field(description="Page ke items")

    class Config:
        json_schema_extra = {
            "example": {
                "total": 100,
                "page": 1,
                "page_size": 10,
                "pages": 10,
                "items": []
            }
        }
