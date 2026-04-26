"""
NLP Processing Pipeline - Main orchestrator.
Coordinates preprocessing, keyword extraction, NER, and embedding generation.
"""
import logging

logger = logging.getLogger('NLP_ProcessingService')


def process_single_article(external_id: str, title: str, abstract: str = "",
                            source_table: str = "article") -> dict:
    """
    Process a single article through the complete NLP pipeline.
    Returns a dict suitable for ArticleNLPProfile creation.
    """
    from .preprocessing import preprocess
    from .keyword_extractor import extract_keywords
    from .ner_extractor import extract_entities
    from .embedder import generate_embedding
    
    full_text = f"{title}. {abstract}" if abstract else title
    
    # 1. Preprocess
    preprocessed = preprocess(full_text)
    
    # 2. Keywords
    keywords = extract_keywords(full_text, top_n=10)
    
    # 3. Entities
    entities = extract_entities(full_text)
    
    # 4. Embedding
    embedding = generate_embedding(title, abstract)
    
    return {
        "external_id": external_id,
        "source_table": source_table,
        "keywords": keywords,
        "entities": entities,
        "embedding": embedding,
        "token_count": preprocessed.get("token_count", 0),
        "language": "en",
    }


def save_nlp_profile(data: dict):
    """Save or update an NLP profile in the database."""
    from .models import ArticleNLPProfile
    
    ArticleNLPProfile.objects.update_or_create(
        external_id=data["external_id"],
        defaults={
            "source_table": data.get("source_table", "article"),
            "keywords": data.get("keywords", []),
            "entities": data.get("entities", {}),
            "embedding": data.get("embedding", []),
            "embedding_model": "all-MiniLM-L6-v2",
            "token_count": data.get("token_count", 0),
            "language": data.get("language", "en"),
            "topic_id": data.get("topic_id"),
            "topic_confidence": data.get("topic_confidence"),
            "topic_words": data.get("topic_words", []),
        }
    )
    logger.info(f"NLP profile saved for {data['external_id']}")
