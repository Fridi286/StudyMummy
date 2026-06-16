"""
Strukturiertes Logging für Observability (Übungsblatt 05).
Jeder Agent-Durchlauf erhält eine trace_id.
"""
import logging
import sys
import uuid
from contextvars import ContextVar
from typing import Optional

trace_id_var: ContextVar[Optional[str]] = ContextVar("trace_id", default=None)


def get_trace_id() -> str:
    tid = trace_id_var.get()
    if tid is None:
        tid = str(uuid.uuid4())[:8]
        trace_id_var.set(tid)
    return tid


class TraceIdFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        if not hasattr(record, "trace_id"):
            record.trace_id = get_trace_id()
        return super().format(record)


def setup_logging(level: str = "INFO") -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        TraceIdFormatter(
            "%(asctime)s [%(levelname)s] trace=%(trace_id)s %(name)s: %(message)s"
        )
    )
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))


class TraceAdapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        kwargs.setdefault("extra", {})["trace_id"] = get_trace_id()
        return msg, kwargs


def get_logger(name: str) -> TraceAdapter:
    return TraceAdapter(logging.getLogger(name), {})
