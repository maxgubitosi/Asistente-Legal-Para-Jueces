"""
Dataset Creation for Test 2: Redaction Robustness

This module creates modified JSON datasets with superficial redaction changes
to test if the RAG system returns similar results with different wording.
"""

import json
import logging
import time
from pathlib import Path
from typing import Dict, List, Any
from tqdm import tqdm

from ..src.text_modifier import TextModifier


def create_test2_dataset(
    json_files: List[Path],
    text_modifier: TextModifier,
    output_dir: Path,
    original_data_path: Path,
    sample_size: int = None,
    resume: bool = False
) -> Dict[str, int]:
    """
    Create Test 2 dataset with superficial redaction modifications.
    
    Args:
        json_files: List of JSON files to process
        text_modifier: TextModifier instance for redaction changes
        output_dir: Output directory for modified files
        original_data_path: Original data path for relative structure
        sample_size: Limit number of files (None for all)
        resume: Continue from existing files
        
    Returns:
        Dictionary with processing statistics
    """
    logger = logging.getLogger(__name__)
    
    # Prepare output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Filter files if sample size specified
    if sample_size:
        json_files = json_files[:sample_size]
    
    # Statistics
    stats = {
        'total_files': len(json_files),
        'processed': 0,
        'errors': 0,
        'skipped': 0
    }
    
    logger.info(f"🚀 Creating Test 2 dataset: Redaction Robustness")
    logger.info(f"📁 Files to process: {stats['total_files']}")
    logger.info(f"📂 Output directory: {output_dir}")
    
    # Process each JSON file
    for json_file in tqdm(json_files, desc="Processing Test 2"):
        try:
            # Calculate output path maintaining relative structure
            relative_path = json_file.relative_to(original_data_path)
            output_file = output_dir / relative_path
            
            # Create parent directories if they don't exist
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Skip if file exists and resume mode
            if resume and output_file.exists():
                logger.debug(f"⏭️ Skipping existing file: {relative_path}")
                stats['skipped'] += 1
                continue
            
            # Load original JSON
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    json_data = json.load(f)
            except UnicodeDecodeError:
                with open(json_file, 'r', encoding='latin-1') as f:
                    json_data = json.load(f)
            
            # Validate JSON structure
            if not json_data or not isinstance(json_data, dict):
                logger.warning(f"⚠️ Invalid JSON structure: {relative_path}")
                stats['errors'] += 1
                continue
            
            # Create modified JSON with redacted content
            modified_json = json_data.copy()
            
            # Modify IDEA_CENTRAL if it exists
            if 'IDEA_CENTRAL' in modified_json and modified_json['IDEA_CENTRAL']:
                logger.debug(f"🔄 Modifying IDEA_CENTRAL: {relative_path}")
                original_idea = modified_json['IDEA_CENTRAL']
                modified_idea = text_modifier.modify_text_sync(original_idea, 'redaccion_superficial')
                
                if modified_idea and len(modified_idea.strip()) > 10:
                    modified_json['IDEA_CENTRAL'] = modified_idea
                else:
                    logger.warning(f"⚠️ Failed to modify IDEA_CENTRAL: {relative_path}")
            
            # Modify CONTENIDO sections if they exist
            if 'CONTENIDO' in modified_json:
                contenido_modified = modified_json['CONTENIDO'].copy()
                
                for section_name, section_content in contenido_modified.items():
                    if isinstance(section_content, list):
                        # Modify each item in the list
                        modified_items = []
                        for item in section_content:
                            if isinstance(item, str) and len(item.strip()) > 20:
                                logger.debug(f"🔄 Modifying {section_name} item: {relative_path}")
                                modified_item = text_modifier.modify_text_sync(item, 'redaccion_superficial')
                                if modified_item and len(modified_item.strip()) > 10:
                                    modified_items.append(modified_item)
                                else:
                                    modified_items.append(item)  # Keep original if modification fails
                            else:
                                modified_items.append(item)  # Keep short items unchanged
                        contenido_modified[section_name] = modified_items
                        
                    elif isinstance(section_content, str) and len(section_content.strip()) > 20:
                        logger.debug(f"🔄 Modifying {section_name}: {relative_path}")
                        modified_content = text_modifier.modify_text_sync(section_content, 'redaccion_superficial')
                        if modified_content and len(modified_content.strip()) > 10:
                            contenido_modified[section_name] = modified_content
                        # If modification fails, keep original content
                
                modified_json['CONTENIDO'] = contenido_modified
            
            # Preserve metadata and structure
            if 'METADATOS' in json_data:
                modified_json['METADATOS'] = json_data['METADATOS'].copy()
            
            # Save modified JSON
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(modified_json, f, ensure_ascii=False, indent=2)
            
            logger.debug(f"✅ Saved: {output_file}")
            stats['processed'] += 1
            
            # Small pause to avoid rate limits
            time.sleep(0.2)  # Slightly longer pause for more complex modifications
            
        except Exception as e:
            logger.error(f"❌ Error processing {json_file}: {e}")
            stats['errors'] += 1
            continue
    
    # Final summary
    logger.info(f"📊 Test 2 Dataset Creation Summary:")
    logger.info(f"  ✅ Processed: {stats['processed']}")
    logger.info(f"  ❌ Errors: {stats['errors']}")
    logger.info(f"  ⏭️ Skipped: {stats['skipped']}")
    logger.info(f"  📁 Saved to: {output_dir}")
    
    return stats 