"""
Text Preprocessing Pipeline for Academic Content.
Handles tokenization, stopword removal, lemmatization, and text cleaning.
"""
import re
import logging

logger = logging.getLogger('NLP_ProcessingService')

# Academic-specific stopwords beyond standard lists
ACADEMIC_STOPWORDS = {
    "et", "al", "fig", "figure", "table", "eq", "equation",
    "ref", "cite", "ibid", "vol", "pp", "doi", "arxiv",
    "http", "https", "www", "abstract", "introduction",
    "conclusion", "acknowledgment", "acknowledgement", "reference",
    "references", "bibliography", "supplementary", "appendix",
}

# Try to load spaCy, gracefully degrade if unavailable
_nlp = None

def _get_nlp():
    global _nlp
    if _nlp is None:
        try:
            import spacy
            _nlp = spacy.load("en_core_web_sm")
            logger.info("spaCy model 'en_core_web_sm' loaded successfully")
        except (ImportError, OSError):
            logger.warning("spaCy not available. Using basic preprocessing fallback.")
            _nlp = False
    return _nlp


def clean_text(text: str) -> str:
    """Remove URLs, emails, DOIs, LaTeX artifacts, and normalize whitespace."""
    if not text:
        return ""
    # Remove URLs
    text = re.sub(r'http\S+|www\.\S+', '', text)
    # Remove emails
    text = re.sub(r'\S+@\S+', '', text)
    # Remove DOIs
    text = re.sub(r'10\.\d{4,}/\S+', '', text)
    # Remove LaTeX math
    text = re.sub(r'\$[^$]+\$', ' ', text)
    # Remove LaTeX commands
    text = re.sub(r'\\[a-zA-Z]+\{[^}]*\}', '', text)
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def preprocess(text: str) -> dict:
    """
    Full preprocessing pipeline for a single text block.
    Returns tokens, lemmas, and sentences.
    """
    cleaned = clean_text(text)
    if not cleaned:
        return {"original": "", "cleaned": "", "tokens": [], "lemmas": [], 
                "sentences": [], "token_count": 0}
    
    nlp = _get_nlp()
    
    if nlp and nlp is not False:
        # spaCy-based preprocessing
        doc = nlp(cleaned)
        tokens = []
        lemmas = []
        for token in doc:
            if (token.is_alpha
                    and not token.is_stop
                    and token.text.lower() not in ACADEMIC_STOPWORDS
                    and len(token.text) > 2):
                tokens.append(token.text.lower())
                lemmas.append(token.lemma_.lower())
        
        sentences = [sent.text.strip() for sent in doc.sents if sent.text.strip()]
    else:
        # Basic fallback preprocessing (no spaCy)
        words = re.findall(r'\b[a-zA-Z]{3,}\b', cleaned.lower())
        # Basic English stopwords
        basic_stops = {
            'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all',
            'can', 'her', 'was', 'one', 'our', 'out', 'has', 'have',
            'with', 'this', 'that', 'from', 'they', 'been', 'will',
            'their', 'would', 'there', 'about', 'which', 'when',
            'what', 'some', 'them', 'than', 'other', 'into', 'more',
            'these', 'also', 'were', 'such', 'each', 'does',
        }
        all_stops = basic_stops | ACADEMIC_STOPWORDS
        tokens = [w for w in words if w not in all_stops]
        lemmas = tokens  # No lemmatization without spaCy
        sentences = [s.strip() for s in re.split(r'[.!?]+', cleaned) if s.strip()]
    
    return {
        "original": text,
        "cleaned": cleaned,
        "tokens": tokens,
        "lemmas": lemmas,
        "sentences": sentences,
        "token_count": len(tokens),
    }
