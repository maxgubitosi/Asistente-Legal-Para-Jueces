"""
Test 2: Redaction Robustness Evaluation

This module evaluates if the RAG system returns similar results when 
content is superficially rewritten with different wording but same meaning.
"""

import logging
from pathlib import Path
from typing import Dict, List, Any
from tqdm import tqdm

from ..src.rag_client import RAGClient, RAGResponse
from ..src.metrics import EvaluationResult


def evaluate_test2_redaction_robustness(
    rag_client_original: RAGClient,
    rag_client_modified: RAGClient,
    queries: List[str],
    output_dir: Path,
    max_queries: int = None
) -> EvaluationResult:
    """
    Evalúa la robustez del RAG ante cambios superficiales de redacción.
    
    Esta función principal ejecuta Test 2: compara respuestas del RAG usando
    textos originales vs textos con redacción superficial modificada.
    
    Args:
        rag_client_original: Cliente RAG para datos originales
        rag_client_modified: Cliente RAG para datos con redacción modificada
        queries: Lista de consultas a evaluar
        output_dir: Directorio donde guardar resultados detallados
        max_queries: Número máximo de consultas a evaluar (None para todas)
        
    Returns:
        EvaluationResult con métricas de robustez de redacción
    """
    logger = logging.getLogger(__name__)
    logger.info("📝 Executing Test 2: Redaction Robustness")
    
    # Verify clients
    if not rag_client_original.check_health():
        return EvaluationResult(
            test_name="Redaction Robustness",
            accuracy=0.0,
            precision=0.0,
            recall=0.0,
            f1_score=0.0,
            details={'error': f'Original backend not available'}
        )
    
    if not rag_client_modified.check_health():
        return EvaluationResult(
            test_name="Redaction Robustness", 
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
    similarity_scores = []
    
    logger.info(f"🔍 Testing {total_queries} queries")
    
    for i, query in enumerate(tqdm(queries, desc="Testing redaction robustness")):
        try:
            # Query original backend
            logger.debug(f"Querying original backend: {query}")
            original_response = rag_client_original.query(query)
            
            # Query modified backend
            logger.debug(f"Querying modified backend: {query}")
            modified_response = rag_client_modified.query(query)
            
            # Calculate similarity between responses
            similarity = calculate_response_similarity(original_response, modified_response)
            similarity_scores.append(similarity)
            
            detailed_results.append({
                'query_id': i + 1,
                'query': query,
                'original_response': original_response.markdown,
                'modified_response': modified_response.markdown,
                'similarity_score': similarity,
                'original_sources': [r.expte for r in original_response.results],
                'modified_sources': [r.expte for r in modified_response.results],
                'robust': similarity >= 0.7  # Threshold for considering robust
            })
            
        except Exception as e:
            logger.error(f"Error processing query {i+1}: {e}")
            detailed_results.append({
                'query_id': i + 1,
                'query': query,
                'error': str(e)
            })
    
    # Calculate metrics
    if similarity_scores:
        avg_similarity = sum(similarity_scores) / len(similarity_scores)
        robust_responses = sum(1 for s in similarity_scores if s >= 0.7)
        robustness_rate = robust_responses / len(similarity_scores)
    else:
        avg_similarity = 0.0
        robustness_rate = 0.0
        robust_responses = 0
    
    logger.info(f"📊 Test 2 Results:")
    logger.info(f"  📈 Average Similarity: {avg_similarity:.3f}")
    logger.info(f"  ✅ Robust Responses: {robust_responses}/{total_queries}")
    logger.info(f"  📈 Robustness Rate: {robustness_rate:.3f}")
    
    return EvaluationResult(
        test_name="Redaction Robustness",
        accuracy=robustness_rate,
        precision=avg_similarity,
        recall=avg_similarity, 
        f1_score=avg_similarity,
        details={
            'total_consultas': total_queries,
            'respuestas_robustas': robust_responses,
            'similitud_promedio': avg_similarity,
            'tasa_robustez': robustness_rate,
            'resultados_detallados': detailed_results,
            'descripcion': 'Evalúa si el RAG retorna resultados similares con redacción diferente'
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
        import numpy as np
        
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


def get_default_test_queries() -> List[str]:
    """
    Get default set of test queries for redaction robustness evaluation.
    
    Returns:
        List of test queries
    """
    return [
        "¿Cuáles son los requisitos para interponer un recurso de inaplicabilidad de ley?",
        "¿Cómo se regulan los honorarios profesionales en Entre Ríos?",
        "¿Qué establece la Ley 7046 sobre notificación de regulación de honorarios?",
        "¿Cuál es el procedimiento para el pago de honorarios regulados judicialmente?",
        "¿Qué consecuencias tiene la mora en el pago de honorarios profesionales?",
        "¿Cómo se aplican los intereses en caso de mora en honorarios?",
        "¿Qué artículos del Código Procesal Civil y Comercial se aplican frecuentemente?",
        "¿Cuáles son las disposiciones sobre accidentes de tránsito en la provincia?",
        "¿Qué establece el Acuerdo General 15/18 SNE?",
        "¿Cómo se determina la competencia en casos de concursos preventivos?"
    ] 