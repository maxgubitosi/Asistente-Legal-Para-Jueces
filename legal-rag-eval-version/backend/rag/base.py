from abc import ABC, abstractmethod
from typing import Tuple, List, Dict, Any

class BaseRAGPipeline(ABC):
    """Interface simple para pipelines RAG"""
    
    @abstractmethod
    def query(self, question: str, top_n: int = 8) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Procesa consulta y retorna respuesta + evidencia
        
        Args:
            question: Pregunta del usuario
            top_n: Número de resultados a recuperar
            
        Returns:
            Tuple[respuesta_generada, lista_de_hits]
        """
        pass
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estadísticas del pipeline"""
        return {"pipeline_type": "base"}
    
    def supports_streaming(self) -> bool:
        """Indica si soporta respuestas streaming"""
        return False