#!/usr/bin/env python3
"""
Script de monitoreo para el sistema Legal RAG.
Verifica el estado de los índices y el uso de recursos.
"""

import os, sys
sys.path.append('/app')

from app.index import get_index_stats
from qdrant_client import QdrantClient
import psutil

def main():
    print("📊 LEGAL RAG - Monitor de Sistema\n")
    
    # Stats generales del sistema
    print("🖥️  SISTEMA:")
    memory = psutil.virtual_memory()
    print(f"   Memoria total: {memory.total / (1024**3):.1f} GB")
    print(f"   Memoria usada: {memory.percent:.1f}%")
    print(f"   Memoria libre: {memory.available / (1024**3):.1f} GB")
    
    disk = psutil.disk_usage('/indexes')
    print(f"   Disco (/indexes): {disk.free / (1024**3):.1f} GB libres")
    
    # Stats de índices
    print("\n📚 ÍNDICES:")
    try:
        stats = get_index_stats()
        if 'total_documents' in stats:
            print(f"   Documentos indexados: {stats['total_documents']:,}")
            print(f"   Promedio palabras/doc: {stats.get('avg_doc_length', 0):.1f}")
        
        if 'bm25_size_mb' in stats:
            print(f"   BM25 index: {stats['bm25_size_mb']:.1f} MB")
        
        if 'corpus_size_mb' in stats:
            print(f"   Corpus file: {stats['corpus_size_mb']:.1f} MB")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Stats de Qdrant
    print("\n🗄️  QDRANT:")
    try:
        qdrant_url = os.getenv("QDRANT_URL", "http://qdrant:6333")
        client = QdrantClient(url=qdrant_url)
        
        collections = client.get_collections().collections
        if any(c.name == "fallos" for c in collections):
            info = client.get_collection("fallos")
            print(f"   Colección 'fallos': {info.points_count:,} vectores")
            print(f"   Estado: {info.status}")
        else:
            print("   ❌ Colección 'fallos' no encontrada")
            
    except Exception as e:
        print(f"   ❌ Error conectando a Qdrant: {e}")
    
    # Recomendaciones
    print("\n💡 RECOMENDACIONES:")
    
    if memory.percent > 80:
        print("   ⚠️  Memoria alta. Considere reducir EMBEDDING_BATCH_SIZE")
    
    if 'total_documents' in stats and stats['total_documents'] > 100000:
        print("   📈 Gran volumen detectado. Active optimizaciones avanzadas")
    
    if disk.free / (1024**3) < 2:
        print("   💾 Poco espacio en disco. Limpie archivos temporales")
    
    print("\n✅ Monitoreo completado")

if __name__ == "__main__":
    main()
