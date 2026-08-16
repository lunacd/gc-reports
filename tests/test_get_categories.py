import importlib.resources
import sqlite3
import typing

import pytest

import gc_reports.accounts
from gc_reports.expenses import ExpenseCategory, get_categories_by_type


@pytest.mark.parametrize(
    "file,expected_categories,type",
    [
        ("empty.gnucash", [], "EXPENSE"),
        ("empty.gnucash", [], "INCOME"),
        (
            "simple.gnucash",
            [
                ExpenseCategory("b07029a6658b46d98b368e2671bc1c25", "Auto:Fees"),
                ExpenseCategory("83920b7ade964953866a36031a2b6ba5", "Medical Expenses"),
            ],
            "EXPENSE",
        ),
        (
            "simple.gnucash",
            [
                ExpenseCategory("979e71279ca54197ac65e53a640dc479", "Salary"),
            ],
            "INCOME",
        ),
    ],
)
def test_get_categories_by_type(
    file: str,
    expected_categories: list[ExpenseCategory],
    type: typing.Literal["EXPENSE", "INCOME"],
) -> None:
    # GIVEN: a gnucash database
    with importlib.resources.path("tests.data", file) as db_path:
        con = sqlite3.connect(db_path)
    accounts = gc_reports.accounts.get_accounts(con)

    # WHEN: we call the function to get expense categories
    categories = get_categories_by_type(con, accounts, type)

    # THEN: we should get the expected categories
    assert categories == expected_categories
