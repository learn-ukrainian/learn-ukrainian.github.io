"""Process-local Prometheus metrics for Sources tool calls."""

from prometheus_client import CollectorRegistry, Counter, Histogram


class ToolMetrics:
    def __init__(self) -> None:
        # A private registry also permits isolated server imports in tests.
        self.registry = CollectorRegistry()
        labels = ("tool", "status_class")
        self.requests = Counter(
            "sources_tool_requests_total", "Completed Sources tool calls.", labels, registry=self.registry,
        )
        self.duration = Histogram(
            "sources_tool_duration_seconds", "Sources tool call latency including queue wait.",
            labels, registry=self.registry,
        )
        self.errors = Counter(
            "sources_tool_errors_total", "Failed Sources tool calls.", labels, registry=self.registry,
        )

    def observe(self, tool: str, status_class: str, duration: float) -> None:
        self.requests.labels(tool, status_class).inc()
        self.duration.labels(tool, status_class).observe(duration)
        if status_class == "error":
            self.errors.labels(tool, status_class).inc()
