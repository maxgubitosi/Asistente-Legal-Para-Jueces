"""
El test 4 testea la precisión del RAG en recuperar documentos específicos.
Para ello, este script genera preguntas específicas, ultra específicas y genéricas
a partir del texto original, y luego se evalúa si el RAG es capaz de recuperar el documento
correcto para cada pregunta.
"""

import logging
import json
from pathlib import Path
from typing import Dict, List, Any

from ..src.text_modifier import TextModifier
from .base_creator import BaseDatasetCreator
from configs.credentials_config import ENDPOINT2, DEPLOYMENT2, MODEL2

logger = logging.getLogger(__name__)

TEST4_PROMPTS = {
    "generate_questions_specific": """
Sos un asistente jurídico que genera preguntas relevantes a partir de un texto legal. 

La pregunta debe ser específica para este documento legal, pero sin entrar en demasiados detalles.
Debe estar directamente relacionada con el contenido del texto y la resolución del caso pero sin mencionar mucho detalle específico.

Documento:
{texto}

Contesta en el siguiente formato JSON estructurado y sin nada más que el JSON:
{{
  "preguntas": [
    "Pregunta 1 sobre este documento?",
    "Pregunta 2 sobre este documento?", 
    "Pregunta 3 sobre este documento?"
  ]
}}
""",
    "generate_questions_ultra_specific": """
    Sos un asistente jurídico que genera preguntas relevantes a partir de un texto legal. 

La pregunta debe ser muy específica para este documento legal, directamente relacionada con el contenido del texto. 
Debe tener nombres, fechas, o leyes específicas de este documento. 

Documento:
{texto}

Contesta en el siguiente formato JSON estructurado y sin nada más que el JSON:
{{
  "preguntas": [
    "Pregunta 1 sobre este documento?",
    "Pregunta 2 sobre este documento?", 
    "Pregunta 3 sobre este documento?"
  ]
}}
""",
    "generate_questions_generic": """
    Sos un asistente jurídico que genera preguntas relevantes a partir de un texto legal. 

La pregunta debe estar libremente basada en este documento legal, relacionada con el tipo de caso jurídico, pero no debe mencionar nombres propios ni leyes ni fechas.
Debe ser una pregunta judicial genérica donde este documento serviría como una referencia. Debe ser una pregunta genérica, no específica.

Documento:
{texto}

Contesta en el siguiente formato JSON estructurado y sin nada más que el JSON:
{{
  "preguntas": [
    "Pregunta 1 sobre este documento?",
    "Pregunta 2 sobre este documento?", 
    "Pregunta 3 sobre este documento?"
  ]
}}
""",
}


def create_test4_dataset(
    json_files: List[Path],
    output_dir: Path,
    original_data_path: Path,
    sample_size: int = None,
    resume: bool = False,
    max_retries: int = 3,
    retry_delay: float = 1.0,
    workers: int = 10
) -> Dict[str, int]:
    """Create Test 4 dataset with question generation using multithreading."""
    text_modifier = TextModifier(
        prompts=TEST4_PROMPTS,
        max_retries=max_retries,
        retry_delay=retry_delay,
        max_workers=workers,
        endpoint=ENDPOINT2,
        deployment=DEPLOYMENT2,
        model_name=MODEL2,
        temperature=0.99
    )
    creator = BaseDatasetCreator(text_modifier, max_workers=workers)
    
    def generate_questions_for_test4(json_data: Dict[str, Any], json_file_path: Path, output_dir: Path) -> Dict[str, Any]:
        """
        Question generation callback for Test 4: Extract sections and generate questions
        """
        try:
            # Extract idea_central and contenido sections
            idea_central = json_data.get('IDEA_CENTRAL', '')
            contenido_sections = []
            # append all sub-sections of contenido
            for key, value in json_data.get('CONTENIDO', {}).items():
                if isinstance(value, list):
                    contenido_sections.extend(value)
                else:
                    contenido_sections.append(value)

            # Combine sections into a single text
            combined_text = idea_central + "\n\n" + "\n\n".join(contenido_sections)
            logger.info(f"📤 Combined text length: {len(combined_text)} chars for {json_file_path.stem}")
            
            if not combined_text.strip():
                logger.warning(f"No text found in {json_file_path}")
                return {"error": "No text found"}
            
            # Define the question types and their corresponding subdirectories
            question_types = {
                'generate_questions_specific': 'specific',
                'generate_questions_ultra_specific': 'ultra_specific', 
                'generate_questions_generic': 'generic'
            }
            
            results = {}
            
            # Generate questions for each type
            for question_type, subdir in question_types.items():
                logger.info(f"📤 Generating {question_type} for {json_file_path.stem}")
                
                try:
                    # Generate questions using GPT
                    questions_response = creator.text_modifier.modify_text_sync(combined_text, question_type)
                    
                    # Log the raw response to debug
                    logger.info(f"📥 Raw GPT response for {json_file_path.stem} ({question_type}): {repr(questions_response)}")
                    
                    # Parse the JSON response (should be clean JSON now with response_format)
                    questions_data = json.loads(questions_response)
                    logger.info(f"📥 Parsed JSON successfully for {json_file_path.stem} ({question_type})")
                    
                    # Create result with JSON ID
                    result = {
                        "json_id": json_file_path.stem,
                        "original_file": str(json_file_path),
                        "question_type": question_type,
                        "questions": questions_data.get("preguntas", []),
                        "generated_at": creator._get_timestamp()
                    }
                    
                    # Create subdirectory for this question type
                    question_subdir = output_dir / "questions" / subdir
                    question_subdir.mkdir(parents=True, exist_ok=True)
                    
                    # Save individual question file
                    questions_file = question_subdir / f"{json_file_path.stem}.json"
                    with open(questions_file, 'w', encoding='utf-8') as f:
                        json.dump(result, f, ensure_ascii=False, indent=2)
                    
                    logger.info(f"✅ Generated {len(result['questions'])} {question_type} questions for {json_file_path.stem}")
                    results[question_type] = len(result['questions'])
                    
                except json.JSONDecodeError as json_error:
                    logger.error(f"❌ JSON decode error for {json_file_path.stem} ({question_type})")
                    logger.error(f"❌ Raw response was: {repr(questions_response)}")
                    logger.error(f"❌ JSON error: {str(json_error)}")
                    results[question_type] = f"JSON decode error: {str(json_error)}"
                except Exception as e:
                    logger.error(f"❌ Error generating {question_type} for {json_file_path.stem}: {str(e)}")
                    results[question_type] = f"Error: {str(e)}"
            
            # Return summary of all results
            return {
                "json_id": json_file_path.stem,
                "original_file": str(json_file_path),
                "results": results,
                "generated_at": creator._get_timestamp()
            }
            
        except Exception as e:
            logger.error(f"❌ General error for {json_file_path.stem}: {str(e)}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            return {"error": str(e)}

    return creator.create_questions_dataset_multithreaded(
        json_files=json_files,
        output_dir=output_dir,
        original_data_path=original_data_path,
        question_generation_callback=generate_questions_for_test4,
        test_name="Test 4: Question Generation",
        sample_size=sample_size,
        resume=resume
    ) 