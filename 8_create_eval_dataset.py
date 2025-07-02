#!/usr/bin/env python3
"""
Creador de Datasets de Evaluación para Sistema RAG Legal

Este script genera versiones modificadas de los textos legales para cada prueba:
- Test 1: Cambios de formato de citas (art. ↔ artículo)
- Test 2: Redacción superficial (mismo significado, diferente redacción)
- Test 3: Cambio de contenido (mismas citas, contenido diferente)

Solo necesita ejecutarse una vez para crear todas las versiones modificadas.
"""

import argparse
import logging
import sys
import shutil
from pathlib import Path
from typing import Dict, List
from tqdm import tqdm
import time

# Importar módulos de evaluación
try:
    from post_evaluation.src.text_modifier import TextModifier
    from post_evaluation.src.utils import setup_logging, check_dependencies, verify_original_data, create_readme_files
    from post_evaluation.dataset_creation import create_test1_dataset, create_test2_dataset, create_test3_dataset
except ImportError as e:
    print("❌ Error: No se pudo importar los módulos de evaluación.")
    print("Asegúrate de que todos los archivos estén en el directorio post_evaluation/")
    print(f"Error específico: {e}")
    sys.exit(1)

def create_test_dataset(
    json_files: List[Path], 
    text_modifier: TextModifier,
    test_name: str,
    test_id: str,
    output_dir: Path,
    original_data_path: Path,
    sample_size: int = None,
    resume: bool = False
) -> Dict[str, int]:
    """
    Crea un dataset modificado para una prueba específica usando módulos modularizados
    
    Args:
        json_files: Lista de archivos JSON originales
        text_modifier: Instancia del modificador de texto
        test_name: Nombre de la prueba (para logging)
        test_id: ID de la prueba (test1, test2, test3)
        output_dir: Directorio de salida para los archivos modificados
        original_data_path: Ruta original de los datos para mantener estructura
        sample_size: Limitar número de archivos (None para todos)
        resume: Si continuar desde archivos ya procesados
        
    Returns:
        Diccionario con estadísticas de procesamiento
    """
    logger = logging.getLogger(__name__)
    
    # Seleccionar función de creación según el test
    if test_id == 'test1':
        return create_test1_dataset(
            json_files=json_files,
            text_modifier=text_modifier,
            output_dir=output_dir,
            original_data_path=original_data_path,
            sample_size=sample_size,
            resume=resume
        )
    elif test_id == 'test2':
        return create_test2_dataset(
            json_files=json_files,
            text_modifier=text_modifier,
            output_dir=output_dir,
            original_data_path=original_data_path,
            sample_size=sample_size,
            resume=resume
        )
    elif test_id == 'test3':
        return create_test3_dataset(
            json_files=json_files,
            text_modifier=text_modifier,
            output_dir=output_dir,
            original_data_path=original_data_path,
            sample_size=sample_size,
            resume=resume
        )
    else:
        raise ValueError(f"Test ID no reconocido: {test_id}")
        
    return stats

