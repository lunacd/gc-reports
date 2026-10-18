import dataclasses
import sqlite3
import typing

from gc_reports.account import Accounts
from gc_reports.algebra import RealNumber, sum_real_numbers
from gc_reports.date_utils import MonthRanges
from gc_reports.transaction import get_transactions_in_date_range


@dataclasses.dataclass
class IncomeExpenseCategory:
    account_guid: str
    name: str


def get_categories_by_type(
    con: sqlite3.Connection,
    accounts: Accounts,
    type: typing.Literal["EXPENSE", "INCOME"],
) -> list[IncomeExpenseCategory]:
    cur = con.cursor()
    # Find accounts that are of type 'EXPENSE' and have at least one split associated with them
    res = cur.execute(
        """
        SELECT guid FROM accounts
        WHERE account_type = ?
            AND EXISTS (SELECT 1 FROM splits WHERE splits.account_guid = accounts.guid)
        """,
        (type,),
    )
    # Here we strip the leading Root Account:Expenses from the full name of the account
    # This assumes all EXPENSE accounts are under a top-level expense account
    categories = [
        IncomeExpenseCategory(
            account_guid=guid, name=":".join(accounts[guid].full_name[2:])
        )
        for (guid,) in res.fetchall()
    ]
    return categories


def get_total_in_time_ranges(
    con: sqlite3.Connection,
    accounts: Accounts,
    ranges: MonthRanges,
    type: typing.Literal["INCOME", "EXPENSE"],
) -> list[tuple[str, list[RealNumber]]]:
    results: list[tuple[str, list[RealNumber]]] = []
    categories = get_categories_by_type(con, accounts, type)

    for category in categories:
        monthly_totals: list[RealNumber] = []
        for month_start, month_end in ranges:
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
        if any(monthly.num != 0 for monthly in monthly_totals):
            # Income is a debit from income accounts, so we negate the total to show it as a positive value in the chart
            if type == "INCOME":
                results.append((category.name, [-x for x in monthly_totals]))
            else:
                results.append((category.name, monthly_totals))

    return results
