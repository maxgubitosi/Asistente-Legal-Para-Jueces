import logging
import time
from typing import List, Dict, Any, Optional
from openai import AzureOpenAI
from backend.config import get_settings


from ..base import BaseLLMProvider

settings = get_settings()

logger = logging.getLogger(__name__)

# Cliente singleton
_azure_client = None

def get_azure_client() -> AzureOpenAI:
    """Singleton para cliente Azure OpenAI"""
    global _azure_client
    if _azure_client is None:
        logger.info("🔑 Inicializando cliente Azure OpenAI...")
        _azure_client = AzureOpenAI(
            api_key=settings.azure_api_key,
            api_version="2024-02-01",
            azure_endpoint=settings.azure_endpoint
        )
    return _azure_client

class AzureProvider(BaseLLMProvider):
    """Proveedor Azure OpenAI optimizado - migrado de azure.py"""
    
    def __init__(self):
        self.client = None
        self.deployment = settings.azure_deployment
        self.default_max_tokens = settings.llm_max_tokens
        self.default_temperature = settings.llm_temperature
        self.timeout = settings.llm_timeout
        self.max_retries = settings.llm_max_retries
        
        logger.info(f"🤖 AzureProvider configured: {self.deployment}")
        
    def _get_client(self) -> AzureOpenAI:
        """Lazy loading del cliente"""
        if self.client is None:
            self.client = get_azure_client()
        return self.client
    
    def generate(
        self, 
        messages: List[Dict[str, str]], 
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> str:
        """
        Genera respuesta usando Azure OpenAI con retry y métricas
        
        Args:
            messages: Lista de mensajes en formato OpenAI
            max_tokens: Límite de tokens (usa default si None)
            temperature: Temperatura para sampling (usa default si None)
            **kwargs: Parámetros adicionales para la API
        
        Returns:
            Texto generado por el modelo
        """
        start_time = time.time()
        
        # Configuración efectiva
        effective_max_tokens = max_tokens or self.default_max_tokens
        effective_temperature = temperature if temperature is not None else self.default_temperature
        
        client = self._get_client()
        
        # Parámetros de la llamada
        call_params = {
            "model": self.deployment,
            "messages": messages,
            "max_tokens": effective_max_tokens,
            "temperature": effective_temperature,
            "timeout": self.timeout,
            **kwargs
        }
        
        # Intentos con retry
        last_error = None
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"🤖 Azure OpenAI call (attempt {attempt + 1}/{self.max_retries})")
                
                response = client.chat.completions.create(**call_params)
                
                # Extraer respuesta
                if response.choices and response.choices[0].message:
                    content = response.choices[0].message.content
                    if content:
                        generation_time = time.time() - start_time
                        
                        # Logging de métricas
                        self._log_generation_metrics(
                            generation_time, 
                            response, 
                            effective_max_tokens, 
                            len(messages)
                        )
                        
                        return content.strip()
                
                logger.warning("⚠️ Empty response from Azure OpenAI")
                return "Error: Empty model response"
                
            except Exception as e:
                last_error = e
                logger.warning(f"⚠️ Error on attempt {attempt + 1}: {str(e)}")
                
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.info(f"🕐 Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
        
        # Si llegamos aquí, fallaron todos los intentos
        logger.error(f"❌ Failed after {self.max_retries} attempts: {last_error}")
        return f"Error: Could not generate response after {self.max_retries} attempts."
    
    def _log_generation_metrics(self, generation_time, response, max_tokens, num_messages):
        """Log detallado de métricas de generación"""
        usage = getattr(response, 'usage', None)
        
        if usage:
            logger.info(f"🤖 LLM completed in {generation_time:.3f}s:")
            logger.info(f"   Tokens: {usage.prompt_tokens} prompt + {usage.completion_tokens} completion = {usage.total_tokens} total")
            logger.info(f"   Efficiency: {usage.completion_tokens/generation_time:.1f} tokens/sec")
            logger.info(f"   Config: max_tokens={max_tokens}, messages={num_messages}")
        else:
            logger.info(f"🤖 LLM completed in {generation_time:.3f}s (no usage stats)")
    
    def get_stats(self) -> Dict[str, Any]:
        """Estadísticas del proveedor Azure"""
        return {
            "provider_type": "azure",
            "deployment": self.deployment,
            "default_max_tokens": self.default_max_tokens,
            "default_temperature": self.default_temperature,
            "timeout": self.timeout,
            "max_retries": self.max_retries,
            "client_initialized": self.client is not None
        }
    
    def get_model_info(self) -> Dict[str, Any]:
        """Información del modelo Azure"""
        return {
            "model": self.deployment,
            "provider": "Azure OpenAI",
            "api_version": "2024-02-01"
        }
    
    def supports_streaming(self) -> bool:
        """Azure OpenAI soporta streaming"""
        return True

# Alias para compatibilidad
AzureLLMProvider = AzureProvider