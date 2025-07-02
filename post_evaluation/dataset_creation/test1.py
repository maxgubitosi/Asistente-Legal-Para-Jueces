"""
Dataset Creation for Test 1: Citation Format Robustness

This module creates modified JSON datasets with citation format changes
to test if the citation extractor is robust to format variations.
"""

import json
import logging
import time
from pathlib import Path
from typing import Dict, List, Any
from tqdm import tqdm

from ..src.text_modifier import TextModifier


def create_test1_dataset(
    json_files: List[Path],
    text_modifier: TextModifier,
    output_dir: Path,
    original_data_path: Path,
    sample_size: int = None,
    resume: bool = False
) -> Dict[str, int]:
    """
    Create Test 1 dataset with citation format modifications.
    
    Args:
        json_files: List of JSON files to process
        text_modifier: TextModifier instance for format changes
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
    
    logger.info(f"🚀 Creating Test 1 dataset: Citation Format Robustness")
    logger.info(f"📁 Files to process: {stats['total_files']}")
    logger.info(f"📂 Output directory: {output_dir}")
    
    # Process each JSON file
    for json_file in tqdm(json_files, desc="Processing Test 1"):
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
            
            # Extract text content from JSON for modification
            content_parts = []
            
            # Extract IDEA_CENTRAL
            if 'IDEA_CENTRAL' in json_data:
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
            original_text = "\n".join(content_parts)
            
            if not original_text.strip():
                logger.warning(f"⚠️ No text content found: {relative_path}")
                stats['errors'] += 1
                continue
            
            # Modify text using TextModifier for citation format changes
            logger.debug(f"🔄 Modifying citation formats: {relative_path}")
            modified_text = text_modifier.modify_text_sync(original_text, 'formato_citas')
            
            # Validate modification was successful
            if not modified_text or len(modified_text.strip()) < 10:
                logger.error(f"❌ Format modification failed for: {relative_path}")
                stats['errors'] += 1
                continue
            
            # Create modified JSON with updated text content
            modified_json = json_data.copy()
            
            # Split modified text back into sections (simple approach)
            modified_lines = modified_text.split('\n')
            
            # Update IDEA_CENTRAL if it exists
            if 'IDEA_CENTRAL' in modified_json:
                # Find the portion that corresponds to IDEA_CENTRAL
                idea_central_lines = len(json_data.get('IDEA_CENTRAL', '').split('\n'))
                modified_json['IDEA_CENTRAL'] = '\n'.join(modified_lines[:idea_central_lines])
                modified_lines = modified_lines[idea_central_lines:]
            
            # Update CONTENIDO sections if they exist
            if 'CONTENIDO' in modified_json:
                contenido_modified = modified_json['CONTENIDO'].copy()
                line_idx = 0
                
                for section_name, section_content in contenido_modified.items():
                    if isinstance(section_content, list):
                        section_length = len(section_content)
                        if line_idx + section_length <= len(modified_lines):
                            contenido_modified[section_name] = modified_lines[line_idx:line_idx + section_length]
                            line_idx += section_length
                    elif isinstance(section_content, str):
                        if line_idx < len(modified_lines):
                            contenido_modified[section_name] = modified_lines[line_idx]
                            line_idx += 1
                
                modified_json['CONTENIDO'] = contenido_modified
            
            # Save modified JSON
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(modified_json, f, ensure_ascii=False, indent=2)
            
            logger.debug(f"✅ Saved: {output_file}")
            stats['processed'] += 1
            
            # Small pause to avoid rate limits
            time.sleep(0.1)
            
        except Exception as e:
            logger.error(f"❌ Error processing {json_file}: {e}")
            stats['errors'] += 1
            continue
    
    # Final summary
    logger.info(f"📊 Test 1 Dataset Creation Summary:")
    logger.info(f"  ✅ Processed: {stats['processed']}")
    logger.info(f"  ❌ Errors: {stats['errors']}")
    logger.info(f"  ⏭️ Skipped: {stats['skipped']}")
    logger.info(f"  📁 Saved to: {output_dir}")
    
    return stats 