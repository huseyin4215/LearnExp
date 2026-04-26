"""
Recommendation Service API Views.
Provides personalized recommendations, NLP processing status, and similar articles.
"""
import logging
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger('recommendationService')


def _auto_process_articles(batch_size: int = 50):
    """Synchronously process articles when no NLP profiles exist."""
    try:
        from NLP_ProcessingService.pipeline import process_single_article, save_nlp_profile
        from NLP_ProcessingService.models import ArticleNLPProfile
        
        processed_ids = set(ArticleNLPProfile.objects.values_list('external_id', flat=True))
        count = 0
        
        # Process API articles
        try:
            from api_collecter.models import Article
            for article in Article.objects.exclude(external_id__in=processed_ids)[:batch_size]:
                result = process_single_article(
                    article.external_id, article.title, article.abstract or "", "article"
                )
                save_nlp_profile(result)
                count += 1
        except Exception as e:
            logger.error(f"Auto-process API articles failed: {e}")
        
        # Process scraped content
        try:
            from webscraping.models import ScrapedContent
            for item in ScrapedContent.objects.exclude(external_id__in=processed_ids)[:batch_size]:
                result = process_single_article(
                    item.external_id, item.title, item.abstract or "", "scraped"
                )
                save_nlp_profile(result)
                count += 1
        except Exception as e:
            logger.error(f"Auto-process scraped content failed: {e}")
        
        logger.info(f"Auto-processed {count} articles for NLP")
    except Exception as e:
        logger.error(f"Auto-processing failed: {e}")


