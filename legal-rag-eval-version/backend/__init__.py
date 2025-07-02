"""
Legal RAG Backend

Sistema RAG modular para consultas legales con:
- Búsqueda híbrida (dense + lexical)
- Pipeline RAG optimizado
- API REST con FastAPI
- Procesamiento de datos robusto
"""

# Factory Manager (nueva API recomendada)
from .factory_manager import (
    get_factory_manager,
    get_configured_processor,
    get_configured_retriever, 
    get_configured_llm,
    get_configured_rag
)

# APIs individuales (compatibilidad)
from . import data, search, llm, rag
from .config import get_settings

__all__ = [
    # Factory Manager (recomendado)
    "get_factory_manager",
    "get_configured_processor",
    "get_configured_retriever",
    "get_configured_llm", 
    "get_configured_rag",
    
    # Módulos individuales
    "data",
    "search", 
    "llm",
    "rag",
    
    # Config
    "get_settings"
]