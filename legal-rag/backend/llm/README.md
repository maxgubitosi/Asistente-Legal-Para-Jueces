# 🤖 Módulo LLM

Módulo encargado de la **generación de texto usando modelos de lenguaje grandes (LLM)**. Proporciona una interface unificada para diferentes proveedores como Azure OpenAI, OpenAI directo, y modelos locales.

## 🏗️ Arquitectura

```
backend/llm/
├── __init__.py          # Exports principales
├── base.py              # Interface base
├── factory.py           # Factory para proveedores
└── providers/
    ├── __init__.py      # Exports de proveedores
    └── azure.py         # Proveedor Azure OpenAI
```

## 📁 Archivos

### [`base.py`](base.py)
**Interface base para todos los proveedores LLM:**
```python
class BaseLLMProvider(ABC):
    @abstractmethod
    def generate(self, messages, max_tokens=None, temperature=None) -> str:
        pass
    
    def get_stats(self) -> Dict[str, Any]:
        return {"provider_type": "base"}
    
    def supports_streaming(self) -> bool:
        return False
```

### [`factory.py`](factory.py)
**Factory principal para crear proveedores LLM:**
- `get_llm_provider(provider)` - Crea proveedor según tipo
- `run_llm(messages, max_tokens)` - Función de conveniencia (legacy)
- `get_azure_provider()` - Singleton para Azure (compatibilidad)
- **Lazy imports** para mejor rendimiento
- **Singleton global** para compatibilidad con código legacy

### [`providers/azure.py`](providers/azure.py)
**Proveedor Azure OpenAI con features completas:**
- ✅ **Retry automático** con exponential backoff
- ✅ **Logging detallado** de métricas y tokens
- ✅ **Manejo robusto de errores** con múltiples intentos
- ✅ **Cliente singleton** para reutilización
- ✅ **Configuración flexible** via env vars
- ✅ **Métricas de rendimiento** (tokens/sec, tiempos)

## 🚀 Uso Básico

```python
# Opción 1: Factory (recomendado)
from backend.llm import get_llm_provider
provider = get_llm_provider("azure")
response = provider.generate([
    {"role": "user", "content": "¿Qué es un contrato?"}
], max_tokens=200)

# Opción 2: Función de conveniencia (legacy)
from backend.llm import run_llm
response = run_llm([
    {"role": "user", "content": "¿Qué es un contrato?"}
], max_tokens=200)

# Opción 3: Acceso directo
from backend.llm.providers.azure import AzureProvider
provider = AzureProvider()
response = provider.generate(messages)

# Ver estadísticas
stats = provider.get_stats()
print(f"Modelo: {stats['deployment']}")
```

## ⚙️ Configuración

```bash
# Variables de entorno para Azure OpenAI
export AZURE_API_KEY="tu-api-key"
export AZURE_ENDPOINT="https://tu-recurso.openai.azure.com/"
export AZURE_DEPLOYMENT="gpt-4o-mini-toni"

# Configuración del LLM
export LLM_PROVIDER=azure              # Proveedor por defecto
export LLM_MAX_TOKENS=300              # Tokens máximos por defecto
export LLM_TEMPERATURE=0.1             # Temperatura por defecto
export LLM_TIMEOUT=30                  # Timeout en segundos
export LLM_MAX_RETRIES=3               # Intentos máximos
```

## 🔧 Agregar Nuevo Proveedor

### 1. Crear nueva implementación:

```python
# providers/openai.py
from ..base import BaseLLMProvider
from openai import OpenAI

class OpenAIProvider(BaseLLMProvider):
    """Proveedor OpenAI directo (sin Azure)"""
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.default_max_tokens = int(os.getenv("LLM_MAX_TOKENS", "300"))
        
    def generate(self, messages, max_tokens=None, temperature=None, **kwargs):
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens or self.default_max_tokens,
                temperature=temperature or 0.1,
                **kwargs
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Error: {str(e)}"
    
    def get_stats(self):
        return {
            "provider_type": "openai",
            "model": self.model,
            "default_max_tokens": self.default_max_tokens
        }
    
    def supports_streaming(self):
        return True
```

### 2. Registrar en factory:

```python
# factory.py
def _import_openai():
    from .providers.openai import OpenAIProvider
    return OpenAIProvider

def get_llm_provider(provider: str = None, **kwargs):
    providers = {
        "azure": lambda: _import_azure(),
        "openai": lambda: _import_openai(),  # ← Agregar aquí
    }
    # ... resto del código
```

### 3. Exportar en providers/__init__.py:

```python
# providers/__init__.py
from .azure import AzureProvider, AzureLLMProvider, get_azure_client
from .openai import OpenAIProvider  # ← Agregar

__all__ = [
    "AzureProvider", 
    "AzureLLMProvider",
    "get_azure_client",
    "OpenAIProvider"  # ← Agregar
]
```

### 4. Usar nuevo proveedor:

```python
# Uso directo
from backend.llm import get_llm_provider
provider = get_llm_provider("openai")

# Via environment variable
export LLM_PROVIDER=openai
provider = get_llm_provider()  # Usa OpenAI automáticamente

# Configurar OpenAI
export OPENAI_API_KEY="sk-..."
export OPENAI_MODEL="gpt-4"
```

## 📊 Ejemplo de Salida

```python
# Respuesta generada
response = "Un contrato es un acuerdo legal entre dos o más partes..."

# Estadísticas del proveedor
stats = {
    "provider_type": "azure",
    "deployment": "gpt-4o-mini-toni",
    "default_max_tokens": 300,
    "default_temperature": 0.1,
    "timeout": 30,
    "max_retries": 3,
    "client_initialized": True
}

# Métricas de generación (en logs)
🤖 LLM completed in 1.234s:
   Tokens: 45 prompt + 67 completion = 112 total
   Efficiency: 54.3 tokens/sec
   Config: max_tokens=200, messages=1
```

## 🎯 Características Clave

- **🔄 Factory Pattern**: Fácil cambio entre proveedores
- **🚀 Lazy Loading**: Carga solo el proveedor necesario
- **🔁 Retry Automático**: Manejo robusto de fallos temporales
- **📊 Métricas Detalladas**: Logging completo de rendimiento
- **⚙️ Configurable**: Todo vía variables de entorno
- **🛡️ Manejo de Errores**: Exponential backoff y timeouts
- **🔧 Extensible**: Fácil agregar nuevos proveedores
- **🎭 Compatibilidad**: Mantiene funciones legacy

## 💡 Proveedores Futuros

### LocalProvider (Modelos locales)
```python
# providers/local.py
class LocalProvider(BaseLLMProvider):
    """Proveedor para modelos locales (Ollama, Transformers)"""
    
    def __init__(self, model_path: str = "llama2:7b"):
        self.model_path = model_path
        # Inicializar modelo local
    
    def generate(self, messages, **kwargs):
        # Lógica para modelo local
        pass
```

### AnthropicProvider (Claude)
```python
# providers/anthropic.py  
class AnthropicProvider(BaseLLMProvider):
    """Proveedor para modelos Claude de Anthropic"""
    
    def generate(self, messages, **kwargs):
        # Lógica para Claude API
        pass
```

## ⚠️ Notas Importantes

- **Singleton de Cliente**: El cliente Azure se reutiliza para eficiencia
- **Rate Limiting**: Implementar si es necesario según proveedor
- **Costos**: Monitorear usage de tokens para control de costos
- **Streaming**: Azure soporta streaming pero no está implementado aún
- **Compatibilidad**: Mantener `run_llm()` para código legacy