## Verificación Automática de Contradicciones Judiciales con RAG
# TP_NLP
INSTALANDO EL PROYECTO
Pueeden hacer desde cualquier entorno nuevo de python:
         pip install -r requirements.txt 
         Y con eso se instalan las librerias necesarias para correr todo el proyecto. A medida que agreguemos más, estaría bueno ir completando el .txt ese asi es facil hacer el setup del proyecto en cualquier lugar.

Para correr el clean_pdfs.py:
1. Descargar zip de toni y descomprimir el archivo
2. Colocar la carpeta en la raíz del proyecto
3. Correr el script clean_pdfs.py para crear la carpeta "clean_txt" con los pdfs limpios:
        $ python pre-processing/clean_pdfs.py --pdf_dir datasets/2024 --out_dir datasets/clean_txt


# Notas
- Por ahora usemos clean_txt, el otro agrega el formato del texto (si es negritas, etc), no anda perfecto y no se si aporta información relevante.
- esta la clase tutorial de RAG aca para usar de referencia
- en embeddings estoy con la primera parte, por ahora no hago los resumenes de cada fallo