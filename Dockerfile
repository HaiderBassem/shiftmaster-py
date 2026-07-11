# ── Build Stage ──
FROM python:3.11-slim AS builder

WORKDIR /build
COPY shared/ /shared/
COPY pyproject.toml ./

RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev && \
    pip install --no-cache-dir --prefix=/install . /shared/

# ── Runtime Stage ──
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install runtime deps for psycopg2 (yoyo uses it)
RUN apt-get update && apt-get install -y --no-install-recommends libpq5 && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app
COPY --from=builder /install /usr/local
COPY app/ ./app/
COPY migrations/ ./migrations/
COPY yoyo.ini ./

# Ensure the script has Linux line endings and is executable
COPY scripts/start.sh ./scripts/
RUN sed -i 's/\r$//' scripts/start.sh && chmod +x scripts/start.sh

USER appuser

EXPOSE 8004

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8004/api/v1/health').raise_for_status()" || exit 1

ENTRYPOINT ["bash", "scripts/start.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8004", "--workers", "4"]
