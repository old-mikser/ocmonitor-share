"""Tests for Prometheus metrics server."""

import re
from decimal import Decimal
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from ocmonitor.config import ModelPricing
from ocmonitor.models.session import SessionData, InteractionFile, TokenUsage, TimeData
from ocmonitor.models.analytics import (
    ModelBreakdownReport,
    ModelUsageStats,
    ProjectBreakdownReport,
    ProjectUsageStats,
)
from ocmonitor.services.metrics_server import OCMonitorCollector, MetricsServer


SAMPLE_PRICING = {
    "test-model": ModelPricing(
        input=Decimal("1.0"),
        output=Decimal("2.0"),
        cacheWrite=Decimal("1.5"),
        cacheRead=Decimal("0.1"),
        contextWindow=128000,
        sessionQuota=Decimal("5.0"),
    )
}


def _make_session(
    session_id="ses_1",
    model_id="test-model",
    input_tokens=1000,
    output_tokens=500,
    cache_read=50,
    cache_write=100,
    created=1700000000000,
    completed=1700003600000,
    project_path="/home/user/project1",
):
    """Helper to create a SessionData with one interaction."""
    return SessionData(
        session_id=session_id,
        files=[
            InteractionFile(
                file_path=Path(f"/tmp/{session_id}/inter_0001.json"),
                session_id=session_id,
                model_id=model_id,
                tokens=TokenUsage(
                    input=input_tokens,
                    output=output_tokens,
                    cache_read=cache_read,
                    cache_write=cache_write,
                ),
                time_data=TimeData(created=created, completed=completed),
                project_path=project_path,
            )
        ],
    )


class TestOCMonitorCollector:
    """Tests for the custom Prometheus collector."""

    def test_collect_with_no_sessions(self):
        """Empty session list should yield metrics with no samples (except duration)."""
        collector = OCMonitorCollector(SAMPLE_PRICING)

        with patch.object(
            collector._analyzer, "analyze_all_sessions", return_value=[]
        ):
            families = list(collector.collect())

        names = [f.name for f in families]
        assert "ocmonitor_tokens_input_total" in names
        assert "ocmonitor_session_duration_hours_total" in names
        assert "ocmonitor_sessions_by_project" in names

        # Duration should be 0
        duration_family = next(
            f for f in families if f.name == "ocmonitor_session_duration_hours_total"
        )
        assert duration_family.samples[0].value == 0.0

    def test_collect_with_sessions(self):
        """Known sessions should produce correct metric values."""
        collector = OCMonitorCollector(SAMPLE_PRICING)
        session = _make_session(input_tokens=1000, output_tokens=500)

        with patch.object(
            collector._analyzer, "analyze_all_sessions", return_value=[session]
        ):
            families = {f.name: f for f in collector.collect()}

        # Check input tokens
        input_fam = families["ocmonitor_tokens_input_total"]
        assert any(s.value == 1000 for s in input_fam.samples)

        # Check output tokens
        output_fam = families["ocmonitor_tokens_output_total"]
        assert any(s.value == 500 for s in output_fam.samples)

    def test_collect_per_model_labels(self):
        """Two distinct models should produce labeled samples for each."""
        pricing = {
            **SAMPLE_PRICING,
            "other-model": ModelPricing(
                input=Decimal("2.0"),
                output=Decimal("4.0"),
                cacheWrite=Decimal("2.0"),
                cacheRead=Decimal("0.2"),
                contextWindow=200000,
                sessionQuota=Decimal("8.0"),
            ),
        }
        collector = OCMonitorCollector(pricing)

        s1 = _make_session(session_id="s1", model_id="test-model", input_tokens=100)
        s2 = _make_session(session_id="s2", model_id="other-model", input_tokens=200)

        with patch.object(
            collector._analyzer, "analyze_all_sessions", return_value=[s1, s2]
        ):
            families = {f.name: f for f in collector.collect()}

        input_fam = families["ocmonitor_tokens_input_total"]
        labels_seen = {s.labels["model"] for s in input_fam.samples}
        assert "test-model" in labels_seen
        assert "other-model" in labels_seen

    def test_collect_per_project_labels(self):
        """Two projects should produce labeled samples in sessions_by_project."""
        collector = OCMonitorCollector(SAMPLE_PRICING)

        s1 = _make_session(session_id="s1", project_path="/home/user/project-a")
        s2 = _make_session(session_id="s2", project_path="/home/user/project-b")

        with patch.object(
            collector._analyzer, "analyze_all_sessions", return_value=[s1, s2]
        ):
            families = {f.name: f for f in collector.collect()}

        proj_fam = families["ocmonitor_sessions_by_project"]
        project_labels = {s.labels["project"] for s in proj_fam.samples}
        assert "project-a" in project_labels
        assert "project-b" in project_labels

    def test_collect_output_rate(self):
        """Output rate metric should be present per model."""
        collector = OCMonitorCollector(SAMPLE_PRICING)
        session = _make_session()

        with patch.object(
            collector._analyzer, "analyze_all_sessions", return_value=[session]
        ):
            families = {f.name: f for f in collector.collect()}

        rate_fam = families["ocmonitor_output_rate_tokens_per_second"]
        assert len(rate_fam.samples) > 0

    def test_collect_session_duration(self):
        """Duration should sum correctly across sessions."""
        collector = OCMonitorCollector(SAMPLE_PRICING)

        # 1 hour each
        s1 = _make_session(
            session_id="s1", created=1700000000000, completed=1700003600000
        )
        s2 = _make_session(
            session_id="s2", created=1700010000000, completed=1700013600000
        )

        with patch.object(
            collector._analyzer, "analyze_all_sessions", return_value=[s1, s2]
        ):
            families = {f.name: f for f in collector.collect()}

        dur_fam = families["ocmonitor_session_duration_hours_total"]
        assert dur_fam.samples[0].value == pytest.approx(2.0, abs=0.01)

    def test_collect_handles_analyzer_error(self):
        """Analyzer exception should yield zero-valued metrics, not crash."""
        collector = OCMonitorCollector(SAMPLE_PRICING)

        with patch.object(
            collector._analyzer,
            "analyze_all_sessions",
            side_effect=RuntimeError("boom"),
        ):
            families = list(collector.collect())

        # Should still return metrics
        assert len(families) > 0
        names = [f.name for f in families]
        assert "ocmonitor_tokens_input_total" in names
        assert "ocmonitor_session_duration_hours_total" in names

    def test_collect_cost_as_float(self):
        """Cost metric values should be floats, not Decimal."""
        collector = OCMonitorCollector(SAMPLE_PRICING)
        session = _make_session()

        with patch.object(
            collector._analyzer, "analyze_all_sessions", return_value=[session]
        ):
            families = {f.name: f for f in collector.collect()}

        cost_fam = families["ocmonitor_cost_dollars_total"]
        for sample in cost_fam.samples:
            assert isinstance(sample.value, (int, float))

    def test_metric_names_follow_conventions(self):
        """All metric names should match Prometheus naming conventions."""
        collector = OCMonitorCollector(SAMPLE_PRICING)

        with patch.object(
            collector._analyzer, "analyze_all_sessions", return_value=[]
        ):
            families = list(collector.collect())

        pattern = re.compile(r"^[a-zA-Z_:][a-zA-Z0-9_:]*$")
        for family in families:
            assert pattern.match(family.name), f"Bad metric name: {family.name}"


