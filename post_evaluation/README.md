# Evaluación

Este módulo contiene las herramientas para evaluar la robustez y rendimiento del sistema RAG legal a través de tres pruebas principales (tests 1, 2, y 4)


## Pruebas de Evaluación

### Prueba 1: Robustez de Formato de Citas

Evalúa si el extractor de citas del sistema es robusto ante variaciones en el formato:
- "art." vs "artículo"
- "ley 7046" vs "ley nacional 7046"
- Formas abreviadas vs completas

**Funcionamiento:**
1. Extrae citas de textos originales
2. Modifica formatos usando GPT-4o-mini
3. Re-extrae citas de textos modificados
4. Compara y calcula métricas

### Prueba 2: Robustez ante cambios de redacción superficiales

Evalúa si el sistema RAG retorna resultados similares cuando la redacción cambia pero el significado legal se mantiene.

**Funcionamiento:**
1. Construye versión modificada de los jsons originales usando GPT-4o
2. Se corre el legal-rag con los jsons originales y el legal-rag-eval-version con los jsons modificados
3. Se construye con GPT-4o una serie de prompts en 3 niveles de 'especificidad' (preguntas más genéricas o más precisas a un documento específico)
4. Se mandan los prompts a cada backend, compara y calcula métricas

### Prueba 3: Sensibilidad a Cambios de Contenido

(Deprecado)

### Prueba 4: Precisión de búsqueda de un documento

Evalúa si el sistema trae un documento específico dado un prompt generado a partir de ese documento.

**Funcionamiento:**
1. Construímos una serie de prompts/preguntas según los jsons originales usando GPT-4o, 9 por documento, en 3 niveles de 'especificidad'.
2. Se corre el legal-rag con los jsons originales
3. Se mandan los prompts al backend, y miramos si aparece el documento deseado en el top 1 o top 5.

## Comandos de Terminal

```bash
# Para crear el dataset de una prueba
python 8_create_eval_dataset.py --test 4 --verbose --test4-input-path <path_a_jsons> --test4-output-path <path_de_output>

# Ejecutar la prueba 4
python 9_evaluate.py --test 4 --sample-size 100 --original-backend http://localhost:8000
```

## Configuración

1. **Azure OpenAI:** Credenciales en `configs/credentials_config.py`
2. **Backend RAG:** `docker compose up --build` para pruebas 2,3,4
3. **Datos:** Archivos json preprocesados en `datasets/fallos_json/`

## Resultados

Los resultados se organizan en `post_evaluation/evaluation_results/` con **estructura de carpetas por timestamp**: