# Notebooks de Legal RAG

Este directorio contiene notebooks para procesar fallos judiciales y crear un sistema RAG (Retrieval Augmented Generation) legal.

## Notebooks

### 1_normalizacion_pdf.ipynb
Normaliza PDFs de fallos judiciales:
- Recorta encabezados y pies de página
- Extrae texto limpio
- Unifica párrafos y estructura secciones
- Genera archivos JSON normalizados con estructura estandarizada
- Requiere carpeta `datasets/2024` con PDFs de fallos

### 2_embeddings.ipynb
Genera embeddings para búsqueda semántica:
- Carga JSONs normalizados
- Divide texto en chunks con overlapping
- Crea embeddings usando Azure OpenAI o modelos locales
- Almacena vectores en índice FAISS
- Permite probar consultas básicas

### 3_rag.ipynb
Implementa sistema RAG completo:
- Carga vectorstore FAISS
- Recupera fragmentos relevantes para consultas
- Genera respuestas contextualizadas con Azure OpenAI
- Incluye sistema de evaluación de calidad con ELO

### 4_article_extraction.ipynb
Extrae citas legales de los fallos:
- Identifica artículos citados mediante regex y LLM
- Estandariza fuentes legales (leyes, códigos, etc.)
- Estructura citas por secciones del documento
- Genera JSONs con citas estructuradas

### 5_summary.ipynb
Genera resúmenes automáticos de fallos:
- Crea síntesis ejecutivas usando Azure OpenAI
- Extrae ideas centrales de cada fallo
- Incluye metadatos de reducción y secciones analizadas
- Permite regenerar resúmenes específicos

### 6_complete_json_build.ipynb
Unifica datos en estructura final:
- Combina contenido, citas y resúmenes
- Crea JSONs consolidados con toda la información
- Mantiene estructura de carpetas original

### 7_limpiar_datos_json.ipynb
Limpia y estandariza datos:
- Normaliza citas de artículos legales
- Elimina encabezados redundantes en ideas centrales
- Genera estadísticas de artículos citados
- Reorganiza referencias a fuentes legales correctas

## Requisitos
- Python con librerías especificadas en requirements.txt
- Credenciales de Azure OpenAI en archivo `configs/credentials_config.py`
- Estructura de carpetas datasets/ para archivos de entrada/salida

## Flujo de ejecución
Ejecutar notebooks en orden numérico para procesar desde PDFs crudos hasta sistema RAG completo con extracción de información legal estructurada.
