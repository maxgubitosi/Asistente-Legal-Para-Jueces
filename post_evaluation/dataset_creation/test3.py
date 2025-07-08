"""
Test 3 DEPRECADO (no funcionaban bien las modificaciones de este estilo)
"""

import logging
from pathlib import Path
from typing import Dict, List, Any

from ..src.text_modifier import TextModifier
from .base_creator import BaseDatasetCreator
from configs.credentials_config import ENDPOINT2, DEPLOYMENT2, MODEL2

logger = logging.getLogger(__name__)

TEST3_PROMPTS = {
    "cambio_contenido": """
Eres un escritor que inventa textos legales. 
Dado un texto de ejemplo, genera una copia estructuralmente similar, pero con contenido totalmente ficticio e inventado. 

No cambiar: 
- Números de artículos y leyes.

Inventar un texto con la misma estructura y largo que el texto dado, y con los mismos números, pero inventar una historia totalmente ficticia. 

Ejemplo:

Version Original: "LUNA, PAULO Y OTRO - ABUSO SEXUAL CON ACCESO CARNAL (L F nro. 12780)\" S/ INCIDENTE COMPETENCIA Y en segundo término por cuanto no surge de la regulación."

Version modificada: "RETENCION DE BIENES RAICES (L F nro. 12780)\" POR HIPOTECA VENCIDA. VERTIENTE DE PLANTEO FORMULADO EN PRIMER INSTANCIA, POR LUNA, quien define, ante PAULO Y OTRO - Sin perjuicio, declaran."

Debe sonar plausible y profesional, pero ser totalmente inventado. 


Texto Original:
{texto}

Texto Modificado:
"""
}


def create_test3_dataset(
    json_files: List[Path],
    output_dir: Path,
    original_data_path: Path,
    sample_size: int = None,
    resume: bool = False,
    max_retries: int = 3,
    retry_delay: float = 1.0,
    workers: int = 10
) -> Dict[str, int]:
    """Create Test 3 dataset with content modifications using multithreading."""
    text_modifier = TextModifier(
        prompts=TEST3_PROMPTS,
        max_retries=max_retries,
        retry_delay=retry_delay,
        max_workers=workers,
        endpoint=ENDPOINT2,
        deployment=DEPLOYMENT2,
        model_name=MODEL2,
        temperature=0.99
    )
    creator = BaseDatasetCreator(text_modifier, max_workers=workers)
    
    def modify_json_for_test3(json_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Modification callback for Test 3: Content Change Sensitivity
        """
        modified_json = json_data.copy()
        modified_json = creator.modify_idea_central(modified_json, 'cambio_contenido')
        priority_sections = ['VISTO Y CONSIDERANDO', 'RESUELVE', 'CONSIDERANDO']
        modified_json = creator.modify_contenido_sections(modified_json, 'cambio_contenido', priority_sections=priority_sections, min_text_length=30)
        if 'METADATOS' in json_data:
            modified_json['METADATOS'] = json_data['METADATOS'].copy()
        if 'MATERIA_PRELIMINAR' in json_data:
            modified_json['MATERIA_PRELIMINAR'] = json_data['MATERIA_PRELIMINAR']
        return modified_json
    
    return creator.create_dataset_multithreaded(
        json_files=json_files,
        output_dir=output_dir,
        original_data_path=original_data_path,
        modification_callback=modify_json_for_test3,
        test_name="Test 3: Content Change Sensitivity",
        sample_size=sample_size,
        resume=resume
    ) 