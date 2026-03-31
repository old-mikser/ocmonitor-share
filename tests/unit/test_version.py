"""Unit tests for runtime version resolution."""

from importlib.metadata import PackageNotFoundError

import ocmonitor.version as version_module


class TestVersionResolution:
    """Tests for get_version fallback behavior."""

    def test_reads_opencode_monitor_distribution(self, monkeypatch):
        calls = []

        def fake_distribution_version(name):
            calls.append(name)
            if name == "opencode-monitor":
                return "1.0.3"
            raise PackageNotFoundError(name)

        monkeypatch.setattr(
            version_module,
            "distribution_version",
            fake_distribution_version,
        )

        assert version_module.get_version() == "1.0.3"
        assert calls == ["opencode-monitor"]

    def test_uses_local_fallback_when_metadata_missing(self, monkeypatch):
        def fake_distribution_version(name):
            raise PackageNotFoundError(name)

        monkeypatch.setattr(
            version_module,
            "distribution_version",
            fake_distribution_version,
        )

        assert version_module.get_version() == version_module.FALLBACK_VERSION
