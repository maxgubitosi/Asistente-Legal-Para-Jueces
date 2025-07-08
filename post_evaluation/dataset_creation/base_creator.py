"""
Base Dataset Creator with Multithreading Support

This module provides the core functionality for creating modified JSON datasets
with concurrent processing to speed up Azure LLM calls.
"""

import json
import logging
import time
from pathlib import Path
from typing import Dict, List, Any, Tuple, Callable
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..src.text_modifier import TextModifier

logger = logging.getLogger(__name__)


class BaseDatasetCreator:
    """
    Base class for creating modified datasets with multithreading support
    """
    
    def __init__(self, text_modifier: TextModifier, max_workers: int = 10):
        self.text_modifier = text_modifier
        self.max_workers = max_workers
    
    def load_json_file(self, json_file: Path) -> Dict[str, Any]:
        """
        Load a JSON file with encoding fallback
        
        Args:
            json_file: Path to JSON file
            
        Returns:
            Loaded JSON data
            
        Raises:
            Exception: If file cannot be loaded
        """
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except UnicodeDecodeError:
            with open(json_file, 'r', encoding='latin-1') as f:
                return json.load(f)
    
    def save_json_file(self, data: Dict[str, Any], output_file: Path) -> None:
        """
        Save JSON data to file
        
        Args:
            data: JSON data to save
            output_file: Output file path
        """
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def extract_text_content(self, json_data: Dict[str, Any]) -> str:
        """
        Extract text content from JSON for modification (used by test1)
        
        Args:
            json_data: JSON data
            
        Returns:
            Combined text content
        """
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
        
        return "\n".join(content_parts)
    
    def apply_text_modifications_to_json(self, 
                                       original_json: Dict[str, Any], 
                                       modified_text: str) -> Dict[str, Any]:
        """
        Apply modified text back to JSON structure (used by test1)
        
        Args:
            original_json: Original JSON data
            modified_text: Modified text content
            
        Returns:
            Modified JSON data
        """
        modified_json = original_json.copy()
        modified_lines = modified_text.split('\n')
        
        # Update IDEA_CENTRAL if it exists
        if 'IDEA_CENTRAL' in modified_json:
            idea_central_lines = len(original_json.get('IDEA_CENTRAL', '').split('\n'))
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
        
        return modified_json
    
    def modify_idea_central(self, 
                          json_data: Dict[str, Any], 
                          modification_type: str) -> Dict[str, Any]:
        """
        Modify IDEA_CENTRAL section (used by test2 and test3)
        
        Args:
            json_data: JSON data
            modification_type: Type of modification
            
        Returns:
            Modified JSON data
        """
        modified_json = json_data.copy()
        
        if 'IDEA_CENTRAL' in modified_json and modified_json['IDEA_CENTRAL']:
            original_idea = modified_json['IDEA_CENTRAL']
            try:
                modified_idea = self.text_modifier.modify_text_sync(original_idea, modification_type)
                if modified_idea and len(modified_idea.strip()) > 10:
                    modified_json['IDEA_CENTRAL'] = modified_idea
                else:
                    logger.warning(f"⚠️ Failed to modify IDEA_CENTRAL")
            except Exception as e:
                logger.warning(f"⚠️ Error modifying IDEA_CENTRAL: {e}")
        
        return modified_json
    
    def modify_contenido_sections(self, 
                                json_data: Dict[str, Any], 
                                modification_type: str,
                                priority_sections: List[str] = None,
                                min_text_length: int = 20) -> Dict[str, Any]:
        """
        Modify CONTENIDO sections (used by test2 and test3)
        
        Args:
            json_data: JSON data
            modification_type: Type of modification
            priority_sections: Sections to prioritize (for test3)
            min_text_length: Minimum text length to modify
            
        Returns:
            Modified JSON data
        """
        modified_json = json_data.copy()
        
        if 'CONTENIDO' not in modified_json:
            return modified_json
        
        contenido_modified = modified_json['CONTENIDO'].copy()
        
        for section_name, section_content in contenido_modified.items():
            # Skip non-priority sections if priority list is specified
            if priority_sections and section_name not in priority_sections:
                continue
            
            if isinstance(section_content, list):
                modified_items = []
                for i, item in enumerate(section_content):
                    if isinstance(item, str) and len(item.strip()) > min_text_length:
                        # For test3, modify every other item to maintain structure
                        if modification_type == 'cambio_contenido' and i % 2 != 0:
                            modified_items.append(item)
                            continue
                        
                        try:
                            modified_item = self.text_modifier.modify_text_sync(item, modification_type)
                            if modified_item and len(modified_item.strip()) > 10:
                                modified_items.append(modified_item)
                            else:
                                modified_items.append(item)
                        except Exception as e:
                            logger.warning(f"⚠️ Error modifying {section_name} item {i}: {e}")
                            modified_items.append(item)
                    else:
                        modified_items.append(item)
                contenido_modified[section_name] = modified_items
            
            elif isinstance(section_content, str) and len(section_content.strip()) > min_text_length:
                try:
                    modified_content = self.text_modifier.modify_text_sync(section_content, modification_type)
                    if modified_content and len(modified_content.strip()) > 10:
                        contenido_modified[section_name] = modified_content
                except Exception as e:
                    logger.warning(f"⚠️ Error modifying {section_name}: {e}")
        
        modified_json['CONTENIDO'] = contenido_modified
        return modified_json
    
    def process_single_file(self, 
                          file_data: Tuple[Path, Path, Path, bool],
                          modification_callback: Callable[[Dict[str, Any]], Dict[str, Any]]) -> Tuple[str, bool, str]:
        """
        Process a single JSON file
        
        Args:
            file_data: Tuple of (json_file, output_file, relative_path, resume)
            modification_callback: Function to apply modifications to JSON data
            
        Returns:
            Tuple of (relative_path_str, success, error_message)
        """
        json_file, output_file, relative_path, resume = file_data
        
        try:
            # Skip if file exists and resume mode
            if resume and output_file.exists():
                return (str(relative_path), True, "skipped")
            
            # Load original JSON
            json_data = self.load_json_file(json_file)
            
            # Validate JSON structure
            if not json_data or not isinstance(json_data, dict):
                return (str(relative_path), False, "Invalid JSON structure")
            
            # Apply modifications using callback
            modified_json = modification_callback(json_data)
            
            # Save modified JSON
            self.save_json_file(modified_json, output_file)
            
            return (str(relative_path), True, "success")
            
        except Exception as e:
            return (str(relative_path), False, str(e))
    
    def create_dataset_multithreaded(self,
                                   json_files: List[Path],
                                   output_dir: Path,
                                   original_data_path: Path,
                                   modification_callback: Callable[[Dict[str, Any]], Dict[str, Any]],
                                   test_name: str,
                                   sample_size: int = None,
                                   resume: bool = False) -> Dict[str, int]:
        """
        Create dataset with multithreaded processing
        
        Args:
            json_files: List of JSON files to process
            output_dir: Output directory
            original_data_path: Original data path for relative structure
            modification_callback: Function to apply modifications
            test_name: Name of the test for logging
            sample_size: Limit number of files
            resume: Continue from existing files
            
        Returns:
            Dictionary with processing statistics
        """
        logger.info(f"🚀 Creating {test_name} dataset with {self.max_workers} threads")
        
        # Prepare output directory
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Filter files if sample size specified
        if sample_size:
            json_files = json_files[:sample_size]
        
        # Prepare file data for processing
        file_data_list = []
        for json_file in json_files:
            relative_path = json_file.relative_to(original_data_path)
            output_file = output_dir / relative_path
            file_data_list.append((json_file, output_file, relative_path, resume))
        
        # Statistics
        stats = {
            'total_files': len(file_data_list),
            'processed': 0,
            'errors': 0,
            'skipped': 0
        }
        
        logger.info(f"📁 Files to process: {stats['total_files']}")
        logger.info(f"📂 Output directory: {output_dir}")
        
        # Process files with multithreading
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_file = {
                executor.submit(self.process_single_file, file_data, modification_callback): file_data 
                for file_data in file_data_list
            }
            
            # Process results as they complete
            with tqdm(total=len(file_data_list), desc=f"Processing {test_name}") as pbar:
                for future in as_completed(future_to_file):
                    file_data = future_to_file[future]
                    relative_path_str, success, message = future.result()
                    
                    if success:
                        if message == "skipped":
                            stats['skipped'] += 1
                            logger.debug(f"⏭️ Skipped: {relative_path_str}")
                        else:
                            stats['processed'] += 1
                            logger.debug(f"✅ Processed: {relative_path_str}")
                    else:
                        stats['errors'] += 1
                        logger.error(f"❌ Error processing {relative_path_str}: {message}")
                    
                    pbar.update(1)
        
        # Final summary
        logger.info(f"📊 {test_name} Dataset Creation Summary:")
        logger.info(f"  ✅ Processed: {stats['processed']}")
        logger.info(f"  ❌ Errors: {stats['errors']}")
        logger.info(f"  ⏭️ Skipped: {stats['skipped']}")
        logger.info(f"  📁 Saved to: {output_dir}")
        
        return stats 

    def _get_timestamp(self) -> str:
        """Get current timestamp for file generation"""
        from datetime import datetime
        return datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def process_single_file_for_questions(self, 
                                        file_data: Tuple[Path, Path, Path, bool],
                                        question_generation_callback: Callable[[Dict[str, Any], Path, Path], Dict[str, Any]]) -> Tuple[str, bool, str]:
        """
        Process a single JSON file for question generation
        
        Args:
            file_data: Tuple of (json_file, output_dir, relative_path, resume)
            question_generation_callback: Function to generate questions from JSON data
            
        Returns:
            Tuple of (relative_path_str, success, error_message)
        """
        json_file, output_dir, relative_path, resume = file_data
        
        try:
            # Check if questions file already exists and resume mode
            questions_file = output_dir / f"{json_file.stem}_questions.json"
            if resume and questions_file.exists():
                return (str(relative_path), True, "skipped")
            
            # Load original JSON
            json_data = self.load_json_file(json_file)
            
            # Validate JSON structure
            if not json_data or not isinstance(json_data, dict):
                return (str(relative_path), False, "Invalid JSON structure")
            
            # Generate questions using callback
            result = question_generation_callback(json_data, json_file, output_dir)
            
            # Check if there was an error
            if "error" in result:
                return (str(relative_path), False, result["error"])
            
            # Check if we have results for multiple question types (test4 format)
            if "results" in result:
                # Count successful generations
                successful_types = sum(1 for v in result["results"].values() if isinstance(v, int))
                total_types = len(result["results"])
                
                if successful_types == 0:
                    # All failed
                    errors = [f"{k}: {v}" for k, v in result["results"].items() if not isinstance(v, int)]
                    return (str(relative_path), False, f"All question types failed: {'; '.join(errors)}")
                elif successful_types < total_types:
                    # Some failed
                    logger.warning(f"⚠️ Some question types failed for {relative_path}")
                    for k, v in result["results"].items():
                        if not isinstance(v, int):
                            logger.warning(f"  {k}: {v}")
                
                return (str(relative_path), True, f"Generated {successful_types}/{total_types} question types")
            
            return (str(relative_path), True, "success")
            
        except Exception as e:
            return (str(relative_path), False, str(e))
    
    def create_questions_dataset_multithreaded(self,
                                             json_files: List[Path],
                                             output_dir: Path,
                                             original_data_path: Path,
                                             question_generation_callback: Callable[[Dict[str, Any], Path, Path], Dict[str, Any]],
                                             test_name: str,
                                             sample_size: int = None,
                                             resume: bool = False) -> Dict[str, int]:
        """
        Create questions dataset with multithreaded processing
        
        Args:
            json_files: List of JSON files to process
            output_dir: Output directory for question files
            original_data_path: Original data path for relative structure
            question_generation_callback: Function to generate questions from JSON data
            test_name: Name of the test for logging
            sample_size: Limit number of files
            resume: Continue from existing files
            
        Returns:
            Dictionary with processing statistics
        """
        logger.info(f"🚀 Creating {test_name} dataset with {self.max_workers} threads")
        
        # Prepare output directory
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Filter files if sample size specified
        if sample_size:
            json_files = json_files[:sample_size]
        
        # Prepare file data for processing
        file_data_list = []
        for json_file in json_files:
            relative_path = json_file.relative_to(original_data_path)
            file_data_list.append((json_file, output_dir, relative_path, resume))
        
        # Statistics
        stats = {
            'total_files': len(file_data_list),
            'processed': 0,
            'errors': 0,
            'skipped': 0
        }
        
        logger.info(f"📁 Files to process: {stats['total_files']}")
        logger.info(f"📂 Output directory: {output_dir}")
        
        # Process files with multithreading
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_file = {
                executor.submit(self.process_single_file_for_questions, file_data, question_generation_callback): file_data 
                for file_data in file_data_list
            }
            
            
            # Process results as they complete
            with tqdm(total=len(file_data_list), desc=f"Processing {test_name}") as pbar:
                for future in as_completed(future_to_file):
                    file_data = future_to_file[future]
                    relative_path_str, success, message = future.result()
                    
                    if success:
                        if message == "skipped":
                            stats['skipped'] += 1
                            logger.debug(f"⏭️ Skipped: {relative_path_str}")
                        else:
                            stats['processed'] += 1
                            logger.debug(f"✅ Generated questions for: {relative_path_str}")
                    else:
                        stats['errors'] += 1
                        logger.error(f"❌ Error generating questions for {relative_path_str}: {message}")
                    
                    pbar.update(1)
        
        # Final summary
        logger.info(f"📊 {test_name} Dataset Creation Summary:")
        logger.info(f"  ✅ Questions generated: {stats['processed']}")
        logger.info(f"  ❌ Errors: {stats['errors']}")
        logger.info(f"  ⏭️ Skipped: {stats['skipped']}")
        logger.info(f"  📁 Saved to: {output_dir}")
        
        return stats 