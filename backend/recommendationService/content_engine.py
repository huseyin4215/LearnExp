"""
Content-Based Filtering Engine.
Builds user profile vectors from interaction history and finds similar articles.
"""
import logging
import math
from datetime import datetime

logger = logging.getLogger('recommendationService')

# Interaction weights
WEIGHT_MAP = {
    "save": 3.0,
    "view": 1.0,
    "search": 0.5,
}

# Time decay half-life in days
HALF_LIFE_DAYS = 30


def build_user_profile(user_id: int):
    """
    Build a 384-dim user profile vector from interaction history.
    Weights: save=3x, view=1x, search=0.5x, with exponential time decay.
    Returns numpy array or None if cold start.
    """
    import numpy as np
    from api.models import UserActivity, SavedArticle
    from NLP_ProcessingService.models import ArticleNLPProfile
    
    # Get recent activities (saves and views)
    activities = UserActivity.objects.filter(
        user_id=user_id,
        activity_type__in=['save', 'view']
    ).order_by('-created_at')[:200]
    
    if not activities:
        return None
    
    # Get saved article IDs for boost
    saved_ids = set(
        SavedArticle.objects.filter(user_id=user_id)
        .values_list('external_id', flat=True)
    )
    
    weighted_embeddings = []
    now = datetime.now()
    
    for act in activities:
        if not act.content_id:
            continue
        
        profile = ArticleNLPProfile.objects.filter(
            external_id=act.content_id
        ).first()
        
        if not profile or not profile.embedding:
            continue
        
        emb = np.array(profile.embedding, dtype=np.float32)
        if len(emb) == 0:
            continue
        
        # Base weight by action type
        weight = WEIGHT_MAP.get(act.activity_type, 1.0)
        
        # Time decay: exponential with 30-day half-life
        try:
            age_days = (now - act.created_at.replace(tzinfo=None)).days
        except (AttributeError, TypeError):
            age_days = 0
        decay = math.exp(-0.693 * age_days / HALF_LIFE_DAYS)
        weight *= decay
        
        # Boost if article is saved
        if act.content_id in saved_ids:
            weight *= 1.5
        
        weighted_embeddings.append(emb * weight)
    
    if not weighted_embeddings:
        return None
    
    # Weighted average → user profile vector
    profile_vec = np.mean(weighted_embeddings, axis=0)
    norm = np.linalg.norm(profile_vec)
    if norm > 0:
        profile_vec = profile_vec / norm
    
    return profile_vec


def content_based_recommend(user_id: int, top_k: int = 20,
                             exclude_ids: set = None) -> list:
    """
    Return top-K articles by cosine similarity to user profile vector.
    """
    import numpy as np
    from NLP_ProcessingService.models import ArticleNLPProfile
    
    user_vec = build_user_profile(user_id)
    if user_vec is None:
        return []
    
    if exclude_ids is None:
        exclude_ids = set()
    
    # Get all article embeddings (cap at 5000 for performance)
    all_profiles = ArticleNLPProfile.objects.exclude(
        embedding=[]
    ).exclude(
        external_id__in=exclude_ids
    )[:5000]
    
    scores = []
    for p in all_profiles:
        if not p.embedding:
            continue
        emb = np.array(p.embedding, dtype=np.float32)
        if len(emb) != len(user_vec):
            continue
        
        # Cosine similarity (vectors are normalized, so dot product = cosine)
        sim = float(np.dot(user_vec, emb))
        scores.append({
            "external_id": p.external_id,
            "score": sim,
            "source_table": p.source_table,
        })
    
    scores.sort(key=lambda x: x["score"], reverse=True)
    return scores[:top_k]
