from pathlib import Path
import os, gc, psutil
import pickle
import numpy as np

from backend.data import iter_paragraphs  # ← Usar factory directamente
from .builders import BM25Builder, QdrantBuilder, EmbeddingBuilder
from backend.config import get_settings

# Configuración de rutas y parámetros
settings = get_settings()


def build_indexes(json_dir: Path, qdrant_url: str = "http://qdrant:6333"):
    """Función principal de construcción de índices"""
    print(f"🚀 Iniciando construcción de índices desde: {json_dir}")
    
    # Verificar memoria disponible
    memory_gb = psutil.virtual_memory().total / (1024**3)
    print(f"💾 Memoria total disponible: {memory_gb:.1f} GB")
    
    # 1) Cargar documentos
    print("📊 Contando documentos...")
    paras = list(iter_paragraphs(Path(json_dir), settings.processing_mode))
    total_docs = len(paras)
    print(f"📄 Total de párrafos a procesar: {total_docs:,}")
    
    texts = [p.text for p in paras]
    
    # 2) Crear builders
    embedding_builder = EmbeddingBuilder()
    qdrant_builder = QdrantBuilder(qdrant_url)
    bm25_builder = BM25Builder(settings.bm25_path, settings.bm25_corpus_path)
    
    # 3) Generar embeddings
    dynamic_batch_size = min(settings.embedding_batch_size, max(8, int(memory_gb * 8)))
    vectors = embedding_builder.build(texts, batch_size=dynamic_batch_size)
    
    # 4) Construir Qdrant
    payloads = [p.model_dump() for p in paras]
    qdrant_builder.build(vectors, payloads, batch_size=settings.upload_batch_size)
    
    # 5) Construir BM25
    bm25_builder.build(texts)
    
    # Cleanup
    del vectors, payloads, embedding_builder
    gc.collect()
    
    # Verificar tamaños de archivo
    bm25_size_mb = os.path.getsize(settings.bm25_path) / (1024**2)
    corpus_size_mb = os.path.getsize(settings.bm25_corpus_path) / (1024**2)

    print(f"✅ Indexación completada:")
    print(f"   📄 Párrafos procesados: {total_docs:,}")
    print(f"   🧠 Vectores en Qdrant: {total_docs:,}")
    print(f"   📝 BM25 index: {bm25_size_mb:.1f} MB")
    print(f"   📚 Corpus file: {corpus_size_mb:.1f} MB")
    print(f"   💾 Memoria final: {psutil.virtual_memory().percent:.1f}% usada")