"""
Factory principal para proveedores LLM
"""
import logging
from typing import Dict, List
from backend.config import get_settings

settings = get_settings()

logger = logging.getLogger(__name__)

def get_llm_provider(provider: str = None, **kwargs):
    """Factory principal para proveedores LLM"""
    provider = provider or settings.llm_provider

    # Lazy imports para evitar cargar todo al inicio
    providers = {
        "azure": lambda: _import_azure(),
        # "openai": lambda: _import_openai(),    # ← Futuro
        # "local": lambda: _import_local(),      # ← Futuro
    }
    
    if provider not in providers:
        available = list(providers.keys())
        raise ValueError(f"Provider '{provider}' no disponible. Opciones: {available}")
    
    logger.info(f"🤖 Creating {provider} LLM provider")
    provider_class = providers[provider]()
    return provider_class(**kwargs)

def _import_azure():
    """Lazy import de AzureProvider"""
    from .providers.azure import AzureProvider
    return AzureProvider

def get_available_providers():
    """Retorna proveedores disponibles"""
    return ["azure"]

def get_default_provider():
    """Retorna proveedor por defecto"""
    return settings.llm_provider

# Re-exportar para compatibilidad
from .providers.azure import AzureProvider, get_azure_client

# Aliases para compatibilidad
AzureLLMProvider = AzureProvider

# Singleton global para compatibilidad
_llm_provider = None

def get_azure_provider() -> AzureProvider:
    """Singleton para el proveedor Azure (compatibilidad)"""
    global _llm_provider
    if _llm_provider is None:
        _llm_provider = get_llm_provider("azure")
    return _llm_provider

def run_llm(messages: List[Dict[str, str]], max_tokens: int = 300) -> str:
    """
    Función wrapper para mantener compatibilidad total
    
    Args:
        messages: Lista de mensajes en formato OpenAI
        max_tokens: Límite de tokens
    
    Returns:
        Texto generado
    """
    provider = get_azure_provider()
    return provider.generate(messages, max_tokens=max_tokens)