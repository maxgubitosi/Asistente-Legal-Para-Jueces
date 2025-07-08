"""
Test 4: Document Retrieval Accuracy Evaluation

Este test evalúa la precisión del RAG en recuperar documentos específicos.
"""

import logging
import json
from pathlib import Path
from typing import Dict, List, Any, Tuple
from tqdm import tqdm
from collections import defaultdict

from ..src.rag_client import RAGClient, RAGResponse
from ..src.metrics import EvaluationResult, MetricsCalculator

logger = logging.getLogger(__name__)


def calculate_best_question_per_document_metrics(detailed_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate metrics based on the best performing question per document.
    
    For each document, we check if at least one of its questions got a hit
    in top1, top3, or top5, rather than averaging all questions.
    
    Args:
        detailed_results: List of individual question results
        
    Returns:
        Dictionary with best-question-per-document metrics
    """
    # Group results by document ID
    doc_results = defaultdict(list)
    for result in detailed_results:
        if 'expected_document_id' in result and 'ranking_position' in result:
            doc_id = result['expected_document_id']
            doc_results[doc_id].append(result)
    
    if not doc_results:
        return {
            'total_documents': 0,
            'best_top1_accuracy': 0.0,
            'best_top3_accuracy': 0.0, 
            'best_top5_accuracy': 0.0,
            'best_average_ranking': 0.0,
            'documents_with_hits': 0,
            'detailed_per_document': []
        }
    
    # Calculate best metrics per document
    per_document_results = []
    best_top1_hits = 0
    best_top3_hits = 0
    best_top5_hits = 0
    documents_with_hits = 0
    all_best_rankings = []
    
    for doc_id, doc_questions in doc_results.items():
        # Find the best ranking among all questions for this document
        rankings = [q.get('ranking_position', 0) for q in doc_questions if q.get('ranking_position', 0) > 0]
        
        best_ranking = min(rankings) if rankings else 0
        has_hit = best_ranking > 0
        
        if has_hit:
            documents_with_hits += 1
            all_best_rankings.append(best_ranking)
        
        # Check if any question hit top1, top3, top5
        has_top1 = any(q.get('ranking_position') == 1 for q in doc_questions)
        has_top3 = any(q.get('ranking_position', 0) > 0 and q.get('ranking_position', 0) <= 3 for q in doc_questions)
        has_top5 = any(q.get('ranking_position', 0) > 0 and q.get('ranking_position', 0) <= 5 for q in doc_questions)
        
        if has_top1:
            best_top1_hits += 1
        if has_top3:
            best_top3_hits += 1
        if has_top5:
            best_top5_hits += 1
        
        per_document_results.append({
            'document_id': doc_id,
            'num_questions': len(doc_questions),
            'best_ranking': best_ranking,
            'has_hit': has_hit,
            'has_top1': has_top1,
            'has_top3': has_top3,
            'has_top5': has_top5,
            'all_rankings': [q.get('ranking_position', 0) for q in doc_questions]
        })
    
    total_documents = len(doc_results)
    
    return {
        'total_documents': total_documents,
        'best_top1_accuracy': best_top1_hits / total_documents if total_documents > 0 else 0.0,
        'best_top3_accuracy': best_top3_hits / total_documents if total_documents > 0 else 0.0,
        'best_top5_accuracy': best_top5_hits / total_documents if total_documents > 0 else 0.0,
        'best_average_ranking': sum(all_best_rankings) / max(len(all_best_rankings), 1),
        'documents_with_hits': documents_with_hits,
        'detailed_per_document': per_document_results
    }


def evaluate_test4_document_retrieval(
    rag_client: RAGClient,
    questions_base_dir: Path,
    output_dir: Path,
    max_questions_per_type: int = None
) -> EvaluationResult:
    """
    Evalúa la precisión del RAG en recuperar documentos específicos usando tres tipos de preguntas.
    
    Esta función ejecuta Test 4: verifica que el RAG devuelva el documento correcto
    cuando se le hacen preguntas específicamente generadas para ese documento.
    
    Args:
        rag_client: Cliente RAG para consultas
        questions_base_dir: Directorio base con subdirectorios specific/, ultra_specific/, generic/
        output_dir: Directorio donde guardar resultados detallados
        max_questions_per_type: Número máximo de preguntas por tipo (None para todas)
        
    Returns:
        EvaluationResult con métricas de precisión de recuperación
    """
    logger.info("🎯 Executing Test 4: Document Retrieval Accuracy with Question Types")
    
    # Verify client
    if not rag_client.check_health():
        return EvaluationResult(
            test_name="Document Retrieval Accuracy",
            accuracy=0.0,
            precision=0.0,
            recall=0.0,
            f1_score=0.0,
            details={'error': f'RAG backend not available'}
        )
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Define question types and their directories
    question_types = {
        'specific': questions_base_dir / 'specific',
        'ultra_specific': questions_base_dir / 'ultra_specific', 
        'generic': questions_base_dir / 'generic'
    }
    
    # Collect questions for each type
    all_results_by_type = {}
    overall_detailed_results = []
    overall_stats = {
        'total_questions': 0,
        'correct_retrievals': 0,
        'by_type': {}
    }
    
    for question_type, type_dir in question_types.items():
        logger.info(f"📂 Processing {question_type} questions from {type_dir}")
        
        if not type_dir.exists():
            logger.warning(f"⚠️ Directory not found: {type_dir}")
            continue
        
        # Load questions for this type
        question_files = list(type_dir.glob("*.json"))
        if not question_files:
            logger.warning(f"⚠️ No question files found in {type_dir}")
            continue
        
        # Limit questions if specified
        if max_questions_per_type and len(question_files) > max_questions_per_type:
            question_files = question_files[:max_questions_per_type]
        
        logger.info(f"📊 Found {len(question_files)} files for {question_type} questions")
        
        # Process questions for this type
        type_results = process_question_type(
            rag_client, 
            question_files, 
            question_type,
            output_dir
        )
        
        all_results_by_type[question_type] = type_results
        overall_detailed_results.extend(type_results['detailed_results'])
        
        # Update overall stats
        overall_stats['total_questions'] += type_results['total_questions']
        overall_stats['correct_retrievals'] += type_results['correct_retrievals']
        overall_stats['by_type'][question_type] = {
            'total_questions': type_results['total_questions'],
            'correct_retrievals': type_results['correct_retrievals'],
            'top3_accuracy': type_results['top3_accuracy'],
            'top1_accuracy': type_results['top1_accuracy'],
            'top5_accuracy': type_results['top5_accuracy'],
            'average_ranking': type_results['average_ranking'],
            'best_question_per_document_metrics': type_results['best_question_per_document_metrics']
        }
    
    # Calculate overall metrics
    overall_top3_accuracy = overall_stats['correct_retrievals'] / max(overall_stats['total_questions'], 1)
    
    # Calculate additional metrics
    top1_overall = sum(1 for r in overall_detailed_results if r.get('ranking_position') == 1) / max(overall_stats['total_questions'], 1)
    top5_overall = sum(1 for r in overall_detailed_results if r.get('ranking_position', 0) > 0 and r.get('ranking_position', 0) <= 5) / max(overall_stats['total_questions'], 1)
    
    found_docs = [r.get('ranking_position', 0) for r in overall_detailed_results if r.get('ranking_position', 0) > 0]
    avg_ranking_overall = sum(found_docs) / max(len(found_docs), 1)
    
    # Calculate overall best question per document metrics
    overall_best_metrics = calculate_best_question_per_document_metrics(overall_detailed_results)
    
    # Log results by type
    logger.info(f"📊 Test 4 Results Summary:")
    logger.info(f"  🎯 Overall Top 3 Accuracy: {overall_top3_accuracy:.3f}")
    logger.info(f"  🥇 Overall Top 1 Accuracy: {top1_overall:.3f}")
    logger.info(f"  🥉 Overall Top 5 Accuracy: {top5_overall:.3f}")
    logger.info(f"  📈 Overall Average Ranking: {avg_ranking_overall:.1f}")
    logger.info(f"  ✅ Overall Correct Retrievals: {overall_stats['correct_retrievals']}/{overall_stats['total_questions']}")
    
    # Log best question per document metrics
    logger.info(f"🏆 Best Question Per Document Metrics:")
    logger.info(f"  🥇 Best Top 1 Accuracy: {overall_best_metrics['best_top1_accuracy']:.3f}")
    logger.info(f"  🎯 Best Top 3 Accuracy: {overall_best_metrics['best_top3_accuracy']:.3f}")
    logger.info(f"  🥉 Best Top 5 Accuracy: {overall_best_metrics['best_top5_accuracy']:.3f}")
    logger.info(f"  📈 Best Average Ranking: {overall_best_metrics['best_average_ranking']:.1f}")
    logger.info(f"  📚 Total Documents: {overall_best_metrics['total_documents']}")
    logger.info(f"  ✅ Documents with Hits: {overall_best_metrics['documents_with_hits']}")
    
    for question_type, type_stats in overall_stats['by_type'].items():
        logger.info(f"  📋 {question_type.title()}: {type_stats['top3_accuracy']:.3f} top3 accuracy ({type_stats['correct_retrievals']}/{type_stats['total_questions']})")
        best_metrics = type_stats['best_question_per_document_metrics']
        logger.info(f"    🏆 Best per doc: Top1={best_metrics['best_top1_accuracy']:.3f}, Top3={best_metrics['best_top3_accuracy']:.3f}, Top5={best_metrics['best_top5_accuracy']:.3f}")
    
    # Put comprehensive results in EvaluationResult.details so ResultsManager saves them correctly
    from datetime import datetime
    comprehensive_details = {
        'test_name': 'Test 4: Document Retrieval Accuracy',
        'evaluation_timestamp': datetime.now().strftime("%Y%m%d_%H%M%S"),
        'total_questions': overall_stats['total_questions'],
        'correct_retrievals': overall_stats['correct_retrievals'],
        'overall_top3_accuracy': overall_top3_accuracy,
        'overall_top1_accuracy': top1_overall,
        'overall_top5_accuracy': top5_overall,
        'overall_average_ranking': avg_ranking_overall,
        'overall_best_question_per_document_metrics': overall_best_metrics,
        'by_question_type': overall_stats['by_type'],
        'by_question_type_only_top_question': {
            question_type: {
                'total_documents': type_data['best_question_per_document_metrics']['total_documents'],
                'documents_with_hits': type_data['best_question_per_document_metrics']['documents_with_hits'],
                'best_top1_accuracy': type_data['best_question_per_document_metrics']['best_top1_accuracy'],
                'best_top3_accuracy': type_data['best_question_per_document_metrics']['best_top3_accuracy'],
                'best_top5_accuracy': type_data['best_question_per_document_metrics']['best_top5_accuracy'],
                'best_average_ranking': type_data['best_question_per_document_metrics']['best_average_ranking']
            }
            for question_type, type_data in all_results_by_type.items()
        },
        'detailed_results_by_type': {
            question_type: {
                'summary': {
                    'question_type': question_type,
                    'total_questions': type_data['total_questions'],
                    'correct_retrievals': type_data['correct_retrievals'],
                    'top3_accuracy': type_data['top3_accuracy'],
                    'top1_accuracy': type_data['top1_accuracy'],
                    'top5_accuracy': type_data['top5_accuracy'],
                    'average_ranking': type_data['average_ranking'],
                    'best_question_per_document_metrics': type_data['best_question_per_document_metrics']
                },
                'detailed_results': type_data['detailed_results']
            }
            for question_type, type_data in all_results_by_type.items()
        },
        'all_detailed_results': overall_detailed_results,
        'descripcion': 'Evalúa si el RAG recupera el documento correcto para preguntas específicas generadas'
    }
    
    logger.info(f"💾 Comprehensive results will be saved by ResultsManager")
    
    return EvaluationResult(
        test_name="Document Retrieval Accuracy",
        accuracy=overall_top3_accuracy,
        precision=0.0,  # Not applicable for document retrieval task
        recall=0.0,     # Not applicable for document retrieval task  
        f1_score=0.0,   # Not applicable for document retrieval task
        details=comprehensive_details
    )


def process_question_type(
    rag_client: RAGClient,
    question_files: List[Path],
    question_type: str,
    output_dir: Path
) -> Dict[str, Any]:
    """
    Process questions for a specific question type.
    
    Args:
        rag_client: RAG client for queries
        question_files: List of JSON files containing questions
        question_type: Type of questions (specific, ultra_specific, generic)
        output_dir: Output directory for results
        
    Returns:
        Dictionary with results for this question type
    """
    detailed_results = []
    correct_retrievals = 0
    total_questions = 0
    
    # Collect all questions with their expected documents
    all_questions = []
    for question_file in question_files:
        try:
            with open(question_file, 'r', encoding='utf-8') as f:
                question_data = json.load(f)
            
            # Use json_id instead of document_id (from our test4 creation)
            document_id = question_data.get('json_id', question_file.stem)
            questions = question_data.get('questions', [])
            
            for i, question in enumerate(questions):
                all_questions.append({
                    'question': question,
                    'expected_document_id': document_id,
                    'source_file': str(question_file),
                    'question_index': i + 1,
                    'question_type': question_type
                })
                
        except Exception as e:
            logger.error(f"❌ Error loading question file {question_file}: {e}")
    
    total_questions = len(all_questions)
    if total_questions == 0:
        return {
            'question_type': question_type,
            'total_questions': 0,
            'correct_retrievals': 0,
            'top3_accuracy': 0.0,
            'top1_accuracy': 0.0,
            'top5_accuracy': 0.0,
            'average_ranking': 0.0,
            'detailed_results': []
        }
    
    # Evaluate each question
    for i, question_data in enumerate(tqdm(all_questions, desc=f"Testing {question_type} questions")):
        try:
            question = question_data['question']
            expected_doc_id = question_data['expected_document_id']
            
            # Query RAG system
            response = rag_client.query(question)
            
            # Check if expected document is in top results
            retrieved_doc_ids = [result.expte for result in response.results]
            
            # Consider it correct if expected document is in top 3 results
            is_correct = expected_doc_id in retrieved_doc_ids[:3]
            if is_correct:
                correct_retrievals += 1
            
            # Calculate ranking position (1-based, 0 if not found)
            ranking_position = 0
            if expected_doc_id in retrieved_doc_ids:
                ranking_position = retrieved_doc_ids.index(expected_doc_id) + 1
            
            detailed_results.append({
                'question_id': f"{question_type}_{i + 1}",
                'question': question,
                'expected_document_id': expected_doc_id,
                'question_type': question_type,
                'retrieved_documents': [
                    {
                        'document_id': result.expte,
                        'score': result.score,
                        'position': j + 1
                    }
                    for j, result in enumerate(response.results[:5])  # Top 5 only
                ],
                'is_correct': is_correct,
                'ranking_position': ranking_position,
                'rag_response': response.markdown,
                'source_file': question_data['source_file'],
                'question_index': question_data['question_index']
            })
            
        except Exception as e:
            logger.error(f"Error processing {question_type} question {i+1}: {e}")
            detailed_results.append({
                'question_id': f"{question_type}_{i + 1}",
                'question': question_data['question'],
                'expected_document_id': question_data['expected_document_id'],
                'question_type': question_type,
                'error': str(e)
            })
    
    # Calculate metrics for this question type
    top3_accuracy = correct_retrievals / total_questions if total_questions > 0 else 0.0
    
    top1_accuracy = sum(1 for r in detailed_results if r.get('ranking_position') == 1) / total_questions
    top5_accuracy = sum(1 for r in detailed_results if r.get('ranking_position', 0) > 0 and r.get('ranking_position', 0) <= 5) / total_questions
    
    # Average ranking (only for found documents)
    found_rankings = [r.get('ranking_position', 0) for r in detailed_results if r.get('ranking_position', 0) > 0]
    avg_ranking = sum(found_rankings) / max(len(found_rankings), 1)
    
    # Calculate best question per document metrics
    best_metrics = calculate_best_question_per_document_metrics(detailed_results)
    
    return {
        'question_type': question_type,
        'total_questions': total_questions,
        'correct_retrievals': correct_retrievals,
        'top3_accuracy': top3_accuracy,
        'top1_accuracy': top1_accuracy,
        'top5_accuracy': top5_accuracy,
        'average_ranking': avg_ranking,
        'best_question_per_document_metrics': best_metrics,
        'detailed_results': detailed_results
    }


def load_question_directories(questions_base_dir: Path) -> Dict[str, Path]:
    """
    Load question directories for all question types.
    
    Args:
        questions_base_dir: Base directory containing subdirectories for each question type
        
    Returns:
        Dictionary mapping question types to their directories
    """
    if not questions_base_dir.exists():
        raise FileNotFoundError(f"Questions base directory not found: {questions_base_dir}")
    
    question_types = {
        'specific': questions_base_dir / 'specific',
        'ultra_specific': questions_base_dir / 'ultra_specific',
        'generic': questions_base_dir / 'generic'
    }
    
    found_types = []
    for q_type, q_dir in question_types.items():
        if q_dir.exists() and list(q_dir.glob("*.json")):
            found_types.append(q_type)
    
    if not found_types:
        raise FileNotFoundError(f"No question directories with JSON files found in {questions_base_dir}")
    
    logger.info(f"✅ Found question types: {', '.join(found_types)}")
    return {k: v for k, v in question_types.items() if k in found_types}


 