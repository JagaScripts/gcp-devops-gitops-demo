# Stage 1: Builder - verify and pre-compile Python application bytecode
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /build

COPY app/ ./app/
RUN python -m compileall -q /build/app

# Stage 2: Minimal non-root runtime image
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOST=0.0.0.0 \
    PORT=8080 \
    APP_ENV=production \
    SERVICE_NAME=gcp-devops-demo

# Create dedicated unprivileged user and group (UID/GID 10001)
RUN groupadd --gid 10001 appgroup \
    && useradd --uid 10001 --gid appgroup --home-dir /app --shell /usr/sbin/nologin appuser

WORKDIR /app

COPY --from=builder --chown=appuser:appgroup /build/app ./app

USER 10001:10001

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD ["python", "-c", "import urllib.request; resp = urllib.request.urlopen('http://127.0.0.1:8080/health', timeout=2); assert resp.status == 200"]

CMD ["python", "-m", "app.main"]
