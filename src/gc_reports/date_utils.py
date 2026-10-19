import datetime

type MonthRanges = list[tuple[datetime.datetime, datetime.datetime]]

def next_month_start(dt: datetime.datetime) -> datetime.datetime:
    next_month = dt.month % 12 + 1
    next_year = dt.year + (1 if dt.month == 12 else 0)
    result   = dt.replace(year=next_year, month=next_month, day=1, hour=0, minute=0, second=0, microsecond=0)
    return result


def generate_month_ranges(
    start: datetime.datetime, end: datetime.datetime
) -> MonthRanges:
    month_ranges: list[tuple[datetime.datetime, datetime.datetime]] = []
    current_start = start.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    while current_start < end:
        current_end = next_month_start(current_start)
        month_ranges.append((current_start, current_end))
        current_start = current_end
    return month_ranges


def format_month_ranges(ranges: MonthRanges) -> list[str]:
    return [month_start.strftime("%Y-%m") for month_start, _ in ranges]
