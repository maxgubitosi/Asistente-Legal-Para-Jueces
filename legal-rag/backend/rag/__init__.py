# Base
from .base import BaseRAGPipeline

# Factory principal
from .factory import get_rag_pipeline, get_available_strategies, get_default_strategy, answer

# Acceso directo a estrategias
from .strategies import StandardRAGPipeline

# Alias para compatibilidad (sin wrapper)
RAGPipeline = StandardRAGPipeline

__all__ = [
    # Base
    "BaseRAGPipeline",
    
    # Factory
    "get_rag_pipeline",
    "get_available_strategies",
    "get_default_strategy", 
    "answer",                           # Función de conveniencia
    
    # Estrategias directas
    "StandardRAGPipeline",
    
    # Compatibilidad
    "RAGPipeline"                       # Alias directo a StandardRAGPipeline
]