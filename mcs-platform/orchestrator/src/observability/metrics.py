"""Prometheus metrics."""

from prometheus_client import Counter, Histogram

# Orchestrator metrics
orchestrator_runs_total = Counter(
    "orchestrator_runs_total",
    "Total number of orchestration runs",
    ["status", "graph_name"],
)

orchestrator_duration_seconds = Histogram(
    "orchestrator_duration_seconds",
    "Orchestration duration in seconds",
    ["graph_name", "step"],
    buckets=[0.1, 0.5, 1.0, 5.0, 10.0, 30.0, 60.0],
)

orchestrator_errors_total = Counter(
    "orchestrator_errors_total",
    "Total number of orchestration errors",
    ["error_code"],
)

# Dify metrics
dify_calls_total = Counter(
    "dify_calls_total",
    "Total number of Dify API calls",
    ["app_key", "status"],
)

# ERP metrics
erp_calls_total = Counter(
    "erp_calls_total",
    "Total number of ERP API calls",
    ["status"],
)

# Idempotency metrics
idempotency_hits_total = Counter(
    "idempotency_hits_total",
    "Total number of idempotency cache hits",
)

