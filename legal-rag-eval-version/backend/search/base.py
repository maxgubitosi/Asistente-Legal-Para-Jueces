# backend/search/base.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseRetriever(ABC):
    """Interface simple para retrievers"""
    
    @abstractmethod
    def query(self, question: str, top_n: int = 10) -> List[Dict[str, Any]]:
        """
        Ejecuta búsqueda y retorna resultados
        
        Args:
            question: Pregunta del usuario
            top_n: Número de resultados
            
        Returns:
            Lista de hits con campos: score, expte, section, paragraph, path
        """
        pass
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estadísticas del retriever"""
        return {"retriever_type": "base"}
    
    def supports_reranking(self) -> bool:
        """Indica si soporta re-ranking"""
        return False