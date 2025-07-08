"""
Test 1: Citation Format Robustness Evaluation

Este test evalúa la robustez del extractor de citas frente a variaciones en el formato de las citas.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Tuple
from tqdm import tqdm

from ..src.citation_extractor import CitationExtractor
from ..src.metrics import EvaluationResult


def evaluate_test1_citation_robustness(
    original_files: List[Path],
    modified_files: List[Path],
    output_dir: Path,
    sample_size: int = None
) -> EvaluationResult:
    """
    Test 1: Citation Format Robustness
    
    Compares citation extractions between original and format-modified JSON files.
    
    Args:
        original_files: List of original JSON files
        modified_files: List of modified JSON files  
        sample_size: Limit number of files to process
        
    Returns:
        EvaluationResult with metrics and detailed results
    """
    logger = logging.getLogger(__name__)
    logger.info("🔍 Executing Test 1: Citation Format Robustness")
    
    citation_extractor = CitationExtractor()
    
    # Limit sample if specified
    if sample_size:
        original_files = original_files[:sample_size]
        modified_files = modified_files[:sample_size]
    
    total_files = len(original_files)
    correct_extractions = 0
    all_metrics = []
    detailed_results = []
    
    for orig_file, mod_file in tqdm(
        zip(original_files, modified_files), 
        total=total_files,
        desc="Evaluating citation robustness"
    ):
        try:
            # Load and extract citations from original JSON
            original_citations = extract_citations_from_json(orig_file, citation_extractor)
            
            # Load and extract citations from modified JSON
            modified_citations = extract_citations_from_json(mod_file, citation_extractor)
            
            # Compare extractions
            comparison = citation_extractor.compare_extractions(original_citations, modified_citations)
            all_metrics.append(comparison)
            
            # Consider correct if citations are exactly equal
            is_correct = comparison['accuracy'] == 1.0
            if is_correct:
                correct_extractions += 1
            
            detailed_results.append({
                'archivo_original': str(orig_file.name),
                'archivo_modificado': str(mod_file.name),
                'correcto': is_correct,
                'citas_originales': len(original_citations),
                'citas_modificadas': len(modified_citations),
                'metricas': comparison,
                'citas_originales_detalle': original_citations,
                'citas_modificadas_detalle': modified_citations
            })
            
        except Exception as e:
            logger.error(f"Error processing {orig_file.name}: {e}")
            detailed_results.append({
                'archivo_original': str(orig_file.name),
                'archivo_modificado': str(mod_file.name),
                'error': str(e)
            })
    
    # Calculate aggregated metrics
    if all_metrics:
        avg_precision = sum(m['precision'] for m in all_metrics) / len(all_metrics)
        avg_recall = sum(m['recall'] for m in all_metrics) / len(all_metrics)
        avg_f1 = sum(m['f1_score'] for m in all_metrics) / len(all_metrics)
    else:
        avg_precision = avg_recall = avg_f1 = 0.0
    
    accuracy = correct_extractions / total_files if total_files > 0 else 0.0
    
    logger.info(f"📊 Test 1 Results:")
    logger.info(f"  ✅ Correct extractions: {correct_extractions}/{total_files}")
    logger.info(f"  📈 Accuracy: {accuracy:.3f}")
    logger.info(f"  📈 Avg Precision: {avg_precision:.3f}")
    logger.info(f"  📈 Avg Recall: {avg_recall:.3f}")
    logger.info(f"  📈 Avg F1: {avg_f1:.3f}")
    
    return EvaluationResult(
        test_name="Citation Format Robustness",
        accuracy=accuracy,
        precision=avg_precision,
        recall=avg_recall,
        f1_score=avg_f1,
        details={
            'total_archivos': total_files,
            'extracciones_correctas': correct_extractions,
            'resultados_detallados': detailed_results,
            'metricas_individuales': all_metrics,
            'descripcion': 'Evalúa si el extractor de citas es robusto ante cambios de formato'
        }
    )


def extract_citations_from_json(json_file: Path, citation_extractor: CitationExtractor) -> List[Dict]:
    """
    Extract citations from a JSON file using the citation extractor.
    
    Args:
        json_file: Path to JSON file
        citation_extractor: CitationExtractor instance
        
    Returns:
        List of extracted citations
    """
    try:
        # Load JSON file
        with open(json_file, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
    except UnicodeDecodeError:
        with open(json_file, 'r', encoding='latin-1') as f:
            json_data = json.load(f)
    
    # Extract text content for citation extraction
    content_parts = []
    
    # Extract IDEA_CENTRAL
    if 'IDEA_CENTRAL' in json_data and json_data['IDEA_CENTRAL']:
        content_parts.append(json_data['IDEA_CENTRAL'])
    
    # Extract CONTENIDO sections
    if 'CONTENIDO' in json_data:
        contenido = json_data['CONTENIDO']
        for section_name, section_content in contenido.items():
            if isinstance(section_content, list):
                content_parts.extend(section_content)
            elif isinstance(section_content, str):
                content_parts.append(section_content)
    
    # Combine all text content
    full_text = "\n".join(content_parts)
    
    # Extract citations using the citation extractor
    citations = citation_extractor.extract_citations(full_text)
    
    return citations


def verify_test1_datasets(original_dir: Path, test_dir: Path) -> Tuple[List[Path], List[Path]]:
    """
    Verify that Test 1 datasets exist and pair files correctly.
    
    Args:
        original_dir: Directory with original JSON files
        test_dir: Directory with modified JSON files
        
    Returns:
        Tuple of (original_files, modified_files) lists
    """
    if not test_dir.exists():
        raise FileNotFoundError(f"Test 1 directory not found: {test_dir}")
    
    if not original_dir.exists():
        raise FileNotFoundError(f"Original directory not found: {original_dir}")
    
    # Get modified files
    modified_files = list(test_dir.rglob("*.json"))
    if len(modified_files) == 0:
        raise FileNotFoundError(f"No JSON files found in {test_dir}")
    
    # Pair with original files
    paired_original = []
    paired_modified = []
    
    for modified_file in modified_files:
        # Calculate relative path from test_dir
        relative_path = modified_file.relative_to(test_dir)
        original_file = original_dir / relative_path
        
        if original_file.exists():
            paired_original.append(original_file)
            paired_modified.append(modified_file)
        else:
            logging.warning(f"No original file found for: {relative_path}")
    
    if len(paired_original) == 0:
        raise FileNotFoundError("No file pairs found between original and modified datasets")
    
    print(f"✅ Found {len(paired_original)} file pairs for Test 1 evaluation")
    return paired_original, paired_modified 