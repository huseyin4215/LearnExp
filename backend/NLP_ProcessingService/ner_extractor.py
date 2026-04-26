"""
Named Entity Recognition (NER) for academic content.
Extracts persons, organizations, locations, and miscellaneous entities.
"""
import re
import logging

logger = logging.getLogger('NLP_ProcessingService')

_nlp = None

def _get_nlp():
    global _nlp
    if _nlp is None:
        try:
            import spacy
            _nlp = spacy.load("en_core_web_sm")
        except (ImportError, OSError):
            logger.warning("spaCy not available. Using regex-based NER fallback.")
            _nlp = False
    return _nlp


def extract_entities_spacy(text: str) -> dict:
    """Extract entities using spaCy's NER pipeline."""
    nlp = _get_nlp()
    if not nlp or nlp is False:
        return extract_entities_fallback(text)
    
    doc = nlp(text[:5000])  # Cap text length for performance
    
    entities = {
        "persons": [],
        "organizations": [],
        "locations": [],
        "misc": [],
    }
    
    label_map = {
        "PERSON": "persons",
        "ORG": "organizations",
        "GPE": "locations",
        "LOC": "locations",
        "FAC": "locations",
    }
    
    seen = set()
    for ent in doc.ents:
        key = f"{ent.label_}:{ent.text.lower()}"
        if key in seen:
            continue
        seen.add(key)
        
        category = label_map.get(ent.label_, "misc")
        entities[category].append({
            "text": ent.text,
            "label": ent.label_,
        })
    
    return entities


def extract_entities_fallback(text: str) -> dict:
    """Fallback entity extraction using regex patterns."""
    entities = {
        "persons": [],
        "organizations": [],
        "locations": [],
        "misc": [],
    }
    
    # University/institution patterns
    org_patterns = [
        r'(?:University|Institute|Laboratory|Department|College|School|Center|Centre)\s+(?:of\s+)?[A-Z][a-zA-Z\s]+',
        r'[A-Z][a-zA-Z]+\s+(?:University|Institute|Lab|College)',
        r'(?:MIT|Stanford|Harvard|Oxford|Cambridge|IEEE|ACM|NASA|NIH|WHO|CERN)',
    ]
    for pattern in org_patterns:
        matches = re.findall(pattern, text)
        for m in matches:
            entities["organizations"].append({"text": m.strip(), "label": "ORG"})
    
    return entities


def extract_entities(text: str) -> dict:
    """Main entry point for entity extraction."""
    if not text or len(text.strip()) < 10:
        return {"persons": [], "organizations": [], "locations": [], "misc": []}
    return extract_entities_spacy(text)
