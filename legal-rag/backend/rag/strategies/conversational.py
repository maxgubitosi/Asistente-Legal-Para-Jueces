import textwrap
import logging
from typing import Tuple, List, Dict, Any

from ..base import BaseRAGPipeline
from backend.search import get_retriever
from backend.llm import get_llm_provider
from backend.config import get_settings

settings = get_settings()

logger = logging.getLogger(__name__)

CONVERSATIONAL_PROMPT = """\
Eres asistente jurídico de la Sala Civil y Comercial.

HISTORIAL DE CONVERSACIÓN:
{conversation_history}

NUEVA PREGUNTA: "{question}"

CONTEXTO LEGAL:
{context}

Responde considerando tanto el historial como la nueva evidencia.
"""

class ConversationalRAGPipeline(BaseRAGPipeline):
    """Pipeline RAG con memoria conversacional"""
    
    def __init__(self, max_history: int = 5):
        self.conversation_history = []
        self.max_history = max_history
        self.retriever = None
        self.llm_provider = None
    
    def query(self, question: str, top_n: int = 8) -> Tuple[str, List[Dict[str, Any]]]:
        """Procesa consulta con contexto conversacional"""
        # Búsqueda normal
        if self.retriever is None:
            self.retriever = get_retriever(settings.search_strategy)
        
        hits = self.retriever.query(question, top_n)
        
        # Construir contexto con historial
        context = self._build_context_with_history(hits)
        conversation_context = self._build_conversation_history()
        
        # Generar respuesta considerando historial
        if self.llm_provider is None:
            self.llm_provider = get_llm_provider("azure")
        
        prompt = textwrap.dedent(CONVERSATIONAL_PROMPT).format(
            conversation_history=conversation_context,
            question=question,
            context=context
        )
        
        messages = [{"role": "user", "content": prompt}]
        response = self.llm_provider.generate(messages, max_tokens=400)
        
        # Guardar en historial
        self._update_history(question, response)
        
        logger.info(f"🗣️ ConversationalRAG: {len(self.conversation_history)} turns in history")
        
        return response, hits
    
    def _build_context_with_history(self, hits: List[Dict[str, Any]]) -> str:
        """Construye contexto considerando hits actuales"""
        return "\n".join(f"[{h['expte']}]: {h['paragraph'][:200]}..." for h in hits)
    
    def _build_conversation_history(self) -> str:
        """Construye contexto del historial conversacional"""
        if not self.conversation_history:
            return "No hay historial previo."
        
        history_text = []
        for i, (q, a) in enumerate(self.conversation_history[-self.max_history:], 1):
            history_text.append(f"Pregunta {i}: {q}")
            history_text.append(f"Respuesta {i}: {a[:100]}...")
        
        return "\n".join(history_text)
    
    def _update_history(self, question: str, response: str):
        """Actualiza el historial conversacional"""
        self.conversation_history.append((question, response))
        
        # Mantener solo los últimos max_history intercambios
        if len(self.conversation_history) > self.max_history:
            self.conversation_history = self.conversation_history[-self.max_history:]
    
    def clear_history(self):
        """Limpia el historial conversacional"""
        self.conversation_history = []
        logger.info("🗑️ Historial conversacional limpiado")
    
    def get_stats(self) -> Dict[str, Any]:
        """Estadísticas del pipeline conversacional"""
        return {
            "pipeline_type": "conversational",
            "conversation_turns": len(self.conversation_history),
            "max_history": self.max_history,
            "retriever_loaded": self.retriever is not None,
            "llm_provider_loaded": self.llm_provider is not None
        }
    
    def supports_streaming(self) -> bool:
        """ConversationalRAG podría soportar streaming"""
        return True