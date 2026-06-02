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


def setup_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        stream=sys.stdout,
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] trace=%(trace_id)s %(name)s: %(message)s",
    )


class TraceAdapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        kwargs.setdefault("extra", {})["trace_id"] = get_trace_id()
        return msg, kwargs


def get_logger(name: str) -> TraceAdapter:
    return TraceAdapter(logging.getLogger(name), {})
