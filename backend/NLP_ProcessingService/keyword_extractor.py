"""
Keyword Extraction using multiple methods:
1. TF-IDF (corpus-level importance)
2. KeyBERT (semantic relevance) [if available]
3. RAKE (graph-based) [fallback]
"""
import re
import logging
from collections import Counter

logger = logging.getLogger('NLP_ProcessingService')

# Lazy-loaded models
_keybert_model = None
_tfidf_vectorizer = None


def _get_keybert():
    global _keybert_model
    if _keybert_model is None:
        try:
            from keybert import KeyBERT
            _keybert_model = KeyBERT(model="all-MiniLM-L6-v2")
            logger.info("KeyBERT model loaded successfully")
        except ImportError:
            logger.warning("KeyBERT not available. Using fallback extraction.")
            _keybert_model = False
    return _keybert_model


def extract_keywords_tfidf(text: str, top_n: int = 10) -> list[dict]:
    """Extract keywords using simple TF-IDF-like scoring."""
    from .preprocessing import clean_text, ACADEMIC_STOPWORDS
    
    cleaned = clean_text(text).lower()
    # Extract words and bigrams
    words = re.findall(r'\b[a-zA-Z]{3,}\b', cleaned)
    
    basic_stops = {
        'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all',
        'can', 'her', 'was', 'one', 'our', 'out', 'has', 'have',
        'with', 'this', 'that', 'from', 'they', 'been', 'will',
        'their', 'would', 'there', 'about', 'which', 'when',
        'what', 'some', 'them', 'than', 'other', 'into', 'more',
        'these', 'also', 'were', 'such', 'each', 'does', 'based',
        'using', 'used', 'proposed', 'paper', 'study', 'results',
        'method', 'approach', 'shows', 'show', 'present', 'work',
    }
    all_stops = basic_stops | ACADEMIC_STOPWORDS
    
    filtered = [w for w in words if w not in all_stops]
    
    # Unigram frequency
    freq = Counter(filtered)
    total = len(filtered) if filtered else 1
    
    # Simple TF scoring with length bonus
    scored = {}
    for word, count in freq.items():
        tf = count / total
        length_bonus = min(len(word) / 10, 1.0)  # Longer words slightly preferred
        scored[word] = tf * (1 + length_bonus)
    
    # Also extract bigrams
    for i in range(len(filtered) - 1):
        bigram = f"{filtered[i]} {filtered[i+1]}"
        scored[bigram] = scored.get(bigram, 0) + (1.5 / total)  # Bigram bonus
    
    ranked = sorted(scored.items(), key=lambda x: x[1], reverse=True)[:top_n]
    max_score = ranked[0][1] if ranked else 1
    
    return [{"keyword": kw, "score": round(s / max_score, 4)} for kw, s in ranked]


def extract_keywords_keybert(text: str, top_n: int = 10) -> list[dict]:
    """Extract keywords using KeyBERT (semantic similarity to document)."""
    model = _get_keybert()
    if not model:
        return []
    
    try:
        keywords = model.extract_keywords(
            text,
            keyphrase_ngram_range=(1, 3),
            stop_words="english",
            top_n=top_n,
            use_mmr=True,
            diversity=0.5,
        )
        return [{"keyword": kw, "score": round(score, 4)} for kw, score in keywords]
    except Exception as e:
        logger.error(f"KeyBERT extraction failed: {e}")
        return []


def extract_keywords(text: str, top_n: int = 10) -> list[dict]:
    """
    Ensemble keyword extraction.
    Uses KeyBERT (60% weight) + TF-IDF (40% weight) when both available.
    Falls back to TF-IDF only.
    """
    if not text or len(text.strip()) < 20:
        return []
    
    tfidf_results = extract_keywords_tfidf(text, top_n=top_n * 2)
    keybert_results = extract_keywords_keybert(text, top_n=top_n * 2)
    
    if keybert_results:
        # Merge with weighted scoring
        merged = {}
        for item in keybert_results:
            merged[item["keyword"].lower()] = item["score"] * 0.6
        for item in tfidf_results:
            key = item["keyword"].lower()
            merged[key] = merged.get(key, 0) + item["score"] * 0.4
        
        ranked = sorted(merged.items(), key=lambda x: x[1], reverse=True)[:top_n]
        return [{"keyword": kw, "score": round(s, 4)} for kw, s in ranked]
    else:
        # TF-IDF only
        return tfidf_results[:top_n]
