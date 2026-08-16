import dataclasses
import sqlite3
import typing

import gc_reports.accounts


@dataclasses.dataclass
class ExpenseCategory:
    account_guid: str
    name: str


def get_categories_by_type(
    con: sqlite3.Connection,
    accounts: gc_reports.accounts.Accounts,
    type: typing.Literal["EXPENSE", "INCOME"],
) -> list[ExpenseCategory]:
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
        ExpenseCategory(account_guid=guid, name=":".join(accounts[guid].full_name[2:]))
        for (guid,) in res.fetchall()
    ]
    return categories
