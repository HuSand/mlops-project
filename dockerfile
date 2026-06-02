# syntax=docker/dockerfile:1.6
FROM python:3.10-slim AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-serve.txt .
RUN pip install --user -r requirements-serve.txt


FROM python:3.10-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH=/home/app/.local/bin:$PATH \
    MODEL_PATH=/app/models/model.pkl

RUN groupadd --system app && useradd --system --gid app --home /home/app app \
    && mkdir -p /app /home/app && chown -R app:app /app /home/app

WORKDIR /app

COPY --from=builder --chown=app:app /root/.local /home/app/.local
COPY --chown=app:app app/ ./app/
# models/ may only contain .gitkeep; the model is fetched from GCS_MODEL_URI at startup.
COPY --chown=app:app models/ ./models/

USER app

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:80/').status==200 else 1)" || exit 1

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "80"]
