import textwrap, time, os
from .retrieve import OptimizedHybridRetriever as HybridRetriever
from .llm_azure import run_llm
import logging

logger = logging.getLogger(__name__)

# Retriever singleton para evitar re-inicialización
_retriever_instance = None

def get_retriever():
    """Singleton pattern para el retriever - evita re-inicializar modelos"""
    global _retriever_instance
    if _retriever_instance is None:
        logger.info("🚀 Inicializando retriever (primera vez)...")
        _retriever_instance = HybridRetriever()
    return _retriever_instance

PROMPT = """\
Eres asistente jurídico de la Sala Civil y Comercial.
Pregunta del juez: "{question}"

Devuelve una tabla Markdown con:
# | Expte. | Sección | Extracto (máx 40 palabras)

Usa **solo** la evidencia de CONTEXT.
CONTEXT:
{context}
"""

def answer(question: str, top_n: int = 8):
    """Versión optimizada de la función answer"""
    start_time = time.time()
    
    # Usar retriever singleton
    retriever = get_retriever()
    
    # Optimización: reducir top_n por defecto para mayor velocidad
    effective_top_n = min(top_n, int(os.getenv("MAX_RESULTS_PER_QUERY", "8")))
    
    # Búsqueda optimizada
    search_start = time.time()
    hits = retriever.query(question, effective_top_n)
    search_time = time.time() - search_start
    
    # Construcción de contexto optimizada
    ctx_start = time.time()
    # Limitar longitud de párrafos para mayor velocidad
    max_paragraph_length = int(os.getenv("MAX_PARAGRAPH_LENGTH", "300"))
    
    ctx = "\n".join(
        f"[{h['expte']} §{h['section']}]: {h['paragraph'][:max_paragraph_length]}{'...' if len(h['paragraph']) > max_paragraph_length else ''}" 
        for h in hits
    )
    ctx_time = time.time() - ctx_start
    
    # LLM optimizado
    llm_start = time.time()
    prompt = textwrap.dedent(PROMPT).format(question=question, context=ctx)
    
    # Tokens más conservadores para mayor velocidad
    max_tokens = min(512, int(os.getenv("LLM_MAX_TOKENS", "300")))
    messages = [{"role": "user", "content": prompt}]
    reply = run_llm(messages, max_tokens=max_tokens)
    llm_time = time.time() - llm_start
    
    total_time = time.time() - start_time
    
    # Logging de rendimiento
    logger.info(f"📊 Answer generated in {total_time:.3f}s:")
    logger.info(f"   Search: {search_time:.3f}s, Context: {ctx_time:.3f}s, LLM: {llm_time:.3f}s")
    logger.info(f"   Results: {len(hits)}, Context length: {len(ctx)} chars")
    
    return reply, hits
