import datetime
import pathlib
import sqlite3

import click

from gc_reports.account import get_accounts
from gc_reports.algebra import RealNumber
from gc_reports.chart import stacked_bar_chart
from gc_reports.date_utils import format_month_ranges, generate_month_ranges
from gc_reports.income_expense import get_categories_by_type, get_total_in_time_ranges
from gc_reports.transaction import (
    get_transaction_date_range,
)


@click.command()
@click.option(
    "--start-date",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    default=None,
    help="Start date for the report (YYYY-MM-DD)",
)
@click.option(
    "--end-date",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    default=None,
    help="End date for the report (YYYY-MM-DD)",
)
@click.argument(
    "db_path",
    type=click.Path(path_type=pathlib.Path, exists=True, dir_okay=False, readable=True),
)
def report(
    db_path: pathlib.Path,
    start_date: datetime.datetime | None,
    end_date: datetime.datetime | None,
):
    con = sqlite3.connect(db_path)

    # Initialize accounts
    accounts = get_accounts(con)

    # Process given time range, defaulting to the min/max dates in the database if not provided
    # The dates provided on the CLI is in the local timezone
    min_date, max_date = get_transaction_date_range(con)
    if min_date is None or max_date is None:
        click.echo("No transactions found in the database.")
        return

    native_tz = datetime.datetime.now().astimezone().tzinfo
    if start_date is None:
        start_date = min_date
    else:
        start_date = start_date.replace(tzinfo=native_tz)
    if end_date is None:
        end_date = max_date
    else:
        end_date = end_date.replace(tzinfo=native_tz)

    # Get a list of start date-end date pairs for each month in the range
    month_ranges = generate_month_ranges(start_date, end_date)

    x_axis_labels = format_month_ranges(month_ranges)

    # Chart income
    y_data: list[tuple[str, list[RealNumber]]] = get_total_in_time_ranges(con, accounts, month_ranges, "INCOME")
    stacked_bar_chart("Income by Category", "Month", x_axis_labels, "Amount", y_data)

    # Chart expense
    y_data = get_total_in_time_ranges(con, accounts, month_ranges, "EXPENSE")
    stacked_bar_chart("Expense by Category", "Month", x_axis_labels, "Amount", y_data)

def main():
    report()
