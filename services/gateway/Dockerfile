# ── Build Stage ──
FROM python:3.11-slim AS builder

WORKDIR /build
COPY shared/ /shared/
COPY services/gateway/pyproject.toml ./

RUN pip install --no-cache-dir --prefix=/install . /shared/

# ── Runtime Stage ──
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app
COPY --from=builder /install /usr/local
COPY services/gateway/app/ ./app/

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health').raise_for_status()" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
