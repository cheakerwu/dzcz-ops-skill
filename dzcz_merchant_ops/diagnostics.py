"""Remote diagnostics export for troubleshooting."""
from __future__ import annotations

import json
import shutil
import sqlite3
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
        self.db_path = self.data_dir / "registry.sqlite"

    def _connect_db(self) -> sqlite3.Connection:
        """Connect to SQLite database."""
        db = sqlite3.connect(self.db_path)
        db.row_factory = sqlite3.Row
        return db

    def list_runs(self) -> list[dict[str, Any]]:
        """List all available runs.

        Returns:
            List of run summaries
        """
        if not self.db_path.exists():
            return []

        db = self._connect_db()
        try:
            cursor = db.execute(
                "SELECT run_id, workflow_id, profile_id, status, started_at, finished_at FROM runs ORDER BY started_at DESC"
            )
            runs = []
            for row in cursor:
                runs.append({
                    "run_id": row["run_id"],
                    "workflow_id": row["workflow_id"],
                    "profile_id": row["profile_id"],
                    "status": row["status"],
                    "started_at": row["started_at"],
                    "finished_at": row["finished_at"],
                })
            return runs
        finally:
            db.close()

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

        # Load run info from SQLite
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found: {self.db_path}")

        db = self._connect_db()
        try:
            cursor = db.execute(
                "SELECT * FROM runs WHERE run_id = ?", (run_id,)
            )
            row = cursor.fetchone()
            if row is None:
                raise FileNotFoundError(f"Run not found: {run_id}")

            run_info = dict(row)
        finally:
            db.close()

        # Copy run info
        with open(export_path / "run_info.json", "w", encoding="utf-8") as f:
            json.dump(run_info, f, indent=2, ensure_ascii=False)

        # Copy artifacts
        artifact_dir = run_info.get("artifact_dir", "")
        if artifact_dir:
            run_artifacts = Path(artifact_dir)
            if run_artifacts.exists():
                dest_artifacts = export_path / "artifacts"
                shutil.copytree(run_artifacts, dest_artifacts, dirs_exist_ok=True)

        # Create summary
        exported_files = list(export_path.rglob("*"))
        summary = {
            "run_id": run_id,
            "workflow_id": run_info.get("workflow_id"),
            "profile_id": run_info.get("profile_id"),
            "status": run_info.get("status"),
            "started_at": run_info.get("started_at"),
            "finished_at": run_info.get("finished_at"),
            "error": run_info.get("error"),
            "exported_files": [str(f.relative_to(export_path)) for f in exported_files if f.is_file()],
        }

        with open(export_path / "summary.json", "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        return export_path