# app/api.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.rag import answer
import os, time

app = FastAPI()

class QueryIn(BaseModel):
    question: str
    top_n: int = 8

class Hit(BaseModel):
    expte: str
    section: str
    paragraph: str  # Cambiar extracto por paragraph para coincidir con los datos
    path: str
    score: float

class QueryOut(BaseModel):
    markdown: str
    results: list[Hit]

@app.post("/query", response_model=QueryOut)
def query(q: QueryIn):
    try:
        md, hits = answer(q.question, q.top_n)
        # Los datos ya vienen con 'paragraph', así que los devolvemos directamente
        return {"markdown": md, "results": hits}
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=503, 
            detail=f"Service temporarily unavailable: {str(e)}"
        )

@app.get("/health")
def health_check():
    """Check if the service is ready with all required indexes"""
    bm25_path = os.getenv("BM25_PATH", "/app/bm25.pkl")
    bm25_corpus_path = os.getenv("BM25_CORPUS_PATH", "/app/bm25_corpus.npy")
    
    missing_files = []
    if not os.path.exists(bm25_path):
        missing_files.append(bm25_path)
    if not os.path.exists(bm25_corpus_path):
        missing_files.append(bm25_corpus_path)
    
    if missing_files:
        return {
            "status": "unhealthy", 
            "message": f"Missing index files: {missing_files}",
            "suggestion": "Please build indexes first using: python scripts/build_index.py /datasets/fallos_json"
        }
    
    return {"status": "healthy", "message": "All indexes are available"}

@app.get("/performance")
def performance_stats():
    """Obtiene estadísticas de rendimiento del sistema"""
    try:
        from app.rag import get_retriever
        retriever = get_retriever()
        stats = retriever.get_stats()
        
        # Agregar info del sistema
        import psutil
        stats.update({
            "memory_usage_percent": psutil.virtual_memory().percent,
            "cpu_usage_percent": psutil.cpu_percent(),
            "disk_usage_percent": psutil.disk_usage('/').percent
        })
        
        return {"status": "success", "stats": stats}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/query-debug", response_model=QueryOut)
def query_debug(q: QueryIn):
    """Versión de query con información de debugging detallada"""
    import time
    start_time = time.time()
    
    try:
        md, hits = answer(q.question, q.top_n)
        total_time = time.time() - start_time
        
        # Agregar metadata de rendimiento
        performance_info = {
            "total_time_seconds": round(total_time, 3),
            "results_count": len(hits),
            "query_length": len(q.question),
            "timestamp": time.time()
        }
        
        return {
            "markdown": md, 
            "results": hits,
            "performance": performance_info
        }
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=503, 
            detail=f"Service temporarily unavailable: {str(e)}"
        )

@app.post("/rebuild-indexes")
def rebuild_indexes():
    """Endpoint para forzar la reconstrucción de índices"""
    try:
        import subprocess
        import os
        
        # Verificar cambios primero
        result = subprocess.run([
            "python", "/app/scripts/check_dataset_changes.py"
        ], capture_output=True, text=True)
        
        needs_update = result.returncode == 1
        
        if needs_update or os.getenv("FORCE_REBUILD", "false").lower() == "true":
            # Eliminar índices existentes
            bm25_path = os.getenv("BM25_PATH", "/indexes/bm25.pkl")
            corpus_path = os.getenv("BM25_CORPUS_PATH", "/indexes/bm25_corpus.npy")
            
            for path in [bm25_path, corpus_path]:
                if os.path.exists(path):
                    os.remove(path)
              # Reconstruir índices
            rebuild_result = subprocess.run([
                "python", "-m", "scripts.build_index", 
                "/datasets/fallos_json", 
                "--qdrant-url", os.getenv("QDRANT_URL", "http://qdrant:6333")
            ], capture_output=True, text=True, cwd="/app")
            
            if rebuild_result.returncode == 0:
                # Reinicializar el retriever global
                import app.rag
                app.rag._retriever_instance = None
                
                return {
                    "status": "success",
                    "message": "Índices reconstruidos exitosamente",
                    "needs_restart": "Considere reiniciar el servicio para liberar memoria"
                }
            else:
                return {
                    "status": "error", 
                    "message": f"Error reconstruyendo índices: {rebuild_result.stderr}"
                }
        else:
            return {
                "status": "no_changes",
                "message": "No se detectaron cambios en el dataset"
            }
            
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/dataset-status")
def dataset_status():
    """Verifica el estado del dataset y si necesita actualización"""
    try:
        import subprocess
        
        result = subprocess.run([
            "python", "/app/scripts/check_dataset_changes.py"
        ], capture_output=True, text=True)
        
        return {
            "needs_update": result.returncode == 1,
            "message": result.stdout.strip(),
            "last_check": time.time()
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
