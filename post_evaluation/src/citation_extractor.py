"""
Extractor de Citas Legales

Este módulo utiliza la lógica de extracción de citas del sistema principal
para la evaluación.
"""

import re
from typing import Set, List
from pathlib import Path

class CitationExtractor:
    """
    Extractor de citas legales usando la misma lógica que el sistema principal.
    Basado en el código de 4_article_extraction.ipynb
    """
    
    def __init__(self):
        # Patrones regex exactos del sistema principal
        self.regex_patterns = [
            # Artículos con diferentes formatos
            r'-?arts?\.\s*(\d+(?:º|°)?)(?:\s*[,y]\s*(\d+(?:º|°)?))*',  # arts. 3, 14, 29 y 94 o -arts. 1º y 4º
            r'Art(?:ículo)?s?\.\s*(\d+(?:º|°)?)(?:\s*[,y]\s*(\d+(?:º|°)?))*',  # Art. 28, Artículo 45
            r'del\s+art\.?\s*(\d+(?:º|°)?)',  # del art.114
            r'artículos?\s+(\d+(?:º|°)?)(?:\s*[,y]\s*(\d+(?:º|°)?))*',  # artículo 123 y 456
            
            # Leyes con diferentes formatos
            r'ley\s+n?º?\s*(\d+(?:/\d+)?)',  # ley 7046, ley nº 5678/90
            r'leyes?\s+n?º?\s*(\d+(?:/\d+)?)(?:\s*[,y]\s*(\d+(?:/\d+)?))*',  # leyes 123 y 456
            
            # Números standalone después de menciones de artículos (para capturar secuencias)
            r'(?:arts?\.|artículos?|Art\.)\s*[^\d]*(\d+(?:º|°)?(?:\s*[,y]\s*\d+(?:º|°)?)*(?:\s*y\s*\d+(?:º|°)?)?)',
        ]
        
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.regex_patterns]
        
        # Patrón para secuencias específicas
        self.sequence_pattern = r'(?:-?arts?\.|artículos?|Art\.)\s*([0-9º°,\s\-y]+?)(?:\s+de\s+la\s+ley|\s+Ac\.|\.|\s|$)'
    
    def extract_numbers_from_match(self, match_groups: tuple) -> List[str]:
        """Extrae todos los números de los grupos de una coincidencia regex"""
        numbers = []
        for group in match_groups:
            if group:  # Si el grupo no es None
                # Buscar todos los números en el grupo
                nums = re.findall(r'\d+(?:º|°)?', group)
                numbers.extend(nums)
        return numbers
    
    def extract_citations(self, text: str) -> Set[str]:
        """
        Extrae artículos de un texto usando múltiples estrategias.
        Replica exactamente la lógica del sistema principal.
        """
        all_articles = set()  # Usar set para evitar duplicados
        
        # Estrategia 1: Patrones específicos
        for pattern in self.compiled_patterns:
            matches = pattern.finditer(text)
            for match in matches:
                numbers = self.extract_numbers_from_match(match.groups())
                all_articles.update(numbers)
        
        # Estrategia 2: Buscar secuencias específicas como "3, 14, 29, 30, 63, 64, 71 y 94"
        # Patrón para capturar listas de números después de "arts." o similar
        seq_matches = re.finditer(self.sequence_pattern, text, re.IGNORECASE)
        for match in seq_matches:
            sequence = match.group(1)
            # Extraer todos los números de la secuencia
            nums = re.findall(r'\d+(?:º|°)?', sequence)
            all_articles.update(nums)
        
        return all_articles
    
    def compare_extractions(self, original_citations: Set[str], modified_citations: Set[str]) -> dict:
        """
        Compara dos conjuntos de citas extraídas y retorna métricas de comparación
        """
        missing_citations = original_citations - modified_citations
        extra_citations = modified_citations - original_citations
        common_citations = original_citations.intersection(modified_citations)
        
        # Calcular métricas
        precision = len(common_citations) / len(modified_citations) if len(modified_citations) > 0 else 0
        recall = len(common_citations) / len(original_citations) if len(original_citations) > 0 else 0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        accuracy = 1.0 if original_citations == modified_citations else 0.0
        
        return {
            'original_citations': list(original_citations),
            'modified_citations': list(modified_citations),
            'missing_citations': list(missing_citations),
            'extra_citations': list(extra_citations),
            'common_citations': list(common_citations),
            'precision': precision,
            'recall': recall,
            'f1_score': f1_score,
            'accuracy': accuracy,
            'total_original': len(original_citations),
            'total_modified': len(modified_citations),
            'total_common': len(common_citations)
        }
    
    def extract_from_file(self, file_path: Path) -> Set[str]:
        """
        Extrae citas de un archivo de texto
        """
        try:
            text = file_path.read_text(encoding='utf-8')
            return self.extract_citations(text)
        except Exception as e:
            raise ValueError(f"Error leyendo archivo {file_path}: {e}")
    
    def validate_extraction(self, text: str, expected_citations: Set[str]) -> bool:
        """
        Valida que la extracción de citas funcione correctamente para un texto dado
        """
        extracted = self.extract_citations(text)
        return extracted == expected_citations 