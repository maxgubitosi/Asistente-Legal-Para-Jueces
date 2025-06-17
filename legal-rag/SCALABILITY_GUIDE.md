# 📈 Guía de Escalabilidad - Legal RAG

## Consideraciones para Grandes Volúmenes de Documentos

### 🎯 Límites Actuales y Recomendaciones

| Número de Documentos | Memoria RAM Recomendada | Tiempo de Indexación | Optimizaciones Necesarias |
|---------------------|-------------------------|---------------------|---------------------------|
| < 10,000 | 4 GB | < 5 min | Configuración básica |
| 10,000 - 50,000 | 8 GB | 10-30 min | Batch processing optimizado |
| 50,000 - 100,000 | 16 GB | 30-60 min | Tokenización optimizada |
| 100,000+ | 32 GB+ | 1+ hora | Procesamiento distribuido |

### ⚡ Optimizaciones Implementadas

#### 1. **Procesamiento en Lotes Dinámico**
```bash
# Variables de entorno para ajustar
EMBEDDING_BATCH_SIZE=32        # Reduce si hay problemas de memoria
UPLOAD_BATCH_SIZE=1000         # Lotes para subir a Qdrant
```

#### 2. **Gestión de Memoria**
- ✅ Liberación automática de memoria con `gc.collect()`
- ✅ Batch size dinámico según memoria disponible
- ✅ Procesamiento secuencial para evitar OOM

#### 3. **Optimizaciones de Qdrant**
- ✅ Configuración de segmentos optimizada para grandes volúmenes
- ✅ Carga en lotes para evitar timeouts
- ✅ Manejo de errores y recuperación

### 🚀 Próximos Pasos para Escalar Más

#### Para 500,000+ Documentos:

1. **Distribución de Carga**
```bash
# Usar múltiples workers para embeddings
docker-compose up --scale backend=3
```

2. **Base de Datos de Metadatos**
```sql
-- Tracking de documentos procesados
CREATE TABLE processed_docs (
    file_path TEXT PRIMARY KEY,
    processed_at TIMESTAMP,
    doc_count INTEGER,
    checksum TEXT
);
```

3. **Indexación Incremental**
```python
# Solo procesar documentos nuevos/modificados
def incremental_update():
    new_files = find_new_files_since_last_run()
    for file in new_files:
        add_to_index(file)
```

### 📊 Monitoreo y Alertas

#### Uso del Monitor
```bash
# Verificar estado del sistema
python scripts/monitor_system.py

# En Docker
docker exec legal-rag-backend-1 python scripts/monitor_system.py
```

#### Métricas Importantes
- **Memoria**: < 80% de uso
- **Disco**: > 2GB libres en `/indexes`
- **Qdrant**: Tiempo de respuesta < 100ms

### 🔧 Configuración para Diferentes Cargas

#### Desarrollo (< 10,000 docs)
```env
EMBEDDING_BATCH_SIZE=64
UPLOAD_BATCH_SIZE=500
```

#### Producción Media (10,000-50,000 docs)
```env
EMBEDDING_BATCH_SIZE=32
UPLOAD_BATCH_SIZE=1000
MAX_MEMORY_USAGE_PERCENT=70
```

#### Producción Alta (50,000+ docs)
```env
EMBEDDING_BATCH_SIZE=16
UPLOAD_BATCH_SIZE=2000
ENABLE_TEXT_PREPROCESSING=true
MIN_TOKEN_LENGTH=3
MAX_TOKEN_LENGTH=20
```

### ⚠️ Señales de Alerta

| Síntoma | Causa Probable | Solución |
|---------|---------------|----------|
| OutOfMemory errors | Batch size muy alto | Reducir `EMBEDDING_BATCH_SIZE` |
| Indexación muy lenta | Hardware insuficiente | Aumentar RAM o usar CPU más rápida |
| Timeouts en Qdrant | Lotes muy grandes | Reducir `UPLOAD_BATCH_SIZE` |
| Disco lleno | Archivos temporales | Limpiar `/tmp` y logs |

### 🏗️ Arquitectura para Producción

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Load Balancer │    │   Index Builder │    │   Data Pipeline │
│    (nginx)      │    │   (Background)  │    │   (Scheduled)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   API Servers   │    │     Qdrant      │    │   File Storage  │
│   (FastAPI x3)  │◄──►│   (Clustered)   │◄──►│   (S3/MinIO)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 📝 Lista de Verificación Pre-Escalado

- [ ] Configurar monitoreo de recursos
- [ ] Establecer límites de memoria y CPU
- [ ] Implementar logging estructurado
- [ ] Configurar backups automáticos de índices
- [ ] Probar recuperación ante fallos
- [ ] Documentar procedimientos de emergencia

### 🎯 Roadmap de Mejoras

#### Corto Plazo (1-2 semanas)
- [ ] Indexación incremental completa
- [ ] Dashboard de monitoreo web
- [ ] Alertas automatizadas

#### Mediano Plazo (1-2 meses)
- [ ] Clustering de Qdrant
- [ ] Cache distribuido (Redis)
- [ ] API rate limiting

#### Largo Plazo (3+ meses)
- [ ] Búsqueda federada multi-índice
- [ ] ML para optimización de relevancia
- [ ] Auto-scaling basado en carga
