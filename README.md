# Eventhub

Aplicación web para venta de entradas utilizada en la cursada 2025 de Ingeniería y Calidad de Software. UTN-FRLP

# Integrantes
- Máximo Preneste
- Tomás Martin
- Emiliano Di Grappa
- Santiago Natalichio Bestosini
- Lautaro Aubert
- Augusto Checa
## Dependencias

- python 3
- Django
- sqlite
- playwright
- ruff

## Instalar dependencias

`pip install -r requirements.txt`

## Iniciar la Base de Datos

`python manage.py migrate`

### Crear usuario admin

`python manage.py createsuperuser`

### Llenar la base de datos

`python manage.py loaddata fixtures/events.json`

## Iniciar app

`python manage.py runserver`

<!-- Prueba #1 de push para verificar el funcionamiento de CI -->