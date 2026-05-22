# =====================================================
# QUERY ROUTES - Question/Answer Endpoints
# =====================================================
# Ye file RAG system ke main endpoints rakhta hai
#
# Available Endpoints:
# ────────────────────────────────────────────────
# POST   /queries/ask          → Question ask karo
# GET    /queries/             → Apne sare questions list karo
# GET    /queries/{id}         → Ek question ki details
# DELETE /queries/{id}         → Question delete karo
# POST   /queries/{id}/bookmark → Bookmark karo
# =====================================================

import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import User, Document, Query as QueryModel
from backend.schemas import QueryCreate, QueryResponse, QueryListResponse
from backend.dependencies import get_current_user
from backend.utils.rag_engine import answer_question

# Logging
logger = logging.getLogger(__name__)

# =====================================================
# ROUTER SETUP
# =====================================================

router = APIRouter(
    prefix="/queries",
    tags=["RAG Queries"],
    responses={
        401: {"description": "Not authenticated"},
        404: {"description": "Query not found"}
    }
)


# =====================================================
# ROUTE 1: ASK QUESTION (MAIN RAG ENDPOINT)
# =====================================================

@router.post(
    "/ask",
    response_model=QueryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Question Ask Karo",
    description="Document se answer lo AI ke through"
)
async def ask_question(
    query_data: QueryCreate,  # Question aur optional document ID
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Question ask karo aur answer lo (RAG System)

    Kya hota hai:
    ──────────────
    1. User question poochta hai
    2. OpenAI se question ka embedding generate hota hai
    3. Pinecone mein search hota hai (similar chunks)
    4. Top 5 chunks mil jate hain
    5. Context banate hain
    6. Claude ko context deke call karte hain
    7. Claude answer generate karta hai
    8. Answer database mein save hota hai
    9. Response return hota hai

    Request Body:
    ──────────────
    {
        "question": "Invoice mein total kya hai?",
        "document_id": 1  // Optional - specific document se answer lo
    }

    Response:
    ──────────
    {
        "id": 1,
        "user_id": 1,
        "question": "Invoice mein total kya hai?",
        "answer": "Invoice mein total 5000 rupees hai",
        "context": "... extracted document parts ...",
        "confidence": 0.85,
        "created_at": "2024-05-09T10:30:00",
        "is_bookmarked": false
    }

    Processing Time:
    ────────────────
    - Embedding generation: ~500ms
    - Pinecone search: ~100ms
    - Claude API call: ~2-5 seconds
    Total: 3-6 seconds

    Errors:
    ────────
    - 401: Not authenticated
    - 404: Document not found (agar document_id diya gaya)
    - 400: Invalid question
    - 500: API error (OpenAI/Anthropic down)
    """

    # ─── Validation ───
    if not query_data.question or len(query_data.question.strip()) < 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question kam se kam 5 characters ka hona chahiye"
        )

    # ─── Document validation (agar specific document select kiya) ───
    document_id = query_data.document_id
    if document_id:
        document = db.query(Document).filter(
            Document.id == document_id,
            Document.user_id == current_user.id
        ).first()

        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document ID={document_id} not found"
            )

        if not document.is_processed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Document abhi process nahi hua. Status: {document.processing_status}"
            )

    # ─── Run RAG Pipeline ───
    logger.info(f"User {current_user.id} asking: {query_data.question[:50]}...")

    try:
        rag_result = answer_question(
            question=query_data.question.strip(),
            user_id=current_user.id,
            document_id=document_id,
            db=db
        )

        if rag_result["status"] != "success":
            error_msg = rag_result.get("error", "Processing failed")
            logger.error(f"RAG pipeline failed: {error_msg}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Could not generate answer: {error_msg}"
            )

        # ─── Query already saved by RAG engine ───
        # Fetch it back to return proper response
        query_record = (
            db.query(QueryModel)
            .filter(
                QueryModel.user_id == current_user.id,
                QueryModel.question == query_data.question.strip()
            )
            .order_by(QueryModel.created_at.desc())
            .first()
        )

        if not query_record:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Query saved nahi ho saka"
            )

        logger.info(f"Query processed successfully: ID={query_record.id}")
        return query_record

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Question processing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing question: {str(e)}"
        )


# =====================================================
# ROUTE 2: LIST USER'S QUERIES
# =====================================================

@router.get(
    "/",
    response_model=List[QueryListResponse],
    summary="Apne Queries List Karo",
    description="Sare questions jo poochy hain"
)
async def list_queries(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 20,
    bookmarked_only: bool = False
):
    """
    User ke sare questions list karna

    Params:
    ───────
    skip: Pagination (offset)
    limit: Max results per page
    bookmarked_only: Sirf bookmarked questions (default False)

    Response:
    ──────────
    [
        {
            "id": 1,
            "question": "Invoice total kya hai?",
            "answer": "...",
            "confidence": 0.85,
            "created_at": "2024-05-09T10:30:00",
            "is_bookmarked": false
        },
        ...
    ]
    """

    query = (
        db.query(QueryModel)
        .filter(QueryModel.user_id == current_user.id)
    )

    if bookmarked_only:
        query = query.filter(QueryModel.is_bookmarked == True)

    queries = (
        query
        .order_by(QueryModel.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    logger.info(f"User {current_user.id} listed {len(queries)} queries")
    return queries


# =====================================================
# ROUTE 3: GET SPECIFIC QUERY
# =====================================================

@router.get(
    "/{query_id}",
    response_model=QueryResponse,
    summary="Query Details",
    description="Ek specific question ki puri details"
)
async def get_query(
    query_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Ek specific query ki details fetch karna

    URL Parameter:
    ──────────────
    query_id: Query ka ID

    Response:
    ──────────
    Full query details including question, answer, context, confidence
    """

    query = db.query(QueryModel).filter(QueryModel.id == query_id).first()

    if not query:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Query ID={query_id} not found"
        )

    if query.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ye query aapka nahi hai"
        )

    return query


