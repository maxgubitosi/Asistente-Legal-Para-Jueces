import heapq, pickle, numpy as np, time
from sentence_transformers import SentenceTransformer, CrossEncoder
from qdrant_client import QdrantClient
from rank_bm25 import BM25Okapi
from functools import lru_cache
import logging
from typing import List, Dict, Any
from backend.config import get_settings
from ..base import BaseRetriever

logger = logging.getLogger(__name__)
settings = get_settings()
EMB_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

class HybridRetrieverEnriched(BaseRetriever):
    """Retriever híbrido que aprovecha campos enriquecidos (artículos citados, idea central, materia, etc.)"""

    def __init__(self, k_dense: int = settings.dense_search_limit, k_lex: int = settings.lexical_search_limit):
        start_time = time.time()
        self.qdrant = QdrantClient(
            url=settings.qdrant_url,
            prefer_grpc=False,
            timeout=10.0
        )
        try:
            with open(settings.bm25_path, "rb") as f:
                self.bm25 = pickle.load(f)
            self.corpus = np.load(settings.bm25_corpus_path, allow_pickle=True)
        except FileNotFoundError as e:
            raise FileNotFoundError(
                f"BM25 index files not found. Please build indexes first.\nMissing: {e.filename}"
            ) from e
        self.encoder = SentenceTransformer(EMB_MODEL, device='cpu')
        self.encoder.max_seq_length = 256
        self.use_reranking = settings.enable_reranking
        if self.use_reranking:
            self.rerank = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
        self.k_dense = k_dense
        self.k_lex = k_lex
        logger.info(f"✅ HybridRetrieverEnriched initialized in {time.time() - start_time:.2f}s")

    @lru_cache(maxsize=100 if settings.enable_query_caching else 0)
    def _encode_question(self, question: str):
        return self.encoder.encode(question)

    def _boost_score(self, payload: dict, question: str) -> float:
        """Aumenta el score si la consulta menciona artículos citados, materia o idea central"""
        boost = 0.0
        q_lower = question.lower()
        # Boost por artículos citados
        articulos = payload.get("articulos_citados", [])
        for art in articulos:
            main_source = art.get("main_source", "").lower()
            for num in art.get("cited_articles", []):
                if str(num) in q_lower or main_source in q_lower:
                    boost += 0.3
        # Boost por materia preliminar
        materia = payload.get("materia_preliminar", "")
        if materia and materia.lower() in q_lower:
            boost += 0.1
        # Boost por idea central
        idea = payload.get("idea_central", "")
        if idea and any(word in idea.lower() for word in q_lower.split()):
            boost += 0.2
        return boost

    def query(self, question: str, top_n: int = 10) -> List[Dict[str, Any]]:
        start_time = time.time()
        query_vector = self._encode_question(question)
        dense_hits = self.qdrant.search(
            collection_name="fallos",
            query_vector=query_vector,
            limit=self.k_dense,
            with_payload=True,
            with_vectors=False
        )
        question_tokens = question.lower().split()
        lex_scores = self.bm25.get_scores(question_tokens)
        lex_ids = np.argpartition(lex_scores, -self.k_lex)[-self.k_lex:]
        lex_ids = lex_ids[np.argsort(lex_scores[lex_ids])[::-1]]
        candidates = {}
        for h in dense_hits:
            candidates[int(h.id)] = (float(h.score), h.payload)
        missing_ids = [int(idx) for idx in lex_ids if int(idx) not in candidates]
        if missing_ids:
            missing_points = self.qdrant.retrieve(
                collection_name="fallos",
                ids=missing_ids,
                with_payload=True,
                with_vectors=False
            )
            for point, idx in zip(missing_points, missing_ids):
                candidates[idx] = (float(lex_scores[idx]), point.payload)
        for idx in lex_ids:
            py_idx = int(idx)
            if py_idx in candidates:
                old_score, payload = candidates[py_idx]
                combined_score = old_score + (float(lex_scores[idx]) * 0.5)
                candidates[py_idx] = (combined_score, payload)
        # Boost por metadatos enriquecidos
        for idx, (score, payload) in candidates.items():
            boost = self._boost_score(payload, question)
            candidates[idx] = (score + boost, payload)
        # Reranking opcional
        if self.use_reranking and len(candidates) > 0:
            texts = [c[1]["text"][:500] for c in candidates.values()]
            pairs = [(question, t) for t in texts]
            scores = self.rerank.predict(pairs)
            scored = [(float(s), p) for s, (_, p) in zip(scores, candidates.values())]
        else:
            scored = [(score, payload) for score, payload in candidates.values()]
        top = heapq.nlargest(top_n, scored, key=lambda x: x[0])
        return [
            {
                "score": s,
                "expte": p.get("expediente", ""),
                "section": p.get("section", ""),
                "paragraph": p.get("text", ""),
                "path": p.get("path", ""),
                "idea_central": p.get("idea_central", ""),
                "articulos_citados": p.get("articulos_citados", []),
                "materia_preliminar": p.get("materia_preliminar", ""),
                "search_type": "hybrid_enriched"
            }
            for s, p in top
        ]
