import logging
import os
from collections.abc import Iterator
from contextlib import contextmanager


@contextmanager
def tracing_context(name: str, enabled: bool = False) -> Iterator[None]:
    """Configure LangSmith-compatible environment without requiring LangSmith."""
    if enabled:
        os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
        logging.getLogger(__name__).debug("trace.start", extra={"run_name": name})
    try:
        yield
    finally:
        if enabled:
            logging.getLogger(__name__).debug("trace.end", extra={"run_name": name})
