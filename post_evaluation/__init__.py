"""
Módulo de Evaluación Post-Entrenamiento para Sistema RAG Legal

Este módulo contiene las herramientas para evaluar la robustez y rendimiento
del sistema RAG legal a través de cuatro pruebas principales:

1. Robustez de Formato de Citas
2. Sensibilidad a cambios superficiales de Redacción  
3. (DEPRECADO) Sensibilidad a Cambios de Contenido 
4. Precisión de Recuperación de Documentos
"""

from .src.citation_extractor import CitationExtractor
from .src.text_modifier import TextModifier
from .src.rag_client import RAGClient
from .src.metrics import EvaluationResult, MetricsCalculator

__version__ = "1.0.0"
__author__ = "Legal RAG Evaluation Team"

__all__ = [
    'CitationExtractor',
    'TextModifier', 
    'RAGClient',
    'EvaluationResult',
    'MetricsCalculator'
] 