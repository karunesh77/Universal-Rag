# =====================================================
# DOCUMENT ROUTES - LangChain Version
# =====================================================
# LangChain document loaders aur splitters use kar rahe hain
# File processing automatically handle hota hai
# =====================================================

import os
import uuid
import logging
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    TextLoader,
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Pinecone

from backend.database import get_db
from backend.models import User, Document, Embedding
from backend.schemas import DocumentResponse, DocumentListResponse
from backend.dependencies import get_current_user
from backend.utils.embeddings import get_embeddings
from backend.utils.file_processor import validate_file, format_file_size, get_file_extension

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
    responses={
        401: {"description": "Not authenticated"},
        404: {"description": "Document not found"}
    }
)

# Lambda only has /tmp writable
_default_upload = "/tmp/uploads" if os.getenv("AWS_LAMBDA_FUNCTION_NAME") else "./uploads"
UPLOAD_DIR = os.getenv("UPLOAD_DIRECTORY", _default_upload)


def ensure_upload_dir():
    """Upload directory create karo"""
    os.makedirs(UPLOAD_DIR, exist_ok=True)


# =====================================================
# LangChain Text Splitter
# =====================================================

def get_text_splitter():
    """
    LangChain text splitter create karo

    RecursiveCharacterTextSplitter:
    ────────────────────────────────
    - 1000 characters per chunk
    - 200 characters overlap
    - Smart splitting (respects sentence boundaries)
    """

    return RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", ". ", " ", ""]
    )


# =====================================================
# LOAD DOCUMENT WITH LANGCHAIN
# =====================================================

def load_document_with_langchain(file_path: str, file_type: str):
    """
    LangChain loaders use karke document load karo

    Supported types:
    ─────────────────
    - pdf: PyPDFLoader
    - docx: Docx2txtLoader
    - txt: TextLoader
    - xlsx: Manual (pandas ke through)

    Params:
        file_path: File ka local path
        file_type: pdf, docx, txt, xlsx

    Returns:
        List of LangChain Document objects
    """

    try:
        if file_type == "pdf":
            loader = PyPDFLoader(file_path)
        elif file_type == "docx":
            loader = Docx2txtLoader(file_path)
        elif file_type == "txt":
            loader = TextLoader(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")

        documents = loader.load()
        logger.info(f"Loaded {len(documents)} pages from {file_type}")
        return documents

    except ImportError as e:
        logger.error(f"Required library missing: {e}")
        raise RuntimeError(f"Document loading failed: missing library")
    except Exception as e:
        logger.error(f"Document loading failed: {e}")
        raise RuntimeError(f"Could not load document: {str(e)}")


# =====================================================
# ROUTE 1: UPLOAD DOCUMENT (LANGCHAIN VERSION)
# =====================================================

@router.post(
    "/upload",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Document Upload"
)
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Document Upload - LangChain Edition

    Kya hota hai:
    ──────────────
    1. File validate aur save karo
    2. LangChain loader se document load karo
    3. RecursiveCharacterTextSplitter se chunks banao
    4. LangChain embeddings generate karo
    5. Pinecone mein vectors store karo
    6. Database mein metadata save karo
    """

    ensure_upload_dir()

    # ─── Validation ───
    original_filename = file.filename
    if not original_filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename missing"
        )

    file_content = await file.read()
    file_size = len(file_content)

    is_valid, error_msg = validate_file(original_filename, file_size)
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)

    file_type = get_file_extension(original_filename)

    # ─── Save file ───
    unique_id = str(uuid.uuid4())[:8]
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    safe_filename = f"{timestamp}_{unique_id}_{original_filename}"
    file_path = os.path.join(UPLOAD_DIR, safe_filename)

    try:
        with open(file_path, "wb") as f:
            f.write(file_content)
        logger.info(f"File saved: {file_path}")
    except OSError as e:
        logger.error(f"File save failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="File save karne mein error"
        )

    # ─── Create database record ───
    try:
        new_document = Document(
            user_id=current_user.id,
            filename=original_filename,
            file_path=file_path,
            file_type=file_type,
            file_size=file_size,
            processing_status="pending",
            is_processed=False,
            created_at=datetime.utcnow()
        )

        db.add(new_document)
        db.commit()
        db.refresh(new_document)

        document_id = new_document.id
        logger.info(f"Document record created: ID={document_id}")

    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        logger.error(f"Database save failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database mein save karne mein error"
        )

    # ─── LangChain Processing ───
    try:
        new_document.processing_status = "processing"
        db.commit()

        # Load document using LangChain
        langchain_docs = load_document_with_langchain(file_path, file_type)

        if not langchain_docs:
            new_document.processing_status = "completed"
            new_document.is_processed = True
            new_document.processing_error = "No content found"
            db.commit()
            return new_document

        # Combine all pages into single text
        full_text = "\n\n".join([doc.page_content for doc in langchain_docs])
        new_document.content = full_text

        # Split into chunks using LangChain
        splitter = get_text_splitter()
        chunk_docs = splitter.split_text(full_text)

        logger.info(f"Text split into {len(chunk_docs)} chunks")

        # Store chunks in database
        for chunk_index, chunk_text_content in enumerate(chunk_docs):
            embedding = Embedding(
                document_id=new_document.id,
                chunk_text=chunk_text_content,
                chunk_index=chunk_index,
                vector_id=None,  # Pinecone integration baad mein
                created_at=datetime.utcnow()
            )
            db.add(embedding)

        # Try to store in Pinecone
        try:
            embeddings_model = get_embeddings()
            vectorstore = Pinecone.from_texts(
                texts=chunk_docs,
                embedding=embeddings_model,
                index_name="rag-documents",
                metadatas=[
                    {
                        "document_id": new_document.id,
                        "chunk_index": i,
                        "filename": original_filename
                    }
                    for i in range(len(chunk_docs))
                ]
            )
            logger.info("Vectors stored in Pinecone")

        except Exception as e:
            logger.warning(f"Pinecone storage failed: {e}. Continuing without vectors...")

        # Mark as processed
        new_document.processing_status = "completed"
        new_document.is_processed = True
        db.commit()
        db.refresh(new_document)

        logger.info(f"Document {document_id} processing complete")

    except Exception as e:
        logger.error(f"Processing failed: {e}")
        new_document.processing_status = "failed"
        new_document.processing_error = str(e)
        db.commit()

    return new_document


# =====================================================
# ROUTE 2: LIST DOCUMENTS
# =====================================================

@router.get(
    "/",
    response_model=List[DocumentListResponse],
    summary="Documents List"
)
async def list_documents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 20
):
    """User ke sare documents list karna"""

    documents = (
        db.query(Document)
        .filter(Document.user_id == current_user.id)
        .order_by(Document.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    logger.info(f"User {current_user.id} listed {len(documents)} documents")
    return documents


# =====================================================
# ROUTE 3: GET SPECIFIC DOCUMENT
# =====================================================

@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
    summary="Document Details"
)
async def get_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Ek specific document ki details"""

    document = db.query(Document).filter(Document.id == document_id).first()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document ID={document_id} not found"
        )

    if document.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ye document aapka nahi hai"
        )

    return document


