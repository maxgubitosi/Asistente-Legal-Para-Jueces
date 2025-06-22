# 🔍 Módulo Search

Módulo encargado del **retrieval de información legal**. Proporciona búsqueda híbrida (vectorial + léxica) y otras estrategias para encontrar párrafos relevantes en documentos legales.

## 🏗️ Arquitectura

```
backend/search/
├── __init__.py          # Exports principales
├── base.py              # Interface base
├── factory.py           # Factory para retrievers
├── builders.py          # Constructores de índices
├── indexing.py          # Función principal de indexing
└── strategies/
    ├── __init__.py      # Exports de estrategias
    ├── hybrid.py        # Búsqueda híbrida (vectorial + BM25)
    └── dense_only.py    # Solo búsqueda vectorial
```

## 📁 Archivos

### [`base.py`](base.py)
**Interface base para todos los retrievers:**
```python
class BaseRetriever(ABC):
    @abstractmethod
    def query(self, question: str, top_n: int = 10) -> List[Dict[str, Any]]:
        pass
    
    def get_stats(self) -> Dict[str, Any]:
        return {"retriever_type": "base"}
    
    def supports_reranking(self) -> bool:
        return False
```

### [`factory.py`](factory.py)
**Factory principal para crear retrievers:**
- `get_retriever(strategy)` - Crea retriever según estrategia
- `get_available_strategies()` - Lista estrategias disponibles
- `get_default_strategy()` - Estrategia por defecto
- **Lazy imports** para mejor rendimiento

### [`builders.py`](builders.py)
**Constructores especializados para índices:**
- `BM25Builder` - Construye índices BM25 (búsqueda lexical)
- `QdrantBuilder` - Construye colección Qdrant (búsqueda vectorial)
- `EmbeddingBuilder` - Genera embeddings densos
- **Optimizaciones** para gran volumen de datos

### [`indexing.py`](indexing.py)
**Función principal de construcción de índices:**
- ✅ **Monitoreo de memoria** automático
- ✅ **Batch processing** configurable
- ✅ **Progreso detallado** con métricas
- ✅ **Cleanup automático** de memoria
- ✅ **Verificación de archivos** generados

### [`strategies/hybrid.py`](strategies/hybrid.py)
**Retriever híbrido de alta performance:**
- ✅ **Búsqueda densa** con Qdrant (embeddings)
- ✅ **Búsqueda lexical** con BM25
- ✅ **Re-ranking opcional** con CrossEncoder
- ✅ **Caching de embeddings** con LRU cache
- ✅ **Combinación de scores** optimizada
- ✅ **Métricas detalladas** de tiempo y rendimiento

### [`strategies/dense_only.py`](strategies/dense_only.py)
**Retriever solo vectorial (más simple y rápido):**
- ✅ **Solo embeddings** sin BM25
- ✅ **Menor consumo de memoria**
- ✅ **Inicialización más rápida**
- ✅ **Ideal para casos simples**

## 🚀 Uso Básico

```python
# Opción 1: Factory (recomendado)
from backend.search import get_retriever
retriever = get_retriever("hybrid")
results = retriever.query("¿Qué dice sobre contratos?", top_n=5)

# Opción 2: Estrategia específica
from backend.search import get_retriever
retriever = get_retriever("dense_only", limit=20)

# Opción 3: Acceso directo
from backend.search import HybridRetriever, DenseOnlyRetriever
retriever = HybridRetriever(k_dense=30, k_lex=30)
retriever = DenseOnlyRetriever(limit=50)

# Ver estrategias disponibles
from backend.search import get_available_strategies
print("Disponibles:", get_available_strategies())

# Construir índices (una sola vez)
from backend.search import build_indexes
build_indexes("/path/to/json", "http://qdrant:6333")
```

## ⚙️ Configuración

```bash
# Estrategia de búsqueda
export SEARCH_STRATEGY=hybrid          # hybrid | dense_only

# Configuración Qdrant
export QDRANT_URL=http://qdrant:6333   # URL del servidor Qdrant

# Configuración BM25
export BM25_PATH=/app/bm25.pkl                 # Índice BM25
export BM25_CORPUS_PATH=/app/bm25_corpus.npy   # Corpus BM25

# Configuración Hybrid
export DENSE_SEARCH_LIMIT=30           # Límite búsqueda densa
export LEXICAL_SEARCH_LIMIT=30         # Límite búsqueda lexical
export ENABLE_RERANKING=true           # Activar re-ranking
export ENABLE_QUERY_CACHING=true       # Cache de embeddings

# Configuración Indexing
export EMBEDDING_BATCH_SIZE=32         # Batch para embeddings
export UPLOAD_BATCH_SIZE=1000          # Batch para upload Qdrant
```

## 🔧 Agregar Nueva Estrategia

### 1. Crear nueva implementación:

