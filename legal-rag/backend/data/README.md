# 📊 Módulo Data

Módulo encargado del **procesamiento y modelado de datos legales**. Extrae párrafos de documentos JSON y los convierte en objetos estructurados para indexing y búsqueda.

## 🏗️ Arquitectura

```
backend/data/
├── __init__.py          # Exports principales
├── factory.py           # Factory para procesadores
├── models.py            # Modelos Pydantic
└── processing/
    ├── __init__.py      # Exports de procesadores
    ├── base.py          # Interface base
    └── standard.py      # Procesador estándar
```

## 📁 Archivos

### [`models.py`](models.py)
**Modelos Pydantic para datos estructurados:**
- `LegalParagraph` - Párrafo legal extraído de documentos
- `Hit` - Resultado de búsqueda individual
- `QueryRequest` - Solicitud de consulta del usuario
- `QueryResponse` - Respuesta completa con resultados
- `ProcessingStats` - Estadísticas de procesamiento

### [`factory.py`](factory.py)
**Factory principal para crear procesadores:**
- `get_processor(mode)` - Crea procesador según estrategia
- `iter_paragraphs(json_dir)` - Función de conveniencia
- `get_available_modes()` - Lista modos disponibles
- **Lazy imports** para mejor rendimiento

### [`processing/base.py`](processing/base.py)
**Interface base para todos los procesadores:**
```python
class DataProcessor(ABC):
    @abstractmethod
    def process_directory(self, json_dir: Path) -> Iterator[LegalParagraph]:
        pass
    
    def get_stats(self) -> dict:
        return {}
```

### [`processing/standard.py`](processing/standard.py)
**Procesador estándar con features completas:**
- ✅ Procesamiento recursivo de directorios JSON
- ✅ Extracción inteligente de números de expediente
- ✅ Logging detallado del progreso
- ✅ Manejo robusto de errores
- ✅ Estadísticas completas
- ✅ Validación con Pydantic

## 🚀 Uso Básico

```python
# Opción 1: Factory (recomendado)
from backend.data import get_processor
processor = get_processor("standard")
for paragraph in processor.process_directory(json_dir):
    print(paragraph.expediente)

# Opción 2: Función de conveniencia
from backend.data import iter_paragraphs
for paragraph in iter_paragraphs("/path/to/json"):
    print(paragraph.text[:100])

# Opción 3: Acceso directo
from backend.data import StandardProcessor
processor = StandardProcessor()
stats = processor.get_stats()
```

## ⚙️ Configuración

```bash
# Variables de entorno
export PROCESSING_MODE=standard    # Modo de procesamiento
```

## 🔧 Agregar Nueva Estrategia

### 1. Crear nueva implementación:

```python
# processing/parallel.py
from .base import DataProcessor
from ..models import LegalParagraph

class ParallelProcessor(DataProcessor):
    """Procesador paralelo usando multiprocessing"""
    
    def __init__(self, workers: int = 4):
        self.workers = workers
        self.stats = {"files_processed": 0}
    
    def process_directory(self, json_dir: Path) -> Iterator[LegalParagraph]:
        # Implementar procesamiento paralelo
        with ProcessPoolExecutor(max_workers=self.workers) as executor:
            # ... lógica paralela
            pass
    
    def get_stats(self) -> dict:
        return {
            "processor_type": "parallel",
            "workers": self.workers,
            **self.stats
        }
```

### 2. Registrar en factory:

```python
# factory.py
def _import_parallel():
    from .processing.parallel import ParallelProcessor
    return ParallelProcessor

def get_processor(mode: str = None, **kwargs):
    processors = {
        "standard": lambda: _import_standard(),
        "parallel": lambda: _import_parallel(),  # ← Agregar aquí
    }
    # ... resto del código
```

### 3. Exportar en __init__.py:

```python
# processing/__init__.py
from .standard import StandardProcessor
from .parallel import ParallelProcessor  # ← Agregar

__all__ = ["StandardProcessor", "ParallelProcessor"]
```

### 4. Usar nueva estrategia:

```python
# Uso directo
from backend.data import get_processor
processor = get_processor("parallel", workers=8)

# Via environment variable
export PROCESSING_MODE=parallel
processor = get_processor()  # Usa parallel automáticamente
```

## 📊 Ejemplo de Salida

```python
# Párrafo extraído
paragraph = LegalParagraph(
    expediente="123/2024",
    section="FUNDAMENTOS",
    paragraph_id=0,
    text="El contrato celebrado entre las partes...",
    path="fallos/2024/enero/fallo_123.json"
)

# Estadísticas del procesador
stats = {
    "processor_type": "standard",
    "files_processed": 150,
    "paragraphs_extracted": 2840,
    "expedientes_found": 145,
    "errors": 2,
    "error_rate": 0.013
}
```

## 🎯 Características Clave

- **🔄 Factory Pattern**: Fácil cambio de estrategias
- **📊 Modelos Pydantic**: Validación automática
- **🚀 Lazy Loading**: Carga solo lo necesario
- **📈 Estadísticas**: Métricas detalladas
- **🛡️ Manejo de Errores**: Procesamiento robusto
- **🔧 Extensible**: Fácil agregar nuevos procesadores