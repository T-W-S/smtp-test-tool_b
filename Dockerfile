# Stage 1: Builder — install dependencies
FROM python:3.12-slim AS builder

WORKDIR /build

RUN pip install --no-cache-dir -U pip

COPY pyproject.toml ./
COPY src/ ./src/

RUN pip install --no-cache-dir --prefix=/install .

# Stage 2: Runtime
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /install /usr/local

COPY src/ ./src/
COPY main.py ./

RUN mkdir -p /data/config /data/logs && \
    chmod -R 777 /data

ENV SMTP_CONFIG_DIR=/data/config
ENV SMTP_LOG_DIR=/data/logs
ENV LOG_LEVEL=INFO
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:5000/health_check || exit 1

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--reuse-port", "--workers=1", "--access-logfile=-", "--error-logfile=-", "smtp_tool:create_app()"]
