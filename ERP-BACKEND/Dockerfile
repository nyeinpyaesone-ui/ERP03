# syntax=docker/dockerfile:1
FROM python:3.12.13-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN addgroup --system app && adduser --system --ingroup app app

COPY requirements.txt dev-requirements.txt ./
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir --prefix=/opt/appdeps -r requirements.txt -r dev-requirements.txt

FROM python:3.12.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH=/opt/appdeps/bin:$PATH \
    PYTHONPATH=/opt/appdeps/lib/python3.12/site-packages

WORKDIR /app

RUN groupadd -g 1000 app && useradd -u 1000 -g app -s /bin/sh app \
    && mkdir -p /app/.local && chown -R app:app /app/.local

COPY --chown=app:app --from=builder /opt/appdeps /opt/appdeps
COPY --chown=app:app app ./app
COPY --chown=app:app alembic ./alembic
COPY --chown=app:app alembic.ini ./

USER app

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=3s --start-period=15s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/v1/healthz', timeout=2)" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
