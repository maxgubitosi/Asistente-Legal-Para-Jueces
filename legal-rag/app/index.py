from pathlib import Path
import os, pickle, numpy as np, gc, psutil
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient, models as qmodels
from rank_bm25 import BM25Okapi
from tqdm import tqdm

from .ingest import iter_paragraphs

EMB_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
BM25_PATH        = os.getenv("BM25_PATH", "/app/bm25.pkl")
BM25_CORPUS_PATH = os.getenv("BM25_CORPUS_PATH", "/app/bm25_corpus.npy")

# Configuración para escalabilidad
BATCH_SIZE = int(os.getenv("EMBEDDING_BATCH_SIZE", "32"))  # Reducido para usar menos memoria
UPLOAD_BATCH_SIZE = int(os.getenv("UPLOAD_BATCH_SIZE", "1000"))  # Para subir a Qdrant en lotes

def build_indexes(json_dir: Path, qdrant_url: str = "http://localhost:6333"):
    """
    Versión optimizada para manejar grandes volúmenes de documentos:
    • Procesamiento en lotes para optimizar memoria
    • Monitoreo de uso de memoria
    • Carga incremental a Qdrant
    • Manejo de errores y recuperación
    """
    print(f"🚀 Iniciando construcción de índices desde: {json_dir}")
    
    # Verificar memoria disponible
    memory_gb = psutil.virtual_memory().total / (1024**3)
    print(f"💾 Memoria total disponible: {memory_gb:.1f} GB")
    
    # 1) Contar documentos primero para mostrar progreso
    print("📊 Contando documentos...")
    paras = list(iter_paragraphs(Path(json_dir)))
    total_docs = len(paras)
    print(f"📄 Total de párrafos a procesar: {total_docs:,}")
    
    if total_docs > 100000:
        print("⚠️  Gran volumen de documentos detectado. Usando procesamiento optimizado...")
    
    texts = [p.text for p in paras]
    
    # 2) Embeddings densos con procesamiento en lotes optimizado
    print("🧠 Generando embeddings densos...")
    encoder = SentenceTransformer(EMB_MODEL)
    
    # Ajustar batch_size según memoria disponible
    dynamic_batch_size = min(BATCH_SIZE, max(8, int(memory_gb * 8)))
    print(f"🔧 Usando batch_size: {dynamic_batch_size}")
    
    vectors = encoder.encode(
        texts, 
        batch_size=dynamic_batch_size, 
        show_progress_bar=True,
        convert_to_numpy=True
    )
    
    # Liberar memoria del encoder si no se va a usar más
    del encoder
    gc.collect()
    
    # 3) Vector DB (Qdrant) con carga en lotes
    print("🗄️  Configurando Qdrant...")
    client = QdrantClient(url=qdrant_url)
    
    # Verificar si la colección ya existe
    try:
        collections = client.get_collections().collections
        if any(c.name == "fallos" for c in collections):
            print("🔄 Recreando colección existente...")
            client.delete_collection("fallos")
    except Exception as e:
        print(f"ℹ️  Colección no existía previamente: {e}")
    
    client.create_collection(
        collection_name="fallos",
        vectors_config=qmodels.VectorParams(
            size=vectors.shape[1], 
            distance="Cosine"
        ),
        # Optimizaciones para grandes volúmenes
        optimizers_config=qmodels.OptimizersConfig(
            default_segment_number=2,
            max_segment_size=20000
        )
    )
    
    # Subir en lotes para evitar timeouts
    print("📤 Subiendo vectores a Qdrant...")
    payloads = [p.model_dump() for p in paras]
    
    for i in tqdm(range(0, len(vectors), UPLOAD_BATCH_SIZE), desc="Subiendo lotes"):
        end_idx = min(i + UPLOAD_BATCH_SIZE, len(vectors))
        batch_vectors = vectors[i:end_idx]
        batch_payloads = payloads[i:end_idx]
        batch_ids = list(range(i, end_idx))
        
        try:
            client.upload_collection(
                collection_name="fallos",
                vectors=batch_vectors,
                payload=batch_payloads,
                ids=batch_ids,
                batch_size=min(100, len(batch_vectors))  # Lotes más pequeños para la API
            )
        except Exception as e:
            print(f"❌ Error subiendo lote {i//UPLOAD_BATCH_SIZE + 1}: {e}")
            raise
    
    # Liberar memoria de vectores
    del vectors, payloads
    gc.collect()    # 4) BM25 (lexical) - Optimizado para grandes volúmenes
    print("📝 Construyendo índice BM25...")
    
    # Para volúmenes muy grandes, considera usar términos más selectivos
    if total_docs > 50000:
        print("⚡ Optimizando tokenización para gran volumen...")
        # Tokenización más eficiente para grandes corpus
        tokenized_texts = []
        for text in tqdm(texts, desc="Tokenizando"):
            # Filtrar palabras muy cortas y muy comunes
            tokens = [
                token.lower() for token in text.split() 
                if len(token) > 2 and len(token) < 20
            ]
            tokenized_texts.append(tokens)
    else:
        tokenized_texts = [text.split() for text in texts]
    
    bm25 = BM25Okapi(tokenized_texts)
    
    # Liberar memoria de textos tokenizados
    del tokenized_texts
    gc.collect()
    
    # Asegurar que los directorios existen
    os.makedirs(os.path.dirname(BM25_CORPUS_PATH), exist_ok=True)
    os.makedirs(os.path.dirname(BM25_PATH), exist_ok=True)
    
    # Guardar archivos
    print("💾 Guardando índices...")
    np.save(BM25_CORPUS_PATH, texts, allow_pickle=True)
    
    with open(BM25_PATH, "wb") as f:
        pickle.dump(bm25, f, protocol=pickle.HIGHEST_PROTOCOL)
    
    # Verificar tamaños de archivo
    bm25_size_mb = os.path.getsize(BM25_PATH) / (1024**2)
    corpus_size_mb = os.path.getsize(BM25_CORPUS_PATH) / (1024**2)
    
    print(f"✅ Indexación completada:")
    print(f"   📄 Párrafos procesados: {total_docs:,}")
    print(f"   🧠 Vectores en Qdrant: {total_docs:,}")
    print(f"   📝 BM25 index: {bm25_size_mb:.1f} MB")
    print(f"   📚 Corpus file: {corpus_size_mb:.1f} MB")
    print(f"   💾 Memoria final: {psutil.virtual_memory().percent:.1f}% usada")

