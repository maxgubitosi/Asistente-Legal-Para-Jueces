# 🚀 Guía de Optimización de Rendimiento - Legal RAG

## ⚠️ Problema: Búsquedas Lentas

Si las búsquedas tardan más de 3-5 segundos, aquí están las soluciones:

## 🔧 Soluciones Inmediatas

### 1. **Configuración Rápida (Recomendado)**
Edita tu archivo `.env` con estas configuraciones optimizadas:

```env
# Deshabilitar reranking para mayor velocidad (sacrifica un poco de precisión)
ENABLE_RERANKING=false

# Reducir límites de búsqueda
DENSE_SEARCH_LIMIT=15
LEXICAL_SEARCH_LIMIT=15

# Activar caché
ENABLE_QUERY_CACHING=true

# Limitar resultados y texto
MAX_RESULTS_PER_QUERY=5
MAX_PARAGRAPH_LENGTH=200
LLM_MAX_TOKENS=200
```

### 2. **Reiniciar el Servicio**
```bash
docker-compose restart backend
```

## 📊 Verificar Mejoras

### Método 1: Benchmark Automático
```bash
# Entrar al contenedor
docker exec -it legal-rag-backend-1 bash

# Ejecutar benchmark
python scripts/benchmark.py --quick

# Benchmark completo
python scripts/benchmark.py --debug
```

### Método 2: Verificación Manual
```bash
# Verificar estado
curl http://localhost:8000/health

# Probar consulta con timing
curl -X POST http://localhost:8000/query-debug \
  -H "Content-Type: application/json" \
  -d '{"question": "contratos de arrendamiento", "top_n": 5}'
```

## 🎯 Configuraciones por Escenario

### 🏃‍♂️ **MÁXIMA VELOCIDAD** (< 1 segundo)
```env
ENABLE_RERANKING=false
DENSE_SEARCH_LIMIT=10
LEXICAL_SEARCH_LIMIT=10
MAX_RESULTS_PER_QUERY=3
MAX_PARAGRAPH_LENGTH=150
LLM_MAX_TOKENS=150
```
- ✅ Muy rápido
- ❌ Menor precisión

### ⚖️ **BALANCEADO** (1-2 segundos)
```env
ENABLE_RERANKING=false
DENSE_SEARCH_LIMIT=20
LEXICAL_SEARCH_LIMIT=20
MAX_RESULTS_PER_QUERY=5
MAX_PARAGRAPH_LENGTH=250
LLM_MAX_TOKENS=250
```
- ✅ Buen balance velocidad/precisión
- ✅ Recomendado para la mayoría

### 🎯 **MÁXIMA PRECISIÓN** (2-4 segundos)
```env
ENABLE_RERANKING=true
DENSE_SEARCH_LIMIT=30
LEXICAL_SEARCH_LIMIT=30
MAX_RESULTS_PER_QUERY=8
MAX_PARAGRAPH_LENGTH=400
LLM_MAX_TOKENS=400
```
- ✅ Mejores resultados
- ❌ Más lento

## 🔍 Diagnóstico de Problemas

### Problema: Tiempo > 5 segundos
**Causas posibles:**
1. **Reranking activado** → `ENABLE_RERANKING=false`
2. **Límites muy altos** → Reducir `DENSE_SEARCH_LIMIT`
3. **Hardware insuficiente** → Verificar memoria/CPU
4. **Documentos muy largos** → Reducir `MAX_PARAGRAPH_LENGTH`

### Problema: Resultados poco relevantes
**Soluciones:**
1. **Activar reranking** → `ENABLE_RERANKING=true`
2. **Aumentar límites** → `DENSE_SEARCH_LIMIT=30`
3. **Más contexto** → `MAX_RESULTS_PER_QUERY=8`

### Problema: Memoria alta
**Soluciones:**
1. **Reducir batch sizes** → `EMBEDDING_BATCH_SIZE=16`
2. **Límites más bajos** → `DENSE_SEARCH_LIMIT=10`
3. **Cache selectivo** → `ENABLE_QUERY_CACHING=false`

## 📈 Monitoreo Continuo

### Dashboard Simple
```bash
# Ver estadísticas en tiempo real
curl http://localhost:8000/performance | jq
```

### Alertas de Rendimiento
Si `memory_usage_percent > 80%` → Reducir configuraciones
Si `avg_query_time > 3s` → Optimizar parámetros

## 🏗️ Optimizaciones Avanzadas

### Para Hardware Limitado
```env
# Configuración minimalista
ENABLE_RERANKING=false
DENSE_SEARCH_LIMIT=8
LEXICAL_SEARCH_LIMIT=8
MAX_RESULTS_PER_QUERY=3
EMBEDDING_BATCH_SIZE=8
```

### Para Hardware Potente
```env
# Aprovechar recursos
ENABLE_RERANKING=true
DENSE_SEARCH_LIMIT=50
LEXICAL_SEARCH_LIMIT=50
MAX_RESULTS_PER_QUERY=10
RERANK_BATCH_SIZE=64
```

## 🎯 Mejores Prácticas

1. **Siempre hacer benchmark** después de cambios
2. **Monitorear memoria** durante operación
3. **Ajustar gradualmente** - no cambiar todo a la vez
4. **Documentar cambios** que funcionan bien
5. **Considerar el trade-off** velocidad vs precisión

## 📞 Solución de Problemas Rápida

### Si nada funciona:
1. Reiniciar completamente:
   ```bash
   docker-compose down
   docker-compose up --build
   ```

2. Verificar logs:
   ```bash
   docker-compose logs backend
   ```

3. Configuración de emergencia ultra-rápida:
   ```env
   ENABLE_RERANKING=false
   DENSE_SEARCH_LIMIT=5
   LEXICAL_SEARCH_LIMIT=5
   MAX_RESULTS_PER_QUERY=2
   ```

## ✅ Checklist de Optimización

- [ ] Configurar `.env` según uso
- [ ] Reiniciar servicio
- [ ] Ejecutar benchmark
- [ ] Verificar tiempo < 2s
- [ ] Verificar resultados relevantes
- [ ] Documentar configuración final