def main():
    parser = argparse.ArgumentParser(
        description="Creador de Datasets de Evaluación para Sistema RAG Legal",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:

  # Crear todos los datasets de evaluación
  python 7_create_eval_dataset.py --all

  # Crear solo dataset para test 1 con muestra de 50 archivos  
  python 7_create_eval_dataset.py --test 1 --sample-size 50

  # Continuar creación anterior (resume archivos ya procesados)
  python 7_create_eval_dataset.py --all --resume

  # Limpiar y recrear todos los datasets
  python 7_create_eval_dataset.py --all --clean

Tests disponibles:
  1: Robustez de Formato de Citas
  2: Robustez de Redacción Superficial  
  3: Sensibilidad a Cambios de Contenido
        """
    )
    
    # Argumentos principales
    parser.add_argument('--all', action='store_true',
                       help='Crear datasets para todas las pruebas')
    parser.add_argument('--test', type=int, choices=[1, 2, 3],
                       help='Crear dataset para una prueba específica')
    
    # Configuración
    parser.add_argument('--sample-size', type=int,
                       help='Limitar número de archivos a procesar (usar todos si no se especifica)')
    parser.add_argument('--data-path', default='datasets/fallos_json',
                       help='Ruta a los datos originales (default: datasets/fallos_json)')
    parser.add_argument('--output-dir', default='datasets_evaluation',
                       help='Directorio base de salida (default: datasets_evaluation)')
    
    # Opciones adicionales
    parser.add_argument('--clean', action='store_true',
                       help='Limpiar datasets existentes antes de crear')
    parser.add_argument('--resume', action='store_true',
                       help='Continuar desde archivos ya procesados')
    parser.add_argument('--verbose', action='store_true',
                       help='Mostrar información detallada de debug')
    
    args = parser.parse_args()
    
    # Configurar logging
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    # Verificar dependencias
    if not check_dependencies():
        sys.exit(1)
    
    # Validar argumentos
    if not args.all and not args.test:
        print("❌ Debes especificar --all o --test <número>")
        parser.print_help()
        sys.exit(1)
    
    if args.clean and args.resume:
        print("❌ No puedes usar --clean y --resume al mismo tiempo")
        sys.exit(1)
    
    # Preparar rutas
    original_data_path = Path(args.data_path)
    output_base_dir = Path(args.output_dir)
    
    try:
        # Verificar datos originales JSON
        json_files = verify_original_data(original_data_path)
        
        # Limpiar datasets existentes si se solicita
        if args.clean and output_base_dir.exists():
            print(f"🧹 Limpiando datasets existentes en {output_base_dir}")
            shutil.rmtree(output_base_dir)
        
        # Inicializar TextModifier
        print("🤖 Inicializando TextModifier...")
        text_modifier = TextModifier()
        
        # Configurar pruebas a ejecutar
        test_configs = {
            1: ('test1', 'Test 1: Robustez de Formato de Citas'),
            2: ('test2', 'Test 2: Robustez de Redacción Superficial'),
            3: ('test3', 'Test 3: Sensibilidad a Cambios de Contenido')
        }
        
        if args.all:
            tests_to_run = [1, 2, 3]
        else:
            tests_to_run = [args.test]
        
        # Ejecutar creación de datasets
        all_stats = {}
        total_start_time = time.time()
        
        for test_num in tests_to_run:
            test_id, test_name = test_configs[test_num]
            output_dir = output_base_dir / test_id
            
            print(f"\n{'='*60}")
            print(f"🚀 Iniciando {test_name}")
            print(f"{'='*60}")
            
            start_time = time.time()
            stats = create_test_dataset(
                json_files=json_files,
                text_modifier=text_modifier,
                test_name=test_name,
                test_id=test_id,
                output_dir=output_dir,
                original_data_path=original_data_path,
                sample_size=args.sample_size,
                resume=args.resume
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            all_stats[test_id] = stats
            
            print(f"⏱️ Tiempo transcurrido: {duration:.1f} segundos")
            print(f"✅ {test_name} completado")
        
        # Crear archivos README
        print(f"\n📝 Creando archivos README...")
        create_readme_files(output_base_dir, all_stats)
        
        # Resumen final
        total_duration = time.time() - total_start_time
        
        print(f"\n{'='*60}")
        print(f"🎉 CREACIÓN DE DATASETS COMPLETADA")
        print(f"{'='*60}")
        print(f"⏱️ Tiempo total: {total_duration:.1f} segundos")
        print(f"📁 Datasets guardados en: {output_base_dir}")
        
        for test_id, stats in all_stats.items():
            test_name = test_configs[[k for k, v in test_configs.items() if v[0] == test_id][0]][1]
            print(f"\n{test_name}:")
            print(f"  ✅ Procesados: {stats['processed']}")
            print(f"  ❌ Errores: {stats['errors']}")
            if stats['skipped'] > 0:
                print(f"  ⏭️ Saltados: {stats['skipped']}")
        
        print(f"\n🔄 Próximo paso:")
        print(f"   python 8_evaluate.py --test <número> --sample-size <tamaño>")
        
    except KeyboardInterrupt:
        print("\n⏸️ Creación interrumpida por el usuario")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Error durante la creación: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 