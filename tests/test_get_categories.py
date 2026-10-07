import sqlite3
import typing

import pytest

import gc_reports.accounts
from gc_reports.expenses import ExpenseCategory, get_categories_by_type

# Minimal gnucash schema covering the tables and columns used by the code under test.
SCHEMA_SQL = """
CREATE TABLE accounts (
    guid TEXT PRIMARY KEY NOT NULL,
    name TEXT NOT NULL,
    account_type TEXT NOT NULL,
    parent_guid TEXT
);

CREATE TABLE splits (
    guid TEXT PRIMARY KEY NOT NULL,
    account_guid TEXT NOT NULL
);
"""

# An empty gnucash book: a chart of accounts without any splits.
EMPTY_SQL = (
    SCHEMA_SQL
    + """
INSERT INTO accounts (guid, name, account_type, parent_guid) VALUES
    ('ea7a8f6160c3469cae341b4d642a6a4a', 'Root Account', 'ROOT', NULL),
    ('ab683de25fe7471b86870934593f9308', 'Income', 'INCOME', 'ea7a8f6160c3469cae341b4d642a6a4a'),
    ('450fa1b67f774633b40c24327236d39a', 'Expenses', 'EXPENSE', 'ea7a8f6160c3469cae341b4d642a6a4a');
"""
)

# A simple gnucash book with splits on some expense and income accounts.
SIMPLE_SQL = (
    SCHEMA_SQL
    + """
INSERT INTO accounts (guid, name, account_type, parent_guid) VALUES
    ('ea7a8f6160c3469cae341b4d642a6a4a', 'Root Account', 'ROOT', NULL),
    ('ab683de25fe7471b86870934593f9308', 'Income', 'INCOME', 'ea7a8f6160c3469cae341b4d642a6a4a'),
    ('979e71279ca54197ac65e53a640dc479', 'Salary', 'INCOME', 'ab683de25fe7471b86870934593f9308'),
    ('450fa1b67f774633b40c24327236d39a', 'Expenses', 'EXPENSE', 'ea7a8f6160c3469cae341b4d642a6a4a'),
    ('fcb946a91c1b4e798ff89d27459a8bc7', 'Auto', 'EXPENSE', '450fa1b67f774633b40c24327236d39a'),
    ('b07029a6658b46d98b368e2671bc1c25', 'Fees', 'EXPENSE', 'fcb946a91c1b4e798ff89d27459a8bc7'),
    ('83920b7ade964953866a36031a2b6ba5', 'Medical Expenses', 'EXPENSE', '450fa1b67f774633b40c24327236d39a');

INSERT INTO splits (guid, account_guid) VALUES
    ('cc121d43e86244e1b3b2ee66d44c3b12', '979e71279ca54197ac65e53a640dc479'),
    ('31d46fa2259846cda46abaa14e19a651', 'b07029a6658b46d98b368e2671bc1c25'),
    ('deb1411bc71747148c21458d5df37374', '83920b7ade964953866a36031a2b6ba5');
"""
)


def create_connection(sql: str) -> sqlite3.Connection:
    con = sqlite3.connect(":memory:")
    con.executescript(sql)
    return con


@pytest.mark.parametrize(
    "sql,expected_categories,type",
    [
        pytest.param(EMPTY_SQL, [], "EXPENSE", id="empty-expense"),
        pytest.param(EMPTY_SQL, [], "INCOME", id="empty-income"),
        pytest.param(
            SIMPLE_SQL,
            [
                ExpenseCategory("b07029a6658b46d98b368e2671bc1c25", "Auto:Fees"),
                ExpenseCategory("83920b7ade964953866a36031a2b6ba5", "Medical Expenses"),
            ],
            "EXPENSE",
            id="simple-expense",
        ),
        pytest.param(
            SIMPLE_SQL,
            [
                ExpenseCategory("979e71279ca54197ac65e53a640dc479", "Salary"),
            ],
            "INCOME",
            id="simple-income",
        ),
    ],
)
def test_get_categories_by_type(
    sql: str,
    expected_categories: list[ExpenseCategory],
    type: typing.Literal["EXPENSE", "INCOME"],
) -> None:
    # GIVEN: an in-memory gnucash database built from the SQL fixture
    con = create_connection(sql)
    accounts = gc_reports.accounts.get_accounts(con)

    # WHEN: we call the function to get expense categories
    categories = get_categories_by_type(con, accounts, type)

    # THEN: we should get the expected categories
    assert categories == expected_categories
