"""
Lightweight observability helpers for pipeline-tools.

- Structured logging (console or JSON) with a per-run request ID.
- Optional StatsD-style metrics (UDP) controlled via env or CLI.
"""
from __future__ import annotations

import json
import logging
import os
import socket
import time
import uuid
from dataclasses import dataclass
from typing import Any, Optional


_LOGGER_NAME = "pipeline_tools"


def _default_request_id() -> str:
    return os.environ.get("PIPELINE_TOOLS_REQUEST_ID") or uuid.uuid4().hex


@dataclass
class MetricsSink:
    """Very small StatsD/UDP client."""

    host: str
    port: int
    enabled: bool = False

    def send(self, payload: str) -> None:
        if not self.enabled:
            return
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.sendto(payload.encode("utf-8"), (self.host, self.port))
        except OSError:
            # Metrics should never break the CLI.
            pass


@dataclass
class ObservabilityState:
    request_id: str
    log_format: str
    log_level: str
    metrics: MetricsSink
    service: str


_STATE = ObservabilityState(
    request_id=_default_request_id(),
    log_format="console",
    log_level="WARNING",  # Changed from INFO - end users shouldn't see technical logs
    metrics=MetricsSink(host="", port=0, enabled=False),
    service="pipely",
)


class JsonFormatter(logging.Formatter):
    """Log records as single-line JSON for shipping to aggregators."""

    def format(self, record: logging.LogRecord) -> str:  # pragma: no cover - formatting glue
        payload = {
            "level": record.levelname,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", _STATE.request_id),
            "service": getattr(record, "service", _STATE.service),
            "time": int(time.time() * 1000),
        }
        if record.args and isinstance(record.args, dict):
            payload.update(record.args)
        for extra_key in ("event", "command", "status"):
            if hasattr(record, extra_key):
                payload[extra_key] = getattr(record, extra_key)
        return json.dumps(payload, ensure_ascii=True)


def _configure_logging(log_level: str, log_format: str, service: str) -> None:
    logger = logging.getLogger(_LOGGER_NAME)
    logger.setLevel(log_level.upper())
    for handler in list(logger.handlers):
        logger.removeHandler(handler)
    handler = logging.StreamHandler()
    if log_format == "json":
        handler.setFormatter(JsonFormatter())
    else:
        formatter = logging.Formatter(
            fmt="%(levelname)s %(message)s [request_id=%(request_id)s]",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = False
    # Stash defaults on the logger for formatters to pick up.
    logger.request_id = _STATE.request_id  # type: ignore[attr-defined]
    logger.service = service  # type: ignore[attr-defined]


def _parse_metrics_endpoint(value: Optional[str]) -> MetricsSink:
    if not value:
        return MetricsSink(host="", port=0, enabled=False)
    raw = value.replace("statsd://", "")
    host, _, port_str = raw.partition(":")
    try:
        port = int(port_str) if port_str else 8125
    except ValueError:
        port = 8125
    return MetricsSink(host=host or "127.0.0.1", port=port, enabled=True)


def init_observability(
    *,
    log_level: str = "WARNING",  # Changed from INFO - end users shouldn't see technical logs
    log_format: str = "console",
    request_id: Optional[str] = None,
    metrics_endpoint: Optional[str] = None,
    service: str = "pipely",
) -> None:
    """
    Configure logging/metrics for this process. Safe to call multiple times.
    """
    if request_id:
        _STATE.request_id = request_id
    _STATE.log_level = log_level
    _STATE.log_format = log_format
    _STATE.metrics = _parse_metrics_endpoint(
        metrics_endpoint or os.environ.get("PIPELINE_TOOLS_METRICS")
    )
    _STATE.service = service
    _configure_logging(log_level, log_format, service)


def get_request_id() -> str:
    return _STATE.request_id


def _clean_fields(fields: dict[str, Any]) -> dict[str, Any]:
    """
    Avoid clobbering LogRecord reserved keys (e.g. args/message/levelname).
    """
    reserved = {
        "name",
        "msg",
        "args",
        "levelname",
        "levelno",
        "pathname",
        "filename",
        "module",
        "exc_info",
        "exc_text",
        "stack_info",
        "lineno",
        "funcName",
        "created",
        "msecs",
        "relativeCreated",
        "thread",
        "threadName",
        "processName",
        "process",
        "message",
    }
    cleaned: dict[str, Any] = {}
    for key, value in fields.items():
        if key in reserved:
            cleaned[f"field_{key}"] = value
        else:
            cleaned[key] = value
    return cleaned


def log_event(event: str, *, level: int = logging.INFO, **fields: Any) -> None:
    logger = logging.getLogger(_LOGGER_NAME)
    extra = {"event": event, "request_id": _STATE.request_id, "service": _STATE.service}
    logger.log(level, event, extra={**extra, **_clean_fields(fields)})


def log_exception(event: str, exc: Exception, **fields: Any) -> None:
    logger = logging.getLogger(_LOGGER_NAME)
    extra = {"event": event, "request_id": _STATE.request_id, "service": _STATE.service}
    logger.error(f"{event}: {exc}", extra={**extra, **_clean_fields(fields)})


def record_timing(metric: str, milliseconds: float) -> None:
    """
    Emit a StatsD timing metric (ms). No-op if metrics are disabled.
    """
    if not _STATE.metrics.enabled:
        return
    payload = f"{metric}:{int(milliseconds)}|ms"
    _STATE.metrics.send(payload)


def increment(metric: str, value: int = 1) -> None:
    """
    Emit a StatsD counter. No-op if metrics are disabled.
    """
    if not _STATE.metrics.enabled:
        return
    payload = f"{metric}:{value}|c"
    _STATE.metrics.send(payload)


def timed(metric: str):
    """
    Context manager for measuring elapsed time in ms and emitting a metric.
    """

    class _Timer:
        def __enter__(self):
            self.start = time.time()
            return self

        def __exit__(self, exc_type, exc, tb):
            elapsed_ms = (time.time() - self.start) * 1000
            record_timing(metric, elapsed_ms)

    return _Timer()
