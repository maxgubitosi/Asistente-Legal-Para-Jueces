# 🧠 Módulo RAG

Módulo encargado del **pipeline RAG (Retrieval-Augmented Generation)** para consultas legales. Orquesta la búsqueda de información relevante y la generación de respuestas usando LLMs, proporcionando diferentes estrategias como RAG estándar y conversacional.

## 🏗️ Arquitectura

```
backend/rag/
├── __init__.py          # Exports principales
├── base.py              # Interface base
├── factory.py           # Factory para pipelines
└── strategies/
    ├── __init__.py      # Exports de estrategias
    ├── standard.py      # RAG estándar con singletons
    └── conversational.py # RAG con memoria conversacional
```

## 📁 Archivos

### [`base.py`](base.py)
**Interface base para todos los pipelines RAG:**
```python
class BaseRAGPipeline(ABC):
    @abstractmethod
    def query(self, question: str, top_n: int = 8) -> Tuple[str, List[Dict[str, Any]]]:
        pass
    
    def get_stats(self) -> Dict[str, Any]:
        return {"pipeline_type": "base"}
    
    def supports_streaming(self) -> bool:
        return False
```

### [`factory.py`](factory.py)
**Factory principal para crear pipelines RAG:**
- `get_rag_pipeline(strategy)` - Crea pipeline según estrategia
- `answer(question, top_n)` - Función de conveniencia
- `get_available_strategies()` - Lista estrategias disponibles
- `get_default_strategy()` - Estrategia por defecto
- **Lazy imports** para mejor rendimiento

### [`strategies/standard.py`](strategies/standard.py)
**Pipeline RAG estándar optimizado:**
- ✅ **Singletons globales** para retriever y LLM (evita re-inicialización)
- ✅ **Métricas detalladas** de tiempo por componente
- ✅ **Prompt especializado** para asistente jurídico
- ✅ **Configuración flexible** via env vars
- ✅ **Contexto optimizado** con truncado inteligente
- ✅ **Logging performance** completo

### [`strategies/conversational.py`](strategies/conversational.py)
**Pipeline RAG con memoria conversacional:**
- ✅ **Historial de conversación** configurable
- ✅ **Contexto combinado** (historial + nueva evidencia)
- ✅ **Prompt conversacional** especializado
- ✅ **Gestión automática** de memoria (límite de turnos)
- ✅ **Clear history** manual
- ✅ **Streaming support** preparado

## 🚀 Uso Básico

```python
# Opción 1: Factory (recomendado)
from backend.rag import get_rag_pipeline
pipeline = get_rag_pipeline("standard")
response, hits = pipeline.query("¿Qué dice sobre contratos?", top_n=5)

# Opción 2: Función de conveniencia
from backend.rag import answer
response, hits = answer("¿Qué dice sobre contratos?")

# Opción 3: Pipeline conversacional
pipeline = get_rag_pipeline("conversational", max_history=10)
response1, hits1 = pipeline.query("¿Qué es un contrato?")
response2, hits2 = pipeline.query("¿Y qué obligaciones genera?")  # Usa contexto previo
pipeline.clear_history()  # Limpiar cuando sea necesario

# Opción 4: Acceso directo
from backend.rag import StandardRAGPipeline, ConversationalRAGPipeline
pipeline = StandardRAGPipeline()
conv_pipeline = ConversationalRAGPipeline(max_history=5)

# Ver estrategias disponibles
from backend.rag import get_available_strategies
print("Disponibles:", get_available_strategies())

# Estadísticas del pipeline
stats = pipeline.get_stats()
print(f"Retriever cargado: {stats['retriever_loaded']}")
```

## ⚙️ Configuración

```bash
# Estrategia RAG
export RAG_STRATEGY=standard           # standard | conversational

# Configuración StandardRAG
export MAX_PARAGRAPH_LENGTH=300        # Caracteres máximos por párrafo
export LLM_MAX_TOKENS=300              # Tokens máximos para respuesta
export MAX_RESULTS_PER_QUERY=8         # Resultados máximos de búsqueda

# Configuración módulos dependientes
export SEARCH_STRATEGY=hybrid          # Estrategia de búsqueda
export LLM_PROVIDER=azure              # Proveedor LLM
```

