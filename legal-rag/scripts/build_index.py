#!/usr/bin/env python3
"""
Construye los índices (denso + BM25) a partir de los JSON de fallos.

Uso:
    python scripts/build_index.py datasets/fallos_json \
           --qdrant-url http://localhost:6333
"""

import argparse
from pathlib import Path
from app.index import build_indexes

def main():
    parser = argparse.ArgumentParser(description="Build legal RAG indexes")
    parser.add_argument("json_dir", type=Path,
                        help="Directorio con fallos en formato JSON")
    parser.add_argument("--qdrant-url", default="http://localhost:6333",
                        help="Endpoint de Qdrant (por defecto localhost)")
    args = parser.parse_args()

    build_indexes(args.json_dir, qdrant_url=args.qdrant_url)

if __name__ == "__main__":
    main()