# =====================================================
# ROUTE 4: DELETE DOCUMENT
# =====================================================

@router.delete(
    "/{document_id}",
    status_code=status.HTTP_200_OK,
    summary="Document Delete"
)
async def delete_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Document delete karna"""

    document = db.query(Document).filter(Document.id == document_id).first()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document ID={document_id} not found"
        )

    if document.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ye document aapka nahi hai"
        )

    file_path = document.file_path
    doc_filename = document.filename

    # Delete embeddings
    embeddings_count = (
        db.query(Embedding)
        .filter(Embedding.document_id == document_id)
        .count()
    )

    db.query(Embedding).filter(Embedding.document_id == document_id).delete()

    # Delete document record
    db.delete(document)
    db.commit()

    logger.info(f"Document {document_id} deleted, {embeddings_count} embeddings removed")

    # Delete file
    if file_path and os.path.exists(file_path):
        try:
            os.remove(file_path)
            logger.info(f"File deleted: {file_path}")
        except OSError as e:
            logger.error(f"File deletion failed: {e}")

    return {
        "message": f"Document '{doc_filename}' deleted",
        "document_id": document_id,
        "embeddings_deleted": embeddings_count
    }


# =====================================================
# ROUTE 5: DOCUMENT STATS
# =====================================================

@router.get(
    "/stats/summary",
    summary="Document Statistics"
)
async def document_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """User ke documents ki statistics"""

    from sqlalchemy import func

    total = db.query(Document).filter(Document.user_id == current_user.id).count()

    processed = (
        db.query(Document)
        .filter(
            Document.user_id == current_user.id,
            Document.processing_status == "completed"
        )
        .count()
    )

    pending = (
        db.query(Document)
        .filter(
            Document.user_id == current_user.id,
            Document.processing_status == "pending"
        )
        .count()
    )

    failed = (
        db.query(Document)
        .filter(
            Document.user_id == current_user.id,
            Document.processing_status == "failed"
        )
        .count()
    )

    size_result = (
        db.query(func.sum(Document.file_size))
        .filter(Document.user_id == current_user.id)
        .scalar()
    )
    total_size_mb = round((size_result or 0) / (1024 * 1024), 2)

    doc_ids = [
        d.id for d in
        db.query(Document.id).filter(Document.user_id == current_user.id).all()
    ]
    total_chunks = 0
    if doc_ids:
        total_chunks = db.query(Embedding).filter(Embedding.document_id.in_(doc_ids)).count()

    return {
        "total_documents": total,
        "processed": processed,
        "pending": pending,
        "failed": failed,
        "total_size_mb": total_size_mb,
        "total_chunks": total_chunks
    }
