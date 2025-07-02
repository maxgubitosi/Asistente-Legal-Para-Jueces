from pathlib import Path
import json
import logging
from typing import Iterator, Set
from pydantic import ValidationError

from .base import DataProcessor
from ..models import LegalParagraph

logger = logging.getLogger(__name__)

class StandardProcessor(DataProcessor):
    """Procesador estándar - migrado de ingest.py"""
    
    def __init__(self):
        self.stats = {
            "files_processed": 0,
            "paragraphs_extracted": 0,
            "expedientes_found": set(),
            "errors": []
        }
    
    def process_directory(self, json_dir: Path) -> Iterator[LegalParagraph]:
        """Procesa directorio completo"""
        logger.info(f"📁 Procesando directorio: {json_dir}")
        
        json_files = list(json_dir.rglob("*.json"))
        logger.info(f"📄 Encontrados {len(json_files)} archivos")
        
        for file_path in json_files:
            try:
                yield from self._process_file(file_path, json_dir)
                self.stats["files_processed"] += 1
            except Exception as e:
                error_msg = f"Error en {file_path.name}: {str(e)}"
                logger.error(error_msg)
                self.stats["errors"].append(error_msg)
                continue
        
        logger.info(f"✅ Procesamiento completado: {self.stats}")
    
    def _process_file(self, file_path: Path, base_dir: Path) -> Iterator[LegalParagraph]:
        """Procesa un archivo JSON"""
        content = file_path.read_text(encoding="utf-8")
        docs = json.loads(content)
        
        if not isinstance(docs, list):
            docs = [docs]
        
        for doc in docs:
            yield from self._process_document(doc, file_path, base_dir)
    
    def _process_document(self, doc: dict, file_path: Path, base_dir: Path) -> Iterator[LegalParagraph]:
        """Procesa un documento individual"""
        contenido = doc["CONTENIDO"]
        expte = self._extract_expediente(doc=doc)
        self.stats["expedientes_found"].add(expte)
        
        for section, paragraphs in contenido.items():
            if not isinstance(paragraphs, list):
                continue
            
            for idx, text in enumerate(paragraphs):
                if not text or not isinstance(text, str) or len(text.strip()) < 10:
                    continue
                
                try:
                    paragraph = LegalParagraph(
                        expediente=expte,
                        section=section,
                        paragraph_id=idx,
                        text=text,
                        path=file_path.relative_to(base_dir).as_posix()
                    )
                    self.stats["paragraphs_extracted"] += 1
                    yield paragraph
                except ValidationError:
                    continue
    
    def _extract_expediente(self, doc: dict) -> str:
        """Extrae el expediente desde METADATOS['ID_FALLO']. Lanza error si no existe."""
        expte = doc.get("METADATOS", {}).get("ID_FALLO")
        if not expte:
            raise ValueError("No se encontró 'ID_FALLO' en METADATOS del documento.")
        return expte
    
    def get_stats(self) -> dict:
        """Estadísticas del proceso"""
        return {
            "processor_type": "standard",
            "files_processed": self.stats["files_processed"],
            "paragraphs_extracted": self.stats["paragraphs_extracted"],
            "expedientes_found": len(self.stats["expedientes_found"]),
            "errors": len(self.stats["errors"]),
            "error_rate": len(self.stats["errors"]) / max(1, self.stats["files_processed"])
        }