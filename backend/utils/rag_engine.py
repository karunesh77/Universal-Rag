# =====================================================
# RAG ENGINE - Groq + Local DB Fallback
# =====================================================
# Pinecone optional hai — SQLite DB se bhi kaam karega
# =====================================================

import logging
import os
from typing import Optional
from datetime import datetime

from sqlalchemy.orm import Session
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate

from backend.models import Query as QueryModel, Embedding, Document

logger = logging.getLogger(__name__)

# =====================================================
# GROQ MODELS
# =====================================================
GROQ_MODELS = {
    "llama3-70b":  "llama-3.3-70b-versatile",
    "llama3-8b":   "llama-3.1-8b-instant",
    "deepseek":    "deepseek-r1-distill-llama-70b",
    "mixtral":     "mixtral-8x7b-32768",
}
DEFAULT_MODEL = "llama3-70b"


# =====================================================
# STEP 1: GET GROQ LLM
# =====================================================

def get_llm(model_key: str = DEFAULT_MODEL):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key or api_key.startswith("gsk_dummy"):
        raise ValueError("GROQ_API_KEY not configured. Get free key: https://console.groq.com")

    model_name = GROQ_MODELS.get(model_key, GROQ_MODELS[DEFAULT_MODEL])

    llm = ChatGroq(
        groq_api_key=api_key,
        model_name=model_name,
        temperature=0.3,
        max_tokens=1024,
    )
    logger.info(f"Groq LLM ready: {model_name}")
    return llm


# =====================================================
# STEP 2: SEARCH DB CHUNKS (No Pinecone needed)
# =====================================================

def search_db_chunks(question: str, db: Session, document_id: Optional[int] = None, top_k: int = 5):
    """
    Simple keyword search through stored chunks in SQLite.
    Works without Pinecone — uses the Embedding table.
    """
    query = db.query(Embedding)

    if document_id:
        query = query.filter(Embedding.document_id == document_id)

    all_chunks = query.all()
    if not all_chunks:
        return []

    # Simple relevance: count keyword matches
    question_words = set(question.lower().split())
    scored = []
    for chunk in all_chunks:
        text = (chunk.chunk_text or "").lower()
        score = sum(1 for word in question_words if word in text)
        scored.append((score, chunk))

    # Sort by score descending, return top_k
    scored.sort(key=lambda x: x[0], reverse=True)
    return [chunk for _, chunk in scored[:top_k] if scored[0][0] > 0]


# =====================================================
# STEP 3: RAG PROMPT
# =====================================================

RAG_PROMPT = PromptTemplate(
    template="""You are a helpful AI assistant. Answer the question based ONLY on the context below.

Context:
{context}

Question: {question}

Rules:
- Answer only from the context provided
- If answer not in context, say "Document mein ye information nahi mili"
- Be concise and clear
- You can respond in the same language as the question

Answer:""",
    input_variables=["context", "question"]
)


# =====================================================
# STEP 4: MAIN ANSWER FUNCTION
# =====================================================

def answer_question(
    question: str,
    user_id: int,
    document_id: Optional[int] = None,
    db: Optional[Session] = None,
    model_key: str = DEFAULT_MODEL
) -> dict:
    """
    RAG pipeline using DB chunks + Groq LLM.
    No Pinecone required.
    """

    result = {
        "question":    question,
        "answer":      None,
        "context":     None,
        "confidence":  0.0,
        "chunks_used": 0,
        "model_used":  GROQ_MODELS.get(model_key, model_key),
        "status":      "pending",
        "error":       None
    }

    try:
        # ─── Search chunks from DB ───
        if not db:
            result["status"] = "error"
            result["error"]  = "No database session provided"
            return result

        chunks = search_db_chunks(question, db, document_id, top_k=5)

        if not chunks:
            # No documents uploaded yet — answer from general knowledge
            context = ""
            result["chunks_used"] = 0
            logger.info("No chunks found — answering from model knowledge")
        else:
            context_parts = [
                f"[Chunk {i+1}]\n{chunk.chunk_text}"
                for i, chunk in enumerate(chunks)
            ]
            context = "\n\n---\n\n".join(context_parts)
            result["chunks_used"] = len(chunks)
            logger.info(f"Found {len(chunks)} relevant chunks")

        # ─── Call Groq LLM ───
        llm = get_llm(model_key)

        if context:
            prompt_text = RAG_PROMPT.format(context=context, question=question)
        else:
            # No documents — direct answer
            prompt_text = f"""You are a helpful AI assistant for a document management system.
The user hasn't uploaded any documents yet.

Question: {question}

Please answer helpfully and also mention that they can upload documents for more specific answers."""

        response = llm.invoke(prompt_text)
        answer   = response.content if hasattr(response, 'content') else str(response)

        result["answer"]     = answer
        result["context"]    = context[:2000] if context else None
        result["confidence"] = min(1.0, len(chunks) / 5) if chunks else 0.3
        result["status"]     = "success"

        logger.info(f"Answer: {len(answer)} chars, {len(chunks)} chunks used")

        # ─── Save to DB ───
        try:
            record = QueryModel(
                user_id=user_id,
                document_id=document_id,
                question=question,
                answer=answer,
                context=(result["context"] or ""),
                confidence=result["confidence"],
                created_at=datetime.utcnow()
            )
            db.add(record)
            db.commit()
            db.refresh(record)
            result["query_id"] = record.id
            logger.info(f"Query saved: ID={record.id}")
        except Exception as e:
            logger.error(f"DB save failed: {e}")

    except Exception as e:
        result["status"] = "error"
        result["error"]  = str(e)
        logger.error(f"RAG error: {e}")

    return result
