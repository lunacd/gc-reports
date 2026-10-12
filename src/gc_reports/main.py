import datetime
import pathlib
import sqlite3

import click

from gc_reports.account import get_accounts
from gc_reports.algebra import RealNumber, sum_real_numbers
from gc_reports.chart import stacked_bar_chart
from gc_reports.income_expense import get_categories_by_type
from gc_reports.transaction import (
    get_transaction_date_range,
    get_transactions_in_date_range,
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

    # Get income and expense categories
    accounts = get_accounts(con)
    income_categories = get_categories_by_type(con, accounts, "INCOME")

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
    month_ranges: list[tuple[datetime.datetime, datetime.datetime]] = []
    current_start = start_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    while current_start < end_date:
        next_month = current_start.month % 12 + 1
        next_year = current_start.year + (1 if current_start.month == 12 else 0)
        current_end = current_start.replace(year=next_year, month=next_month)
        month_ranges.append((current_start, current_end))
        current_start = current_end

    # Get income by month by category
    x_axis_labels = [month_start.strftime("%Y-%m") for month_start, _ in month_ranges]
    y_data: list[tuple[str, list[float]]] = []
    for category in income_categories:
        monthly_totals: list[RealNumber] = []
        for month_start, month_end in month_ranges:
            transactions = get_transactions_in_date_range(
                con, category.account_guid, month_start, month_end
            )
            total = sum_real_numbers(
                RealNumber(transaction.value_num, transaction.value_denom)
                for transaction in transactions
                if transaction.value_num is not None
                and transaction.value_denom is not None
            )
            monthly_totals.append(total)

        # If the category has any non-zero monthly totals, we include it in the chart
        # Income is a debit from income accounts, so we negate the total to show it as a positive value in the chart
        if any(monthly.num != 0 for monthly in monthly_totals):
            y_data.append((category.name, [-float(x) for x in monthly_totals]))

    stacked_bar_chart("Income by Category", "Month", x_axis_labels, "Amount", y_data)


def main():
    report()
