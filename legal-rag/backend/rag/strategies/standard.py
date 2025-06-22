import textwrap, time, os
import logging
from typing import Tuple, List, Dict, Any

from ..base import BaseRAGPipeline
from backend.search import get_retriever
from backend.llm import get_llm_provider

logger = logging.getLogger(__name__)

# Retriever singleton para evitar re-inicialización
_retriever_instance = None
_llm_provider_instance = None

def get_retriever_singleton():
    """Singleton pattern para el retriever - evita re-inicializar modelos"""
    global _retriever_instance
    if _retriever_instance is None:
        logger.info("🚀 Inicializando retriever (primera vez)...")
        _retriever_instance = get_retriever("hybrid")
    return _retriever_instance

def get_llm_singleton():
    """Singleton pattern para el LLM provider"""
    global _llm_provider_instance
    if _llm_provider_instance is None:
        logger.info("🤖 Inicializando LLM provider (primera vez)...")
        _llm_provider_instance = get_llm_provider("azure")
    return _llm_provider_instance

PROMPT = """\
Eres asistente jurídico de la Sala Civil y Comercial.
Pregunta del juez: "{question}"

Devuelve una tabla Markdown con:
# | Expte. | Sección | Extracto (máx 40 palabras)

Usa **solo** la evidencia de CONTEXT.
CONTEXT:
{context}
"""

class StandardRAGPipeline(BaseRAGPipeline):
    """Pipeline RAG estándar - migrado de pipeline.py"""
    
    def __init__(self):
        self.retriever = None
        self.llm_provider = None
        self.max_paragraph_length = int(os.getenv("MAX_PARAGRAPH_LENGTH", "300"))
        self.max_tokens = int(os.getenv("LLM_MAX_TOKENS", "300"))
        self.max_results = int(os.getenv("MAX_RESULTS_PER_QUERY", "8"))
    
    def _get_retriever(self):
        """Lazy loading del retriever"""
        if self.retriever is None:
            self.retriever = get_retriever_singleton()
        return self.retriever
    
    def _get_llm_provider(self):
        """Lazy loading del LLM provider"""
        if self.llm_provider is None:
            self.llm_provider = get_llm_singleton()
        return self.llm_provider
    
    def query(self, question: str, top_n: int = 8) -> Tuple[str, List[Dict[str, Any]]]:
        """Procesa una consulta y devuelve respuesta + evidencia"""
        start_time = time.time()
        
        # Búsqueda
        retriever = self._get_retriever()
        effective_top_n = min(top_n, self.max_results)
        
        search_start = time.time()
        hits = retriever.query(question, effective_top_n)
        search_time = time.time() - search_start
        
        # Construcción de contexto
        ctx_start = time.time()
        context = self._build_context(hits)
        ctx_time = time.time() - ctx_start
        
        # Generación de respuesta
        llm_start = time.time()
        response = self._generate_response(question, context)
        llm_time = time.time() - llm_start
        
        total_time = time.time() - start_time
        
        # Logging
        self._log_performance(total_time, search_time, ctx_time, llm_time, hits, context)
        
        return response, hits
    
    def _build_context(self, hits: List[Dict[str, Any]]) -> str:
        """Construye el contexto optimizado"""
        return "\n".join(
            f"[{h['expte']} §{h['section']}]: {h['paragraph'][:self.max_paragraph_length]}{'...' if len(h['paragraph']) > self.max_paragraph_length else ''}" 
            for h in hits
        )
    
    def _generate_response(self, question: str, context: str) -> str:
        """Genera respuesta usando LLM"""
        prompt = textwrap.dedent(PROMPT).format(question=question, context=context)
        messages = [{"role": "user", "content": prompt}]
        
        llm_provider = self._get_llm_provider()
        return llm_provider.generate(messages, max_tokens=self.max_tokens)
    
    def _log_performance(self, total_time, search_time, ctx_time, llm_time, hits, context):
        """Log de métricas de rendimiento"""
        logger.info(f"📊 StandardRAG query processed in {total_time:.3f}s:")
        logger.info(f"   Search: {search_time:.3f}s, Context: {ctx_time:.3f}s, LLM: {llm_time:.3f}s")
        logger.info(f"   Results: {len(hits)}, Context length: {len(context)} chars")
    
    def get_stats(self) -> Dict[str, Any]:
        """Estadísticas del pipeline estándar"""
        retriever = self._get_retriever() if self.retriever else None
        llm_provider = self._get_llm_provider() if self.llm_provider else None
        
        return {
            "pipeline_type": "standard",
            "retriever_loaded": retriever is not None,
            "llm_provider_loaded": llm_provider is not None,
            "max_paragraph_length": self.max_paragraph_length,
            "max_tokens": self.max_tokens,
            "max_results": self.max_results,
            "retriever_stats": retriever.get_stats() if retriever else None,
            "llm_stats": llm_provider.get_stats() if llm_provider else None
        }
    
    def supports_streaming(self) -> bool:
        """StandardRAG no soporta streaming por ahora"""
        return False

# Alias para compatibilidad
RAGPipeline = StandardRAGPipeline