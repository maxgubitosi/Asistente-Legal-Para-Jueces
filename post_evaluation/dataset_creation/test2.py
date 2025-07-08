"""
El test 2 testea la robustez del extractor de citas frente a variaciones en la redacción superficial del texto.
Para ello, este script modifica la redacción superficial del texto original.
"""

import logging
from pathlib import Path
from typing import Dict, List, Any

from ..src.text_modifier import TextModifier
from .base_creator import BaseDatasetCreator

logger = logging.getLogger(__name__)

TEST2_PROMPTS = {
    "redaccion_superficial": """
Eres un editor de textos legales. Reescribe el siguiente extracto de un fallo judicial superficialmente. El mensaje real del texto NO debe modificarse.

Mantén SIN CAMBIOS:
- No cambies las citas de artículos y leyes. Deben permanecer EXACTAMENTE iguales (por ejemplo "art. 3" o "ley 7046", etc.)
- No cambies el mensaje real del texto. NO debe modificarse el contenido fáctico.
- No cambies las conclusiones legales y decisiones
- No cambies Nombres, fechas, montos

Cambia:
- Estructura de la oración y orden de palabras
- Estilo de redacción y elección de palabras superficiales.

Texto original:
{texto}

Texto reescrito:
"""
}


def create_test2_dataset(
    json_files: List[Path],
    output_dir: Path,
    original_data_path: Path,
    sample_size: int = None,
    resume: bool = False,
    max_retries: int = 3,
    retry_delay: float = 1.0,
    workers: int = 10
) -> Dict[str, int]:
    """Create Test 2 dataset with redaction modifications using multithreading."""
    text_modifier = TextModifier(
        prompts=TEST2_PROMPTS,
        max_retries=max_retries,
        retry_delay=retry_delay,
        max_workers=workers
    )
    creator = BaseDatasetCreator(text_modifier, max_workers=workers)
    
    def modify_json_for_test2(json_data: Dict[str, Any]) -> Dict[str, Any]:
        modified_json = json_data.copy()
        modified_json = creator.modify_idea_central(modified_json, 'redaccion_superficial')
        modified_json = creator.modify_contenido_sections(modified_json, 'redaccion_superficial', min_text_length=20)
        if 'METADATOS' in json_data:
            modified_json['METADATOS'] = json_data['METADATOS'].copy()
        return modified_json
    
    return creator.create_dataset_multithreaded(
        json_files=json_files,
        output_dir=output_dir,
        original_data_path=original_data_path,
        modification_callback=modify_json_for_test2,
        test_name="Test 2: Redaction Robustness",
        sample_size=sample_size,
        resume=resume
    ) 