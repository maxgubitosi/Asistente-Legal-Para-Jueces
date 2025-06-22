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

class HybridRetriever(BaseRetriever):
    """Retriever híbrido optimizado - migrado de retrieve.py"""

    def __init__(self, k_dense: int = settings.dense_search_limit, k_lex: int = settings.lexical_search_limit):
        start_time = time.time()
        
        # Qdrant client optimizado
        self.qdrant = QdrantClient(
            url=settings.qdrant_url,
            prefer_grpc=False,
            timeout=10.0
        )
        
        # Cargar BM25 con manejo de errores
        try:
            with open(settings.bm25_path, "rb") as f:
                self.bm25 = pickle.load(f)
            self.corpus = np.load(settings.bm25_corpus_path, allow_pickle=True)
        except FileNotFoundError as e:
            raise FileNotFoundError(
                f"BM25 index files not found. Please build indexes first.\n"
                f"Missing: {e.filename}"
            ) from e
        
        # Modelos pre-cargados
        self.encoder = SentenceTransformer(EMB_MODEL, device='cpu')
        self.encoder.max_seq_length = 256
        
        # Re-ranking opcional
        self.use_reranking = settings.enable_reranking
        if self.use_reranking:
            self.rerank = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
        
        self.k_dense = k_dense
        self.k_lex = k_lex
        
        logger.info(f"✅ HybridRetriever initialized in {time.time() - start_time:.2f}s")
        logger.info(f"   Dense: {k_dense}, Lexical: {k_lex}, Reranking: {self.use_reranking}")

    @lru_cache(maxsize=100 if settings.enable_query_caching else 0)
    def _encode_question(self, question: str):
        """Cache de embeddings para consultas repetidas"""
        return self.encoder.encode(question)

    def query(self, question: str, top_n: int = 10) -> List[Dict[str, Any]]:
        """Búsqueda híbrida optimizada"""
        start_time = time.time()
        
        # 1) Búsqueda densa
        dense_start = time.time()
        query_vector = self._encode_question(question)
        
        dense_hits = self.qdrant.search(
            collection_name="fallos",
            query_vector=query_vector,
            limit=self.k_dense,
            with_payload=True,
            with_vectors=False
        )
        dense_time = time.time() - dense_start

        # 2) Búsqueda léxica BM25
        lex_start = time.time()
        question_tokens = question.lower().split()
        lex_scores = self.bm25.get_scores(question_tokens)
        lex_ids = np.argpartition(lex_scores, -self.k_lex)[-self.k_lex:]
        lex_ids = lex_ids[np.argsort(lex_scores[lex_ids])[::-1]]
        lex_time = time.time() - lex_start

        # 3) Merge de candidatos
        merge_start = time.time()
        candidates = {}
        
        # Agregar hits densos
        for h in dense_hits:
            candidates[int(h.id)] = (float(h.score), h.payload)
        
        # Agregar hits léxicos
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
        
        # Combinar scores
        for idx in lex_ids:
            py_idx = int(idx)
            if py_idx in candidates:
                old_score, payload = candidates[py_idx]
                combined_score = old_score + (float(lex_scores[idx]) * 0.5)
                candidates[py_idx] = (combined_score, payload)
        
        merge_time = time.time() - merge_start

        # 4) Re-ranking opcional
        if self.use_reranking and len(candidates) > 0:
            rerank_start = time.time()
            texts = [c[1]["text"][:500] for c in candidates.values()]
            pairs = [(question, t) for t in texts]
            scores = self.rerank.predict(pairs)
            scored = [(float(s), p) for s, (_, p) in zip(scores, candidates.values())]
            rerank_time = time.time() - rerank_start
        else:
            scored = [(score, payload) for score, payload in candidates.values()]
            rerank_time = 0
        
        # 5) Selección final
        top = heapq.nlargest(top_n, scored, key=lambda x: x[0])
        
        total_time = time.time() - start_time
        
        # Logging optimizado
        logger.info(f"🔍 HybridRetriever query in {total_time:.3f}s:")
        logger.info(f"   Dense: {dense_time:.3f}s, Lexical: {lex_time:.3f}s")
        logger.info(f"   Merge: {merge_time:.3f}s, Rerank: {rerank_time:.3f}s")
        logger.info(f"   Candidates: {len(candidates)}, Final: {len(top)}")

        return [
            {
                "score": s,
                "expte": p["expediente"],
                "section": p["section"],
                "paragraph": p["text"],
                "path": p["path"],
                "search_type": "hybrid"
            }
            for s, p in top
        ]

    def get_stats(self) -> Dict[str, Any]:
        """Estadísticas del retriever híbrido"""
        return {
            "retriever_type": "hybrid",
            "dense_limit": self.k_dense,
            "lexical_limit": self.k_lex,
            "reranking_enabled": self.use_reranking,
            "caching_enabled": settings.enable_query_caching,
            "corpus_size": len(self.corpus) if hasattr(self, 'corpus') else 0
        }
    
    def supports_reranking(self) -> bool:
        """HybridRetriever soporta re-ranking"""
        return True
    
    def __del__(self):
        """Cleanup de recursos"""
        if hasattr(self, 'qdrant'):
            try:
                self.qdrant.close()
            except:
                pass