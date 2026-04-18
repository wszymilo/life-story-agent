from datetime import date

from utils.date_parser import format_date_for_display, parse_date


class TestParseDate:
    """Tests for date parser utility."""

    def test_parse_year_only(self):
        """Test parsing year only format."""
        assert parse_date("1956") == date(1956, 1, 1)
        assert parse_date("1970") == date(1970, 1, 1)
        assert parse_date("2020") == date(2020, 1, 1)

    def test_parse_month_year_long(self):
        """Test parsing month + year format (long form)."""
        assert parse_date("March 1956") == date(1956, 3, 1)
        assert parse_date("January 1970") == date(1970, 1, 1)
        assert parse_date("December 2020") == date(2020, 12, 1)

    def test_parse_month_year_short(self):
        """Test parsing month + year format (short form)."""
        assert parse_date("Mar 1956") == date(1956, 3, 1)
        assert parse_date("Jan 1970") == date(1970, 1, 1)
        assert parse_date("Dec 2020") == date(2020, 12, 1)

    def test_parse_month_year_numeric(self):
        """Test parsing numeric month/year format."""
        assert parse_date("03/1956") == date(1956, 3, 1)
        assert parse_date("1/1970") == date(1970, 1, 1)
        assert parse_date("12/2020") == date(2020, 12, 1)

    def test_parse_full_date_long(self):
        """Test parsing full date (Month Day, Year)."""
        assert parse_date("March 15, 1956") == date(1956, 3, 15)
        assert parse_date("January 1, 1970") == date(1970, 1, 1)
        assert parse_date("December 31, 2020") == date(2020, 12, 31)

    def test_parse_full_date_short(self):
        """Test parsing full date (Day Month Year)."""
        assert parse_date("15 March 1956") == date(1956, 3, 15)
        assert parse_date("1 January 1970") == date(1970, 1, 1)

    def test_parse_numeric_full_date(self):
        """Test parsing numeric full date formats."""
        assert parse_date("15/03/1956") == date(1956, 3, 15)
        assert parse_date("03-15-1956") == date(1956, 3, 15)
        assert parse_date("15.03.1956") == date(1956, 3, 15)

    def test_parse_invalid_returns_none(self):
        """Test that invalid dates return None."""
        assert parse_date("") is None
        assert parse_date("unknown") is None
        assert parse_date("not a date") is None
        assert parse_date("sometime in the past") is None
        assert parse_date(None) is None

    def test_parse_out_of_range_year(self):
        """Test that out of range years return None."""
        assert parse_date("1800") is None
        assert parse_date("2150") is None


class TestFormatDateForDisplay:
    """Tests for date display formatting."""

    def test_format_year_only(self):
        """Test formatting year-only date."""
        assert format_date_for_display(date(1956, 1, 1)) == "1956"

    def test_format_month_year(self):
        """Test formatting month/year date."""
        assert format_date_for_display(date(1956, 3, 1)) == "March 1956"

    def test_format_full_date(self):
        """Test formatting full date."""
        assert format_date_for_display(date(1956, 3, 15)) == "March 15, 1956"

    def test_format_none(self):
        """Test formatting None."""
        assert format_date_for_display(None) == "Unknown date"
