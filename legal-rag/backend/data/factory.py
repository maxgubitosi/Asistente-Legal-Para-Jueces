from pathlib import Path
import logging
from backend.config import get_settings

settings = get_settings()

logger = logging.getLogger(__name__)

def get_processor(mode: str = None, **kwargs):
    """Factory para crear procesadores de datos según modo"""
    mode = mode or settings.processing_mode

    # Lazy imports para evitar cargar todo al inicio
    processors = {
        "standard": lambda: _import_standard(),
        # "parallel": lambda: _import_parallel(),    # ← Futuro
        # "streaming": lambda: _import_streaming(),  # ← Futuro
    }
    
    if mode not in processors:
        available = list(processors.keys())
        raise ValueError(f"Modo '{mode}' no disponible. Opciones: {available}")
    
    logger.info(f"📊 Creating {mode} data processor")
    processor_class = processors[mode]()
    return processor_class(**kwargs)

def _import_standard():
    """Lazy import de StandardProcessor"""
    from .processing.standard import StandardProcessor
    return StandardProcessor

def get_available_modes():
    """Retorna modos disponibles"""
    return ["standard"]

def get_default_mode():
    """Retorna modo por defecto"""
    return settings.processing_mode

# Función de conveniencia sin wrapper complejo
def iter_paragraphs(json_dir):
    """Función de conveniencia para procesamiento rápido"""
    if isinstance(json_dir, str):
        json_dir = Path(json_dir)
    
    processor = get_processor("standard")
    yield from processor.process_directory(json_dir)