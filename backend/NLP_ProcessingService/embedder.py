"""
Sentence Embedding Generator using sentence-transformers.
Primary model: all-MiniLM-L6-v2 (384 dimensions).
Falls back to TF-IDF vectorization when sentence-transformers is unavailable.
"""
import logging
import hashlib
import numpy as np

logger = logging.getLogger('NLP_ProcessingService')

_st_model = None
_tfidf_vectorizer = None
EMBEDDING_DIM = 384


def _get_sentence_transformer():
    global _st_model
    if _st_model is None:
        try:
            from sentence_transformers import SentenceTransformer
            _st_model = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info("SentenceTransformer 'all-MiniLM-L6-v2' loaded")
        except ImportError:
            logger.warning("sentence-transformers not available. Using TF-IDF fallback.")
            _st_model = False
    return _st_model


def _get_tfidf_fallback():
    """Build a simple TF-IDF vectorizer as fallback embedding generator."""
    global _tfidf_vectorizer
    if _tfidf_vectorizer is None:
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            _tfidf_vectorizer = TfidfVectorizer(
                max_features=EMBEDDING_DIM,
                stop_words='english',
                ngram_range=(1, 2)
            )
            # We'll fit on-the-fly with a dummy corpus
            _tfidf_vectorizer.fit(["machine learning artificial intelligence research"])
            logger.info("TF-IDF fallback vectorizer initialized")
        except ImportError:
            logger.warning("scikit-learn not available for TF-IDF fallback.")
            _tfidf_vectorizer = False
    return _tfidf_vectorizer


def _hash_embedding(text: str, dim: int = EMBEDDING_DIM) -> list:
    """
    Deterministic hash-based embedding as ultimate fallback.
    Not semantically meaningful but provides consistent vectors.
    """
    h = hashlib.sha256(text.encode('utf-8')).hexdigest()
    # Use hash chars to generate pseudo-random floats
    values = []
    for i in range(0, len(h), 2):
        val = int(h[i:i+2], 16) / 255.0 - 0.5
        values.append(val)
    # Pad or truncate to desired dimension
    while len(values) < dim:
        h = hashlib.sha256(h.encode('utf-8')).hexdigest()
        for i in range(0, len(h), 2):
            values.append(int(h[i:i+2], 16) / 255.0 - 0.5)
    values = values[:dim]
    # Normalize
    norm = sum(v**2 for v in values) ** 0.5
    if norm > 0:
        values = [v / norm for v in values]
    return values


def generate_embedding(title: str, abstract: str = "") -> list:
    """
    Generate a 384-dim embedding from title + abstract.
    Title is weighted by repetition.
    """
    combined = f"{title}. {title}. {abstract}".strip()
    if not combined:
        return [0.0] * EMBEDDING_DIM
    
    model = _get_sentence_transformer()
    
    if model and model is not False:
        try:
            embedding = model.encode(combined, normalize_embeddings=True)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
    
    # Fallback: TF-IDF
    tfidf = _get_tfidf_fallback()
    if tfidf and tfidf is not False:
        try:
            vec = tfidf.transform([combined]).toarray()[0]
            # Pad to EMBEDDING_DIM
            if len(vec) < EMBEDDING_DIM:
                vec = np.pad(vec, (0, EMBEDDING_DIM - len(vec)))
            vec = vec[:EMBEDDING_DIM]
            # Normalize
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm
            return vec.tolist()
        except Exception as e:
            logger.error(f"TF-IDF fallback failed: {e}")
    
    # Ultimate fallback: hash-based
    return _hash_embedding(combined)


def batch_generate(articles: list, batch_size: int = 64) -> list:
    """
    Batch embedding generation for bulk processing.
    Each article dict must have 'title' and optionally 'abstract'.
    """
    model = _get_sentence_transformer()
    texts = [f"{a.get('title', '')}. {a.get('title', '')}. {a.get('abstract', '')}" 
             for a in articles]
    
    if model and model is not False:
        try:
            embeddings = model.encode(
                texts, batch_size=batch_size,
                normalize_embeddings=True, show_progress_bar=True
            )
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Batch embedding failed: {e}")
    
    # Fallback: one-by-one
    return [generate_embedding(a.get('title', ''), a.get('abstract', '')) 
            for a in articles]
