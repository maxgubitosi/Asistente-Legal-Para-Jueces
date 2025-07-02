"""
Test 3: Content Change Sensitivity Evaluation

This module evaluates if the RAG system can detect fundamental content changes
by comparing responses when content is significantly modified but citations remain.
"""

import logging
from pathlib import Path
from typing import Dict, List, Any
from tqdm import tqdm

from ..src.rag_client import RAGClient, RAGResponse
from ..src.metrics import EvaluationResult


def evaluate_test3_content_sensitivity(
    rag_client_original: RAGClient,
    rag_client_modified: RAGClient,
    queries: List[str],
    output_dir: Path,
    max_queries: int = None
) -> EvaluationResult:
    """
    Evalúa la sensibilidad del RAG ante cambios fundamentales de contenido.
    
    Esta función principal ejecuta Test 3: verifica que el RAG detecte diferencias
    cuando el contenido fundamental cambia pero las citas se mantienen.
    
    Args:
        rag_client_original: Cliente RAG para datos originales
        rag_client_modified: Cliente RAG para datos con contenido modificado
        queries: Lista de consultas a evaluar
        output_dir: Directorio donde guardar resultados detallados
        max_queries: Número máximo de consultas a evaluar (None para todas)
        
    Returns:
        EvaluationResult con métricas de sensibilidad de contenido
    """
    logger = logging.getLogger(__name__)
    logger.info("🔬 Executing Test 3: Content Change Sensitivity")
    
    # Verify clients
    if not rag_client_original.check_health():
        return EvaluationResult(
            test_name="Content Change Sensitivity",
            accuracy=0.0,
            precision=0.0,
            recall=0.0,
            f1_score=0.0,
            details={'error': f'Original backend not available'}
        )
    
    if not rag_client_modified.check_health():
        return EvaluationResult(
            test_name="Content Change Sensitivity",
            accuracy=0.0,
            precision=0.0,
            recall=0.0,
            f1_score=0.0,
            details={'error': f'Modified backend not available'}
        )
    
    # Limit queries if max_queries specified
    if max_queries:
        queries = queries[:max_queries]
    
    total_queries = len(queries)
    detailed_results = []
    dissimilarity_scores = []
    
    logger.info(f"🔍 Testing {total_queries} queries")
    
    for i, query in enumerate(tqdm(queries, desc="Testing content sensitivity")):
        try:
            # Query original backend
            logger.debug(f"Querying original backend: {query}")
            original_response = rag_client_original.query(query)
            
            # Query modified backend
            logger.debug(f"Querying modified backend: {query}")
            modified_response = rag_client_modified.query(query)
            
            # Calculate dissimilarity between responses (opposite of similarity)
            similarity = calculate_response_similarity(original_response, modified_response)
            dissimilarity = 1.0 - similarity
            dissimilarity_scores.append(dissimilarity)
            
            # Check if system detected content changes
            content_change_detected = dissimilarity >= 0.3  # Threshold for detecting changes
            
            detailed_results.append({
                'query_id': i + 1,
                'query': query,
                'original_response': original_response.markdown,
                'modified_response': modified_response.markdown,
                'similarity_score': similarity,
                'dissimilarity_score': dissimilarity,
                'content_change_detected': content_change_detected,
                'original_sources': [r.expte for r in original_response.results],
                'modified_sources': [r.expte for r in modified_response.results],
                'expected': 'Content changes should be detected'
            })
            
        except Exception as e:
            logger.error(f"Error processing query {i+1}: {e}")
            detailed_results.append({
                'query_id': i + 1,
                'query': query,
                'error': str(e)
            })
    
    # Calculate metrics
    if dissimilarity_scores:
        avg_dissimilarity = sum(dissimilarity_scores) / len(dissimilarity_scores)
        changes_detected = sum(1 for d in dissimilarity_scores if d >= 0.3)
        sensitivity_rate = changes_detected / len(dissimilarity_scores)
    else:
        avg_dissimilarity = 0.0
        sensitivity_rate = 0.0
        changes_detected = 0
    
    logger.info(f"📊 Test 3 Results:")
    logger.info(f"  📈 Average Dissimilarity: {avg_dissimilarity:.3f}")
    logger.info(f"  🔍 Changes Detected: {changes_detected}/{total_queries}")
    logger.info(f"  📈 Sensitivity Rate: {sensitivity_rate:.3f}")
    
    return EvaluationResult(
        test_name="Content Change Sensitivity",
        accuracy=sensitivity_rate,
        precision=avg_dissimilarity,
        recall=avg_dissimilarity,
        f1_score=avg_dissimilarity,
        details={
            'total_consultas': total_queries,
            'cambios_detectados': changes_detected,
            'disimilitud_promedio': avg_dissimilarity,
            'tasa_sensibilidad': sensitivity_rate,
            'resultados_detallados': detailed_results,
            'descripcion': 'Evalúa si el RAG detecta cambios fundamentales de contenido'
        }
    )


def calculate_response_similarity(response1: RAGResponse, response2: RAGResponse) -> float:
    """
    Calculate similarity between two RAG responses.
    
    Args:
        response1: First RAGResponse object
        response2: Second RAGResponse object
        
    Returns:
        Similarity score between 0 and 1
    """
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        
        # Extract answer texts
        text1 = response1.markdown.strip()
        text2 = response2.markdown.strip()
        
        if not text1 or not text2:
            return 0.0
        
        # Calculate TF-IDF cosine similarity
        vectorizer = TfidfVectorizer(stop_words='english')
        tfidf_matrix = vectorizer.fit_transform([text1, text2])
        similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        
        return float(similarity)
        
    except ImportError:
        # Fallback to simple word overlap if sklearn not available
        logger = logging.getLogger(__name__)
        logger.warning("sklearn not available, using simple word overlap for similarity")
        
        words1 = set(response1.markdown.lower().split())
        words2 = set(response2.markdown.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    except Exception as e:
        logging.getLogger(__name__).error(f"Error calculating similarity: {e}")
        return 0.0


def get_content_sensitive_queries() -> List[str]:
    """
    Get queries specifically designed to test content change sensitivity.
    
    Returns:
        List of test queries that should show different results with content changes
    """
    return [
        "¿Cuál es la decisión principal del tribunal en este caso?",
        "¿Qué montos específicos se establecen en la regulación de honorarios?",
        "¿Cuáles son los fundamentos legales principales de la decisión?",
        "¿Qué consecuencias se establecen para el caso de mora?",
        "¿Cuál es el razonamiento del tribunal para esta decisión?",
        "¿Qué plazos se establecen en la resolución?",
        "¿Cuáles son las obligaciones específicas que establece el fallo?",
        "¿Qué procedimientos se ordenan seguir según la resolución?",
        "¿Cuáles son los derechos que se reconocen en esta decisión?",
        "¿Qué criterios utiliza el tribunal para fundamentar su decisión?"
    ] 