@api_view(['GET'])
@permission_classes([AllowAny])
def get_recommendations(request):
    """
    GET /api/recommendations/?user_id=1&limit=20
    Returns personalized article recommendations for a user.
    """
    user_id = request.query_params.get('user_id')
    top_k = int(request.query_params.get('limit', 20))
    
    if not user_id:
        return Response(
            {'success': False, 'message': 'user_id gerekli'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        from .hybrid import hybrid_recommend
        from NLP_ProcessingService.models import ArticleNLPProfile
        
        # Auto-process if no NLP profiles exist yet
        nlp_count = ArticleNLPProfile.objects.count()
        if nlp_count == 0:
            _auto_process_articles(batch_size=50)
        
        results = hybrid_recommend(int(user_id), top_k=top_k)
        
        if not results:
            return Response({
                'success': True,
                'recommendations': [],
                'message': 'Henüz yeterli veri yok. Daha fazla makale keşfedin!',
                'strategy': 'no_data'
            })
        
        # Hydrate with full article data
        hydrated = _hydrate_results(results)
        
        return Response({
            'success': True,
            'recommendations': hydrated,
            'count': len(hydrated),
        })
    except Exception as e:
        logger.error(f"Recommendation failed for user {user_id}: {e}")
        return Response(
            {'success': False, 'message': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def get_similar_articles(request):
    """
    GET /api/recommendations/similar/?external_id=arxiv:123&limit=10
    Returns articles similar to a given article.
    """
    external_id = request.query_params.get('external_id')
    top_k = int(request.query_params.get('limit', 10))
    
    if not external_id:
        return Response(
            {'success': False, 'message': 'external_id gerekli'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        import numpy as np
        from NLP_ProcessingService.models import ArticleNLPProfile
        
        # Get the target article's embedding
        target = ArticleNLPProfile.objects.filter(
            external_id=external_id
        ).first()
        
        if not target or not target.embedding:
            return Response({
                'success': True,
                'similar': [],
                'message': 'Makale henüz işlenmedi'
            })
        
        target_vec = np.array(target.embedding, dtype=np.float32)
        
        # Search all profiles
        all_profiles = ArticleNLPProfile.objects.exclude(
            external_id=external_id
        ).exclude(embedding=[])[:3000]
        
        scores = []
        for p in all_profiles:
            emb = np.array(p.embedding, dtype=np.float32)
            if len(emb) != len(target_vec):
                continue
            sim = float(np.dot(target_vec, emb))
            scores.append({
                "external_id": p.external_id,
                "score": sim,
                "source_table": p.source_table,
            })
        
        scores.sort(key=lambda x: x["score"], reverse=True)
        top_results = scores[:top_k]
        
        hydrated = _hydrate_results(top_results)
        
        return Response({
            'success': True,
            'similar': hydrated,
            'count': len(hydrated),
        })
    except Exception as e:
        logger.error(f"Similar articles failed for {external_id}: {e}")
        return Response(
            {'success': False, 'message': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def nlp_status(request):
    """
    GET /api/recommendations/nlp-status/
    Returns NLP processing statistics.
    """
    from NLP_ProcessingService.models import ArticleNLPProfile
    
    total_processed = ArticleNLPProfile.objects.count()
    
    # Count unprocessed
    total_articles = 0
    total_scraped = 0
    try:
        from api_collecter.models import Article
        total_articles = Article.objects.count()
    except Exception:
        pass
    try:
        from webscraping.models import ScrapedContent
        total_scraped = ScrapedContent.objects.count()
    except Exception:
        pass
    
    total_content = total_articles + total_scraped
    
    return Response({
        'success': True,
        'nlp_processed': total_processed,
        'total_content': total_content,
        'unprocessed': max(0, total_content - total_processed),
        'coverage': round(total_processed / total_content * 100, 1) if total_content > 0 else 0,
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def trigger_nlp_processing(request):
    """
    POST /api/recommendations/process/
    Manually trigger NLP processing for unprocessed articles.
    """
    batch_size = request.data.get('batch_size', 50)
    
    try:
        from NLP_ProcessingService.tasks import process_all_unprocessed_task
        result = process_all_unprocessed_task.delay(batch_size=batch_size)
        return Response({
            'success': True,
            'message': f'NLP processing task queued (batch: {batch_size})',
            'task_id': str(result.id) if result else None
        })
    except Exception as e:
        # If Celery is not available, process synchronously
        logger.warning(f"Celery unavailable, processing synchronously: {e}")
        from NLP_ProcessingService.pipeline import process_single_article, save_nlp_profile
        from NLP_ProcessingService.models import ArticleNLPProfile
        
        processed_ids = set(
            ArticleNLPProfile.objects.values_list('external_id', flat=True)
        )
        
        count = 0
        try:
            from api_collecter.models import Article
            for article in Article.objects.exclude(
                external_id__in=processed_ids
            )[:batch_size]:
                result = process_single_article(
                    article.external_id, article.title, article.abstract or ""
                )
                save_nlp_profile(result)
                count += 1
        except Exception as ex:
            logger.error(f"Sync processing failed: {ex}")
        
        return Response({
            'success': True,
            'message': f'{count} articles processed synchronously',
            'processed': count,
        })


def _hydrate_results(results: list) -> list:
    """Enrich recommendation results with full article metadata."""
    hydrated = []
    
    ext_ids = [r["external_id"] for r in results]
    score_map = {r["external_id"]: r["score"] for r in results}
    
    # Fetch from Article table
    try:
        from api_collecter.models import Article
        articles = Article.objects.filter(external_id__in=ext_ids)
        
        for a in articles:
            hydrated.append({
                "external_id": a.external_id,
                "title": a.title,
                "abstract": (a.abstract or "")[:300],
                "authors": a.authors or [],
                "published_date": str(a.published_date) if a.published_date else "",
                "url": a.url,
                "pdf_url": a.pdf_url,
                "image_url": a.image_url,
                "doi": a.doi,
                "source": a.api_source.name if a.api_source else "Unknown",
                "categories": a.categories or [],
                "score": score_map.get(a.external_id, 0),
            })
    except Exception as e:
        logger.error(f"Article hydration failed: {e}")
    
    # Fetch remaining from ScrapedContent
    found_ids = {h["external_id"] for h in hydrated}
    missing_ids = [eid for eid in ext_ids if eid not in found_ids]
    
    if missing_ids:
        try:
            from webscraping.models import ScrapedContent
            scraped = ScrapedContent.objects.filter(external_id__in=missing_ids)
            
            for s in scraped:
                hydrated.append({
                    "external_id": s.external_id,
                    "title": s.title,
                    "abstract": (s.abstract or "")[:300],
                    "authors": s.authors or [],
                    "published_date": str(s.published_date) if s.published_date else "",
                    "url": s.source_url,
                    "pdf_url": s.pdf_url or "",
                    "image_url": s.image_url or "",
                    "doi": s.doi or "",
                    "source": s.scraper_config.name if s.scraper_config else "Scraper",
                    "categories": s.categories or [],
                    "score": score_map.get(s.external_id, 0),
                })
        except Exception as e:
            logger.error(f"ScrapedContent hydration failed: {e}")
    
    # Sort by original score order
    hydrated.sort(key=lambda x: x["score"], reverse=True)
    return hydrated
