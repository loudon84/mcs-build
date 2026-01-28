"""LangSmith tracing integration."""

import os
from contextlib import contextmanager
from typing import Any, Optional

from langchain_core.tracers import LangChainTracer
from langchain_core.tracers.context import tracing_v2_enabled

from mcs_orchestrator.observability.redaction import redact_dict
from mcs_orchestrator.settings import Settings


class LangSmithTracer:
    """LangSmith tracer wrapper."""

    def __init__(self, settings: Settings):
        """Initialize LangSmith tracer."""
        self.settings = settings
        self.enabled = settings.langchain_tracing_v2 and bool(settings.langsmith_api_key)

        if self.enabled:
            os.environ["LANGCHAIN_TRACING_V2"] = "true"
            os.environ["LANGCHAIN_API_KEY"] = settings.langsmith_api_key
            os.environ["LANGCHAIN_PROJECT"] = settings.langchain_project

    @contextmanager
    def trace_span(self, step_name: str, metadata: Optional[dict[str, Any]] = None):
        """Create a trace span."""
        if not self.enabled:
            yield
            return

        # Redact metadata before tracing
        if metadata:
            metadata = redact_dict(metadata)

        with tracing_v2_enabled():
            tracer = LangChainTracer(project_name=self.settings.langchain_project)
            # LangGraph/LangChain will automatically use the tracer
            yield

