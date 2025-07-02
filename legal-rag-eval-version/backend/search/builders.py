import pickle
import numpy as np
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient, models as qmodels
from rank_bm25 import BM25Okapi
from tqdm import tqdm
from backend.config import get_settings
import os

settings = get_settings()


EMB_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

class BM25Builder:
    """Construye y guarda índices BM25"""
    
    def __init__(self, bm25_path: str, corpus_path: str):
        self.bm25_path = bm25_path
        self.corpus_path = corpus_path
    
    def build(self, texts: list[str]) -> BM25Okapi:
        """Construye el índice BM25"""
        if not texts:
            raise ValueError("Lista de textos no puede estar vacía")
            
        print("📝 Construyendo índice BM25...")
        
        # Tu lógica de tokenización optimizada
        if len(texts) > 50000:
            print("⚡ Optimizando tokenización para gran volumen...")
            tokenized_texts = []
            for text in tqdm(texts, desc="Tokenizando"):
                tokens = [
                    token.lower() for token in text.split() 
                    if len(token) > 2 and len(token) < 20
                ]
                tokenized_texts.append(tokens)
        else:
            tokenized_texts = [text.split() for text in texts]
        
        bm25 = BM25Okapi(tokenized_texts)
        
        # Guardar
        os.makedirs(os.path.dirname(self.bm25_path), exist_ok=True)
        os.makedirs(os.path.dirname(self.corpus_path), exist_ok=True)
        
        np.save(self.corpus_path, texts, allow_pickle=True)
        with open(self.bm25_path, "wb") as f:
            pickle.dump(bm25, f, protocol=pickle.HIGHEST_PROTOCOL)
        
        return bm25

class QdrantBuilder:
    """Construye colección Qdrant"""
    
    def __init__(self, qdrant_url: str):
        self.client = QdrantClient(url=qdrant_url)
    
    def build(self, vectors: np.ndarray, payloads: list, batch_size: int = 1000):
        """Construye la colección Qdrant"""
        print("🗄️  Configurando Qdrant...")
        
        # Recrear colección
        try:
            collections = self.client.get_collections().collections
            if any(c.name == "fallos" for c in collections):
                print("🔄 Recreando colección existente...")
                self.client.delete_collection("fallos")
        except Exception as e:
            print(f"ℹ️  Colección no existía previamente: {e}")
        
        self.client.create_collection(
            collection_name="fallos",
            vectors_config=qmodels.VectorParams(
                size=vectors.shape[1], 
                distance="Cosine"
            ),
            optimizers_config=qmodels.OptimizersConfigDiff(
                deleted_threshold=0.2,
                vacuum_min_vector_number=1000,
                default_segment_number=2,
                max_segment_size=20000,
                flush_interval_sec=5
            )
        )
        
        # Subir en lotes
        print("📤 Subiendo vectores a Qdrant...")
        for i in tqdm(range(0, len(vectors), batch_size), desc="Subiendo lotes"):
            end_idx = min(i + batch_size, len(vectors))
            batch_vectors = vectors[i:end_idx]
            batch_payloads = payloads[i:end_idx]
            batch_ids = list(range(i, end_idx))
            
            try:
                self.client.upload_collection(
                    collection_name="fallos",
                    vectors=batch_vectors,
                    payload=batch_payloads,
                    ids=batch_ids,
                    batch_size=min(100, len(batch_vectors))
                )
            except Exception as e:
                print(f"❌ Error subiendo lote {i//batch_size + 1}: {e}")
                raise

class EmbeddingBuilder:
    """Genera embeddings"""
    
    def __init__(self, model_name: str = EMB_MODEL):
        self.encoder = SentenceTransformer(model_name)
    
    def build(self, texts: list[str], batch_size: int = 32) -> np.ndarray:
        """Genera embeddings para los textos"""
        print("🧠 Generando embeddings densos...")
        
        vectors = self.encoder.encode(
            texts, 
            batch_size=batch_size, 
            show_progress_bar=True,
            convert_to_numpy=True
        )
        
        return vectors