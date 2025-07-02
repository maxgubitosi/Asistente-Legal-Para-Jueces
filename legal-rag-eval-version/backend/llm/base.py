from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class BaseLLMProvider(ABC):
    """Interface simple para proveedores LLM"""
    
    @abstractmethod
    def generate(
        self, 
        messages: List[Dict[str, str]], 
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> str:
        """
        Genera respuesta usando el modelo LLM
        
        Args:
            messages: Lista de mensajes en formato OpenAI
            max_tokens: Límite de tokens
            temperature: Temperatura para sampling
            **kwargs: Parámetros adicionales
            
        Returns:
            Texto generado por el modelo
        """
        pass
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estadísticas del proveedor"""
        return {"provider_type": "base"}
    
    def supports_streaming(self) -> bool:
        """Indica si soporta streaming"""
        return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """Información del modelo"""
        return {"model": "unknown"}