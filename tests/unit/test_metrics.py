"""Tests for metrics collector."""
import pytest
from dzcz_merchant_ops.monitor.metrics import MetricsCollector


def test_metrics_collector_initialization():
    """Test MetricsCollector initialization."""
    collector = MetricsCollector()
    assert collector.counters == {}
    assert collector.gauges == {}
    assert collector.histograms == {}


def test_metrics_collector_increment():
    """Test counter increment."""
    collector = MetricsCollector()

    collector.increment("requests")
    assert collector.counters["requests"] == 1

    collector.increment("requests")
    assert collector.counters["requests"] == 2

    collector.increment("requests", 5)
    assert collector.counters["requests"] == 7


def test_metrics_collector_set_gauge():
    """Test gauge setting."""
    collector = MetricsCollector()

    collector.set_gauge("cpu_usage", 50.0)
    assert collector.gauges["cpu_usage"] == 50.0

    collector.set_gauge("cpu_usage", 75.0)
    assert collector.gauges["cpu_usage"] == 75.0


def test_metrics_collector_record_histogram():
    """Test histogram recording."""
    collector = MetricsCollector()

    collector.record_histogram("response_time", 1.0)
    collector.record_histogram("response_time", 2.0)
    collector.record_histogram("response_time", 3.0)

    assert collector.histograms["response_time"] == [1.0, 2.0, 3.0]


def test_metrics_collector_get_summary_empty():
    """Test summary with no data."""
    collector = MetricsCollector()
    summary = collector.get_summary()

    assert summary["counters"] == {}
    assert summary["gauges"] == {}
    assert summary["histograms"] == {}


def test_metrics_collector_get_summary_with_data():
    """Test summary with data."""
    collector = MetricsCollector()

    collector.increment("requests", 10)
    collector.set_gauge("cpu_usage", 50.0)
    collector.record_histogram("response_time", 1.0)
    collector.record_histogram("response_time", 2.0)
    collector.record_histogram("response_time", 3.0)

    summary = collector.get_summary()

    assert summary["counters"]["requests"] == 10
    assert summary["gauges"]["cpu_usage"] == 50.0
    assert summary["histograms"]["response_time"]["count"] == 3
    assert summary["histograms"]["response_time"]["mean"] == 2.0
    assert summary["histograms"]["response_time"]["median"] == 2.0
    assert summary["histograms"]["response_time"]["min"] == 1.0
    assert summary["histograms"]["response_time"]["max"] == 3.0


def test_metrics_collector_get_summary_with_p95():
    """Test summary with p95 calculation."""
    collector = MetricsCollector()

    # Add 20 values to trigger p95 calculation
    for i in range(20):
        collector.record_histogram("response_time", float(i))

    summary = collector.get_summary()

    # p95 should be approximately 18.0 (95th percentile of 0-19)
    assert summary["histograms"]["response_time"]["p95"] is not None
    assert 17.0 <= summary["histograms"]["response_time"]["p95"] <= 19.0
