"""
Core utilities for RAG system evaluation.

This module contains the core utility classes and functions:
- Citation extraction and comparison  
- RAG client for backend communication
- Metrics calculation and reporting
- Text modification utilities

Usage:
    from post_evaluation.src.citation_extractor import CitationExtractor
    from post_evaluation.src.rag_client import RAGClient
"""

# Import main utility classes for easier access
from .citation_extractor import CitationExtractor
from .rag_client import RAGClient
from .metrics import EvaluationResult, MetricsCalculator, ResultsManager
from .text_modifier import TextModifier
from .docker_manager import EvalDockerManager

__all__ = [
    'CitationExtractor',
    'RAGClient', 
    'EvaluationResult',
    'MetricsCalculator',
    'ResultsManager',
    'TextModifier',
    'EvalDockerManager'
]

__version__ = "1.0.0"

# Main evaluation components
from .citation_extractor import CitationExtractor
from .rag_client import RAGClient  
from .metrics import EvaluationResult, MetricsCalculator, ResultsManager
from .text_modifier import TextModifier

__all__ = [
    'CitationExtractor',
    'RAGClient', 
    'EvaluationResult',
    'MetricsCalculator',
    'ResultsManager',
    'TextModifier'
] 