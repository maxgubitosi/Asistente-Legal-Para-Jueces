#!/usr/bin/env bash
set -e

INDEX_DIR=/indexes
BM25_PKL=$INDEX_DIR/bm25.pkl
BM25_NPY=$INDEX_DIR/bm25_corpus.npy

###############################################################################
# 1) Construir índices sólo la primera vez
###############################################################################
if [ ! -f "$BM25_PKL" ]; then
  echo "👉 Construyendo índices (primera vez)…"
  mkdir -p "$INDEX_DIR"
  python -m scripts.build_index /datasets/fallos_json \
        --qdrant-url http://qdrant:6333
  echo "✅ Índices construidos exitosamente"
else
  echo "✅ Índices ya existen, omitiendo construcción"
fi

###############################################################################
# 2) Lanzar la demo CLI (opcional) — puedes comentar esto si sólo usas la API
###############################################################################
echo "👉 Ejecutando demo CLI..."
python -m scripts.demo_cli ask "Listame fallos donde se discuta la constitución en mora"

echo "✅ Entrypoint script completed successfully"