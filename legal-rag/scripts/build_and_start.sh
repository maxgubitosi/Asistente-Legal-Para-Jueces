#!/usr/bin/env bash
set -e

INDEX_DIR=/indexes
BM25_PKL=$INDEX_DIR/bm25.pkl
FORCE_REBUILD=${FORCE_REBUILD:-false}

###############################################################################
# 1) Verificar cambios en el dataset
###############################################################################
echo "🔍 Verificando estado del dataset..."

# Verificar si se fuerza la reconstrucción
if [ "$FORCE_REBUILD" = "true" ]; then
  echo "🔨 Forzando reconstrucción de índices..."
  rm -f "$BM25_PKL" 2>/dev/null || true
fi

# Verificar cambios en el dataset (si existe el script)
if [ -f "/app/scripts/check_dataset_changes.py" ]; then
  python /app/scripts/check_dataset_changes.py
  DATASET_CHANGED=$?
  
  if [ $DATASET_CHANGED -eq 1 ] && [ -f "$BM25_PKL" ]; then
    echo "📋 Dataset cambió - reconstruyendo índices..."
    rm -f "$BM25_PKL" 2>/dev/null || true
  fi
fi

###############################################################################
# 2) Build indexes if they don't exist or if dataset changed
###############################################################################
if [ ! -f "$BM25_PKL" ]; then
  echo "👉 Building indexes..."
  mkdir -p "$INDEX_DIR"
  python -m scripts.build_index /datasets/fallos_json --qdrant-url http://qdrant:6333
  echo "✅ Indexes built successfully"
else
  echo "✅ Indexes already exist and dataset unchanged"
fi

###############################################################################
# 2) Wait a moment for Qdrant to be fully ready
###############################################################################
echo "👉 Waiting for services to be ready..."
sleep 5

###############################################################################
# 3) Start the FastAPI application
###############################################################################
echo "👉 Starting FastAPI application..."
exec uvicorn app.api:app --host 0.0.0.0 --port 8000
