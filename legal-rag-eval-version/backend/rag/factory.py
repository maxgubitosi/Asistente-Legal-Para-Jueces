import logging
from backend.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

def _import_standard():
    """Lazy import de StandardRAGPipeline"""
    from .strategies.standard import StandardRAGPipeline
    return StandardRAGPipeline

def _import_conversational():
    """Lazy import de ConversationalRAGPipeline"""
    from .strategies.conversational import ConversationalRAGPipeline
    return ConversationalRAGPipeline

def _import_enriched():
    """Lazy import de EnrichedRAGPipeline"""
    from .strategies.enriched import EnrichedRAGPipeline
    return EnrichedRAGPipeline

def get_rag_pipeline(strategy: str = None, **kwargs):
    """Factory para crear pipelines RAG según estrategia"""
    strategy = strategy or settings.rag_strategy
    
    # Lazy imports para evitar cargar todo al inicio
    strategies = {
        "standard": lambda: _import_standard(),
        "conversational": lambda: _import_conversational(),
        "enriched": lambda: _import_enriched(),
        # "multi_step": lambda: _import_multi_step(),  # ← Futuro
    }
    
    if strategy not in strategies:
        available = list(strategies.keys())
        raise ValueError(f"Strategy '{strategy}' no disponible. Opciones: {available}")
    
    logger.info(f"🧠 Creating {strategy} RAG pipeline")
    pipeline_class = strategies[strategy]()
    
    # Manejar kwargs según la estrategia
    if strategy == "standard":
        # StandardRAGPipeline no acepta parámetros
        return pipeline_class()
    elif strategy == "conversational":
        # ConversationalRAGPipeline sí acepta parámetros
        return pipeline_class(**kwargs)
    elif strategy == "enriched":
        return pipeline_class()
    else:
        return pipeline_class(**kwargs)

def get_available_strategies():
    """Retorna estrategias disponibles"""
    return ["standard", "conversational", "enriched"]

def get_default_strategy():
    """Retorna estrategia por defecto"""
    return settings.rag_strategy

# Función de conveniencia sin singleton complejo
def answer(question: str, top_n: int = 8, strategy: str = "standard"):
    """Función de conveniencia para consultas rápidas"""
    pipeline = get_rag_pipeline(strategy)
    return pipeline.query(question, top_n)