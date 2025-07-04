# Legal-RAG 🏛️

Sistema de Retrieval-Augmented Generation (RAG) orientado a jurisprudencia. Permite consultar fallos judiciales usando un enfoque híbrido (denso + BM25) y generar respuestas enriquecidas con un LLM (Azure OpenAI).

Además, el backend adopta el **patrón de diseño *Factory***: un `FactoryManager` centraliza la creación y cacheo de procesadores, retrievers, proveedores LLM y pipelines RAG. Esto permite cambiar estrategias (por ejemplo `processing_mode`, `search_strategy`, etc.) solo modificando variables de entorno, sin tocar el código.

> **⚠️ Requisito de dataset:** Para que las búsquedas funcionen es imprescindible contar con la carpeta `datasets/fallos_json` que contiene los fallos judiciales en con toda la metadata, chuncks y Features. Este repositorio incluye **algunos** archivos de muestra para probar la aplicación rápidamente; si quieren el dataset completo (~160 archivos) avisenos y vemos como lo pasamos.

---

## 1. Arquitectura

1. **Backend** (`backend/`)
   * `api/` – API REST construida con FastAPI (`/query`, `/health`, …).
   * `data/` – Carga y pre-procesamiento (modes `standard | enriched`).
   * `search/` – Recuperadores híbridos (Qdrant + BM25).
   * `rag/` – Pipelines RAG (`standard | enriched`).
   * `llm/` – Capa de proveedores LLM (Azure OpenAI).
2. **Infraestructura**
   * **Qdrant** – Base de vectores (contenedor `qdrant`).
   * **BM25** – Índice léxico serializado (`bm25.pkl`, `bm25_corpus.npy`).
3. **Frontend** (`frontend/ui.py`)
   * UI de **Streamlit** que consume el endpoint `/query`.

### Detalle de carpetas en `backend/`

| Carpeta / Archivo        | Propósito principal                                                                                                   |
|--------------------------|-----------------------------------------------------------------------------------------------------------------------|
| `api/`                   | Endpoints FastAPI que exponen la API REST (`/query`, `/health`, etc.).                                                 |
| `config.py`              | Configuración global basada en *pydantic-settings*; centraliza variables de entorno y parámetros por defecto.         |
| `factory_manager.py`     | *Factory Manager* que instancia y cachea procesadores, retrievers, LLMs y pipelines RAG según la configuración.       |
| `data/`                  | Ingesta y preprocesamiento de documentos. Contiene `processing/` con modos `standard` y `enriched`, y modelos Pydantic.|
| `search/`                | Construcción de índices (BM25 + vectores) y estrategias de recuperación híbridas (`hybrid_enriched`, `hybrid` y `dense_only`).      |
| `rag/`                   | Implementación de pipelines RAG (`standard`, `enriched`) y estrategias de combinación de contexto.                    |
| `llm/`                   | Abstracción de proveedores LLM; actualmente `providers/azure.py` para Azure OpenAI.                                    |
---

## 2. Estructura de carpetas (resumen)

```
legal-rag/
 ├─ backend/              # Lógica principal
 │   ├─ api/
 │   ├─ data/
 │   ├─ search/
 │   ├─ rag/
 │   └─ llm/
 ├─ deployment/scripts/   # Scripts de automatización
 ├─ datasets/             # Dataset de fallos en JSON
 ├─ bm25_cache/           # Índices BM25 persistentes
 ├─ frontend/             # UI Streamlit
 ├─ docker-compose.yaml   # Stack completo
 ├─ Dockerfile            # Imagen "backend"
 └─ requirements.txt      # Dependencias
```

---

## 3. Requisitos

1. **Docker & Docker Compose** (opción recomendada)  
2. **Python 3.11+** (solo si se desea ejecutar componentes individuales).

---

## 4. Variables de entorno clave

| Variable            | Descripción                                           |
|---------------------|-------------------------------------------------------|
| `AZURE_API_KEY`     | API-Key de Azure OpenAI                               |
| `AZURE_ENDPOINT`    | Endpoint (p.ej. `https://…openai.azure.com/`)         |
| `AZURE_DEPLOYMENT`  | Nombre del deployment (por defecto `gpt-4o-mini-toni`)|
| `QDRANT_URL`        | URL de Qdrant (`http://qdrant:6333`)                  |

> Copia el archivo `.env.example` y completa estas variables personales antes de levantar el stack.

Otras configuraciones opcionales están documentadas en `backend/config.py` (límites de búsqueda, temperatura del LLM, etc.).

---

## 5. Ejecución con Docker Compose (💡 la forma más sencilla)

```bash
# 1) Clonar el repo y ubicarse en él
git clone https://github.com/maxgubitosi/TP_NLP.git && cd TP_NLP/legal-rag

# 2) Crear .env a partir del ejemplo y editarlo
cp .env.example .env

# 3) Levantar todo el stack
docker compose up -d  # backend, qdrant y UI

# 4) Abrir la UI
# → http://localhost:8501

```
(Cuando corres por primera vez, va a tardar a levantar el backend ya que esta indexando la informacion de los JSON)

Durante el primer inicio el contenedor `backend` ejecutará automáticamente:
1. Verificación del dataset (`datasets/…`).
2. Construcción o actualización de índices (`deployment/scripts/build_and_start.sh`).
3. Arranque de FastAPI (`uvicorn`).

---

## 6. Endpoints REST principales

| Método | Ruta           | Descripción                                 |
|--------|----------------|---------------------------------------------|
| `POST` | `/query`       | Consulta individual (`question`, `top_n`)   |
| `POST` | `/query-batch` | Consulta en lote (máx. 10)                  |
| `GET`  | `/health`      | Health-check de servicio e índices          |
| `GET`  | `/stats`       | Estadísticas internas                       |
| `POST` | `/rebuild-indexes` | Reconstruye índices en *background*     |

---

## 7. Construcción automática de índices

El script `build_and_start.sh` se encarga de crear o actualizar los índices cada vez que se inicia el contenedor `backend`, por lo que no se requieren pasos manuales.

---

## 8. Scripts útiles (`deployment/scripts/`)

* `build_and_start.sh` – verifica el entorno, construye índices y levanta FastAPI.
* `verify_setup.sh` – chequeo rápido de variables, carpetas y conectividad.