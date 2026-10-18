import datetime

type MonthRanges = list[tuple[datetime.datetime, datetime.datetime]]


def generate_month_ranges(
    start: datetime.datetime, end: datetime.datetime
) -> MonthRanges:
    month_ranges: list[tuple[datetime.datetime, datetime.datetime]] = []
    current_start = start.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    while current_start < end:
        next_month = current_start.month % 12 + 1
        next_year = current_start.year + (1 if current_start.month == 12 else 0)
        current_end = current_start.replace(year=next_year, month=next_month)
        month_ranges.append((current_start, current_end))
        current_start = current_end
    return month_ranges


def format_month_ranges(ranges: MonthRanges) -> list[str]:
    return [month_start.strftime("%Y-%m") for month_start, _ in ranges]
