"""Tests for diagnostics export."""
import pytest
import json
from pathlib import Path
from dzcz_merchant_ops.diagnostics import DiagnosticsExporter


@pytest.fixture
def tmp_data_dir(tmp_path):
    """Create temporary data directory with test data."""
    # Create artifact directory
    artifacts_dir = tmp_path / "artifacts" / "test-run-123"
    artifacts_dir.mkdir(parents=True)

    # Create test files
    (artifacts_dir / "final.png").write_bytes(b"fake-png")
    (artifacts_dir / "result.json").write_text(json.dumps({
        "ok": True,
        "confirmed": True,
    }))
    (artifacts_dir / "error.txt").write_text("Test error")

    # Create run record
    runs_dir = tmp_path / "runs"
    runs_dir.mkdir()
    (runs_dir / "test-run-123.json").write_text(json.dumps({
        "run_id": "test-run-123",
        "workflow_id": "test.workflow",
        "status": "failed",
    }))

    return tmp_path


@pytest.fixture
def exporter(tmp_data_dir):
    """Create DiagnosticsExporter instance."""
    return DiagnosticsExporter(tmp_data_dir)


def test_export_diagnostics(exporter, tmp_data_dir):
    """Test exporting diagnostics package."""
    export_path = tmp_data_dir / "export"
    export_path.mkdir()

    exporter.export("test-run-123", export_path)

    # Verify export files exist
    assert (export_path / "run_info.json").exists()
    assert (export_path / "artifacts").exists()
    assert (export_path / "artifacts" / "final.png").exists()
    assert (export_path / "artifacts" / "result.json").exists()


def test_export_diagnostics_with_summary(exporter, tmp_data_dir):
    """Test export includes summary."""
    export_path = tmp_data_dir / "export"
    export_path.mkdir()

    exporter.export("test-run-123", export_path)

    # Verify summary
    summary_path = export_path / "summary.json"
    assert summary_path.exists()

    with open(summary_path) as f:
        summary = json.load(f)

    assert summary["run_id"] == "test-run-123"
    assert "exported_files" in summary


def test_export_nonexistent_run(exporter, tmp_data_dir):
    """Test exporting nonexistent run raises error."""
    export_path = tmp_data_dir / "export"
    export_path.mkdir()

    with pytest.raises(FileNotFoundError):
        exporter.export("nonexistent-run", export_path)


def test_list_runs(exporter, tmp_data_dir):
    """Test listing available runs."""
    runs = exporter.list_runs()
    assert len(runs) == 1
    assert runs[0]["run_id"] == "test-run-123"