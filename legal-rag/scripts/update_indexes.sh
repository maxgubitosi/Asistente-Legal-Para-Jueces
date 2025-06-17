#!/usr/bin/env bash
set -e

echo "🔄 ACTUALIZACIÓN MANUAL DE ÍNDICES"
echo "=================================="

# Verificar si hay cambios
echo "1. Verificando cambios..."
python /app/scripts/check_dataset_changes.py

echo -e "\n2. ¿Continuar con la actualización? (y/N)"
read -r response

if [[ "$response" =~ ^[Yy]$ ]]; then
    echo "3. Eliminando índices existentes..."
    rm -f /indexes/bm25.pkl /indexes/bm25_corpus.npy 2>/dev/null || true
    
    echo "4. Reconstruyendo índices..."
    python -m scripts.build_index /datasets/fallos_json --qdrant-url http://qdrant:6333
    
    echo "✅ Actualización completada!"
    echo "   Reinicie el servicio para aplicar cambios:"
    echo "   docker-compose restart backend"
else
    echo "❌ Actualización cancelada"
fi
