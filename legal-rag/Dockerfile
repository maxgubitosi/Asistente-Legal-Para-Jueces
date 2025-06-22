FROM python:3.11-slim-bookworm

# Carpeta base dentro del contenedor
WORKDIR /app

# Dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos todo el código
COPY . .

# Hacemos ejecutables los scripts (nueva ubicación)
RUN chmod +x /app/deployment/scripts/build_and_start.sh \
    && chmod +x /app/deployment/scripts/update_indexes.sh \
    && chmod +x /app/deployment/scripts/verify_setup.sh

# Configurar PYTHONPATH por defecto
ENV PYTHONPATH="/app"

# El CMD será sobrescrito por docker-compose
CMD ["bash"]

