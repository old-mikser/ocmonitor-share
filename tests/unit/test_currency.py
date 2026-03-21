"""Unit tests for currency conversion utilities."""

from decimal import Decimal

from ocmonitor.utils.currency import CurrencyConverter


class TestCurrencyConverter:
    """Tests for CurrencyConverter."""

    def test_default_format_matches_usd(self):
        converter = CurrencyConverter()
        assert converter.format(Decimal("1.23")) == "$1.23"

    def test_gbp_conversion_and_symbol(self):
        converter = CurrencyConverter(code="GBP", symbol="£", rate=Decimal("0.79"))
        assert converter.convert(Decimal("10.00")) == Decimal("7.90")
        assert converter.format(Decimal("10.00")) == "£7.90"

    def test_jpy_zero_decimals(self):
        """Test JPY formatting with 0 decimal places and proper rounding."""
        converter = CurrencyConverter(code="JPY", symbol="¥", rate=Decimal("150"))
        # 1.23 * 150 = 184.5, should round to 185 (not truncate to 184)
        assert converter.format(Decimal("1.23")) == "¥185"

    def test_code_suffix_format(self):
        converter = CurrencyConverter(
            code="EUR",
            symbol="€",
            rate=Decimal("0.92"),
            display_format="code_suffix",
        )
        assert converter.format(Decimal("1.00")) == "0.92 EUR"

    def test_explicit_decimals_override(self):
        converter = CurrencyConverter(code="USD", decimals=4)
        assert converter.format(Decimal("1.2")) == "$1.2000"

    def test_zero_amount(self):
        converter = CurrencyConverter(code="USD")
        assert converter.format(Decimal("0")) == "$0.00"

    def test_rounding_half_up(self):
        """Test ROUND_HALF_UP rounding behavior for zero-decimal currencies."""
        converter = CurrencyConverter(code="JPY", symbol="¥", rate=Decimal("150"))
        # 1.23 * 150 = 184.5 -> rounds to 185
        assert converter.format(Decimal("1.23")) == "¥185"
        # 1.22 * 150 = 183.0 -> stays 183
        assert converter.format(Decimal("1.22")) == "¥183"
        # 1.24 * 150 = 186.0 -> stays 186
        assert converter.format(Decimal("1.24")) == "¥186"
        # 1.233 * 150 = 184.95 -> rounds to 185
        assert converter.format(Decimal("1.233")) == "¥185"

    def test_rounding_with_decimals(self):
        """Test ROUND_HALF_UP rounding for currencies with decimals."""
        converter = CurrencyConverter(code="GBP", symbol="£", rate=Decimal("0.79"))
        # 10.005 * 0.79 = 7.90395 -> rounds to 7.90
        assert converter.format(Decimal("10.005")) == "£7.90"
        # 10.015 * 0.79 = 7.91185 -> rounds to 7.91
        assert converter.format(Decimal("10.015")) == "£7.91"

    def test_lowercase_currency_code_normalized(self):
        """Test that lowercase currency codes are normalized to uppercase.

        This ensures consistency when users configure lowercase currency codes
        (e.g., "gbp" instead of "GBP"). The code should be normalized internally
        while preserving the correct symbol and decimals for that currency.
        """
        converter = CurrencyConverter(code="gbp", symbol="£", rate=Decimal("0.79"))
        assert converter.code == "GBP"
        assert converter.format(Decimal("10.00")) == "£7.90"

    def test_lowercase_currency_code_zero_decimal(self):
        """Test that lowercase JPY currency code gets 0 decimals."""
        converter = CurrencyConverter(code="jpy", symbol="¥", rate=Decimal("150"))
        assert converter.code == "JPY"
        assert converter.decimals == 0
        # 1.23 * 150 = 184.5 -> rounds to 185
        assert converter.format(Decimal("1.23")) == "¥185"

    def test_mixed_case_currency_code_normalized(self):
        """Test that mixed-case currency codes are normalized."""
        converter = CurrencyConverter(code="GbP", symbol="£", rate=Decimal("0.79"))
        assert converter.code == "GBP"
        assert converter.format(Decimal("10.00")) == "£7.90"

    def test_rounding_zero_decimal_boundary_cases(self):
        """Test rounding boundary cases for 0-decimal currencies."""
        converter = CurrencyConverter(code="JPY", symbol="¥", rate=Decimal("150"))

        # Test exact .5 rounding up
        assert converter.format(Decimal("1.23")) == "¥185"  # 184.5 -> 185
        assert converter.format(Decimal("1.22")) == "¥183"  # 183.0 -> 183

        # Test just below .5 rounds down
        assert converter.format(Decimal("1.229")) == "¥184"  # 184.35 -> 184

        # Test just above .5 rounds up
        assert converter.format(Decimal("1.231")) == "¥185"  # 184.65 -> 185

        # Test large amounts
        assert converter.format(Decimal("100.00")) == "¥15000"
        assert converter.format(Decimal("100.50")) == "¥15075"  # 15075.0 -> 15075
        assert converter.format(Decimal("100.51")) == "¥15077"  # 15076.5 -> 15077

    def test_rounding_zero_decimal_custom_rate(self):
        """Test rounding with custom rate for 0-decimal currency."""
        # Rate that produces fractional results
        converter = CurrencyConverter(code="KRW", symbol="₩", rate=Decimal("1350.5"))

        # 1.00 * 1350.5 = 1350.5 -> rounds to 1351
        assert converter.format(Decimal("1.00")) == "₩1351"

        # 1.01 * 1350.5 = 1364.005 -> rounds to 1364
        assert converter.format(Decimal("1.01")) == "₩1364"

        # 1.99 * 1350.5 = 2687.495 -> rounds to 2687
        assert converter.format(Decimal("1.99")) == "₩2687"
