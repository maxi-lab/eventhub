# Usar una imagen base oficial de Python con la versión más reciente y estable
# Se usa la variante slim para reducir el tamaño de la imagen
FROM python:3.12-slim

# Establecer variables de entorno
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    # pip
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100

# Establecer el directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema necesarias
# Se combinan los comandos para reducir capas y se limpia la caché de apt
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements.txt primero para aprovechar la caché de capas de Docker
COPY requirements.txt .

# Instalar dependencias de Python
# Se usa --no-cache-dir para reducir el tamaño de la imagen
RUN pip install --no-cache-dir -r requirements.txt

# Crear directorios necesarios
RUN mkdir -p /app/staticfiles /app/media

# Copiar el código de la aplicación
COPY . .

# Script de entrada para iniciar la aplicación
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Crear un usuario no root para ejecutar la aplicación y asignar permisos
RUN adduser --disabled-password --gecos '' django_user && \
    chown -R django_user:django_user /app && \
    chmod -R 755 /app/staticfiles /app/media

# Cambiar al usuario no root
USER django_user

# Exponer el puerto que usará Django
EXPOSE 8000

# Comando para ejecutar la aplicación
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"] 