"""
Hybrid Recommendation Engine.
Combines content-based and collaborative filtering with adaptive weights.
Includes cold start handling and diversity re-ranking.
"""
import logging

logger = logging.getLogger('recommendationService')


def get_viewed_ids(user_id: int) -> set:
    """Get set of article IDs the user has already interacted with."""
    from api.models import UserActivity
    return set(
        UserActivity.objects.filter(
            user_id=user_id,
            activity_type__in=['save', 'view']
        ).values_list('content_id', flat=True)
    )


def cold_start_recommend(user_id: int, top_k: int = 20) -> list:
    """
    Fallback recommendations for users with no/little interaction history.
    Strategy:
    1. Use profile interests to build query vector
    2. Fall back to globally popular articles
    """
    from api.models import UserProfile, SavedArticle
    from NLP_ProcessingService.models import ArticleNLPProfile
    
    # Strategy 1: Interest-based
    try:
        profile = UserProfile.objects.filter(user_id=user_id).first()
        if profile and (profile.interests or profile.research_areas):
            interests_text = " ".join(
                (profile.interests or []) + (profile.research_areas or [])
            )
            if interests_text.strip():
                from NLP_ProcessingService.embedder import generate_embedding
                import numpy as np
                
                query_vec = np.array(
                    generate_embedding(interests_text, ""),
                    dtype=np.float32
                )
                
                # Search against all profiles
                all_profiles = ArticleNLPProfile.objects.exclude(embedding=[])[:3000]
                scores = []
                for p in all_profiles:
                    if not p.embedding:
                        continue
                    emb = np.array(p.embedding, dtype=np.float32)
                    if len(emb) != len(query_vec):
                        continue
                    sim = float(np.dot(query_vec, emb))
                    scores.append({
                        "external_id": p.external_id,
                        "score": sim,
                        "source_table": p.source_table,
                    })
                
                scores.sort(key=lambda x: x["score"], reverse=True)
                if scores:
                    return scores[:top_k]
    except Exception as e:
        logger.error(f"Interest-based cold start failed: {e}")
    
    # Strategy 2: Popular articles (by save count)
    from django.db.models import Count
    popular = (
        SavedArticle.objects
        .values('external_id', 'title')
        .annotate(save_count=Count('id'))
        .order_by('-save_count')[:top_k]
    )
    
    return [
        {"external_id": p["external_id"], "score": float(p["save_count"]),
         "source_table": "article"}
        for p in popular
    ]


def diversity_rerank(candidates: list, lambda_param: float = 0.7,
                      top_k: int = 20) -> list:
    """
    Apply Maximal Marginal Relevance (MMR) for diversity.
    Balances relevance with diversity to avoid showing all similar articles.
    """
    if len(candidates) <= top_k:
        return candidates
    
    try:
        import numpy as np
        from NLP_ProcessingService.models import ArticleNLPProfile
        
        # Load embeddings for candidates
        ext_ids = [c["external_id"] for c in candidates]
        profiles = {
            p.external_id: np.array(p.embedding, dtype=np.float32)
            for p in ArticleNLPProfile.objects.filter(
                external_id__in=ext_ids
            ).exclude(embedding=[])
        }
        
        # If we can't load embeddings, just return top-K by score
        if not profiles:
            return candidates[:top_k]
        
        selected = []
        remaining = list(candidates)
        
        # Pick the highest-scoring item first
        selected.append(remaining.pop(0))
        
        while len(selected) < top_k and remaining:
            best_score = -float('inf')
            best_idx = 0
            
            for i, cand in enumerate(remaining):
                relevance = cand["score"]
                
                # Max similarity to already selected items
                cand_emb = profiles.get(cand["external_id"])
                if cand_emb is None:
                    max_sim = 0.0
                else:
                    max_sim = 0.0
                    for sel in selected:
                        sel_emb = profiles.get(sel["external_id"])
                        if sel_emb is not None and len(sel_emb) == len(cand_emb):
                            sim = float(np.dot(cand_emb, sel_emb))
                            max_sim = max(max_sim, sim)
                
                mmr = lambda_param * relevance - (1 - lambda_param) * max_sim
                if mmr > best_score:
                    best_score = mmr
                    best_idx = i
            
            selected.append(remaining.pop(best_idx))
        
        return selected
    except Exception as e:
        logger.error(f"Diversity reranking failed: {e}")
        return candidates[:top_k]


def hybrid_recommend(user_id: int, top_k: int = 20) -> list:
    """
    Main recommendation function.
    Combines content-based + collaborative with adaptive alpha/beta.
    
    Formula: final_score = alpha * content_score + beta * collab_score
    
    Adaptive weighting:
    - <5 interactions: alpha=0.9, beta=0.1 (content-heavy)
    - 5-50 interactions: alpha=0.65, beta=0.35 (default)
    - >50 interactions: alpha=0.5, beta=0.5 (balanced)
    """
    from api.models import UserActivity
    from .content_engine import content_based_recommend
    from .collab_engine import collaborative_recommend
    
    # Count user interactions for adaptive weighting
    interaction_count = UserActivity.objects.filter(
        user_id=user_id,
        activity_type__in=['save', 'view']
    ).count()
    
    # Cold start check
    if interaction_count < 3:
        logger.info(f"Cold start for user {user_id} ({interaction_count} interactions)")
        results = cold_start_recommend(user_id, top_k=top_k)
        return results
    
    # Adaptive alpha/beta
    if interaction_count < 5:
        alpha, beta = 0.9, 0.1
    elif interaction_count > 50:
        alpha, beta = 0.5, 0.5
    else:
        alpha, beta = 0.65, 0.35
    
    # Get already-viewed IDs to exclude
    exclude_ids = get_viewed_ids(user_id)
    
    # Content-based recommendations
    content_results = content_based_recommend(
        user_id, top_k=100, exclude_ids=exclude_ids
    )
    
    # Collaborative recommendations
    collab_results = collaborative_recommend(
        user_id, top_k=100, exclude_ids=exclude_ids
    )
    
    # Merge scores
    score_map = {}
    for r in content_results:
        score_map[r["external_id"]] = {
            "content": r["score"],
            "collab": 0.0,
            "source_table": r.get("source_table", "article"),
        }
    for r in collab_results:
        if r["external_id"] in score_map:
            score_map[r["external_id"]]["collab"] = r["score"]
        else:
            score_map[r["external_id"]] = {
                "content": 0.0,
                "collab": r["score"],
                "source_table": "article",
            }
    
    # Normalize scores to [0, 1] range
    if score_map:
        max_content = max((s["content"] for s in score_map.values()), default=1) or 1
        max_collab = max((s["collab"] for s in score_map.values()), default=1) or 1
        
        for ext_id in score_map:
            score_map[ext_id]["content"] /= max_content
            score_map[ext_id]["collab"] /= max_collab
    
    # Compute final hybrid scores
    final = []
    for ext_id, scores in score_map.items():
        combined = alpha * scores["content"] + beta * scores["collab"]
        final.append({
            "external_id": ext_id,
            "score": round(combined, 4),
            "source_table": scores["source_table"],
        })
    
    final.sort(key=lambda x: x["score"], reverse=True)
    
    # Apply diversity re-ranking
    final = diversity_rerank(final, lambda_param=0.7, top_k=top_k)
    
    return final
