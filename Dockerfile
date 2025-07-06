# Dockerfile para la API Contable con servicios de IA
FROM python:3.11-slim

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Configurar directorio de trabajo
WORKDIR /app

# Copiar archivos de dependencias
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código fuente
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini .

# Copiar archivos de configuración por ambiente
COPY .env.production ./
COPY .env.development ./
COPY .env.testing ./

# Variables de entorno por defecto
ENV PYTHONPATH=/app
ENV ENVIRONMENT=production
ENV DEBUG=false

# Puerto de la aplicación
EXPOSE 8000

# Script de inicio que permite configuración dinámica
COPY docker-entrypoint.sh ./
RUN chmod +x docker-entrypoint.sh

# Comando para iniciar la aplicación
CMD ["./docker-entrypoint.sh"]
