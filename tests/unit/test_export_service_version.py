"""Unit tests for export metadata version reporting."""

import json
from pathlib import Path

import ocmonitor.services.export_service as export_module
from ocmonitor.services.export_service import ExportService


class TestExportServiceVersion:
    """Tests for export version metadata."""

    def test_export_json_uses_resolved_version(self, tmp_path, monkeypatch):
        monkeypatch.setattr(export_module, "get_version", lambda: "9.9.9")

        service = ExportService(export_dir=str(tmp_path))
        output_path = service.export_to_json(
            data=[{"report": "sessions"}],
            filename="version_test",
            include_metadata=True,
        )

        exported = json.loads(Path(output_path).read_text(encoding="utf-8"))
        assert exported["metadata"]["export_info"]["version"] == "9.9.9"
