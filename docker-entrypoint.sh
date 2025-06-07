#!/bin/bash

echo "Aplicando migraciones..."
python manage.py migrate --noinput

echo "Creando directorios de archivos estáticos y media si no existen..."
mkdir -p staticfiles media

echo "Recolectando archivos estáticos..."
python manage.py collectstatic --noinput --clear

# Cargar datos iniciales si existen
if [ -d "fixtures" ]; then
    echo "Cargando fixtures..."
    python manage.py loaddata fixtures/*.json
fi

echo "Iniciando servidor..."
exec "$@" 