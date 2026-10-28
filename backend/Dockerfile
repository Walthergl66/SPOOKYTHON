FROM python:3.12-slim@sha256:1148dbb014615300fa7e713b2f94f550c0d1c69780c0805f84f093ceee34dd0b

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/opt/navira/backend/src

WORKDIR /opt/navira/backend

COPY requirements-container.lock ./
COPY src ./src
COPY data ./data

RUN python -m pip install --no-cache-dir --requirement requirements-container.lock \
    && useradd --system --uid 10001 --home-dir /nonexistent --shell /usr/sbin/nologin navira \
    && chown -R navira:navira /opt/navira

USER navira

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD ["python", "-c", "from urllib.request import urlopen; urlopen('http://127.0.0.1:8000/salud', timeout=2).read()"]

CMD ["uvicorn", "navira.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
