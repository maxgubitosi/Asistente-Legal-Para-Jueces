#!/usr/bin/env python3
"""
Evaluador del Sistema RAG Legal usando Datasets Pre-creados

Este script ejecuta las evaluaciones reales usando los datasets modificados
creados por 7_create_eval_dataset.py.

- Test 1: Compara extracción de citas entre textos originales y modificados
- Test 2: Compara respuestas RAG entre backend original y backend con datos modificados  
- Test 3: Compara respuestas RAG para detectar cambios de contenido

Este script NO modifica textos dinámicamente, solo usa los datasets ya creados.
"""

import argparse
import logging
import sys
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from tqdm import tqdm
import time
from datetime import datetime

# Importar módulos de evaluación
try:
    from post_evaluation.src.citation_extractor import CitationExtractor
    from post_evaluation.src.rag_client import RAGClient
    from post_evaluation.src.metrics import EvaluationResult, MetricsCalculator, ResultsManager
    from post_evaluation.src.utils import setup_logging, check_dependencies, verify_evaluation_dataset, display_system_status
    from post_evaluation.src.docker_manager import EvalDockerManager
    from post_evaluation.tests.test1 import evaluate_test1_citation_robustness, verify_test1_datasets
    from post_evaluation.tests.test2 import evaluate_test2_redaction_robustness, get_default_test_queries
    from post_evaluation.tests.test3 import evaluate_test3_content_sensitivity, get_content_sensitive_queries
except ImportError as e:
    print("❌ Error: No se pudo importar los módulos de evaluación.")
    print("Asegúrate de que todos los archivos estén en el directorio post_evaluation/")
    print(f"Error específico: {e}")
    sys.exit(1)

# All utility and test functions moved to post_evaluation/src/utils.py and post_evaluation/tests/

