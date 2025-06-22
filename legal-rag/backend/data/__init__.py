from .models import LegalParagraph, QueryRequest, QueryResponse, Hit, ProcessingStats

# Factory principal
from .factory import get_processor, get_available_modes, get_default_mode, iter_paragraphs

# Acceso directo a procesadores
from .processing import StandardProcessor

# Alias para compatibilidad (sin wrapper)
DataProcessor = StandardProcessor

__all__ = [
    # Models
    "LegalParagraph",
    "QueryRequest", 
    "QueryResponse",
    "Hit",
    "ProcessingStats",
    
    # Factory
    "get_processor",
    "get_available_modes",
    "get_default_mode",
    "iter_paragraphs",          # Función de conveniencia
    
    # Procesadores directos
    "StandardProcessor",
    
    # Compatibilidad
    "DataProcessor"             # Alias directo a StandardProcessor
]