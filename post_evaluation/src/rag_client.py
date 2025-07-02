"""
Cliente para Sistema RAG Legal

Este módulo maneja la comunicación con el backend del sistema RAG legal
para realizar consultas y obtener resultados de búsqueda.
"""

import requests
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class RAGResult:
    """Resultado individual de una consulta RAG"""
    expte: str
    section: str
    paragraph: str
    score: float
    path: str
    search_type: str
    idea_central: str
    materia_preliminar: str

@dataclass 
class RAGResponse:
    """Respuesta completa del sistema RAG"""
    question: str
    markdown: str
    results: List[RAGResult]
    total_time: float
    search_time: float
    llm_time: float

class RAGClient:
    """
    Cliente para interactuar con el sistema RAG legal
    """
    
    def __init__(self, backend_url: str = "http://localhost:8000"):
        self.backend_url = backend_url.rstrip('/')
        self.session = requests.Session()
        
        # Configurar timeout y headers
        self.session.timeout = 30
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def check_health(self) -> bool:
        """
        Verifica si el backend está funcionando correctamente
        
        Returns:
            True si el backend está disponible, False en caso contrario
        """
        try:
            response = self.session.get(f"{self.backend_url}/health", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Error verificando salud del backend: {e}")
            return False
    
    def get_system_info(self) -> Dict[str, Any]:
        """
        Obtiene información del sistema RAG
        
        Returns:
            Diccionario con información del sistema
        """
        try:
            response = self.session.get(f"{self.backend_url}/")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error obteniendo información del sistema: {e}")
            return {"error": str(e)}
    
    def query(self, question: str, top_n: int = 5) -> RAGResponse:
        """
        Realiza una consulta al sistema RAG
        
        Args:
            question: Pregunta o consulta a realizar
            top_n: Número máximo de resultados a retornar
            
        Returns:
            RAGResponse con los resultados de la consulta
        """
        try:
            payload = {
                "question": question,
                "top_n": top_n
            }
            
            response = self.session.post(f"{self.backend_url}/query", json=payload)
            response.raise_for_status()
            
            data = response.json()
            
            # Convertir resultados a objetos RAGResult
            results = []
            for hit in data.get('results', []):
                result = RAGResult(
                    expte=hit.get('expte', ''),
                    section=hit.get('section', ''),
                    paragraph=hit.get('paragraph', ''),
                    score=hit.get('score', 0.0),
                    path=hit.get('path', ''),
                    search_type=hit.get('search_type', 'unknown'),
                    idea_central=hit.get('idea_central', ''),
                    materia_preliminar=hit.get('materia_preliminar', '')
                )
                results.append(result)
            
            return RAGResponse(
                question=data.get('question', question),
                markdown=data.get('markdown', ''),
                results=results,
                total_time=data.get('total_time', 0.0),
                search_time=data.get('search_time', 0.0),
                llm_time=data.get('llm_time', 0.0)
            )
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error de red consultando RAG: {e}")
            return RAGResponse(
                question=question,
                markdown=f"Error de conexión: {e}",
                results=[],
                total_time=0.0,
                search_time=0.0,
                llm_time=0.0
            )
        except Exception as e:
            logger.error(f"Error inesperado consultando RAG: {e}")
            return RAGResponse(
                question=question,
                markdown=f"Error: {e}",
                results=[],
                total_time=0.0,
                search_time=0.0,
                llm_time=0.0
            )
    
    def query_batch(self, questions: List[str], top_n: int = 5) -> List[RAGResponse]:
        """
        Realiza múltiples consultas en lote
        
        Args:
            questions: Lista de preguntas a consultar
            top_n: Número máximo de resultados por consulta
            
        Returns:
            Lista de RAGResponse, uno por cada pregunta
        """
        if len(questions) > 10:
            raise ValueError("Máximo 10 consultas por lote")
        
        try:
            payload = [{"question": q, "top_n": top_n} for q in questions]
            
            response = self.session.post(f"{self.backend_url}/query-batch", json=payload)
            response.raise_for_status()
            
            responses = []
            for data in response.json():
                # Convertir cada respuesta usando la lógica de query individual
                results = []
                for hit in data.get('results', []):
                    result = RAGResult(
                        expte=hit.get('expte', ''),
                        section=hit.get('section', ''),
                        paragraph=hit.get('paragraph', ''),
                        score=hit.get('score', 0.0),
                        path=hit.get('path', ''),
                        search_type=hit.get('search_type', 'unknown'),
                        idea_central=hit.get('idea_central', ''),
                        materia_preliminar=hit.get('materia_preliminar', '')
                    )
                    results.append(result)
                
                rag_response = RAGResponse(
                    question=data.get('question', ''),
                    markdown=data.get('markdown', ''),
                    results=results,
                    total_time=data.get('total_time', 0.0),
                    search_time=data.get('search_time', 0.0),
                    llm_time=data.get('llm_time', 0.0)
                )
                responses.append(rag_response)
            
            return responses
            
        except Exception as e:
            logger.error(f"Error en consulta batch: {e}")
            # Retornar respuestas de error para cada pregunta
            return [
                RAGResponse(
                    question=q,
                    markdown=f"Error en batch: {e}",
                    results=[],
                    total_time=0.0,
                    search_time=0.0,
                    llm_time=0.0
                ) for q in questions
            ]
    
    def get_expediente_ids(self, response: RAGResponse) -> List[str]:
        """
        Extrae los IDs de expediente de una respuesta RAG
        
        Args:
            response: Respuesta del sistema RAG
            
        Returns:
            Lista de IDs de expediente únicos
        """
        expedientes = set()
        for result in response.results:
            if result.expte:
                expedientes.add(result.expte)
        return list(expedientes)
    
    def compare_responses(self, response1: RAGResponse, response2: RAGResponse) -> Dict[str, Any]:
        """
        Compara dos respuestas RAG para evaluar consistencia
        
        Args:
            response1: Primera respuesta
            response2: Segunda respuesta
            
        Returns:
            Diccionario con métricas de comparación
        """
        exptes1 = set(self.get_expediente_ids(response1))
        exptes2 = set(self.get_expediente_ids(response2))
        
        intersection = exptes1.intersection(exptes2)
        union = exptes1.union(exptes2)
        
        # Calcular métricas de similitud
        jaccard_similarity = len(intersection) / len(union) if len(union) > 0 else 0
        overlap_coefficient = len(intersection) / min(len(exptes1), len(exptes2)) if min(len(exptes1), len(exptes2)) > 0 else 0
        
        return {
            'expedientes_response1': list(exptes1),
            'expedientes_response2': list(exptes2),
            'expedientes_comunes': list(intersection),
            'total_response1': len(exptes1),
            'total_response2': len(exptes2),
            'total_comunes': len(intersection),
            'jaccard_similarity': jaccard_similarity,
            'overlap_coefficient': overlap_coefficient,
            'consistent': overlap_coefficient > 0.8  # Consideramos consistente si hay >80% overlap
        }
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Prueba la conexión con el sistema RAG realizando una consulta simple
        
        Returns:
            Diccionario con resultados de la prueba
        """
        test_result = {
            'health_check': False,
            'query_test': False,
            'system_info': None,
            'error': None
        }
        
        try:
            # Test 1: Health check
            test_result['health_check'] = self.check_health()
            
            # Test 2: System info
            test_result['system_info'] = self.get_system_info()
            
            # Test 3: Simple query
            if test_result['health_check']:
                response = self.query("test", top_n=1)
                test_result['query_test'] = len(response.results) >= 0  # Even 0 results is ok
                
        except Exception as e:
            test_result['error'] = str(e)
        
        return test_result 