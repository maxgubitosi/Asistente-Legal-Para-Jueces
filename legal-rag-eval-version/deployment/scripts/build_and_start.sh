#!/usr/bin/env bash
set -e

echo "🚀 LEGAL RAG - Modular Backend Startup"
echo "======================================"

# Verificar que PYTHONPATH esté configurado
if [ -z "$PYTHONPATH" ]; then
    export PYTHONPATH="/app"
    echo "⚙️  PYTHONPATH configurado: $PYTHONPATH"
fi

# Verificar estructura del backend
echo "📁 Verificando estructura modular..."
required_modules=(
    "/app/backend/__init__.py"
    "/app/backend/config.py"
    "/app/backend/search/indexing.py"
    "/app/backend/api/api.py"
)

for module in "${required_modules[@]}"; do
    if [ ! -f "$module" ]; then
        echo "❌ Error: Módulo faltante $module"
        exit 1
    fi
done
echo "✅ Estructura del backend verificada"

# Verificar dataset
if [ ! -d "/datasets/fallos_json" ]; then
    echo "❌ Error: Dataset no encontrado en /datasets/fallos_json"
    echo "   Verifica que el volumen esté montado correctamente"
    exit 1
fi

# Verificar/construir índices usando la nueva estructura
echo "🔍 Verificando índices..."
if [ -f "/indexes/bm25.pkl" ] && [ -f "/indexes/bm25_corpus.npy" ]; then
    echo "✅ Índices existentes encontrados"
    
    # Verificar si necesita actualización (opcional)
    echo "🔄 Verificando si necesita actualización..."
    python -c "
from pathlib import Path
import os

dataset_path = Path('/datasets/fallos_json')
index_path = Path('/indexes/bm25.pkl')

if not index_path.exists():
    exit(1)

# Verificar si hay archivos más nuevos que el índice
dataset_files = list(dataset_path.rglob('*.json'))
if not dataset_files:
    print('⚠️  No se encontraron archivos JSON')
    exit(1)

newest_dataset = max(f.stat().st_mtime for f in dataset_files)
index_time = index_path.stat().st_mtime

if newest_dataset > index_time:
    print('🔄 Dataset actualizado, reconstruyendo índices...')
    exit(1)
else:
    print('✅ Índices actualizados')
    exit(0)
"
    
    update_needed=$?
    if [ $update_needed -eq 1 ]; then
        echo "🔧 Reconstruyendo índices..."
        python -c "
from backend.search.indexing import build_indexes
from pathlib import Path
import os

dataset_path = Path('/datasets/fallos_json')
qdrant_url = os.getenv('QDRANT_URL', 'http://qdrant:6333')

print(f'📊 Construyendo índices desde: {dataset_path}')
build_indexes(dataset_path, qdrant_url)
print('✅ Índices construidos exitosamente')
"
    fi
else
    echo "🔧 Construyendo índices por primera vez..."
    python -c "
from backend.search.indexing import build_indexes
from pathlib import Path
import os

dataset_path = Path('/datasets/fallos_json')
qdrant_url = os.getenv('QDRANT_URL', 'http://qdrant:6333')

print(f'📊 Construyendo índices desde: {dataset_path}')
build_indexes(dataset_path, qdrant_url)
print('✅ Índices construidos exitosamente')
"
fi

# Esperar a que Qdrant esté listo
echo "⏳ Esperando a que Qdrant esté listo..."
sleep 10

# Verificar que el backend se puede importar
echo "🧪 Verificando imports del backend..."
python -c "
from backend.api.api import app
from backend.rag import RAGPipeline
from backend.search import HybridRetriever
print('✅ Todos los módulos se importan correctamente')
"

# Iniciar la aplicación FastAPI
echo "🚀 Iniciando aplicación FastAPI..."
exec uvicorn backend.api.api:app --host 0.0.0.0 --port 8000