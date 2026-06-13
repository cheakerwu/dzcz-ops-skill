"""Metrics collection for monitoring."""
import statistics
from typing import Dict, Any, List


class MetricsCollector:
    """Collector for various metrics.

    Supports counters, gauges, and histograms.
    """

    def __init__(self) -> None:
        """Initialize metrics collector."""
        self.counters: Dict[str, int] = {}
        self.gauges: Dict[str, float] = {}
        self.histograms: Dict[str, List[float]] = {}

    def increment(self, name: str, value: int = 1) -> None:
        """Increment a counter.

        Args:
            name: Counter name
            value: Value to increment by
        """
        self.counters[name] = self.counters.get(name, 0) + value

    def set_gauge(self, name: str, value: float) -> None:
        """Set a gauge value.

        Args:
            name: Gauge name
            value: Gauge value
        """
        self.gauges[name] = value

    def record_histogram(self, name: str, value: float) -> None:
        """Record a histogram value.

        Args:
            name: Histogram name
            value: Value to record
        """
        if name not in self.histograms:
            self.histograms[name] = []
        self.histograms[name].append(value)

    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary.

        Returns:
            Dictionary with counters, gauges, and histograms
        """
        summary: Dict[str, Any] = {
            "counters": self.counters.copy(),
            "gauges": self.gauges.copy(),
            "histograms": {},
        }

        for name, values in self.histograms.items():
            if values:
                histogram_summary: Dict[str, Any] = {
                    "count": len(values),
                    "mean": statistics.mean(values),
                    "median": statistics.median(values),
                    "min": min(values),
                    "max": max(values),
                    "p95": None,
                }

                # Calculate p95 if enough data points
                if len(values) >= 20:
                    histogram_summary["p95"] = statistics.quantiles(values, n=20)[18]

                summary["histograms"][name] = histogram_summary

        return summary
