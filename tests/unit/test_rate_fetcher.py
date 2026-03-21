"""Unit tests for rate_fetcher service."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

from ocmonitor.config import CurrencyConfig
from ocmonitor.services.price_fetcher import (
    load_cached_payload,
    save_cached_payload_atomic,
)
from ocmonitor.services.rate_fetcher import get_exchange_rate


def _make_currency_config(tmp_path: Path, **overrides):
    defaults = {
        "code": "GBP",
        "symbol": "£",
        "rate": Decimal("0.79"),
        "remote_rates": True,
        "remote_rates_url": "https://api.frankfurter.dev/v1/latest?base=USD",
        "remote_rates_timeout_seconds": 8,
        "remote_rates_cache_ttl_hours": 24,
        "remote_rates_cache_path": str(tmp_path / "rates.json"),
        "allow_stale_rates_on_error": True,
    }
    defaults.update(overrides)
    return CurrencyConfig(**defaults)


class TestGetExchangeRate:
    """Tests for get_exchange_rate function."""

    def test_fresh_cache_skips_network(self, tmp_path):
        cfg = _make_currency_config(tmp_path)
        cache_path = Path(cfg.remote_rates_cache_path)
        future = datetime.now(timezone.utc) + timedelta(hours=1)
        envelope = {
            "schema_version": 1,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": future.isoformat(),
            "payload": {"rates": {"GBP": 0.81}},
        }
        save_cached_payload_atomic(cache_path, envelope)

        with patch(
            "ocmonitor.services.rate_fetcher.fetch_exchange_rates"
        ) as mock_fetch:
            result = get_exchange_rate(cfg)

        mock_fetch.assert_not_called()
        assert result == Decimal("0.81")

    def test_stale_cache_refreshes(self, tmp_path):
        cfg = _make_currency_config(tmp_path)
        cache_path = Path(cfg.remote_rates_cache_path)
        past = datetime.now(timezone.utc) - timedelta(hours=1)
        envelope = {
            "schema_version": 1,
            "fetched_at": (past - timedelta(hours=25)).isoformat(),
            "expires_at": past.isoformat(),
            "payload": {"rates": {"GBP": 0.70}},
        }
        save_cached_payload_atomic(cache_path, envelope)

        with patch(
            "ocmonitor.services.rate_fetcher.fetch_exchange_rates",
            return_value={"rates": {"GBP": 0.82}},
        ) as mock_fetch:
            result = get_exchange_rate(cfg)

        mock_fetch.assert_called_once()
        assert result == Decimal("0.82")

        updated = load_cached_payload(cache_path)
        assert updated["payload"]["rates"]["GBP"] == 0.82

    def test_stale_cache_fetch_failure_uses_stale_when_allowed(self, tmp_path):
        cfg = _make_currency_config(tmp_path, allow_stale_rates_on_error=True)
        cache_path = Path(cfg.remote_rates_cache_path)
        past = datetime.now(timezone.utc) - timedelta(hours=1)
        envelope = {
            "schema_version": 1,
            "expires_at": past.isoformat(),
            "payload": {"rates": {"GBP": 0.75}},
        }
        save_cached_payload_atomic(cache_path, envelope)

        with patch(
            "ocmonitor.services.rate_fetcher.fetch_exchange_rates",
            return_value=None,
        ):
            result = get_exchange_rate(cfg)

        assert result == Decimal("0.75")

    def test_stale_cache_fetch_failure_returns_none_when_disallowed(self, tmp_path):
        cfg = _make_currency_config(tmp_path, allow_stale_rates_on_error=False)
        cache_path = Path(cfg.remote_rates_cache_path)
        past = datetime.now(timezone.utc) - timedelta(hours=1)
        envelope = {
            "schema_version": 1,
            "expires_at": past.isoformat(),
            "payload": {"rates": {"GBP": 0.75}},
        }
        save_cached_payload_atomic(cache_path, envelope)

        with patch(
            "ocmonitor.services.rate_fetcher.fetch_exchange_rates",
            return_value=None,
        ):
            result = get_exchange_rate(cfg)

        assert result is None

    def test_missing_currency_returns_none(self, tmp_path):
        cfg = _make_currency_config(tmp_path, code="EUR")

        with patch(
            "ocmonitor.services.rate_fetcher.fetch_exchange_rates",
            return_value={"rates": {"GBP": 0.8}},
        ):
            result = get_exchange_rate(cfg)

        assert result is None

    def test_lowercase_currency_code_normalized(self, tmp_path):
        """Test that lowercase currency codes are normalized to uppercase for lookup.

        This ensures remote rate fetching works even if users configure lowercase
        currency codes (e.g., "gbp" instead of "GBP"). The frankfurter.dev API
        returns uppercase currency codes, so normalization is required.
        """
        # Configure with lowercase currency code
        cfg = _make_currency_config(tmp_path, code="gbp")
        cache_path = Path(cfg.remote_rates_cache_path)

        # Simulate stale cache
        past = datetime.now(timezone.utc) - timedelta(hours=1)
        envelope = {
            "schema_version": 1,
            "expires_at": past.isoformat(),
            "payload": {"rates": {"GBP": 0.75}},
        }
        save_cached_payload_atomic(cache_path, envelope)

        # Mock fetch returns uppercase keys (as frankfurter.dev does)
        with patch(
            "ocmonitor.services.rate_fetcher.fetch_exchange_rates",
            return_value={"rates": {"GBP": 0.82, "EUR": 0.92}},
        ):
            result = get_exchange_rate(cfg)

        # Should successfully find GBP rate despite lowercase config
        assert result == Decimal("0.82")

    def test_mixed_case_currency_code_normalized(self, tmp_path):
        """Test that mixed-case currency codes (e.g., 'GbP') are normalized."""
        cfg = _make_currency_config(tmp_path, code="GbP")
        cache_path = Path(cfg.remote_rates_cache_path)

        past = datetime.now(timezone.utc) - timedelta(hours=1)
        envelope = {
            "schema_version": 1,
            "expires_at": past.isoformat(),
            "payload": {"rates": {"GBP": 0.75}},
        }
        save_cached_payload_atomic(cache_path, envelope)

        with patch(
            "ocmonitor.services.rate_fetcher.fetch_exchange_rates",
            return_value={"rates": {"GBP": 0.85}},
        ):
            result = get_exchange_rate(cfg)

        assert result == Decimal("0.85")

    def test_lock_not_acquired_uses_stale_cache_when_allowed(self, tmp_path):
        """Test fallback to stale cache when lock cannot be acquired.

        This tests the edge case at rate_fetcher.py:84 where the lock
        acquisition fails (e.g., another process holds it). When
        allow_stale_rates_on_error is True, the function should return
        the stale cached rate instead of None.
        """
        cfg = _make_currency_config(tmp_path, allow_stale_rates_on_error=True)
        cache_path = Path(cfg.remote_rates_cache_path)

        # Set up stale cache
        past = datetime.now(timezone.utc) - timedelta(hours=1)
        envelope = {
            "schema_version": 1,
            "expires_at": past.isoformat(),
            "payload": {"rates": {"GBP": 0.77}},
        }
        save_cached_payload_atomic(cache_path, envelope)

        # Mock lock acquisition failure
        with patch(
            "ocmonitor.services.rate_fetcher.acquire_lock",
            return_value=False,
        ) as mock_acquire:
            # Also mock fetch to verify it's NOT called when lock fails
            with patch(
                "ocmonitor.services.rate_fetcher.fetch_exchange_rates"
            ) as mock_fetch:
                result = get_exchange_rate(cfg)

        mock_acquire.assert_called_once()
        mock_fetch.assert_not_called()
        # Should return stale cache value
        assert result == Decimal("0.77")

    def test_lock_not_acquired_returns_none_when_stale_disallowed(self, tmp_path):
        """Test that None is returned when lock fails and stale cache is disallowed.

        When allow_stale_rates_on_error is False and the lock cannot be acquired,
        the function should return None rather than using potentially stale data.
        """
        cfg = _make_currency_config(tmp_path, allow_stale_rates_on_error=False)
        cache_path = Path(cfg.remote_rates_cache_path)

        # Set up stale cache
        past = datetime.now(timezone.utc) - timedelta(hours=1)
        envelope = {
            "schema_version": 1,
            "expires_at": past.isoformat(),
            "payload": {"rates": {"GBP": 0.77}},
        }
        save_cached_payload_atomic(cache_path, envelope)

        # Mock lock acquisition failure
        with patch(
            "ocmonitor.services.rate_fetcher.acquire_lock",
            return_value=False,
        ) as mock_acquire:
            result = get_exchange_rate(cfg)

        mock_acquire.assert_called_once()
        # Should return None when stale cache is not allowed
        assert result is None

    def test_lock_not_acquired_no_cache_returns_none(self, tmp_path):
        """Test that None is returned when lock fails and no cache exists.

        Edge case: lock acquisition fails AND there's no existing cache file.
        Should return None regardless of allow_stale_rates_on_error setting.
        """
        cfg = _make_currency_config(tmp_path, allow_stale_rates_on_error=True)
        cache_path = Path(cfg.remote_rates_cache_path)

        # Ensure no cache file exists
        if cache_path.exists():
            cache_path.unlink()

        # Mock lock acquisition failure
        with patch(
            "ocmonitor.services.rate_fetcher.acquire_lock",
            return_value=False,
        ):
            result = get_exchange_rate(cfg)

        # No cache to fall back to, should return None
        assert result is None