def update_indexes_incremental(json_dir: Path, qdrant_url: str = "http://localhost:6333"):
    """
    Actualización incremental de índices para nuevos documentos.
    Útil cuando se agregan documentos sin necesidad de reconstruir todo.
    """
    print("🔄 Actualizando índices de forma incremental...")
    
    client = QdrantClient(url=qdrant_url)
    
    # Obtener el último ID usado en Qdrant
    try:
        info = client.get_collection("fallos")
        last_id = info.points_count - 1
        print(f"📊 Último ID en colección: {last_id}")
    except Exception:
        print("❌ Colección no existe. Use build_indexes() primero.")
        return
    
    # Procesar solo documentos nuevos (esto requeriría lógica adicional
    # para identificar qué documentos son nuevos)
    print("ℹ️  Función incremental en desarrollo...")
    print("💡 Para volúmenes grandes, considere implementar:")
    print("   - Tracking de documentos procesados")
    print("   - Checksums o timestamps")
    print("   - Base de datos de metadatos")


def get_index_stats():
    """Obtiene estadísticas de los índices actuales"""
    stats = {}
    
    # Stats de archivos BM25
    if os.path.exists(BM25_PATH):
        stats['bm25_size_mb'] = os.path.getsize(BM25_PATH) / (1024**2)
    if os.path.exists(BM25_CORPUS_PATH):
        stats['corpus_size_mb'] = os.path.getsize(BM25_CORPUS_PATH) / (1024**2)
        corpus = np.load(BM25_CORPUS_PATH, allow_pickle=True)
        stats['total_documents'] = len(corpus)
        stats['avg_doc_length'] = np.mean([len(doc.split()) for doc in corpus[:1000]])  # Muestra
    
    # Stats de sistema
    stats['system_memory_gb'] = psutil.virtual_memory().total / (1024**3)
    stats['memory_usage_percent'] = psutil.virtual_memory().percent
    
    return stats
