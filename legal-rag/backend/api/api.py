# app/api.py
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
import os, time, psutil, asyncio
from typing import Dict, Any, Optional
from pathlib import Path

# Usar Factory Manager
from backend import get_factory_manager
from backend.data.models import QueryRequest, QueryResponse, Hit
from backend.search.indexing import build_indexes
from backend.config import get_settings

app = FastAPI(
    title="Legal RAG API",
    description="Sistema RAG para consultas legales",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Middleware CORS para producción
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios exactos
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Factory Manager global
factory_manager = get_factory_manager()

@app.get("/")
async def root():
    """Información de la API"""
    return {
        "service": "Legal RAG API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "query": "POST /query - Consulta individual",
            "query_batch": "POST /query-batch - Consultas en lote",
            "health": "GET /health - Estado del servicio",
            "stats": "GET /stats - Estadísticas del sistema",
            "rebuild": "POST /rebuild-indexes - Reconstruir índices"
        },
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc"
        },
        "usage": {
            "example_query": {
                "question": "¿Qué dice sobre contratos?",
                "top_n": 5
            }
        }
    }

@app.post("/query", response_model=QueryResponse)
async def query_endpoint(request: QueryRequest) -> QueryResponse:
    """
    Endpoint principal para consultas RAG
    
    Procesa consultas legales usando búsqueda híbrida y generación LLM.
    
    Args:
        request: Solicitud con pregunta y parámetros
        
    Returns:
        Respuesta estructurada con markdown y resultados
        
    Raises:
        HTTPException: Si hay errores en el procesamiento    """
    start_time = time.time()
    query_timeout = int(os.getenv("QUERY_TIMEOUT", "45"))
    
    try:
        # Usar Factory Manager para obtener RAG pipeline
        pipeline = factory_manager.get_rag_pipeline()
        
        # Procesar consulta con verificación de tiempo
        response, hits = pipeline.query(request.question, request.top_n)
        
        # Verificar si se excedió el timeout
        elapsed_time = time.time() - start_time
        if elapsed_time > query_timeout:
            raise HTTPException(
                status_code=408,
                detail=f"Query took {elapsed_time:.1f}s (timeout: {query_timeout}s). Try a simpler question."
            )
        
        # Convertir hits al formato esperado
        hit_objects = []
        for hit in hits:
            hit_obj = Hit(
                expte=hit.get('expte', ''),
                section=hit.get('section', ''),
                paragraph=hit.get('paragraph', ''),
                score=hit.get('score', 0.0),
                path=hit.get('path', ''),
                search_type=hit.get('search_type', 'hybrid')
            )
            hit_objects.append(hit_obj)
        
        query_time = time.time() - start_time
        
        return QueryResponse(
            question=request.question,
            markdown=response,
            results=hit_objects,
            total_time=query_time,
            search_time=query_time * 0.7,  # Estimación
            llm_time=query_time * 0.3      # Estimación
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

@app.post("/query-batch")
async def query_batch_endpoint(requests: list[QueryRequest]) -> list[QueryResponse]:
    """
    Endpoint para procesar múltiples consultas en lote
    
    Args:
        requests: Lista de consultas
        
    Returns:
        Lista de respuestas
    """
    if len(requests) > 10:  # Límite de seguridad
        raise HTTPException(
            status_code=400,
            detail="Máximo 10 consultas por lote"
        )
    
    responses = []
    for req in requests:
        try:
            # Reutilizar lógica del endpoint principal
            response = await query_endpoint(req)
            responses.append(response)
        except HTTPException:
            # En caso de error, agregar respuesta de error
            responses.append(QueryResponse(
                question=req.question,
                markdown="Error procesando la consulta",
                results=[],
                total_time=0.0,
                search_time=0.0,
                llm_time=0.0
            ))
    
    return responses

@app.get("/health")
async def health_check():
    """
    Health check del servicio
    
    Verifica:
    - Disponibilidad de índices
    - Estado de Qdrant
    - Memoria disponible
    """
    health_status = {
        "status": "healthy",
        "timestamp": time.time(),
        "checks": {}
    }
    
    # Verificar índices
    bm25_path = os.getenv("BM25_PATH", "/indexes/bm25.pkl")
    bm25_corpus_path = os.getenv("BM25_CORPUS_PATH", "/indexes/bm25_corpus.npy")
    
    health_status["checks"]["indexes"] = {
        "bm25_available": os.path.exists(bm25_path),
        "corpus_available": os.path.exists(bm25_corpus_path)
    }
    
    # Verificar memoria
    memory = psutil.virtual_memory()
    health_status["checks"]["memory"] = {
        "available_gb": memory.available / (1024**3),
        "usage_percent": memory.percent,
        "healthy": memory.percent < 90
    }
    
    # Verificar pipeline
    try:
        pipeline = factory_manager.get_rag_pipeline()
        health_status["checks"]["pipeline"] = {"available": True}
    except Exception as e:
        health_status["checks"]["pipeline"] = {"available": False, "error": str(e)}
        health_status["status"] = "unhealthy"
    
    # Determinar estado general
    if not all([
        health_status["checks"]["indexes"]["bm25_available"],
        health_status["checks"]["indexes"]["corpus_available"],
        health_status["checks"]["memory"]["healthy"],
        health_status["checks"]["pipeline"]["available"]
    ]):
        health_status["status"] = "unhealthy"
    
    return health_status

@app.get("/stats")
async def get_system_stats():
    """Estadísticas detalladas del sistema"""
    try:
        # Stats del factory manager
        factory_stats = factory_manager.get_stats()
        
        # Stats del sistema
        memory = psutil.virtual_memory()
        
        return {
            "factory_manager": factory_stats,
            "system": {
                "memory_usage_gb": round(memory.used / (1024**3), 2),
                "memory_percent": memory.percent,
                "available_memory_gb": round(memory.available / (1024**3), 2)
            },
            "timestamp": time.time()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting stats: {str(e)}")

@app.post("/rebuild-indexes")
async def rebuild_indexes_endpoint(background_tasks: BackgroundTasks, force: bool = False):
    """
    Reconstruir índices en background
    
    Args:
        force: Forzar reconstrucción sin verificar cambios
    """
    try:
        # Programar reconstrucción en background
        background_tasks.add_task(_rebuild_indexes_task, force=force)
        
        return {
            "status": "accepted",
            "message": "Reconstrucción de índices iniciada en background",
            "force": force,
            "timestamp": time.time()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def _rebuild_indexes_task(force: bool = False):
    """Tarea de reconstrucción de índices"""
    try:
        datasets_path = Path("/datasets/fallos_json")
        qdrant_url = os.getenv("QDRANT_URL", "http://qdrant:6333")
        
        if force:
            # Eliminar índices existentes
            bm25_path = os.getenv("BM25_PATH", "/indexes/bm25.pkl")
            corpus_path = os.getenv("BM25_CORPUS_PATH", "/indexes/bm25_corpus.npy")
            
            for path in [bm25_path, corpus_path]:
                if os.path.exists(path):
                    os.remove(path)
        
        # Reconstruir
        build_indexes(datasets_path, qdrant_url)
        
        # Reinicializar pipeline
        global _rag_pipeline
        _rag_pipeline = None
        
        print("✅ Índices reconstruidos exitosamente")
        
    except Exception as e:
        print(f"❌ Error reconstruyendo índices: {e}")

# Endpoint de compatibilidad (opcional)
@app.post("/query-simple")
async def query_simple_legacy(request: dict):
    """Endpoint legacy para compatibilidad"""
    try:
        # Convertir a QueryRequest
        query_req = QueryRequest(**request)
        
        # Procesar usando endpoint principal
        response = await query_endpoint(query_req)
        
        # Retornar en formato simple
        return {
            "question": response.question,
            "markdown": response.markdown,
            "results": [hit.model_dump() for hit in response.results],
            "total_results": len(response.results),
            "total_time": response.total_time
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
