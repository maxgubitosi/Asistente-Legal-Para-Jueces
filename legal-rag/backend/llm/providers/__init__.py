from .azure import AzureProvider
# from .openai import OpenAIProvider    # ← Futuro
# from .local import LocalProvider      # ← Futuro
from backend.config import get_settings

settings = get_settings()

def get_llm_provider(provider: str = None, **kwargs):
    """Factory simple para proveedores LLM"""
    provider = provider or settings.llm_provider

    providers = {
        "azure": AzureProvider,
        # "openai": OpenAIProvider,     # ← Futuro
        # "local": LocalProvider,       # ← Futuro
    }
    
    if provider not in providers:
        raise ValueError(f"Provider '{provider}' no disponible. Opciones: {list(providers.keys())}")
    
    return providers[provider](**kwargs)

# Solo exports, sin factory (el factory está en llm/factory.py)
from .azure import AzureProvider, AzureLLMProvider, get_azure_client

__all__ = [
    "AzureProvider", 
    "AzureLLMProvider",     # Alias compatibilidad
    "get_azure_client"      # Para compatibilidad directa
]