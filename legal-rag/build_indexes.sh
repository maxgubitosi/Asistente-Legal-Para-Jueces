#!/usr/bin/env bash
set -e

echo "🔧 Building BM25 indexes for Legal RAG..."

# Check if running in Docker or local environment
if [ -d "/datasets/fallos_json" ]; then
    echo "👉 Running in Docker environment"
    DATASET_PATH="/datasets/fallos_json"
    QDRANT_URL="http://qdrant:6333"
elif [ -d "../datasets/fallos_json" ]; then
    echo "👉 Running in local environment"
    DATASET_PATH="../datasets/fallos_json"
    QDRANT_URL="http://localhost:6333"
else
    echo "❌ Error: Cannot find fallos_json dataset"
    echo "Please ensure the dataset is available at:"
    echo "  - /datasets/fallos_json (Docker)"
    echo "  - ../datasets/fallos_json (Local)"
    exit 1
fi

# Create indexes directory if it doesn't exist
mkdir -p /indexes 2>/dev/null || mkdir -p ./bm25_cache

echo "👉 Building indexes..."
python -m scripts.build_index "$DATASET_PATH" --qdrant-url "$QDRANT_URL"

echo "✅ Indexes built successfully!"
echo "You can now start the application."
