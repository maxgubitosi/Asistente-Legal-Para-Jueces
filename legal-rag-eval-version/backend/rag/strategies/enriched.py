import textwrap, time
import logging
from typing import Tuple, List, Dict, Any

from ..base import BaseRAGPipeline
from backend.search import get_retriever
from backend.llm import get_llm_provider
from backend.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

MULTI_JUSTIFY_PROMPT = """
Eres asistente jurídico de la Sala Civil y Comercial.

OBJETIVO  
Redacta UN párrafo por cada bloque «===== FALLO … =====» del CONTEXT
(expedientes ordenados tal como aparecen).

Formato de salida (sin tablas):

[123/2024] «párrafo justificativo…»
[456/2023] «párrafo justificativo…»
…

Cada párrafo debe:
• mencionar los artículos y códigos de ser necesario (ej. art. 67 CCyC);  
• Usa la informacion de la idea central de ser necesario;  
• incluir una o varias citas textuales: «cita» (§).  
No inventes datos: usa solo lo que veas en el CONTEXT.
Si un fallo carece de algún dato, pon “NO HAY EVIDENCIA SUFICIENTE EN EL CORPUS.”.

Pregunta del juez: "{question}"

CONTEXT:
{context}
"""

class EnrichedRAGPipeline(BaseRAGPipeline):
    """Pipeline RAG que aprovecha campos enriquecidos"""
    def __init__(self):
        self.retriever = None
        self.llm_provider = None
        self.max_paragraph_length = int(settings.max_paragraph_length)
        self.max_tokens = int(settings.llm_max_tokens)
        self.max_results = int(settings.max_results_per_query)

    def _get_retriever(self):
        if self.retriever is None:
            self.retriever = get_retriever("hybrid_enriched")
        return self.retriever

    def _get_llm_provider(self):
        if self.llm_provider is None:
            self.llm_provider = get_llm_provider("azure")
        return self.llm_provider

    def _group_hits_by_expediente(self, hits: list) -> List[Dict[str, Any]]:
        """Une los hits de un mismo expediente y consolida campos, usando nombres correctos del retriever."""
        grouped: Dict[str, Dict[str, Any]] = {}

        for h in hits:
            expte = h.get("expte") or h.get("expediente") or "N/A"
            g = grouped.setdefault(expte, {
                "expte": expte,
                "idea_central": h.get("idea_central", "-"),
                "articulos_citados": [],
                "materia_preliminar": h.get("materia_preliminar", h.get("materia", "-")),
                "extractos": [],
                "sections": [],
                "paths": [],
                "scores": [],
                "search_types": [],
            })

            # artículos (lista de dicts) sin duplicados
            for art in h.get("articulos_citados", []):
                if art not in g["articulos_citados"]:
                    g["articulos_citados"].append(art)

            # resto de info
            g["extractos"].append(h.get("paragraph", h.get("text", "Sin contenido")))
            g["sections"].append(h.get("section", "N/A"))
            g["paths"].append(h.get("path", ""))
            g["scores"].append(h.get("score", 0))
            g["search_types"].append(h.get("search_type", "-"))

        return list(grouped.values())
    
    def query(self, question: str, top_n: int = 8) -> Tuple[str, List[Dict[str, Any]]]:
        start_time = time.time()
        retriever = self._get_retriever()
        effective_top_n = min(top_n, self.max_results)
        search_start = time.time()
        hits = retriever.query(question, effective_top_n)
        search_time = time.time() - search_start
        ctx_start = time.time()
        grouped_hits = self._group_hits_by_expediente(hits)
        context = self._build_context(grouped_hits)
        ctx_time = time.time() - ctx_start
        llm_start = time.time()
        response = self._generate_response(question, context)
        llm_time = time.time() - llm_start
        total_time = time.time() - start_time
        self._log_performance(total_time, search_time, ctx_time, llm_time, hits, context)
        return response, grouped_hits

    def _build_context(self, grouped_hits: List[Dict[str, Any]]) -> str:
        """Devuelve:  FALLO → GENERAL → DETALLES  para cada expediente."""
        def fmt_articulos(arts):
            if not arts:
                return "-"
            return ", ".join(
                f"{a['main_source']} {', '.join(map(str, a['cited_articles']))}"
                for a in arts
            )

        lines = []
        for h in grouped_hits:
            # encabezado
            lines.append(f"===== FALLO {h['expte']} =====")
            # GENERAL
            lines.append(
                f"GENERAL: Materia: {h['materia_preliminar']}; "
                f"Artículos: {fmt_articulos(h['articulos_citados'])}; "
                f"Idea: {h['idea_central']}"
            )
            # DETALLES (extractos y secciones emparejados)
            for sec, txt in zip(h["sections"], h["extractos"]):
                snippet = txt.strip().replace("\n", " ")
                if len(snippet) > self.max_paragraph_length:
                    snippet = snippet[: self.max_paragraph_length] + "…"
                lines.append(f"DETALLE §{sec}: {snippet}")

            lines.append("")  # línea en blanco separadora

        return "\n".join(lines)

    def _generate_response(self, question: str, context: str) -> str:
        prompt = textwrap.dedent(MULTI_JUSTIFY_PROMPT).format(question=question, context=context)
        messages = [{"role": "user", "content": prompt}]
        llm_provider = self._get_llm_provider()
        return llm_provider.generate(messages, max_tokens=self.max_tokens)

    def _log_performance(self, total_time, search_time, ctx_time, llm_time, hits, context):
        logger.info(f"📊 EnrichedRAG query processed in {total_time:.3f}s:")
        logger.info(f"   Search: {search_time:.3f}s, Context: {ctx_time:.3f}s, LLM: {llm_time:.3f}s")
        logger.info(f"   Results: {len(hits)}, Context length: {len(context)} chars")

    def get_stats(self) -> Dict[str, Any]:
        retriever = self._get_retriever() if self.retriever else None
        llm_provider = self._get_llm_provider() if self.llm_provider else None
        return {
            "pipeline_type": "enriched",
            "retriever_loaded": retriever is not None,
            "llm_provider_loaded": llm_provider is not None,
            "max_paragraph_length": self.max_paragraph_length,
            "max_tokens": self.max_tokens,
            "max_results": self.max_results,
            "retriever_stats": retriever.get_stats() if retriever else None,
            "llm_stats": llm_provider.get_stats() if llm_provider else None
        }

    def supports_streaming(self) -> bool:
        return False

# Alias para compatibilidad
RAGPipeline = EnrichedRAGPipeline
