# 🚀 Pasos Finales para Ejecutar Legal RAG - Versión Optimizada

## ✅ Estado Actual
- ✅ Código limpiado y optimizado
- ✅ Archivo `retrieve.py` viejo movido a `retrieve_old.py.bak`
- ✅ Usando `retrieve_optimized.py` con mejoras de rendimiento
- ✅ Detección automática de archivos nuevos implementada
- ✅ APIs de monitoreo y debugging agregadas
- ✅ Configuración optimizada para velocidad

## 🔧 Pasos para Ejecutar

### 1. **Preparar el Entorno**
```bash
# Ir al directorio del proyecto
cd "c:\Users\MSI\Desktop\Udesa\Materias\2025 - 1er Semestre\NLP\Proyecto Final\TP_NLP\legal-rag"

# Verificar que tienes los datasets
ls ../datasets/fallos_json/
```

### 2. **Configurar Variables (Opcional)**
Edita `.env` si necesitas ajustar el rendimiento:
```bash
# Para máxima velocidad (recomendado para pruebas)
ENABLE_RERANKING=false
DENSE_SEARCH_LIMIT=15
LEXICAL_SEARCH_LIMIT=15

# Para primera vez o cuando agregues muchos archivos
FORCE_REBUILD=true  # Solo la primera vez
```

### 3. **Levantar el Sistema**
```bash
# Construcción completa (primera vez)
docker-compose down
docker-compose up --build

# O si ya lo tienes construido
docker-compose up
```

### 4. **Verificar que Todo Funciona**
```bash
# Verificar salud del sistema
curl http://localhost:8000/health

# Debería responder:
# {"status":"healthy","message":"All indexes are available"}
```

### 5. **Probar una Búsqueda**
```bash
# Prueba básica
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "contratos de arrendamiento", "top_n": 5}'

# Prueba con debugging (para ver tiempos)
curl -X POST http://localhost:8000/query-debug \
  -H "Content-Type: application/json" \
  -d '{"question": "responsabilidad civil", "top_n": 5}'
```

### 6. **Acceder a la Interfaz Web (Opcional)**
```bash
# Si tienes Streamlit configurado
http://localhost:8501
```

## 🔍 Verificación de Rendimiento

### Benchmark Automático
```bash
# Entrar al contenedor
docker exec -it legal-rag-backend-1 bash

# Ejecutar benchmark rápido
python scripts/benchmark.py --quick

# Debería mostrar tiempos < 2 segundos por consulta
```

### Monitoreo del Sistema
```bash
# Ver estadísticas
curl http://localhost:8000/performance | jq

# Verificar estado del dataset
curl http://localhost:8000/dataset-status | jq

# Monitor completo del sistema
docker exec -it legal-rag-backend-1 python scripts/monitor_system.py
```

## 📁 Agregar Archivos Nuevos

### Automático (Recomendado)
```bash
# 1. Agregar JSONs a la carpeta de datasets
cp nuevos_archivos/*.json ../datasets/fallos_json/2024/06/

# 2. Reiniciar (detecta cambios automáticamente)
docker-compose restart backend

# 3. Verificar en logs que se detectaron
docker-compose logs backend | grep "Dataset"
# Deberías ver: "🔄 Dataset cambió: +X archivos"
```

### Manual (Si el automático falla)
```bash
# Forzar reconstrucción completa
docker exec -it legal-rag-backend-1 ./scripts/update_indexes.sh

# O vía API
curl -X POST http://localhost:8000/rebuild-indexes
```

## 🚨 Solución de Problemas

### Si las búsquedas son lentas (>3 segundos)
```bash
# Editar .env y poner:
ENABLE_RERANKING=false
DENSE_SEARCH_LIMIT=10
LEXICAL_SEARCH_LIMIT=10

# Reiniciar
docker-compose restart backend
```

### Si no encuentra los archivos BM25
```bash
# Verificar paths
docker exec -it legal-rag-backend-1 ls -la /indexes/

# Si están vacíos, forzar rebuild
FORCE_REBUILD=true docker-compose up
```

### Si hay errores de memoria
```bash
# Reducir batch sizes en .env
EMBEDDING_BATCH_SIZE=16
UPLOAD_BATCH_SIZE=250

# Reiniciar
docker-compose restart backend
```

### Reset completo (última opción)
```bash
# Limpiar todo y empezar de cero
docker-compose down
docker volume rm legal-rag_bm25_cache legal-rag_qdrant_data
FORCE_REBUILD=true docker-compose up --build
```

## 📊 Endpoints Disponibles

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/health` | GET | Estado del sistema |
| `/performance` | GET | Estadísticas de rendimiento |
| `/dataset-status` | GET | Estado del dataset |
| `/query` | POST | Búsqueda normal |
| `/query-debug` | POST | Búsqueda con debugging |
| `/rebuild-indexes` | POST | Forzar reconstrucción |

## ✅ Checklist Final

- [ ] Docker levantado exitosamente
- [ ] `/health` responde con status "healthy"
- [ ] Búsqueda de prueba funciona en < 2 segundos
- [ ] Dataset detecta cambios automáticamente
- [ ] Interfaz web accesible (si aplicable)
- [ ] Logs no muestran errores críticos

## 🎯 Configuración Recomendada para Producción

```env
# Rendimiento balanceado
ENABLE_RERANKING=false
DENSE_SEARCH_LIMIT=20
LEXICAL_SEARCH_LIMIT=20
ENABLE_QUERY_CACHING=true
MAX_RESULTS_PER_QUERY=8
MAX_PARAGRAPH_LENGTH=300
LLM_MAX_TOKENS=300

# Detección automática
AUTO_UPDATE_INDEXES=true
FORCE_REBUILD=false
```

## 📞 Soporte Rápido

Si algo falla:
1. Verificar logs: `docker-compose logs backend`
2. Probar health check: `curl http://localhost:8000/health`
3. Reset completo si es necesario
4. Revisar configuración en `.env`

¡Listo! Con estos pasos deberías tener un sistema Legal RAG funcionando optimizado y con detección automática de archivos nuevos. 🎉