## 🔧 Agregar Nueva Estrategia

### 1. Crear nueva implementación:

```python
# strategies/multi_step.py
import time
from ..base import BaseRAGPipeline
from backend.search import get_retriever
from backend.llm import get_llm_provider

class MultiStepRAGPipeline(BaseRAGPipeline):
    """Pipeline RAG con reasoning multi-paso"""
    
    def __init__(self, max_steps: int = 3):
        self.max_steps = max_steps
        self.retriever = None
        self.llm_provider = None
    
    def query(self, question: str, top_n: int = 8):
        """RAG con multiple pasos de reasoning"""
        if self.retriever is None:
            self.retriever = get_retriever("hybrid")
        if self.llm_provider is None:
            self.llm_provider = get_llm_provider("azure")
        
        steps = []
        current_question = question
        
        for step in range(self.max_steps):
            # 1. Búsqueda para el paso actual
            hits = self.retriever.query(current_question, top_n)
            
            # 2. Generar sub-respuesta
            context = self._build_context(hits)
            sub_response = self._generate_step_response(
                current_question, context, step + 1
            )
            
            steps.append({
                "step": step + 1,
                "question": current_question,
                "response": sub_response,
                "hits": hits
            })
            
            # 3. Generar siguiente pregunta (si no es último paso)
            if step < self.max_steps - 1:
                current_question = self._generate_next_question(
                    question, steps
                )
        
        # 4. Combinar todos los pasos en respuesta final
        final_response = self._combine_steps(question, steps)
        all_hits = [hit for step in steps for hit in step["hits"]]
        
        return final_response, all_hits[:top_n]
    
    def _build_context(self, hits):
        return "\n".join(f"[{h['expte']}]: {h['paragraph'][:200]}" for h in hits)
    
    def _generate_step_response(self, question, context, step_num):
        prompt = f"""
        Paso {step_num} de análisis legal:
        Pregunta: {question}
        Contexto: {context}
        
        Analiza este aspecto específico:
        """
        messages = [{"role": "user", "content": prompt}]
        return self.llm_provider.generate(messages, max_tokens=200)
    
    def _generate_next_question(self, original_question, steps):
        # Lógica para generar siguiente pregunta basada en pasos previos
        prompt = f"""
        Pregunta original: {original_question}
        Análisis previo: {steps[-1]['response'][:100]}...
        
        ¿Qué aspecto legal específico debería analizar a continuación?
        Responde solo la pregunta específica:
        """
        messages = [{"role": "user", "content": prompt}]
        return self.llm_provider.generate(messages, max_tokens=50)
    
    def _combine_steps(self, original_question, steps):
        # Combinar todos los pasos en respuesta final coherente
        combined_analysis = "\n\n".join([
            f"**Paso {s['step']}:** {s['response']}" for s in steps
        ])
        
        prompt = f"""
        Pregunta original: {original_question}
        
        Análisis multi-paso realizado:
        {combined_analysis}
        
        Proporciona respuesta final integrada en formato de tabla Markdown:
        """
        messages = [{"role": "user", "content": prompt}]
        return self.llm_provider.generate(messages, max_tokens=400)
    
    def get_stats(self):
        return {
            "pipeline_type": "multi_step",
            "max_steps": self.max_steps,
            "retriever_loaded": self.retriever is not None,
            "llm_provider_loaded": self.llm_provider is not None
        }
    
    def supports_streaming(self):
        return True
```

### 2. Registrar en factory:

```python
# factory.py
def _import_multi_step():
    from .strategies.multi_step import MultiStepRAGPipeline
    return MultiStepRAGPipeline

def get_rag_pipeline(strategy: str = None, **kwargs):
    strategies = {
        "standard": lambda: _import_standard(),
        "conversational": lambda: _import_conversational(),
        "multi_step": lambda: _import_multi_step(),  # ← Agregar
    }
    # ... resto del código

def get_available_strategies():
    return ["standard", "conversational", "multi_step"]  # ← Agregar
```

### 3. Exportar en strategies/__init__.py:

