import re
from datetime import date
from typing import Optional


def parse_date(date_string: str) -> Optional[date]:
    """Parse various date formats into a sortable date object.

    Handles:
    - Full date: "March 15, 1956", "15 March 1956", "15/03/1956", "03-15-1956"
    - Month + year: "March 1956", "Mar 1956", "03/1956"
    - Year only: "1956"

    Returns None for unparseable dates.
    """
    if not date_string or not isinstance(date_string, str):
        return None

    date_string = date_string.strip()

    month_map = {
        "january": 1, "jan": 1,
        "february": 2, "feb": 2,
        "march": 3, "mar": 3,
        "april": 4, "apr": 4,
        "may": 5,
        "june": 6, "jun": 6,
        "july": 7, "jul": 7,
        "august": 8, "aug": 8,
        "september": 9, "sep": 9, "sept": 9,
        "october": 10, "oct": 10,
        "november": 11, "nov": 11,
        "december": 12, "dec": 12,
    }

    # Try year only: "1956"
    year_only = re.match(r"^(\d{4})$", date_string)
    if year_only:
        year = int(year_only.group(1))
        if 1900 <= year <= 2100:
            return date(year, 1, 1)

    # Try month/year: "March 1956", "Mar 1956", "03/1956"
    month_year = re.match(r"^([a-zA-Z]+)\s+(\d{4})$", date_string)
    if month_year:
        month_name = month_year.group(1).lower()
        year = int(month_year.group(2))
        if month_name in month_map and 1900 <= year <= 2100:
            return date(year, month_map[month_name], 1)

    month_year_short = re.match(r"^(\d{1,2})/(\d{4})$", date_string)
    if month_year_short:
        month = int(month_year_short.group(1))
        year = int(month_year_short.group(2))
        if 1 <= month <= 12 and 1900 <= year <= 2100:
            return date(year, month, 1)

    # Try full date: "March 15, 1956", "15 March 1956"
    full_date_long = re.match(r"^([a-zA-Z]+)\s+(\d{1,2}),?\s+(\d{4})$", date_string)
    if full_date_long:
        month_name = full_date_long.group(1).lower()
        day = int(full_date_long.group(2))
        year = int(full_date_long.group(3))
        if month_name in month_map and 1 <= day <= 31 and 1900 <= year <= 2100:
            try:
                return date(year, month_map[month_name], day)
            except ValueError:
                return None

    full_date_long2 = re.match(r"^(\d{1,2})\s+([a-zA-Z]+)\s+(\d{4})$", date_string)
    if full_date_long2:
        day = int(full_date_long2.group(1))
        month_name = full_date_long2.group(2).lower()
        year = int(full_date_long2.group(3))
        if month_name in month_map and 1 <= day <= 31 and 1900 <= year <= 2100:
            try:
                return date(year, month_map[month_name], day)
            except ValueError:
                return None

    # Try numeric formats: "15/03/1956", "03-15-1956", "15.03.1956"
    for separator in ["/", "-", "."]:
        parts = date_string.split(separator)
        if len(parts) == 3:
            try:
                first, second, third = int(parts[0]), int(parts[1]), int(parts[2])
                # Handle 2-digit years
                if third < 100:
                    year = 1900 + third if third > 50 else 2000 + third
                else:
                    year = third

                # Try both DD-MM-YYYY and MM-DD-YYYY interpretations
                # If first > 12, it must be day (DD-MM-YYYY)
                if first > 12 and 1 <= second <= 12:
                    day, month = first, second
                # If second > 12, it must be day (MM-DD-YYYY)
                elif second > 12 and 1 <= first <= 12:
                    day, month = second, first
                # Otherwise default to DD-MM-YYYY
                else:
                    day, month = first, second

                if 1 <= day <= 31 and 1 <= month <= 12 and 1900 <= year <= 2100:
                    return date(year, month, day)
            except ValueError:
                continue

    # Could not parse
    return None


def format_date_for_display(parsed_date: Optional[date]) -> str:
    """Format a parsed date for human-readable display."""
    if parsed_date is None:
        return "Unknown date"

    months = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]

    if parsed_date.day == 1 and parsed_date.month == 1:
        return str(parsed_date.year)

    if parsed_date.day == 1:
        return f"{months[parsed_date.month - 1]} {parsed_date.year}"

    return f"{months[parsed_date.month - 1]} {parsed_date.day}, {parsed_date.year}"
