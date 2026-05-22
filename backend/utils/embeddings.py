# =====================================================
# EMBEDDINGS - Sentence Transformers (FREE, Local)
# =====================================================
# OpenAI ki zarurat nahi!
# Sentence Transformers local machine par run karta hai
# Model pehli baar download hoga (~90MB), phir offline kaam karta hai
# =====================================================

import logging
from typing import List

logger = logging.getLogger(__name__)

# Global embeddings instance (ek baar load, baar baar use)
_embeddings_instance = None


def get_embeddings():
    """
    HuggingFace Sentence Transformers initialize karo

    Model: all-MiniLM-L6-v2
    ─────────────────────────
    - Size: ~90 MB (ek baar download)
    - Dimensions: 384
    - Language: English + multilingual
    - Speed: Fast on CPU
    - Cost: FREE ✅

    Returns:
        LangChain HuggingFaceEmbeddings object
    """

    global _embeddings_instance

    # Already loaded hai to same instance return karo (memory save)
    if _embeddings_instance is not None:
        return _embeddings_instance

    try:
        from langchain.embeddings import HuggingFaceEmbeddings

        logger.info("Loading Sentence Transformers model (first time may take a minute)...")

        _embeddings_instance = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2",
            model_kwargs={"device": "cpu"},   # CPU par run karo (GPU nahi chahiye)
            encode_kwargs={"normalize_embeddings": True}
        )

        logger.info("Embeddings model loaded! (384 dimensions)")
        return _embeddings_instance

    except ImportError:
        raise RuntimeError(
            "sentence-transformers not installed. "
            "Run: pip install sentence-transformers"
        )
    except Exception as e:
        logger.error(f"Embeddings load failed: {e}")
        raise RuntimeError(f"Could not load embeddings model: {str(e)}")


def embed_text(text: str) -> List[float]:
    """Single text ko embed karo (384-dim vector)"""
    if not text or not text.strip():
        raise ValueError("Text empty hai")
    embeddings = get_embeddings()
    return embeddings.embed_query(text)


def embed_texts(texts: List[str]) -> List[List[float]]:
    """Multiple texts batch embed karo"""
    texts = [t.strip() for t in texts if t.strip()]
    if not texts:
        raise ValueError("Texts list empty")
    embeddings = get_embeddings()
    return embeddings.embed_documents(texts)


# =====================================================
# COMPARISON
# =====================================================
"""
OpenAI Embeddings vs Sentence Transformers:

                OpenAI          Sentence Transformers
Cost:           Paid ($)        FREE ✅
API Key:        Required        Not needed ✅
Internet:       Always needed   Only first download ✅
Dimensions:     1536            384
Quality:        Excellent       Very Good ✅
Speed:          Fast (API)      Fast (local) ✅
Privacy:        Data sent to OAI  Stays local ✅

Pinecone Index Dimensions:
  OpenAI        → 1536
  Sentence Trans → 384  ← Hamara use hai
"""
