"""
Utility functions for RAG evaluation system.

This module contains common utility functions used across the evaluation system:
- Dependency checking
- Logging setup
- File system operations
- Dataset verification
"""

import logging
import sys
import time
from pathlib import Path
from typing import Dict, List
import psutil

def setup_logging(verbose: bool = False):
    """Configura el sistema de logging"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('evaluation.log', encoding='utf-8')
        ]
    )

def check_dependencies():
    """Verifica que todas las dependencias estén instaladas"""
    required_packages = ['openai', 'tqdm', 'requests', 'psutil']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Paquetes faltantes:")
        for package in missing_packages:
            print(f"  - {package}")
        print("\nInstala los paquetes faltantes con:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    return True

def verify_original_data(data_path: Path) -> List[Path]:
    """Verifica que los datos originales existan y retorna la lista de archivos JSON"""
    if not data_path.exists():
        raise FileNotFoundError(f"No se encontró el directorio de datos: {data_path}")
    
    json_files = list(data_path.rglob("*.json"))
    if len(json_files) == 0:
        raise FileNotFoundError(f"No se encontraron archivos .json en {data_path}")
    
    print(f"✅ Encontrados {len(json_files)} archivos JSON en {data_path}")
    return json_files

def verify_evaluation_dataset(dataset_path: Path, test_name: str) -> List[Path]:
    """Verifica que el dataset de evaluación exista y contenga archivos"""
    if not dataset_path.exists():
        raise FileNotFoundError(
            f"❌ Dataset de {test_name} no encontrado en {dataset_path}\n"
            f"Ejecuta primero: python 7_create_eval_dataset.py --test {test_name[-1]}"
        )
    
    json_files = list(dataset_path.rglob("*.json"))
    if len(json_files) == 0:
        raise FileNotFoundError(f"No se encontraron archivos JSON en {dataset_path}")
    
    print(f"✅ Dataset {test_name} encontrado: {len(json_files)} archivos")
    return json_files

def display_system_status():
    """Muestra información del estado del sistema"""
    print(f"\n📊 Estado del Sistema:")
    print(f"   💾 Memoria disponible: {psutil.virtual_memory().available / (1024**3):.1f} GB")
    print(f"   🖥️  CPU: {psutil.cpu_count()} cores, {psutil.cpu_percent(interval=1):.1f}% uso")
    print(f"   ⏰ Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")

def create_readme_files(datasets_dir: Path, stats: Dict[str, Dict[str, int]]):
    """Crea archivos README informativos en cada directorio de test"""
    
    test_descriptions = {
        'test1': {
            'name': 'Robustez de Formato de Citas',
            'description': 'Textos con formatos de citas modificados (art. ↔ artículo, etc.)',
            'modification': 'formato_citas',
            'purpose': 'Evaluar si el extractor de citas es robusto ante cambios de formato'
        },
        'test2': {
            'name': 'Robustez de Redacción Superficial',
            'description': 'Textos reescritos manteniendo el mismo significado legal',
            'modification': 'redaccion_superficial',
            'purpose': 'Evaluar si el RAG retorna resultados similares con redacción diferente'
        },
        'test3': {
            'name': 'Sensibilidad a Cambios de Contenido',
            'description': 'Textos con contenido fundamental cambiado pero mismas citas',
            'modification': 'cambio_contenido',
            'purpose': 'Evaluar si el RAG detecta cambios fundamentales de contenido'
        }
    }
    
    for test_id, info in test_descriptions.items():
        test_dir = datasets_dir / test_id
        readme_file = test_dir / "README.md"
        
        test_stats = stats.get(test_id, {})
        
        readme_content = f"""# {info['name']}

## Descripción
{info['description']}

## Tipo de Modificación
`{info['modification']}`

## Propósito
{info['purpose']}

## Estadísticas de Creación
- **Total de archivos:** {test_stats.get('total_files', 'N/A')}
- **Procesados exitosamente:** {test_stats.get('processed', 'N/A')}
- **Errores:** {test_stats.get('errors', 'N/A')}
- **Saltados (ya existían):** {test_stats.get('skipped', 'N/A')}

## Uso
Para la evaluación Test {test_id[-1]}, usa los archivos de este directorio como dataset modificado.

## Estructura
Los archivos mantienen la misma estructura relativa que en `datasets/fallos_json/`.
"""
        
        readme_file.write_text(readme_content, encoding='utf-8')
        print(f"📝 README creado: {readme_file}") 