# 🔄 Actualización Automática de Índices - Legal RAG

## ❌ Problema Actual
**El sistema NO detecta automáticamente archivos JSON nuevos** cuando levantas Docker. Solo indexa la primera vez.

## ✅ Soluciones Implementadas

### 🔧 **Opción 1: Detección Automática al Iniciar** (Recomendado)

El sistema ahora verifica cambios automáticamente al iniciar:

```bash
# Activar detección automática
export AUTO_UPDATE_INDEXES=true

# Levantar Docker (detectará cambios automáticamente)
docker-compose up
```

### 🔧 **Opción 2: Forzar Reconstrucción**

```bash
# Forzar reconstrucción completa
export FORCE_REBUILD=true
docker-compose up --build

# O con docker-compose
FORCE_REBUILD=true docker-compose up
```

### 🔧 **Opción 3: Actualización Manual**

```bash
# Entrar al contenedor
docker exec -it legal-rag-backend-1 bash

# Verificar si hay cambios
python scripts/check_dataset_changes.py

# Actualizar manualmente
./scripts/update_indexes.sh
```

### 🔧 **Opción 4: API de Actualización**

```bash
# Verificar estado del dataset
curl http://localhost:8000/dataset-status

# Forzar actualización vía API
curl -X POST http://localhost:8000/rebuild-indexes
```

## 📋 Cómo Funciona la Detección

### Sistema de Checksums
- ✅ Calcula hash MD5 del dataset completo
- ✅ Incluye: nombres de archivos, tamaños, fechas de modificación
- ✅ Detecta: archivos nuevos, eliminados, modificados
- ✅ Persiste metadata en `/indexes/dataset_metadata.json`

### Log de Ejemplo
```
🔍 Verificando cambios en el dataset...
📊 Dataset actual: 157 archivos, 23845672 bytes
🔄 Dataset cambió: +3 archivos, +145832 bytes
👉 Building indexes...
```

## 🚀 Flujo de Trabajo Recomendado

### Para Desarrollo Diario
```bash
# 1. Agregar nuevos JSONs a ../datasets/fallos_json/
cp nuevos_fallos/*.json ../datasets/fallos_json/2024/06/

# 2. Reiniciar (detecta cambios automáticamente)
docker-compose restart backend

# 3. Verificar en logs
docker-compose logs backend | grep "Dataset"
```

### Para Actualización Masiva
```bash
# 1. Parar el servicio
docker-compose down

# 2. Agregar archivos masivamente
# ... copiar archivos ...

# 3. Forzar reconstrucción completa
FORCE_REBUILD=true docker-compose up
```

## 📊 Monitoreo de Estado

### Verificar Estado Actual
```bash
# Via API
curl http://localhost:8000/dataset-status | jq

# Respuesta ejemplo:
{
  "needs_update": false,
  "message": "✅ Dataset sin cambios",
  "last_check": 1640995200
}
```

### Verificar Metadata
```bash
# Ver metadata del dataset
docker exec legal-rag-backend-1 cat /indexes/dataset_metadata.json

# Ejemplo:
{
  "hash": "a1b2c3d4e5f6...",
  "file_count": 157,
  "total_size": 23845672,
  "last_check": "2025-06-16T10:30:00"
}
```

## ⚙️ Configuración Avanzada

### Variables de Entorno
```env
# Activar/desactivar detección automática
AUTO_UPDATE_INDEXES=true

# Forzar reconstrucción en próximo inicio
FORCE_REBUILD=false

# Intervalo de verificación (en desarrollo)
UPDATE_CHECK_INTERVAL=3600  # segundos
```

### Personalizar Comportamiento
```bash
# Solo verificar sin actualizar
CHECK_ONLY=true docker-compose up

# Actualizar solo si hay más de X archivos nuevos
MIN_CHANGES_THRESHOLD=5 docker-compose up
```

## 🔍 Troubleshooting

### Problema: "No detecta mis archivos nuevos"
**Solución:**
```bash
# Verificar que están en la ruta correcta
docker exec legal-rag-backend-1 find /datasets -name "*.json" | wc -l

# Forzar actualización manual
docker exec legal-rag-backend-1 ./scripts/update_indexes.sh
```

### Problema: "Error en la detección"
**Solución:**
```bash
# Ver logs detallados
docker-compose logs backend

# Limpiar metadata corrupta
docker exec legal-rag-backend-1 rm -f /indexes/dataset_metadata.json
docker-compose restart backend
```

### Problema: "Actualización muy lenta"
**Solución:**
```bash
# Para datasets grandes (>10k archivos), usar optimizaciones
export EMBEDDING_BATCH_SIZE=16
export UPLOAD_BATCH_SIZE=500
docker-compose restart backend
```

## 📈 Mejores Prácticas

### ✅ Recomendado
- Usar detección automática para desarrollo diario
- Forzar rebuild para cambios masivos (>100 archivos)
- Monitorear logs durante actualizaciones grandes
- Hacer backup de índices antes de cambios masivos

### ❌ Evitar
- Agregar archivos mientras el servicio está corriendo
- Modificar archivos existentes (mejor crear nuevos)
- Forzar rebuild innecesariamente (desperdicia tiempo)

## 🚦 Estados del Sistema

| Estado | Descripción | Acción |
|--------|-------------|--------|
| 🆕 Primera vez | No hay índices | Indexa automáticamente |
| ✅ Sin cambios | Dataset igual | Usa índices existentes |
| 🔄 Cambios detectados | Archivos nuevos/modificados | Reconstruye automáticamente |
| 🔨 Forzado | FORCE_REBUILD=true | Reconstruye siempre |
| ❌ Error | Problema en detección | Ver logs y troubleshooting |

## 📞 Comandos de Emergencia

```bash
# Si todo falla, reset completo:
docker-compose down
docker volume rm legal-rag_bm25_cache
docker volume rm legal-rag_qdrant_data
FORCE_REBUILD=true docker-compose up --build

# Verificación rápida:
curl http://localhost:8000/health
curl http://localhost:8000/dataset-status
```
