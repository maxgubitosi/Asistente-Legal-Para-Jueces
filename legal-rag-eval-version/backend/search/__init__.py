# Base e infraestructura
from .base import BaseRetriever
from .builders import BM25Builder, QdrantBuilder, EmbeddingBuilder
from .indexing import build_indexes

# Factory principal
from .factory import get_retriever, get_available_strategies, get_default_strategy

# Acceso directo a estrategias
from .strategies import HybridRetriever, DenseOnlyRetriever

__all__ = [
    # Base e infraestructura
    "BaseRetriever",
    "BM25Builder",
    "QdrantBuilder", 
    "EmbeddingBuilder",
    "build_indexes",
    
    # Factory
    "get_retriever",
    "get_available_strategies", 
    "get_default_strategy",
    
    # Estrategias directas
    "HybridRetriever",
    "DenseOnlyRetriever"
]