# ETAPA 1: Constructor (Builder)
FROM python:3.11-slim-bookworm as builder

# Cambiamos el directorio de trabajo temporal
WORKDIR /build

RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN pip install --no-cache-dir -r requirements.txt


# ETAPA 2: Tiempo de Ejecución (Runtime)
FROM python:3.11-slim-bookworm

# CAMBIO CRÍTICO 1: Usamos una carpeta raíz neutra "/code"
WORKDIR /code

RUN apt-get update && apt-get install -y \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# CAMBIO CRÍTICO 2: Copiamos el código DENTRO de una carpeta 'app'
# Esto crea la estructura /code/app/main.py
COPY . ./app

# Permisos
RUN useradd -m appuser && chown -R appuser /code
USER appuser

# CAMBIO CRÍTICO 3: Agregamos el directorio actual al PYTHONPATH
# Para que Python sepa buscar paquetes aquí
ENV PYTHONPATH="/code:$PYTHONPATH"

EXPOSE 5000

# CAMBIO CRÍTICO 4: Volvemos a llamar al módulo como paquete "app.main"
# Como estamos en /code, ahora sí existe la carpeta "app"
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app.main:app"]