```python
# strategies/__init__.py
from .standard import StandardRAGPipeline
from .conversational import ConversationalRAGPipeline
from .multi_step import MultiStepRAGPipeline  # ← Agregar

__all__ = [
    "StandardRAGPipeline",
    "ConversationalRAGPipeline",
    "MultiStepRAGPipeline"  # ← Agregar
]
```

### 4. Usar nueva estrategia:

```python
# Uso directo
from backend.rag import get_rag_pipeline
pipeline = get_rag_pipeline("multi_step", max_steps=5)

# Via environment variable
export RAG_STRATEGY=multi_step
pipeline = get_rag_pipeline()  # Usa multi_step automáticamente
```

## 📊 Ejemplo de Salida

```python
# Respuesta StandardRAG
response = """
| # | Expte. | Sección | Extracto (máx 40 palabras) |
|---|--------|---------|----------------------------|
| 1 | 123/2024 | FUNDAMENTOS | El contrato celebrado entre las partes establece obligaciones recíprocas... |
| 2 | 456/2024 | CONSIDERANDO | Los contratos deben cumplirse de buena fe según art. 961 CCyC... |
"""

# Hits de búsqueda
hits = [
    {
        "score": 0.8234,
        "expte": "123/2024", 
        "section": "FUNDAMENTOS",
        "paragraph": "El contrato celebrado entre las partes...",
        "path": "fallos/2024/enero/fallo_123.json"
    }
]

# Estadísticas StandardRAG
stats = {
    "pipeline_type": "standard",
    "retriever_loaded": True,
    "llm_provider_loaded": True,
    "max_paragraph_length": 300,
    "max_tokens": 300,
    "max_results": 8,
    "retriever_stats": {"retriever_type": "hybrid", ...},
    "llm_stats": {"provider_type": "azure", ...}
}

# Logs de performance
📊 StandardRAG query processed in 1.234s:
   Search: 0.456s, Context: 0.012s, LLM: 0.766s
   Results: 8, Context length: 1847 chars
```

## 🎯 Características Clave

- **🔄 Factory Pattern**: Fácil cambio entre estrategias
- **🚀 Singletons Optimizados**: Evita re-cargar modelos pesados
- **📊 Métricas Detalladas**: Logging completo de performance
- **🗣️ Memoria Conversacional**: Contexto multi-turn automático
- **⚙️ Configurable**: Todo vía variables de entorno
- **🎯 Prompts Especializados**: Para contexto jurídico
- **🔧 Extensible**: Fácil agregar nuevas estrategias
- **📈 Performance Tracking**: Tiempos por componente

## 💡 Estrategias Futuras

### CitationRAGPipeline
```python
class CitationRAGPipeline(BaseRAGPipeline):
    """RAG con citas precisas y verificación de fuentes"""
    
    def query(self, question, top_n=8):
        # Generar respuesta con citas verificables
        # Validar que cada afirmación tenga respaldo
        # Formato: "Según expediente X, sección Y: [afirmación]"
        pass
```

### FactCheckRAGPipeline  
```python
class FactCheckRAGPipeline(BaseRAGPipeline):
    """RAG con verificación automática de hechos"""
    
    def query(self, question, top_n=8):
        # 1. RAG normal
        # 2. Extraer afirmaciones clave
        # 3. Verificar cada afirmación contra corpus
        # 4. Marcar nivel de confianza
        pass
```

### SummarizeRAGPipeline
```python
class SummarizeRAGPipeline(BaseRAGPipeline):
    """RAG especializado en resúmenes de jurisprudencia"""
    
    def query(self, question, top_n=20):
        # Recuperar más documentos
        # Agrupar por tema/año/tipo
        # Generar resumen consolidado
        pass
```

## ⚠️ Notas Importantes

- **Singletons**: Los retrievers y LLM providers se reutilizan para eficiencia
- **Memoria**: ConversationalRAG mantiene estado entre consultas
- **Performance**: StandardRAG típicamente 1-2 segundos por consulta
- **Context Length**: Cuidar límites de contexto del LLM (300 tokens por defecto)
- **Dependencies**: Requiere backend.search y backend.llm configurados
- **Prompts**: Especializados para contexto jurídico argentino
- **Lazy Loading**: Componentes se cargan solo cuando se necesitan