"""
API Adapters Package
Adapter pattern implementation for different academic APIs
"""
from .factory import AdapterFactory
from .base import BaseAPIAdapter, NormalizedArticle

__all__ = ['AdapterFactory', 'BaseAPIAdapter', 'NormalizedArticle']
