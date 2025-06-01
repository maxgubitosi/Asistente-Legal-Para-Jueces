## Verificación Automática de Contradicciones Judiciales con RAG
# TP_NLP
INSTALANDO EL PROYECTO
Pueeden hacer desde cualquier entorno nuevo de python:
         pip install -r requirements.txt 
         Y con eso se instalan las librerias necesarias para correr todo el proyecto. A medida que agreguemos más, estaría bueno ir completando el .txt ese asi es facil hacer el setup del proyecto en cualquier lugar.

# Correr los archivos numerados en el orden correspondiente
0. Antes de correr código, descargar la carpeta de toni y colocarla dentro de la carpeta `datasets` con el nombre `2024`. También se debe crear un archivo credentials_config.py en la carpeta configs, siguiendo el template de template_config.py con las credenciales personales de Azure.

1. **1_normalization.ipynb**: 
   - Normaliza los textos de los fallos judiciales.
   - los croppea y elimina datos irrelevantes.
   - devuelve una carpeta con los jsons de los fallos dados
2. **2_embeddings.ipynb**: 
   - Crear archivo en configs con datos de la API.
   - Seleccionar los parametros
   - Crea los embeddings de los textos de los fallos judiciales.
   - Utiliza la librería `sentence_transformers` para generar representaciones vectoriales de los textos.

# Notas
- esta la clase tutorial de RAG aca para usar de referencia
- el flujo actual solo carga los fallos de febrero, son 10.