# =====================================================
# ROUTE 4: DELETE QUERY
# =====================================================

@router.delete(
    "/{query_id}",
    status_code=status.HTTP_200_OK,
    summary="Query Delete Karo"
)
async def delete_query(
    query_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Query delete karna (history cleaner)

    Note: Ye permanent hai!
    """

    query = db.query(QueryModel).filter(QueryModel.id == query_id).first()

    if not query:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Query ID={query_id} not found"
        )

    if query.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ye query aapka nahi hai"
        )

    db.delete(query)
    db.commit()

    logger.info(f"Query {query_id} deleted by user {current_user.id}")

    return {
        "message": "Query deleted successfully",
        "query_id": query_id
    }


# =====================================================
# ROUTE 5: BOOKMARK/UNBOOKMARK QUERY
# =====================================================

@router.post(
    "/{query_id}/bookmark",
    response_model=QueryResponse,
    summary="Query Bookmark Karo",
    description="Important question ko bookmark rakhna"
)
async def toggle_bookmark(
    query_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Query ko bookmark/unbookmark karna

    Bookmark = Important questions ko save rakhna (star jaisa)

    Returns:
    ─────────
    Updated query with is_bookmarked flipped
    """

    query = db.query(QueryModel).filter(QueryModel.id == query_id).first()

    if not query:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Query ID={query_id} not found"
        )

    if query.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ye query aapka nahi hai"
        )

    # Toggle bookmark status
    query.is_bookmarked = not query.is_bookmarked
    db.commit()
    db.refresh(query)

    status_text = "bookmarked" if query.is_bookmarked else "unbookmarked"
    logger.info(f"Query {query_id} {status_text} by user {current_user.id}")

    return query


# =====================================================
# ROUTE 6: QUERY STATISTICS
# =====================================================

@router.get(
    "/stats/summary",
    summary="Query Statistics",
    description="Questions ke liye statistics"
)
async def query_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    User ke questions ka statistics

    Response:
    ──────────
    {
        "total_queries": 10,
        "bookmarked": 3,
        "average_confidence": 0.82,
        "queries_by_document": {
            "1": 5,
            "2": 3,
            "3": 2
        }
    }
    """

    from sqlalchemy import func

    # Total queries
    total = db.query(QueryModel).filter(
        QueryModel.user_id == current_user.id
    ).count()

    # Bookmarked count
    bookmarked = db.query(QueryModel).filter(
        QueryModel.user_id == current_user.id,
        QueryModel.is_bookmarked == True
    ).count()

    # Average confidence
    avg_confidence_result = db.query(func.avg(QueryModel.confidence)).filter(
        QueryModel.user_id == current_user.id
    ).scalar()
    avg_confidence = float(avg_confidence_result) if avg_confidence_result else 0.0

    # Queries by document
    queries_by_doc = {}
    results = db.query(
        QueryModel.document_id,
        func.count(QueryModel.id)
    ).filter(
        QueryModel.user_id == current_user.id
    ).group_by(QueryModel.document_id).all()

    for doc_id, count in results:
        if doc_id:
            queries_by_doc[str(doc_id)] = count

    return {
        "total_queries": total,
        "bookmarked": bookmarked,
        "average_confidence": round(avg_confidence, 2),
        "queries_by_document": queries_by_doc
    }


# =====================================================
# DOCUMENTATION
# =====================================================
"""
QUERY WORKFLOW:

1. User POST /queries/ask:
   {
       "question": "Invoice total kya hai?",
       "document_id": 1
   }

2. Backend processing:
   - Generate embedding for question (OpenAI)
   - Search Pinecone for similar chunks
   - Get top 5 chunks with similarity scores
   - Build context from chunks
   - Call Claude with context
   - Claude generates answer
   - Save to database
   - Return response

3. Response:
   {
       "id": 1,
       "question": "Invoice total kya hai?",
       "answer": "Invoice mein total 5000 rupees hai",
       "context": "... extracted parts ...",
       "confidence": 0.85,
       "created_at": "2024-05-09T10:30:00",
       "is_bookmarked": false
   }

4. User can:
   - View answer
   - Bookmark important answers
   - Delete questions
   - See statistics
"""
