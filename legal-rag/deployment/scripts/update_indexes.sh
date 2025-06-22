#!/usr/bin/env bash
set -e

echo "🔄 ACTUALIZACIÓN MANUAL DE ÍNDICES - Backend Modular"
echo "=================================================="

# Configurar PYTHONPATH
export PYTHONPATH="/app"

echo "0. Verificando servicios requeridos..."
# Verificar que Qdrant esté disponible
if ! curl -s "${QDRANT_URL:-http://qdrant:6333}/health" > /dev/null; then
    echo "❌ Qdrant no está disponible en ${QDRANT_URL:-http://qdrant:6333}"
    echo "   Asegúrese de que el servicio esté ejecutándose"
    exit 1
fi
echo "✅ Qdrant disponible"

echo "1. Verificando cambios en el dataset..."
VERIFICATION_OUTPUT=$(python -c "
import sys
import logging
from pathlib import Path
import os

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

try:
    dataset_path = Path('/datasets/fallos_json')
    index_path = Path('/indexes/bm25.pkl')

    logger.info(f'Dataset: {dataset_path}')
    json_files = list(dataset_path.rglob('*.json'))
    logger.info(f'Archivos JSON encontrados: {len(json_files)}')

    if index_path.exists():
        logger.info(f'Índice actual encontrado')
        if json_files:
            newest = max(f.stat().st_mtime for f in json_files)
            if newest > index_path.stat().st_mtime:
                print('NEEDS_UPDATE')
            else:
                print('UP_TO_DATE')
        else:
            logger.warning('No se encontraron archivos JSON')
            print('NO_JSON_FILES')
    else:
        logger.warning('Índices no existen')
        print('NO_INDEXES')
except Exception as e:
    logger.error(f'Error en verificación: {e}')
    print('ERROR')
    sys.exit(1)
")

case $VERIFICATION_OUTPUT in
    "NEEDS_UPDATE")
        echo "🔄 ACTUALIZACIÓN NECESARIA"
        ;;
    "UP_TO_DATE")
        echo "✅ Índices ya están actualizados"
        exit 0
        ;;
    "NO_INDEXES")
        echo "❌ Índices no existen - construcción inicial necesaria"
        ;;
    "ERROR")
        echo "❌ Error en verificación"
        exit 1
        ;;
esac

echo -e "\n2. ¿Continuar con la actualización? (y/N)"
read -r response

if [[ "$response" =~ ^[Yy]$ ]]; then
    echo "3. Eliminando índices existentes..."
    rm -f /indexes/bm25.pkl /indexes/bm25_corpus.npy 2>/dev/null || true
    
    echo "4. Reconstruyendo índices con backend modular..."
    python -c "
    import sys
    try:
        from backend.search.indexing import build_indexes
        from pathlib import Path
        import os

        dataset_path = Path('/datasets/fallos_json')
        qdrant_url = os.getenv('QDRANT_URL', 'http://qdrant:6333')

        print('🔧 Iniciando reconstrucción...')
        build_indexes(dataset_path, qdrant_url)
        print('✅ Reconstrucción completada')
    except Exception as e:
        print(f'❌ Error durante reconstrucción: {e}')
        sys.exit(1)
    " || {
        echo "❌ Error en la reconstrucción de índices"
        exit 1
    }
    
    echo "✅ Actualización completada!"
    echo "   Reinicie el servicio para aplicar cambios:"
    echo "   docker-compose restart backend"
else
    echo "❌ Actualización cancelada"
fi