"""
El test 1 testea la robustez del extractor de citas frente a variaciones en el formato de las citas.
Para ello, este script modifica el formato de las citas en el texto original
"""

import logging
from pathlib import Path
from typing import Dict, List, Any

from ..src.text_modifier import TextModifier
from .base_creator import BaseDatasetCreator

logger = logging.getLogger(__name__)

TEST1_PROMPTS = {
    "formato_citas": """
Eres un editor de textos legales especializado. Modifica los formatos de las citas en el siguiente texto legal, pero manteniendo EXACTAMENTE el mismo contenido.

Solo cambia la sintaxis de las citas, para variar un poco el formato:

Ejemplos de cambios a realizar:
- Intercambia instancias de "artículo" por "art." o "artículo número"
- Intercambia instancias de "arts." por "artículos"
- Intercambia instancias de "ley 7046" por "ley número 7046"
- Intercambia instancias de "Expte. Nº 434." por "Expediente Nº 434."
- Intercambia instancias de "Acuerdo Gral." por "Acuerdo General" o "Ac. Gral."

En general, intercambia formas abreviadas por formas completas, y viceversa.

- Mantén todos los números de artículos y leyes EXACTAMENTE iguales
- NO cambies ningún otro contenido, SOLO el formato de las citas

Texto original:
{texto}

Texto modificado:
"""
}


def create_test1_dataset(
    json_files: List[Path],
    output_dir: Path,
    original_data_path: Path,
    sample_size: int = None,
    resume: bool = False,
    max_retries: int = 3,
    retry_delay: float = 1.0,
    workers: int = 10
) -> Dict[str, int]:
    """
    Create Test 1 dataset with citation format modifications using multithreading.
    """
    
    # Initialize TextModifier with specific prompts
    text_modifier = TextModifier(
        prompts=TEST1_PROMPTS,
        max_retries=max_retries,
        retry_delay=retry_delay,
        max_workers=workers
    )
    
    # Initialize base creator
    creator = BaseDatasetCreator(text_modifier, max_workers=workers)
    
    def modify_json_for_test1(json_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply citation-format modification section-by-section to avoid giant prompts."""
        modified_json = json_data.copy()

        # Modify IDEA_CENTRAL individually (if present and non-empty)
        if 'IDEA_CENTRAL' in modified_json and modified_json['IDEA_CENTRAL']:
            try:
                modified_idea = text_modifier.modify_text_sync(modified_json['IDEA_CENTRAL'], 'formato_citas')
                if modified_idea and len(modified_idea.strip()) > 5:
                    modified_json['IDEA_CENTRAL'] = modified_idea
            except Exception as e:
                logger.warning(f"⚠️ Could not modify IDEA_CENTRAL: {e}")

        # Process each subsection of CONTENIDO separately
        if 'CONTENIDO' in modified_json:
            contenido_mod = modified_json['CONTENIDO'].copy()

            for section_name, section_content in contenido_mod.items():
                # If list → modify each item string separately
                if isinstance(section_content, list):
                    new_items = []
                    for item in section_content:
                        if isinstance(item, str) and len(item.strip()) > 5:
                            try:
                                new_item = text_modifier.modify_text_sync(item, 'formato_citas')
                                new_items.append(new_item if new_item else item)
                            except Exception as e:
                                logger.warning(f"⚠️ Could not modify item in {section_name}: {e}")
                                new_items.append(item)
                        else:
                            new_items.append(item)
                    contenido_mod[section_name] = new_items

                # If plain string → modify directly
                elif isinstance(section_content, str) and len(section_content.strip()) > 5:
                    try:
                        new_text = text_modifier.modify_text_sync(section_content, 'formato_citas')
                        if new_text and len(new_text.strip()) > 5:
                            contenido_mod[section_name] = new_text
                    except Exception as e:
                        logger.warning(f"⚠️ Could not modify section {section_name}: {e}")

            modified_json['CONTENIDO'] = contenido_mod

        return modified_json
    
    return creator.create_dataset_multithreaded(
        json_files=json_files,
        output_dir=output_dir,
        original_data_path=original_data_path,
        modification_callback=modify_json_for_test1,
        test_name="Test 1: Citation Format Robustness",
        sample_size=sample_size,
        resume=resume
    ) 