class TestMetricsServer:
    """Tests for the MetricsServer wrapper."""

    @patch("ocmonitor.services.metrics_server.start_http_server")
    def test_server_starts_http(self, mock_start):
        """start_http_server should be called with correct args."""
        server = MetricsServer(SAMPLE_PRICING, host="127.0.0.1", port=8080)

        # Make threading.Event.wait() raise immediately
        with patch("threading.Event.wait", side_effect=KeyboardInterrupt):
            with pytest.raises(KeyboardInterrupt):
                server.start()

        mock_start.assert_called_once()
        args, kwargs = mock_start.call_args
        assert args[0] == 8080
        assert kwargs["addr"] == "127.0.0.1"
        assert "registry" in kwargs

    @patch("ocmonitor.services.metrics_server.start_http_server")
    def test_server_registers_collector(self, mock_start):
        """Registry should have OCMonitorCollector registered."""
        server = MetricsServer(SAMPLE_PRICING, host="0.0.0.0", port=9090)

        with patch("threading.Event.wait", side_effect=KeyboardInterrupt):
            with pytest.raises(KeyboardInterrupt):
                server.start()

        # The registry passed to start_http_server should have our collector
        registry = mock_start.call_args.kwargs["registry"]
        collector_types = [type(c).__name__ for c in registry._collector_to_names.keys()]
        assert "OCMonitorCollector" in collector_types

    @patch("ocmonitor.services.metrics_server.start_http_server")
    def test_server_keyboard_interrupt(self, mock_start):
        """KeyboardInterrupt should propagate to caller."""
        server = MetricsServer(SAMPLE_PRICING)

        with patch("threading.Event.wait", side_effect=KeyboardInterrupt):
            with pytest.raises(KeyboardInterrupt):
                server.start()
