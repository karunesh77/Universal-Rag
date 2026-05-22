# =====================================================
# DATABASE MODELS - SQLAlchemy ORM
# =====================================================
# Ye file database tables ko represent karti hai
# Python classes ke through, SQL likhe bina!
#
# Model = Python class
# Table = Database mein table
# Column = Database mein column (field)
# =====================================================

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

# Base = Sabhi models ka parent class
# Jab models define karenge to Base se inherit karenge
Base = declarative_base()

# =====================================================
# MODEL 1: USER
# =====================================================
# Ye model users ko represent karta hai
# Kaunse users app use kar rahe hain track karte hain

class User(Base):
    """
    User Model - App ke users

    Attributes:
        id: Unique user ID (primary key)
        email: User ka email (unique)
        name: User ka naam
        password_hash: Encrypted password
        created_at: Account banane ka time
        is_active: User active hai ya nahi
    """

    # Table ka naam database mein
    __tablename__ = "users"

    # Columns define karo
    # Column(Type, constraints)

    # Primary Key - Har user ka unique ID (1, 2, 3, ...)
    id = Column(Integer, primary_key=True, index=True)

    # Email - Unique hona chahiye (ek hi email do baar nahi)
    email = Column(String(255), unique=True, index=True, nullable=False)

    # User ka naam
    name = Column(String(255), nullable=False)

    # Password (hashed/encrypted)
    # Plaintext password kabhi store nahi karte!
    password_hash = Column(String(255), nullable=False)

    # Account creation time (default = abhi ka time)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Last login time
    last_login = Column(DateTime, nullable=True)

    # User active hai ya nahi (delete karna nahi chahte to inactive kar sakte ho)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationship - Ye user ke documents kaunse hain
    # backref = Document model se 'user' se access kar sakte ho
    documents = relationship("Document", back_populates="owner")
    queries = relationship("Query", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, name={self.name})>"


# =====================================================
# MODEL 2: DOCUMENT
# =====================================================
# Ye model uploaded documents ko represent karta hai
# PDFs, Word files, etc track karte hain

class Document(Base):
    """
    Document Model - User ke uploaded documents

    Attributes:
        id: Unique document ID
        user_id: Kaunse user ne upload kiya
        filename: File ka naam
        file_path: Server par file ki location
        file_type: File type (pdf, docx, xlsx, etc)
        file_size: File ki size (bytes mein)
        content: Extracted text from document
        created_at: Upload ka time
        is_processed: Kya embeddings generate ho gaye
    """

    __tablename__ = "documents"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)

    # Foreign Key - Kaunse user ne upload kiya
    # ForeignKey = dusre table ke saath relationship
    # "users.id" = users table ke id column se connect
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # File name (jo user ne upload kiya)
    filename = Column(String(255), nullable=False)

    # Server par file ki path
    # Example: "./uploads/2024/document_123.pdf"
    file_path = Column(String(500), nullable=False)

    # File type (pdf, docx, xlsx, pptx)
    file_type = Column(String(50), nullable=False)

    # File size in bytes
    file_size = Column(Integer, nullable=False)

    # Extracted text from document (jo embeddings banayenge)
    # Text = full document ka text
    content = Column(Text, nullable=True)

    # Upload ka time
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Updated/modified time
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Kya document process ho gaya (embeddings generate ho gaye)
    # True = embeddings ban gaye aur vector DB mein store ho gaye
    is_processed = Column(Boolean, default=False, nullable=False)

    # Embedding generation status
    # "pending", "processing", "completed", "failed"
    processing_status = Column(String(50), default="pending")

    # Agar processing fail ho to error message
    processing_error = Column(Text, nullable=True)

    # Relationship - Ye document kaunse user ka hai
    owner = relationship("User", back_populates="documents")

    # Relationship - Is document ke embeddings
    embeddings = relationship("Embedding", back_populates="document")

    # Relationship - Is document se kaunse queries pooche gaye
    queries = relationship("Query", back_populates="document")

    def __repr__(self):
        return f"<Document(id={self.id}, filename={self.filename}, user_id={self.user_id})>"


# =====================================================
# MODEL 3: EMBEDDING
# =====================================================
# Ye model document ke chunks aur unke embeddings store karta hai
# Vector DB mein jaate hain

