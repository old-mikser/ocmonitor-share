"""Unit tests for timeframe filtering in models and projects reports."""

from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, PropertyMock, patch

import pytest

from ocmonitor.services.report_generator import ReportGenerator
from ocmonitor.utils.time_utils import TimeUtils


class TestTimeframeFilteringInReportGenerator:
    """Test that report_generator correctly converts timeframe to date ranges."""

    def test_models_weekly_converts_to_date_range(self):
        """Test that weekly timeframe calls get_current_week_range and filter_sessions."""
        mock_analyzer = MagicMock()
        mock_sessions = [MagicMock(), MagicMock()]
        mock_analyzer.analyze_all_sessions.return_value = mock_sessions

        mock_model_breakdown = MagicMock()
        mock_model_breakdown.timeframe = "weekly"
        mock_model_breakdown.start_date = date.today()
        mock_model_breakdown.end_date = date.today()
        mock_model_breakdown.total_cost = Decimal("0.0")
        mock_model_breakdown.total_tokens = MagicMock()
        mock_model_breakdown.total_tokens.model_dump.return_value = {}
        mock_model_breakdown.model_stats = []
        mock_analyzer.create_model_breakdown.return_value = mock_model_breakdown

        report_gen = ReportGenerator(mock_analyzer)

        week_start = date.today() - timedelta(days=date.today().weekday())
        week_end = week_start + timedelta(days=6)

        with patch.object(
            TimeUtils, "get_current_week_range", return_value=(week_start, week_end)
        ):
            with patch.object(mock_analyzer, "filter_sessions_by_date") as mock_filter:
                mock_filter.return_value = mock_sessions

                result = report_gen.generate_models_report(
                    base_path="/fake/path", timeframe="weekly", output_format="json"
                )

                TimeUtils.get_current_week_range.assert_called_once()
                mock_filter.assert_called_once_with(mock_sessions, week_start, week_end)

                call_args = mock_analyzer.create_model_breakdown.call_args
                assert call_args[0][1] == "weekly"
                assert call_args[0][2] == week_start
                assert call_args[0][3] == week_end

    def test_models_monthly_converts_to_date_range(self):
        """Test that monthly timeframe calls get_current_month_range and filter_sessions."""
        mock_analyzer = MagicMock()
        mock_sessions = [MagicMock()]
        mock_analyzer.analyze_all_sessions.return_value = mock_sessions

        mock_model_breakdown = MagicMock()
        mock_model_breakdown.timeframe = "monthly"
        mock_model_breakdown.start_date = date.today()
        mock_model_breakdown.end_date = date.today()
        mock_model_breakdown.total_cost = Decimal("0.0")
        mock_model_breakdown.total_tokens = MagicMock()
        mock_model_breakdown.total_tokens.model_dump.return_value = {}
        mock_model_breakdown.model_stats = []
        mock_analyzer.create_model_breakdown.return_value = mock_model_breakdown

        report_gen = ReportGenerator(mock_analyzer)

        month_start = date(date.today().year, date.today().month, 1)
        month_end = date(date.today().year, date.today().month, 28)

        with patch.object(
            TimeUtils, "get_current_month_range", return_value=(month_start, month_end)
        ):
            with patch.object(mock_analyzer, "filter_sessions_by_date") as mock_filter:
                mock_filter.return_value = mock_sessions

                result = report_gen.generate_models_report(
                    base_path="/fake/path", timeframe="monthly", output_format="json"
                )

                TimeUtils.get_current_month_range.assert_called_once()
                mock_filter.assert_called_once_with(
                    mock_sessions, month_start, month_end
                )

    def test_models_daily_converts_to_date_range(self):
        """Test that daily timeframe calls get_last_n_days_range(1) and filter_sessions."""
        mock_analyzer = MagicMock()
        mock_sessions = [MagicMock()]
        mock_analyzer.analyze_all_sessions.return_value = mock_sessions

        mock_model_breakdown = MagicMock()
        mock_model_breakdown.timeframe = "daily"
        mock_model_breakdown.start_date = date.today()
        mock_model_breakdown.end_date = date.today()
        mock_model_breakdown.total_cost = Decimal("0.0")
        mock_model_breakdown.total_tokens = MagicMock()
        mock_model_breakdown.total_tokens.model_dump.return_value = {}
        mock_model_breakdown.model_stats = []
        mock_analyzer.create_model_breakdown.return_value = mock_model_breakdown

        report_gen = ReportGenerator(mock_analyzer)

        today = date.today()

        with patch.object(
            TimeUtils, "get_last_n_days_range", return_value=(today, today)
        ) as mock_daily:
            with patch.object(mock_analyzer, "filter_sessions_by_date") as mock_filter:
                mock_filter.return_value = mock_sessions

                result = report_gen.generate_models_report(
                    base_path="/fake/path", timeframe="daily", output_format="json"
                )

                mock_daily.assert_called_once_with(1)
                mock_filter.assert_called_once_with(mock_sessions, today, today)

    def test_models_all_skips_date_filtering(self):
        """Test that 'all' timeframe doesn't call date filtering."""
        mock_analyzer = MagicMock()
        mock_sessions = [MagicMock()]
        mock_analyzer.analyze_all_sessions.return_value = mock_sessions

        mock_model_breakdown = MagicMock()
        mock_model_breakdown.timeframe = "all"
        mock_model_breakdown.start_date = None
        mock_model_breakdown.end_date = None
        mock_model_breakdown.total_cost = Decimal("0.0")
        mock_model_breakdown.total_tokens = MagicMock()
        mock_model_breakdown.total_tokens.model_dump.return_value = {}
        mock_model_breakdown.model_stats = []
        mock_analyzer.create_model_breakdown.return_value = mock_model_breakdown

        report_gen = ReportGenerator(mock_analyzer)

        with patch.object(TimeUtils, "get_current_week_range") as mock_weekly:
            with patch.object(TimeUtils, "get_current_month_range") as mock_monthly:
                with patch.object(TimeUtils, "get_last_n_days_range") as mock_daily:
                    with patch.object(
                        mock_analyzer, "filter_sessions_by_date"
                    ) as mock_filter:
                        result = report_gen.generate_models_report(
                            base_path="/fake/path",
                            timeframe="all",
                            output_format="json",
                        )

                        mock_weekly.assert_not_called()
                        mock_monthly.assert_not_called()
                        mock_daily.assert_not_called()
                        mock_filter.assert_not_called()

    def test_models_explicit_dates_override_timeframe(self):
        """Test that explicit dates override timeframe conversion."""
        mock_analyzer = MagicMock()
        mock_sessions = [MagicMock()]
        mock_analyzer.analyze_all_sessions.return_value = mock_sessions

        mock_model_breakdown = MagicMock()
        mock_model_breakdown.timeframe = "weekly"
        mock_model_breakdown.start_date = date(2024, 1, 1)
        mock_model_breakdown.end_date = date(2024, 1, 31)
        mock_model_breakdown.total_cost = Decimal("0.0")
        mock_model_breakdown.total_tokens = MagicMock()
        mock_model_breakdown.total_tokens.model_dump.return_value = {}
        mock_model_breakdown.model_stats = []
        mock_analyzer.create_model_breakdown.return_value = mock_model_breakdown

        report_gen = ReportGenerator(mock_analyzer)

        with patch.object(TimeUtils, "get_current_week_range") as mock_weekly:
            with patch.object(mock_analyzer, "filter_sessions_by_date") as mock_filter:
                result = report_gen.generate_models_report(
                    base_path="/fake/path",
                    timeframe="weekly",
                    start_date="2024-01-01",
                    end_date="2024-01-31",
                    output_format="json",
                )

                mock_weekly.assert_not_called()
                mock_filter.assert_not_called()

    def test_projects_weekly_converts_to_date_range(self):
        """Test that weekly timeframe works for projects report too."""
        mock_analyzer = MagicMock()
        mock_sessions = [MagicMock()]
        mock_analyzer.analyze_all_sessions.return_value = mock_sessions

        mock_project_breakdown = MagicMock()
        mock_project_breakdown.timeframe = "weekly"
        mock_project_breakdown.start_date = date.today()
        mock_project_breakdown.end_date = date.today()
        mock_project_breakdown.total_cost = Decimal("0.0")
        mock_project_breakdown.total_tokens = MagicMock()
        mock_project_breakdown.total_tokens.model_dump.return_value = {}
        mock_project_breakdown.project_stats = []
        mock_analyzer.create_project_breakdown.return_value = mock_project_breakdown

        report_gen = ReportGenerator(mock_analyzer)

        week_start = date.today() - timedelta(days=date.today().weekday())
        week_end = week_start + timedelta(days=6)

        with patch.object(
            TimeUtils, "get_current_week_range", return_value=(week_start, week_end)
        ):
            with patch.object(mock_analyzer, "filter_sessions_by_date") as mock_filter:
                mock_filter.return_value = mock_sessions

                result = report_gen.generate_projects_report(
                    base_path="/fake/path", timeframe="weekly", output_format="json"
                )

                TimeUtils.get_current_week_range.assert_called_once()
                mock_filter.assert_called_once_with(mock_sessions, week_start, week_end)

    def test_projects_monthly_converts_to_date_range(self):
        """Test that monthly timeframe works for projects report."""
        mock_analyzer = MagicMock()
        mock_sessions = [MagicMock()]
        mock_analyzer.analyze_all_sessions.return_value = mock_sessions

        mock_project_breakdown = MagicMock()
        mock_project_breakdown.timeframe = "monthly"
        mock_project_breakdown.start_date = date.today()
        mock_project_breakdown.end_date = date.today()
        mock_project_breakdown.total_cost = Decimal("0.0")
        mock_project_breakdown.total_tokens = MagicMock()
        mock_project_breakdown.total_tokens.model_dump.return_value = {}
        mock_project_breakdown.project_stats = []
        mock_analyzer.create_project_breakdown.return_value = mock_project_breakdown

        report_gen = ReportGenerator(mock_analyzer)

        month_start = date(date.today().year, date.today().month, 1)
        month_end = date(date.today().year, date.today().month, 28)

        with patch.object(
            TimeUtils, "get_current_month_range", return_value=(month_start, month_end)
        ):
            with patch.object(mock_analyzer, "filter_sessions_by_date") as mock_filter:
                mock_filter.return_value = mock_sessions

                result = report_gen.generate_projects_report(
                    base_path="/fake/path", timeframe="monthly", output_format="json"
                )

                TimeUtils.get_current_month_range.assert_called_once()
                mock_filter.assert_called_once_with(
                    mock_sessions, month_start, month_end
                )

    def test_report_json_output_includes_resolved_dates(self):
        """Test that JSON output includes the resolved date range."""
        mock_analyzer = MagicMock()
        mock_sessions = [MagicMock()]
        mock_analyzer.analyze_all_sessions.return_value = mock_sessions

        week_start = date.today() - timedelta(days=date.today().weekday())
        week_end = week_start + timedelta(days=6)

        mock_model_breakdown = MagicMock()
        mock_model_breakdown.timeframe = "weekly"
        mock_model_breakdown.start_date = week_start
        mock_model_breakdown.end_date = week_end
        mock_model_breakdown.total_cost = Decimal("0.0")
        mock_model_breakdown.total_tokens = MagicMock()
        mock_model_breakdown.total_tokens.model_dump.return_value = {}
        mock_model_breakdown.model_stats = []
        mock_analyzer.create_model_breakdown.return_value = mock_model_breakdown

        report_gen = ReportGenerator(mock_analyzer)

        with patch.object(
            TimeUtils, "get_current_week_range", return_value=(week_start, week_end)
        ):
            with patch.object(
                mock_analyzer, "filter_sessions_by_date", return_value=mock_sessions
            ):
                result = report_gen.generate_models_report(
                    base_path="/fake/path", timeframe="weekly", output_format="json"
                )

                assert result["timeframe"] == "weekly"
                assert result["start_date"] == week_start.isoformat()
                assert result["end_date"] == week_end.isoformat()
