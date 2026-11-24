"""Lightweight HTTP microservice with JSON /health endpoint and structured logging."""

from __future__ import annotations

import json
import logging
import os
import signal
import sys
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from app import __version__


class JsonLogFormatter(logging.Formatter):
    """Formats log records as single-line JSON for Cloud Logging / stdout."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "severity": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        extra = getattr(record, "extra_fields", None)
        if isinstance(extra, dict):
            payload.update(extra)
        return json.dumps(payload, ensure_ascii=False)


def configure_logging() -> logging.Logger:
    """Configure structured JSON logging on stdout."""
    logger = logging.getLogger("gcp_devops_demo.app")
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JsonLogFormatter())
        logger.addHandler(handler)
    logger.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())
    logger.propagate = False
    return logger


LOGGER = configure_logging()


def build_health_payload() -> dict[str, Any]:
    """Return the JSON payload for the /health endpoint."""
    return {
        "status": "ok",
        "service": os.getenv("SERVICE_NAME", "gcp-devops-demo"),
        "version": os.getenv("APP_VERSION", __version__),
        "environment": os.getenv("APP_ENV", "dev"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def build_root_payload() -> dict[str, Any]:
    """Return the JSON payload for the root endpoint."""
    return {
        "service": os.getenv("SERVICE_NAME", "gcp-devops-demo"),
        "version": os.getenv("APP_VERSION", __version__),
        "environment": os.getenv("APP_ENV", "dev"),
        "endpoints": ["/", "/health"],
    }


class MicroserviceHandler(BaseHTTPRequestHandler):
    """HTTP request handler serving JSON responses."""

    server_version = f"gcp-devops-demo/{__version__}"

    def _send_json(self, status: HTTPStatus, payload: dict[str, Any]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(int(status))
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler naming
        path = self.path.split("?", 1)[0]
        if path == "/health":
            self._send_json(HTTPStatus.OK, build_health_payload())
            LOGGER.info(
                "request_handled",
                extra={"extra_fields": {"method": "GET", "path": path, "status": 200}},
            )
            return

        if path == "/":
            self._send_json(HTTPStatus.OK, build_root_payload())
            LOGGER.info(
                "request_handled",
                extra={"extra_fields": {"method": "GET", "path": path, "status": 200}},
            )
            return

        self._send_json(HTTPStatus.NOT_FOUND, {"error": "not_found", "path": path})
        LOGGER.warning(
            "route_not_found",
            extra={"extra_fields": {"method": "GET", "path": path, "status": 404}},
        )

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        # Suppress default stderr access log in favor of structured JSON logging.
        return


def create_server(host: str = "0.0.0.0", port: int = 8080) -> ThreadingHTTPServer:
    """Create a configured ThreadingHTTPServer instance."""
    return ThreadingHTTPServer((host, port), MicroserviceHandler)


def run() -> None:
    """Start the HTTP server and handle graceful shutdown signals."""
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8080"))
    server = create_server(host=host, port=port)

    def _shutdown_handler(signum: int, _frame: Any) -> None:
        LOGGER.info(
            "server_shutdown_requested",
            extra={"extra_fields": {"signal": signum}},
        )
        server.shutdown()

    signal.signal(signal.SIGTERM, _shutdown_handler)
    signal.signal(signal.SIGINT, _shutdown_handler)

    LOGGER.info(
        "server_started",
        extra={"extra_fields": {"host": host, "port": port}},
    )
    try:
        server.serve_forever()
    finally:
        server.server_close()


if __name__ == "__main__":
    run()
