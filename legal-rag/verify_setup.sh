#!/usr/bin/env bash
set -e

echo "🔍 VERIFICACIÓN FINAL - Legal RAG"
echo "================================"

# Verificar estructura de archivos
echo "📁 Verificando estructura de archivos..."

REQUIRED_FILES=(
    "app/api.py"
    "app/rag.py"
    "app/retrieve_optimized.py"
    "app/index.py"
    "app/ingest.py"
    "app/models.py"
    "scripts/build_index.py"
    "scripts/build_and_start.sh"
    "scripts/check_dataset_changes.py"
    "scripts/update_indexes.sh"
    "scripts/benchmark.py"
    "scripts/monitor_system.py"
    "requirements.txt"
    ".env"
    "docker-compose.yaml"
    "Dockerfile"
)

missing_files=()
for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        missing_files+=("$file")
    fi
done

if [ ${#missing_files[@]} -eq 0 ]; then
    echo "✅ Todos los archivos requeridos están presentes"
else
    echo "❌ Archivos faltantes:"
    printf '%s\n' "${missing_files[@]}"
    echo "   Por favor, verifica que tengas todos los archivos"
fi

# Verificar que el archivo viejo esté respaldado
if [ -f "app/retrieve.py" ]; then
    echo "⚠️  Archivo retrieve.py viejo aún presente"
    echo "   Ejecuta: mv app/retrieve.py app/retrieve_old.py.bak"
fi

# Verificar dataset
echo "📊 Verificando dataset..."
if [ -d "../datasets/fallos_json" ]; then
    json_count=$(find ../datasets/fallos_json -name "*.json" | wc -l)
    echo "✅ Dataset encontrado: $json_count archivos JSON"
else
    echo "❌ Dataset no encontrado en ../datasets/fallos_json"
    echo "   Verifica que tengas los archivos JSON en la ubicación correcta"
fi

# Verificar configuración
echo "⚙️  Verificando configuración..."

# Verificar variables críticas en .env
critical_vars=("AZURE_API_KEY" "AZURE_ENDPOINT" "AZURE_DEPLOYMENT" "BM25_PATH" "BM25_CORPUS_PATH")
for var in "${critical_vars[@]}"; do
    if grep -q "^$var=" .env 2>/dev/null; then
        echo "✅ $var configurado"
    else
        echo "❌ $var faltante en .env"
    fi
done

# Verificar configuración de rendimiento
if grep -q "ENABLE_RERANKING=false" .env 2>/dev/null; then
    echo "🚀 Configuración optimizada para velocidad"
else
    echo "⚠️  Reranking activado (puede ser más lento)"
fi

# Verificar Docker
echo "🐳 Verificando Docker..."
if command -v docker >/dev/null 2>&1; then
    echo "✅ Docker disponible"
    if command -v docker-compose >/dev/null 2>&1; then
        echo "✅ Docker Compose disponible"
    else
        echo "❌ Docker Compose no encontrado"
    fi
else
    echo "❌ Docker no encontrado"
fi

# Resumen final
echo ""
echo "📋 RESUMEN DE VERIFICACIÓN"
echo "========================="

if [ ${#missing_files[@]} -eq 0 ] && [ -d "../datasets/fallos_json" ]; then
    echo "🎉 ¡Todo listo para ejecutar!"
    echo ""
    echo "Próximos pasos:"
    echo "1. docker-compose up --build"
    echo "2. curl http://localhost:8000/health"
    echo "3. Probar una búsqueda"
    echo ""
    echo "Para agregar archivos nuevos:"
    echo "1. Copiar JSONs a ../datasets/fallos_json/"
    echo "2. docker-compose restart backend"
else
    echo "⚠️  Algunos elementos necesitan atención antes de ejecutar"
    echo "   Revisa los mensajes de arriba para ver qué falta"
fi

echo ""
echo "📚 Documentación disponible:"
echo "   - FINAL_SETUP_GUIDE.md (pasos de ejecución)"
echo "   - AUTO_UPDATE_GUIDE.md (manejo de archivos nuevos)"
echo "   - PERFORMANCE_OPTIMIZATION.md (optimización)"
echo "   - SCALABILITY_GUIDE.md (escalabilidad)"
