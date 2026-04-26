"""
Collaborative Filtering Engine.
Uses SVD matrix factorization on user-item interaction data.
"""
import logging

logger = logging.getLogger('recommendationService')

# In-memory model cache
_svd_model = None


def build_interaction_matrix():
    """
    Build a sparse user-item interaction matrix from UserActivity.
    Returns matrix, user list, item list, and index mappings.
    """
    import numpy as np
    from scipy.sparse import csr_matrix
    from api.models import UserActivity
    
    activities = list(UserActivity.objects.filter(
        activity_type__in=['save', 'view']
    ).values_list('user_id', 'content_id', 'activity_type'))
    
    if not activities:
        return None, [], [], {}, {}
    
    users = sorted(set(a[0] for a in activities))
    items = sorted(set(a[1] for a in activities if a[1]))
    
    if not items:
        return None, users, items, {}, {}
    
    user_idx = {u: i for i, u in enumerate(users)}
    item_idx = {it: i for i, it in enumerate(items)}
    
    rows, cols, vals = [], [], []
    for user_id, content_id, act_type in activities:
        if not content_id or content_id not in item_idx:
            continue
        w = 3.0 if act_type == 'save' else 1.0
        rows.append(user_idx[user_id])
        cols.append(item_idx[content_id])
        vals.append(w)
    
    if not rows:
        return None, users, items, user_idx, item_idx
    
    matrix = csr_matrix(
        (vals, (rows, cols)),
        shape=(len(users), len(items))
    )
    return matrix, users, items, user_idx, item_idx


def train_svd_model(n_components: int = 50):
    """
    Train SVD model on interaction matrix.
    Returns model dict with user/item factors.
    """
    global _svd_model
    import numpy as np
    
    matrix, users, items, user_idx, item_idx = build_interaction_matrix()
    
    if matrix is None or matrix.nnz < 10:
        logger.warning("Not enough interaction data for collaborative filtering "
                       f"(interactions: {matrix.nnz if matrix is not None else 0})")
        _svd_model = None
        return None
    
    # Adjust n_components to not exceed matrix dimensions
    max_components = min(n_components, min(matrix.shape) - 1)
    if max_components < 2:
        logger.warning("Matrix too small for SVD")
        _svd_model = None
        return None
    
    try:
        from sklearn.decomposition import TruncatedSVD
        
        svd = TruncatedSVD(n_components=max_components, random_state=42)
        user_factors = svd.fit_transform(matrix)
        item_factors = svd.components_.T
        
        _svd_model = {
            "user_factors": user_factors,
            "item_factors": item_factors,
            "users": users,
            "items": items,
            "user_idx": user_idx,
            "item_idx": item_idx,
            "explained_variance": float(svd.explained_variance_ratio_.sum()),
        }
        
        logger.info(f"SVD model trained: {len(users)} users, {len(items)} items, "
                     f"explained variance: {_svd_model['explained_variance']:.3f}")
        return _svd_model
    except ImportError:
        logger.error("scikit-learn required for collaborative filtering")
        return None
    except Exception as e:
        logger.error(f"SVD training failed: {e}")
        return None


def get_svd_model():
    """Get or train the SVD model."""
    global _svd_model
    if _svd_model is None:
        train_svd_model()
    return _svd_model


def collaborative_recommend(user_id: int, top_k: int = 20,
                             exclude_ids: set = None) -> list:
    """
    Generate recommendations using collaborative filtering (SVD).
    Returns list of {external_id, score}.
    """
    import numpy as np
    
    model = get_svd_model()
    if model is None:
        return []
    
    if user_id not in model["user_idx"]:
        return []
    
    if exclude_ids is None:
        exclude_ids = set()
    
    u_idx = model["user_idx"][user_id]
    u_vec = model["user_factors"][u_idx]
    
    # Predict scores for all items
    scores = model["item_factors"] @ u_vec
    
    # Rank and return top-K
    top_indices = np.argsort(scores)[::-1]
    
    results = []
    for i in top_indices:
        if i >= len(model["items"]):
            continue
        ext_id = model["items"][i]
        if ext_id in exclude_ids:
            continue
        results.append({
            "external_id": ext_id,
            "score": float(scores[i]),
        })
        if len(results) >= top_k:
            break
    
    return results
