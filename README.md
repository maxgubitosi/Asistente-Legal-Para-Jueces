# Asistente Legal Para Jueces

**Autores:** Antonio Santiago Tepsich, Máximo Gubitosi, Gabor Gorondi y Bruno Castagnino Rossi

Este repositorio agrupa todo el trabajo realizado para construir, evaluar y desplegar un sistema *Retrieval-Augmented Generation* (RAG) especializado en jurisprudencia argentina.

## Estructura del repositorio

| Carpeta | Descripción |
|---------|-------------|
| `legal-rag/` | Proyecto final listo para producción: backend (FastAPI), frontend (Streamlit) y un subconjunto del dataset. Contiene **su propio README** con los pasos detallados para construir índices, configurar variables de entorno y ejecutar el stack mediante *docker-compose*. |
| `legal-rag-eval-version/` | Clon de `legal-rag` ampliado para correr varias configuraciones de RAG **en paralelo** sobre versiones modificadas del dataset. Lo usamos para comparar estrategias de búsqueda, distintos LLMs y parámetros. |
| `post_evaluation/` | Código y resultados de la fase de evaluación offline. Dentro encontrarás un archivo `reporte_evaluacion.md` donde explicamos la metodología y las métricas utilizadas. |
| `pre-processing/` | Scripts exploratorios de limpieza de PDFs (legacy). El pipeline definitivo está documentado en `legal-rag/Notebooks/`. |

## Flujo de pre-procesamiento
Los cuadernos Jupyter bajo `legal-rag/Notebooks` muestran paso a paso cómo transformamos los fallos en PDF al formato JSON enriquecido que consume el backend en producción.

## Datos
Por motivos de confidencialidad sólo incluimos **unas pocas sentencias** para que puedas levantar el sistema y probar su funcionamiento. Durante el desarrollo trabajamos con **más de 160 fallos reales**. Si necesitás acceso completo para investigación o pruebas, no dudes en contactarnos y coordinamos el envío.

## Cómo empezar
Para correr la aplicación:
1. Lee el README dentro de `legal-rag/`.
2. Sigue las instrucciones allí indicadas (crear entorno, construir índices y lanzar `docker-compose`).

Con eso obtendrás el backend, el frontend y los índices mínimos para explorar las funcionalidades del sistema.
