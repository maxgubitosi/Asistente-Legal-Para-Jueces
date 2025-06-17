import os, heapq, pickle, numpy as np, time
from sentence_transformers import SentenceTransformer, CrossEncoder
from qdrant_client import QdrantClient
from rank_bm25 import BM25Okapi
from functools import lru_cache
import logging

# Configuración de logging para debug de rendimiento
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

EMB_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
BM25_PATH        = os.getenv("BM25_PATH", "/app/bm25.pkl")
BM25_CORPUS_PATH = os.getenv("BM25_CORPUS_PATH", "/app/bm25_corpus.npy")
QDRANT_URL       = os.getenv("QDRANT_URL", "http://qdrant:6333")

# Configuración de rendimiento
ENABLE_CACHING = os.getenv("ENABLE_QUERY_CACHING", "true").lower() == "true"
RERANK_BATCH_SIZE = int(os.getenv("RERANK_BATCH_SIZE", "32"))
DENSE_SEARCH_LIMIT = int(os.getenv("DENSE_SEARCH_LIMIT", "30"))  # Reducido de 50
LEXICAL_SEARCH_LIMIT = int(os.getenv("LEXICAL_SEARCH_LIMIT", "30"))  # Reducido de 50

class OptimizedHybridRetriever:
    def __init__(self, k_dense: int = DENSE_SEARCH_LIMIT, k_lex: int = LEXICAL_SEARCH_LIMIT):
        """Versión optimizada del retriever híbrido"""
        start_time = time.time()
        
        # Configuración más agresiva para Qdrant
        self.qdrant = QdrantClient(
            url=QDRANT_URL, 
            prefer_grpc=False,
            timeout=10.0  # Timeout más corto
        )
        
        # Cargar BM25 con manejo de errores
        try:
            with open(BM25_PATH, "rb") as f:
                self.bm25 = pickle.load(f)
            self.corpus = np.load(BM25_CORPUS_PATH, allow_pickle=True)
        except FileNotFoundError as e:
            raise FileNotFoundError(
                f"BM25 index files not found. Please build the indexes first.\n"
                f"Missing file: {e.filename}"
            ) from e
        
        # Modelos pre-cargados con configuración optimizada
        self.encoder = SentenceTransformer(EMB_MODEL, device='cpu')
        self.encoder.max_seq_length = 256  # Limitar longitud de secuencia
        
        # Cross-encoder más ligero o deshabilitado para mayor velocidad
        self.use_reranking = os.getenv("ENABLE_RERANKING", "true").lower() == "true"
        if self.use_reranking:
            self.rerank = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
        
        self.k_dense = k_dense
        self.k_lex = k_lex
        
        logger.info(f"✅ Retriever inicializado en {time.time() - start_time:.2f}s")
        logger.info(f"   Dense limit: {k_dense}, Lexical limit: {k_lex}")
        logger.info(f"   Reranking: {'Enabled' if self.use_reranking else 'Disabled'}")

    @lru_cache(maxsize=100 if ENABLE_CACHING else 0)
    def _encode_question(self, question: str):
        """Cache de embeddings para consultas repetidas"""
        return self.encoder.encode(question)

    def query(self, question: str, top_n: int = 10):
        """Versión optimizada de búsqueda híbrida"""
        start_time = time.time()
        
        # 1) Búsqueda densa - con embedding cacheado
        dense_start = time.time()
        query_vector = self._encode_question(question)
        
        dense_hits = self.qdrant.search(
            collection_name="fallos",
            query_vector=query_vector,
            limit=self.k_dense,
            with_payload=True,
            with_vectors=False  # No necesitamos los vectores de vuelta
        )
        dense_time = time.time() - dense_start

        # 2) Búsqueda léxica BM25 - optimizada
        lex_start = time.time()
        question_tokens = question.lower().split()  # Pre-procesar una vez
        lex_scores = self.bm25.get_scores(question_tokens)
        lex_ids = np.argpartition(lex_scores, -self.k_lex)[-self.k_lex:]  # Más rápido que argsort
        lex_ids = lex_ids[np.argsort(lex_scores[lex_ids])[::-1]]  # Ordenar solo los top-k
        lex_time = time.time() - lex_start

        # 3) Merge de candidatos - optimizado
        merge_start = time.time()
        candidates = {}
        
        # Agregar hits densos
        for h in dense_hits:
            candidates[int(h.id)] = (float(h.score), h.payload)
        
        # Agregar hits léxicos - batch retrieval para eficiencia
        missing_ids = [int(idx) for idx in lex_ids if int(idx) not in candidates]
        if missing_ids:
            # Recuperar múltiples puntos de una vez
            missing_points = self.qdrant.retrieve(
                collection_name="fallos",
                ids=missing_ids,
                with_payload=True,
                with_vectors=False
            )
            for point, idx in zip(missing_points, missing_ids):
                candidates[idx] = (float(lex_scores[idx]), point.payload)
        
        # Combinar scores para documentos que aparecen en ambas búsquedas
        for idx in lex_ids:
            py_idx = int(idx)
            if py_idx in candidates:
                old_score, payload = candidates[py_idx]
                # Combinar scores con pesos optimizados
                combined_score = old_score + (float(lex_scores[idx]) * 0.5)
                candidates[py_idx] = (combined_score, payload)
        
        merge_time = time.time() - merge_start

        # 4) Re-ranking (opcional para mayor velocidad)
        if self.use_reranking and len(candidates) > 0:
            rerank_start = time.time()
            texts = [c[1]["text"] for c in candidates.values()]
            
            # Limitar longitud de texto para re-ranking más rápido
            texts = [t[:500] for t in texts]  # Truncar a 500 caracteres
            
            # Re-ranking en lotes para eficiencia
            pairs = [(question, t) for t in texts]
            scores = self.rerank.predict(pairs)
            
            scored = [(float(s), p) for s, (_, p) in zip(scores, candidates.values())]
            rerank_time = time.time() - rerank_start
        else:
            # Sin re-ranking, usar scores combinados
            scored = [(score, payload) for score, payload in candidates.values()]
            rerank_time = 0
        
        # 5) Selección final
        top = heapq.nlargest(top_n, scored, key=lambda x: x[0])
        
        total_time = time.time() - start_time
        
        # Logging de rendimiento
        logger.info(f"🔍 Query processed in {total_time:.3f}s:")
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
            }
            for s, p in top
        ]

    def get_stats(self):
        """Estadísticas del retriever para debugging"""
        return {
            "dense_limit": self.k_dense,
            "lexical_limit": self.k_lex,            "reranking_enabled": self.use_reranking,
            "caching_enabled": ENABLE_CACHING,
            "corpus_size": len(self.corpus) if hasattr(self, 'corpus') else 0
        }