def main():
    parser = argparse.ArgumentParser(
        description="Evaluador del Sistema RAG Legal usando Datasets Pre-creados",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:

  # Ejecutar Test 1 (no requiere backend)
  python 8_evaluate.py --test 1 --sample-size 50

  # Ejecutar Test 2 (automático con Docker eval)
  python 8_evaluate.py --test 2 --auto-docker

  # Ejecutar Test 2 (manual con dos backends)
  python 8_evaluate.py --test 2 --original-backend http://localhost:8000 --modified-backend http://localhost:8001

  # Ejecutar todos los tests con Docker automático
  python 8_evaluate.py --all --auto-docker --sample-size 20

Requisitos por test:
  Test 1: Solo requiere datasets_evaluation/test1/
  Test 2: Requiere datasets_evaluation/test2/ Y legal-rag-eval-version/ (con --auto-docker)
  Test 3: Requiere datasets_evaluation/test3/ Y legal-rag-eval-version/ (con --auto-docker)
        """
    )
    
    # Argumentos principales
    parser.add_argument('--all', action='store_true',
                       help='Ejecutar todos los tests disponibles')
    parser.add_argument('--test', type=int, choices=[1, 2, 3],
                       help='Ejecutar un test específico')
    
    # Configuración de datos
    parser.add_argument('--sample-size', type=int,
                       help='Limitar número de archivos/consultas a evaluar')
    parser.add_argument('--original-data', default='datasets/fallos_json',
                       help='Ruta a los datos originales (default: datasets/fallos_json)')
    parser.add_argument('--evaluation-data', default='datasets_evaluation',
                       help='Ruta a los datasets de evaluación (default: datasets_evaluation)')
    
    # Configuración de backends (para tests 2 y 3)
    parser.add_argument('--original-backend', default='http://localhost:8000',
                       help='URL del backend con datos originales (default: http://localhost:8000)')
    parser.add_argument('--modified-backend', default='http://localhost:8001',
                       help='URL del backend con datos modificados (default: http://localhost:8001)')
    
    # Configuración de Docker eval version
    parser.add_argument('--eval-docker-path', default='legal-rag-eval-version',
                       help='Ruta al directorio Docker de evaluación (default: legal-rag-eval-version)')
    parser.add_argument('--auto-docker', action='store_true',
                       help='Configurar automáticamente el Docker de evaluación para tests 2 y 3')
    parser.add_argument('--eval-port', type=int, default=8001,
                       help='Puerto para el backend de evaluación (default: 8001)')
    
    # Salida
    parser.add_argument('--output-dir', default='post_evaluation/evaluation_results',
                       help='Directorio de salida (default: post_evaluation/evaluation_results)')
    
    # Opciones adicionales
    parser.add_argument('--clean', action='store_true',
                       help='Limpiar resultados anteriores antes de evaluar')
    parser.add_argument('--verbose', action='store_true',
                       help='Mostrar información detallada de debug')
    
    args = parser.parse_args()
    
    # Configurar logging
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    # Validar argumentos
    if not args.all and not args.test:
        print("❌ Debes especificar --all o --test <número>")
        parser.print_help()
        sys.exit(1)
    
    # Preparar rutas
    original_data_path = Path(args.original_data)
    evaluation_data_path = Path(args.evaluation_data)
    output_dir = Path(args.output_dir)
    
    # Limpiar resultados anteriores si se solicita
    if args.clean and output_dir.exists():
        import shutil
        print(f"🧹 Limpiando resultados anteriores en {output_dir}")
        shutil.rmtree(output_dir)
    
    # Configurar tests a ejecutar
    if args.all:
        tests_to_run = [1, 2, 3]
    else:
        tests_to_run = [args.test]
    
    # Inicializar ResultsManager
    results_manager = ResultsManager(output_dir)
    
    # Ejecutar evaluaciones
    all_results = {}
    total_start_time = time.time()
    
    for test_num in tests_to_run:
        print(f"\n{'='*60}")
        print(f"🚀 Ejecutando Test {test_num}")
        print(f"{'='*60}")
        
        start_time = time.time()
        
        try:
            if test_num == 1:                            # Test 1: Robustez de Formato de Citas
                test_dir = evaluation_data_path / "test1"
                original_files, modified_files = verify_test1_datasets(original_data_path, test_dir)
                
                result = evaluate_test1_citation_robustness(
                    original_files=original_files,
                    modified_files=modified_files,
                    output_dir=output_dir / "test1",
                    sample_size=args.sample_size
                )
                
            elif test_num == 2:                # Test 2: Robustez de Redacción Superficial
                if args.auto_docker:
                    # Setup eval Docker automatically
                    docker_manager = EvalDockerManager(args.eval_docker_path, args.eval_port)
                    test_data_path = evaluation_data_path / "test2"
                    
                    if not docker_manager.setup_test_data(test_data_path):
                        raise RuntimeError("❌ Failed to setup test data for eval Docker")
                    
                    if not docker_manager.start_eval_docker():
                        raise RuntimeError("❌ Failed to start eval Docker")
                    
                    modified_backend_url = docker_manager.get_eval_backend_url()
                    print(f"🐳 Eval Docker started at: {modified_backend_url}")
                else:
                    modified_backend_url = args.modified_backend
                
                rag_original = RAGClient(backend_url=args.original_backend)
                rag_modified = RAGClient(backend_url=modified_backend_url)
                
                if not rag_original.check_health():
                    raise ConnectionError(f"❌ No se puede conectar al backend original: {args.original_backend}")
                if not rag_modified.check_health():
                    raise ConnectionError(f"❌ No se puede conectar al backend modificado: {modified_backend_url}")
                
                queries = get_default_test_queries()
                if args.sample_size:
                    queries = queries[:args.sample_size]
                
                try:
                    result = evaluate_test2_redaction_robustness(
                        rag_client_original=rag_original,
                        rag_client_modified=rag_modified,
                        queries=queries,
                        output_dir=output_dir / "test2",
                        max_queries=args.sample_size
                    )
                finally:
                    # Clean up Docker if we started it
                    if args.auto_docker:
                        docker_manager.stop_eval_docker()
                
            elif test_num == 3:                            # Test 3: Sensibilidad a Cambios de Contenido
                if args.auto_docker:
                    # Setup eval Docker automatically
                    docker_manager = EvalDockerManager(args.eval_docker_path, args.eval_port)
                    test_data_path = evaluation_data_path / "test3"
                    
                    if not docker_manager.setup_test_data(test_data_path):
                        raise RuntimeError("❌ Failed to setup test data for eval Docker")
                    
                    if not docker_manager.start_eval_docker():
                        raise RuntimeError("❌ Failed to start eval Docker")
                    
                    modified_backend_url = docker_manager.get_eval_backend_url()
                    print(f"🐳 Eval Docker started at: {modified_backend_url}")
                else:
                    modified_backend_url = args.modified_backend
                
                rag_original = RAGClient(backend_url=args.original_backend)
                rag_modified = RAGClient(backend_url=modified_backend_url)
                
                if not rag_original.check_health():
                    raise ConnectionError(f"❌ No se puede conectar al backend original: {args.original_backend}")
                if not rag_modified.check_health():
                    raise ConnectionError(f"❌ No se puede conectar al backend modificado: {modified_backend_url}")
                
                queries = get_content_sensitive_queries()
                if args.sample_size:
                    queries = queries[:args.sample_size]
                
                try:
                    result = evaluate_test3_content_sensitivity(
                        rag_client_original=rag_original,
                        rag_client_modified=rag_modified,
                        queries=queries,
                        output_dir=output_dir / "test3",
                        max_queries=args.sample_size
                    )
                finally:
                    # Clean up Docker if we started it
                    if args.auto_docker:
                        docker_manager.stop_eval_docker()
            
            all_results[f'test{test_num}'] = result
            
            end_time = time.time()
            duration = end_time - start_time
            
            print(f"⏱️ Tiempo transcurrido: {duration:.1f} segundos")
            print(f"✅ Test {test_num} completado")
            print(f"📈 Exactitud: {result.accuracy:.3f}")
            
        except Exception as e:
            logger.error(f"❌ Error ejecutando Test {test_num}: {e}")
            if args.verbose:
                import traceback
                traceback.print_exc()
    
    # Guardar resultados
    if all_results:
        print(f"\n💾 Guardando resultados...")
        saved_files = results_manager.save_results(all_results)
        
        # Resumen final
        total_duration = time.time() - total_start_time
        
        print(f"\n{'='*60}")
        print(f"🎉 EVALUACIÓN COMPLETADA")
        print(f"{'='*60}")
        print(f"⏱️ Tiempo total: {total_duration:.1f} segundos")
        print(f"📁 Resultados guardados en: {output_dir}")
        
        for test_key, result in all_results.items():
            print(f"\n{result.test_name}:")
            print(f"  📈 Exactitud: {result.accuracy:.3f}")
            print(f"  🎯 Precisión: {result.precision:.3f}")
            print(f"  📊 Recall: {result.recall:.3f}")
            print(f"  🏆 F1-Score: {result.f1_score:.3f}")
        
        print(f"\n📝 Archivos generados:")
        for file_type, file_path in saved_files.items():
            print(f"  - {file_type}: {file_path}")
    
    else:
        print("❌ No se completó ninguna evaluación")
        sys.exit(1)

if __name__ == "__main__":
    main() 