class Embedding(Base):
    """
    Embedding Model - Document ke text chunks aur vectors

    Ye table document ke small pieces (chunks) store karta hai
    aur har chunk ka embedding (vector) store karta hai

    Attributes:
        id: Unique embedding ID
        document_id: Kaunse document ka ye chunk hai
        chunk_text: Text ka small piece
        chunk_index: Chunk number (1st, 2nd, 3rd...)
        vector_id: Pinecone mein stored vector ka ID
        metadata: Additional info (for search)
        created_at: Creation time
    """

    __tablename__ = "embeddings"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)

    # Foreign Key - Kaunse document ka ye embedding hai
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)

    # Text ka small piece (chunk)
    # Document ko 500-word chunks mein divide karte hain
    chunk_text = Column(Text, nullable=False)

    # Chunk number (1st chunk, 2nd chunk, etc)
    chunk_index = Column(Integer, nullable=False)

    # Pinecone vector database mein ye chunk ka ID
    # Jab query aati hai tab Pinecone mein search karte hain
    vector_id = Column(String(255), nullable=True)

    # Extra info (search ke liye helpful info)
    # JSON format mein: {"page": 1, "section": "Introduction"}
    extra_info = Column(Text, nullable=True)

    # Created time
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship - Ye embedding kaunse document ka hai
    document = relationship("Document", back_populates="embeddings")

    def __repr__(self):
        return f"<Embedding(id={self.id}, document_id={self.document_id}, chunk_index={self.chunk_index})>"


# =====================================================
# MODEL 4: QUERY
# =====================================================
# Ye model user ke questions aur AI ke answers track karta hai
# Chat history ke liye

class Query(Base):
    """
    Query Model - User ke questions aur AI responses

    Attributes:
        id: Unique query ID
        user_id: Kaunse user ne question pocha
        document_id: Kaunse document se answer milaya
        question: User ka question
        answer: AI ka answer
        context: Document se extract kiye gaye relevant parts
        confidence: Answer ka confidence score (0-100)
        created_at: Query time
    """

    __tablename__ = "queries"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)

    # Foreign Key - Kaunse user ne question pocha
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Foreign Key - Kaunse document se answer milaya
    # Nullable kyunki general question ho sakta hai (kisi document se nahi)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)

    # User ka question
    question = Column(Text, nullable=False)

    # AI ka generated answer
    answer = Column(Text, nullable=False)

    # Document se extract kiye gaye relevant parts
    # Jo Claude ko diye gaye the
    context = Column(Text, nullable=True)

    # Answer ki confidence (0-100)
    # 100 = bilkul sure, 50 = half-sure, 0 = confused
    confidence = Column(Float, default=0.0)

    # Query ka time
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Is query ko bookmark kiya ya nahi
    is_bookmarked = Column(Boolean, default=False)

    # Relationship - Ye query kaunse user ka hai
    user = relationship("User", back_populates="queries")

    # Relationship - Ye query kaunse document se related hai
    document = relationship("Document", back_populates="queries")

    def __repr__(self):
        return f"<Query(id={self.id}, user_id={self.user_id}, question={self.question[:50]}...)>"


# =====================================================
# DATABASE SUMMARY
# =====================================================
"""
Database Tables (Models):

1. USERS TABLE
   ├── id (PK)
   ├── email (unique)
   ├── name
   ├── password_hash
   └── created_at

2. DOCUMENTS TABLE
   ├── id (PK)
   ├── user_id (FK) → Users
   ├── filename
   ├── file_path
   ├── file_type
   ├── content
   └── is_processed

3. EMBEDDINGS TABLE
   ├── id (PK)
   ├── document_id (FK) → Documents
   ├── chunk_text
   ├── chunk_index
   ├── vector_id (Pinecone)
   └── metadata

4. QUERIES TABLE
   ├── id (PK)
   ├── user_id (FK) → Users
   ├── document_id (FK) → Documents
   ├── question
   ├── answer
   ├── context
   └── confidence

RELATIONSHIPS:
- User has many Documents
- User has many Queries
- Document has many Embeddings
- Document has many Queries
"""
