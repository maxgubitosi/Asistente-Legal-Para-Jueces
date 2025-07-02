# Manual Docker Setup Guide

## 📁 Data Directory Used
The system uses `datasets/fallos_json/` (NOT `unified_json`).

## 🐳 Manual Dual-Docker Setup

### Step 1: Keep Original RAG Running
```bash
cd legal-rag
docker compose up --build
# Runs on http://localhost:8000
```

### Step 2: Setup Eval RAG on Different Port

#### Option A: Modify docker-compose.yaml in eval version
Edit `legal-rag-eval-version/docker-compose.yaml` to change ALL ports:
```yaml
# Qdrant (line ~7): Change from:
ports: ["6333:6333"]
# To:
ports: ["6334:6333"]

# Backend (line ~20): Change from:
ports: ["8000:8000"]
# To:
ports: ["8001:8000"]

# Streamlit (line ~33): Change from:
ports: ["8501:8501"]
# To:
ports: ["8502:8501"]

# Also change container name (line ~26):
container_name: rag-ui-eval  # Instead of rag-ui
```

#### Option B: Use docker compose override
Create `legal-rag-eval-version/docker-compose.override.yaml`:
```yaml
version: "3.9"
services:
  qdrant:
    ports: ["6334:6333"]
  backend:
    ports: ["8001:8000"]
  streamlit:
    container_name: rag-ui-eval
    ports: ["8502:8501"]
```

### Step 3: Run Eval Docker
```bash
# Copy test data
cp -r datasets_evaluation/test2/* legal-rag-eval-version/datasets/fallos_json/

# Clear cache (IMPORTANT!)
rm -rf legal-rag-eval-version/bm25_cache/*

# Start eval version on different ports
cd legal-rag-eval-version
docker compose up --build
# Backend: http://localhost:8001
# Streamlit UI: http://localhost:8502
# Qdrant: http://localhost:6334
```

### Step 4: Run Evaluation
```bash
# Manual mode - specify both backends
python 8_evaluate.py --test 2 \
  --original-backend http://localhost:8000 \
  --modified-backend http://localhost:8001 \
  --sample-size 5
```

## ⚡ Quick Commands

### Test 2: Redaction Robustness
```bash
# Setup data and cache
cp -r datasets_evaluation/test2/* legal-rag-eval-version/datasets/fallos_json/
rm -rf legal-rag-eval-version/bm25_cache/*

# Start eval Docker (in new terminal)
cd legal-rag-eval-version && docker compose up --build

# Run evaluation (wait ~30 seconds for startup)
python 8_evaluate.py --test 2 --original-backend http://localhost:8000 --modified-backend http://localhost:8001
```

### Test 3: Content Sensitivity
```bash
# Setup data and cache
cp -r datasets_evaluation/test3/* legal-rag-eval-version/datasets/fallos_json/
rm -rf legal-rag-eval-version/bm25_cache/*

# Start eval Docker (restart container)
cd legal-rag-eval-version && docker compose down && docker compose up --build

# Run evaluation
python 8_evaluate.py --test 3 --original-backend http://localhost:8000 --modified-backend http://localhost:8001
```

## 🚨 Important Notes

1. **Always clear cache**: `rm -rf legal-rag-eval-version/bm25_cache/*` forces recomputation of embeddings
2. **Wait for startup**: Allow ~30 seconds after `docker compose up` before running evaluation
3. **Port mapping**: 
   - Original: Backend:8000, Streamlit:8501, Qdrant:6333
   - Eval: Backend:8001, Streamlit:8502, Qdrant:6334
4. **Data location**: Test data goes in `legal-rag-eval-version/datasets/fallos_json/`
5. **Internal networks**: Services within each Docker network still communicate on standard ports

## 🔄 Auto Mode (Easier)
If you prefer automatic setup:
```bash
python 8_evaluate.py --test 2 --auto-docker
```
This handles all the file copying, cache clearing, and Docker management automatically. 