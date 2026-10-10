# Imagen base oficial, mantenida y con versión concreta fijada
FROM python:3.12.9-slim-bookworm

# Metadatos del contenedor
LABEL maintainer="EF+ Team"
LABEL description="Plataforma de Educación Física Funcional"

# Variables de entorno para ejecución en producción
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    EF_ENV=production \
    EF_HOST=0.0.0.0 \
    EF_PORT=8080 \
    PORT=8080 \
    EF_DATA_DIR=/app/datos

# Instalar curl para healthchecks del orquestador y limpiar lista de paquetes
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Crear usuario y grupo sin privilegios para ejecución segura
RUN groupadd -r -g 1001 appgroup \
    && useradd -r -u 1001 -g appgroup -d /app -s /sbin/nologin appuser

# Directorio de trabajo
WORKDIR /app

# Copiar el código fuente de la aplicación
COPY . /app

# Crear directorio para persistencia de datos SQLite y asignar permisos al usuario sin privilegios
RUN mkdir -p /app/datos \
    && chown -R appuser:appgroup /app

# Cambiar a usuario sin privilegios
USER appuser

# Declarar exactamente un único puerto estándar para Hexper Ops y Dokploy
EXPOSE 8080

# Healthcheck consultando directamente la IP interna 127.0.0.1 (evita resolución IPv6)
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://127.0.0.1:8080/ || exit 1

# Comando principal de larga duración: ejecuta migraciones/esquema y arranca el servidor HTTP
CMD ["python", "app.py"]
