#!/bin/bash

# Script de verificación del setup
echo "🔍 Verificando configuración del sistema..."

# Verificar variables de entorno críticas
required_vars=("AZURE_API_KEY" "AZURE_ENDPOINT" "AZURE_DEPLOYMENT" "QDRANT_URL")

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "❌ Variable de entorno faltante: $var"
        exit 1
    else
        echo "✅ $var configurada"
    fi
done

# Verificar directorios
directories=("/indexes" "/data")
for dir in "${directories[@]}"; do
    if [ ! -d "$dir" ]; then
        echo "📁 Creando directorio: $dir"
        mkdir -p "$dir"
    fi
done

# Verificar conectividad a Qdrant
echo "🔗 Verificando conexión a Qdrant..."
if curl -s "${QDRANT_URL}/health" > /dev/null; then
    echo "✅ Qdrant disponible"
else
    echo "⚠️  Qdrant no disponible (normal durante el primer inicio)"
fi

echo "✅ Verificación completada"