import time
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
import logging
from typing import List, Dict, Any

from ..base import BaseRetriever
from backend.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

EMB_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

class DenseOnlyRetriever(BaseRetriever):
    """Retriever que solo usa búsqueda vectorial (sin BM25)"""
    
    def __init__(self, limit: int = 50):
        start_time = time.time()
        
        self.qdrant = QdrantClient(url=settings.qdrant_url, prefer_grpc=False, timeout=10.0)
        self.encoder = SentenceTransformer(EMB_MODEL, device='cpu')
        self.limit = limit
        
        logger.info(f"✅ DenseOnlyRetriever initialized in {time.time() - start_time:.2f}s")
    
    def query(self, question: str, top_n: int = 10) -> List[Dict[str, Any]]:
        """Solo búsqueda vectorial"""
        start_time = time.time()
        
        query_vector = self.encoder.encode(question)
        
        hits = self.qdrant.search(
            collection_name="fallos",
            query_vector=query_vector,
            limit=max(top_n, self.limit),
            with_payload=True,
            with_vectors=False
        )
        
        results = [
            {
                "score": float(h.score),
                "expte": h.payload["expediente"],
                "section": h.payload["section"],
                "paragraph": h.payload["text"],
                "path": h.payload["path"],
                "search_type": "dense_only"
            }
            for h in hits[:top_n]
        ]
        
        logger.info(f"🔍 DenseOnly query in {time.time() - start_time:.3f}s: {len(results)} results")
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """Estadísticas del retriever dense-only"""
        return {
            "retriever_type": "dense_only",
            "limit": self.limit,
            "reranking_enabled": False
        }
    
    def supports_reranking(self) -> bool:
        return False