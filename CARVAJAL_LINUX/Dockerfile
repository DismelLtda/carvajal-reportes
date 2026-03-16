# ============================================================================
# CARVAJAL VENTAS - Dockerfile para Producción
# Base: Python 3.11 Alpine (ligero ~100MB)
# ============================================================================

FROM python:3.11-alpine

# Información de imagen
LABEL maintainer="Soporte CARVAJAL <soporte@dismelltda.com>"
LABEL description="CARVAJAL VENTAS - Sistema de procesamiento de reportes"

# Variables de entorno para Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Directorio de trabajo
WORKDIR /app

# ============================================================================
# Instalar dependencias del sistema
# ============================================================================
RUN apk add --no-cache \
    curl \
    postgresql-client \
    gcc \
    musl-dev \
    libpq-dev \
    && rm -rf /var/cache/apk/*

# ============================================================================
# Copiar archivos de requisitos
# ============================================================================
COPY requirements.txt .

# ============================================================================
# Instalar dependencias de Python
# ============================================================================
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt

# ============================================================================
# Copiar código fuente
# ============================================================================
COPY . .

# ============================================================================
# Crear directorios necesarios
# ============================================================================
RUN mkdir -p \
    /app/data/descargas_ventas \
    /app/data/descargas_inventario \
    /app/data/procesados_ventas \
    /app/data/procesados_inventario \
    /app/logs \
    && chmod -R 755 /app/data /app/logs

# ============================================================================
# Health check
# ============================================================================
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:10000/health || exit 1

# ============================================================================
# Exponer puerto
# ============================================================================
EXPOSE 10000

# ============================================================================
# Comando por defecto (inicializar BD y correr API)
# ============================================================================
CMD ["sh", "-c", "python init_db.py && python run_api.py"]
