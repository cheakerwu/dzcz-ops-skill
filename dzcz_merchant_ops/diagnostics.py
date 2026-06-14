"""Remote diagnostics export for troubleshooting."""
from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any


__all__ = ["DiagnosticsExporter"]


class DiagnosticsExporter:
    """Export diagnostic packages for remote troubleshooting."""

    def __init__(self, data_dir: Path):
        """Initialize diagnostics exporter.

        Args:
            data_dir: Base data directory
        """
        self.data_dir = Path(data_dir)
        self.artifacts_dir = self.data_dir / "artifacts"
        self.runs_dir = self.data_dir / "runs"

    def list_runs(self) -> list[dict[str, Any]]:
        """List all available runs.

        Returns:
            List of run summaries
        """
        runs = []
        for run_file in self.runs_dir.glob("*.json"):
            try:
                with open(run_file, encoding="utf-8") as f:
                    data = json.load(f)
                runs.append({
                    "run_id": data.get("run_id", run_file.stem),
                    "workflow_id": data.get("workflow_id"),
                    "status": data.get("status"),
                })
            except (json.JSONDecodeError, KeyError):
                continue

        return runs

    def export(self, run_id: str, export_path: Path) -> Path:
        """Export diagnostics for a run.

        Args:
            run_id: Run identifier
            export_path: Directory to export to

        Returns:
            Path to export directory

        Raises:
            FileNotFoundError: If run not found
        """
        export_path = Path(export_path)
        export_path.mkdir(parents=True, exist_ok=True)

        # Load run info
        run_file = self.runs_dir / f"{run_id}.json"
        if not run_file.exists():
            raise FileNotFoundError(f"Run not found: {run_id}")

        with open(run_file, encoding="utf-8") as f:
            run_info = json.load(f)

        # Copy run info
        with open(export_path / "run_info.json", "w", encoding="utf-8") as f:
            json.dump(run_info, f, indent=2, ensure_ascii=False)

        # Copy artifacts
        run_artifacts = self.artifacts_dir / run_id
        if run_artifacts.exists():
            dest_artifacts = export_path / "artifacts"
            shutil.copytree(run_artifacts, dest_artifacts, dirs_exist_ok=True)

        # Create summary
        exported_files = list(export_path.rglob("*"))
        summary = {
            "run_id": run_id,
            "workflow_id": run_info.get("workflow_id"),
            "status": run_info.get("status"),
            "exported_files": [str(f.relative_to(export_path)) for f in exported_files if f.is_file()],
        }

        with open(export_path / "summary.json", "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        return export_path