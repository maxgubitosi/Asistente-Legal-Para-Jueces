FROM python:3.11-slim

# Carpeta base dentro del contenedor
WORKDIR /app

# Dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos todo el código (app/, scripts/, entrypoint)
COPY . .

# Hacemos ejecutable el entrypoint y scripts
RUN chmod +x /app/entrypoint.sh /app/scripts/build_and_start.sh /app/build_indexes.sh /app/scripts/update_indexes.sh /app/verify_setup.sh

CMD ["/app/entrypoint.sh"]

