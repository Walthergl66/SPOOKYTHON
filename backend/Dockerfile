FROM python:3.12-alpine3.24@sha256:69ebe56e2a764c399514a0a6117131cb730cc4d0e71e85c08deb9af74cbb9f41

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/opt/navira/backend/src

WORKDIR /opt/navira/backend

COPY requirements-container.lock ./
COPY src ./src
COPY data ./data

RUN python -m pip install --no-cache-dir --requirement requirements-container.lock \
    && adduser -D -H -u 10001 -s /sbin/nologin navira \
    && chown -R navira:navira /opt/navira

USER navira

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD ["python", "-c", "from urllib.request import urlopen; urlopen('http://127.0.0.1:8000/salud', timeout=2).read()"]

CMD ["uvicorn", "navira.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