```python
# strategies/lexical_only.py
from ..base import BaseRetriever
import pickle, numpy as np
from rank_bm25 import BM25Okapi

class LexicalOnlyRetriever(BaseRetriever):
    """Retriever que solo usa BM25 (sin vectores)"""
    
    def __init__(self, k_results: int = 50):
        self.k_results = k_results
        
        # Cargar BM25
        with open("/app/bm25.pkl", "rb") as f:
            self.bm25 = pickle.load(f)
        self.corpus = np.load("/app/bm25_corpus.npy", allow_pickle=True)
    
    def query(self, question: str, top_n: int = 10):
        question_tokens = question.lower().split()
        scores = self.bm25.get_scores(question_tokens)
        
        # Top K indices
        top_indices = np.argpartition(scores, -self.k_results)[-self.k_results:]
        top_indices = top_indices[np.argsort(scores[top_indices])[::-1]]
        
        # Construir resultados (necesitarías obtener metadata de algún lado)
        results = []
        for idx in top_indices[:top_n]:
            results.append({
                "score": float(scores[idx]),
                "paragraph": self.corpus[idx],
                "search_type": "lexical_only"
                # Agregar más campos según tu formato
            })
        
        return results
    
    def get_stats(self):
        return {
            "retriever_type": "lexical_only",
            "k_results": self.k_results,
            "corpus_size": len(self.corpus)
        }
    
    def supports_reranking(self):
        return False
```

### 2. Registrar en factory:

```python
# factory.py
def _import_lexical_only():
    from .strategies.lexical_only import LexicalOnlyRetriever
    return LexicalOnlyRetriever

def get_retriever(strategy: str = None, **kwargs):
    strategies = {
        "hybrid": lambda: _import_hybrid(),
        "dense_only": lambda: _import_dense_only(),
        "lexical_only": lambda: _import_lexical_only(),  # ← Agregar
    }
    # ... resto del código
    
def get_available_strategies():
    return ["hybrid", "dense_only", "lexical_only"]  # ← Agregar
```

### 3. Exportar en strategies/__init__.py:

```python
# strategies/__init__.py
from .hybrid import HybridRetriever
from .dense_only import DenseOnlyRetriever
from .lexical_only import LexicalOnlyRetriever  # ← Agregar

__all__ = [
    "HybridRetriever",
    "DenseOnlyRetriever", 
    "LexicalOnlyRetriever"  # ← Agregar
]
```

### 4. Usar nueva estrategia:

```python
# Uso directo
from backend.search import get_retriever
retriever = get_retriever("lexical_only", k_results=100)

# Via environment variable
export SEARCH_STRATEGY=lexical_only
retriever = get_retriever()  # Usa lexical_only automáticamente
```

## 📊 Ejemplo de Salida

```python
# Resultado de búsqueda híbrida
results = [
    {
        "score": 0.8234,
        "expte": "123/2024",
        "section": "FUNDAMENTOS",
        "paragraph": "El contrato celebrado entre las partes establece...",
        "path": "fallos/2024/enero/fallo_123.json",
        "search_type": "hybrid"
    },
    # ... más resultados
]

# Estadísticas del retriever
stats = {
    "retriever_type": "hybrid",
    "dense_limit": 30,
    "lexical_limit": 30,
    "reranking_enabled": True,
    "caching_enabled": True,
    "corpus_size": 15420
}

# Métricas de rendimiento (en logs)
🔍 HybridRetriever query in 0.234s:
   Dense: 0.089s, Lexical: 0.045s
   Merge: 0.012s, Rerank: 0.088s  
   Candidates: 45, Final: 10
```

## 🎯 Características Clave

- **🔄 Factory Pattern**: Fácil cambio entre estrategias
- **🚀 Lazy Loading**: Carga solo la estrategia necesaria
- **⚡ Performance**: Optimizaciones para gran volumen
- **🎯 Híbrido**: Combina búsqueda vectorial + lexical
- **🧠 Re-ranking**: CrossEncoder para mejorar relevancia
- **💾 Caching**: LRU cache para embeddings repetidos
- **📊 Métricas**: Logging detallado de rendimiento
- **🔧 Configurable**: Todo vía variables de entorno

## 💡 Estrategias Futuras

### ReRankingRetriever
```python
class ReRankingRetriever(BaseRetriever):
    """Retriever con re-ranking avanzado usando múltiples modelos"""
    
    def __init__(self):
        self.base_retriever = HybridRetriever()
        self.rerankers = [
            CrossEncoder("model1"),
            CrossEncoder("model2")
        ]
    
    def query(self, question, top_n=10):
        # 1. Búsqueda base con más resultados
        candidates = self.base_retriever.query(question, top_n * 3)
        
        # 2. Re-ranking ensemble
        for reranker in self.rerankers:
            # Aplicar cada re-ranker
            pass
        
        return final_results[:top_n]
```

### MultiModalRetriever
```python
class MultiModalRetriever(BaseRetriever):
    """Retriever que considera texto + metadatos + fechas"""
    
    def query(self, question, filters=None):
        # Búsqueda por texto + filtros por metadata
        pass
```

## ⚠️ Notas Importantes

- **Índices requeridos**: Ejecutar `build_indexes()` antes del primer uso
- **Memoria**: HybridRetriever usa ~2GB RAM (embeddings + BM25)
- **Qdrant**: Debe estar corriendo en la URL configurada
- **Modelos**: Se descargan automáticamente la primera vez
- **Re-ranking**: Opcional pero mejora significativamente la relevancia
- **Caching**: Mejora performance para consultas repetidas