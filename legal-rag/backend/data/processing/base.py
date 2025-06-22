from abc import ABC, abstractmethod
from pathlib import Path
from typing import Iterator

from ..models import LegalParagraph

class DataProcessor(ABC):
    """Interface simple para procesadores de datos"""
    
    @abstractmethod
    def process_directory(self, json_dir: Path) -> Iterator[LegalParagraph]:
        """Procesa directorio y retorna párrafos"""
        pass
    
    def get_stats(self) -> dict:
        """Retorna estadísticas básicas"""
        return {}