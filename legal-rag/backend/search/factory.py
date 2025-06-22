import logging
from backend.config import get_settings

settings = get_settings()

logger = logging.getLogger(__name__)

def get_retriever(strategy: str = None, **kwargs):
    """Factory para crear retrievers según estrategia"""
    strategy = strategy or settings.search_strategy

    # Lazy imports para evitar cargar todo al inicio
    strategies = {
        "hybrid": lambda: _import_hybrid(),
        "dense_only": lambda: _import_dense_only(),
        # "lexical_only": lambda: _import_lexical_only(),  # ← Futuro
    }
    
    if strategy not in strategies:
        available = list(strategies.keys())
        raise ValueError(f"Strategy '{strategy}' no disponible. Opciones: {available}")
    
    logger.info(f"🔍 Creating {strategy} retriever")
    retriever_class = strategies[strategy]()
    return retriever_class(**kwargs)

def _import_hybrid():
    """Lazy import de HybridRetriever"""
    from .strategies.hybrid import HybridRetriever
    return HybridRetriever

def _import_dense_only():
    """Lazy import de DenseOnlyRetriever"""  
    from .strategies.dense_only import DenseOnlyRetriever
    return DenseOnlyRetriever

def get_available_strategies():
    """Retorna estrategias disponibles"""
    return ["hybrid", "dense_only"]

def get_default_strategy():
    """Retorna estrategia por defecto"""
    return settings.search_strategy