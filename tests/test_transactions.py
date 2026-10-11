import datetime
import sqlite3

import pytest

from gc_reports.transaction import get_transactions_in_date_range


@pytest.fixture
def con() -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    connection.executescript(
        """
        CREATE TABLE transactions (
            guid TEXT PRIMARY KEY,
            post_date TEXT NOT NULL,
            description TEXT NOT NULL
        );
        CREATE TABLE splits (
            tx_guid TEXT NOT NULL,
            account_guid TEXT NOT NULL,
            value_num INTEGER,
            value_denom INTEGER
        );
        CREATE TABLE accounts (guid TEXT PRIMARY KEY);
        INSERT INTO accounts (guid) VALUES ('account');
        INSERT INTO transactions VALUES
            ('tx1', '2024-01-01 00:00:00', 'January'),
            ('tx2', '2024-02-01 00:00:00', 'February'),
            ('tx3', '2024-03-01 00:00:00', 'March');
        INSERT INTO splits VALUES
            ('tx1', 'account', 100, 1),
            ('tx2', 'account', 200, 1),
            ('tx3', 'account', 300, 1);
        """
    )
    return connection


@pytest.mark.parametrize(
    "start_date,end_date,expected",
    [
        (None, None, {("January", 100, 1), ("February", 200, 1), ("March", 300, 1)}),
        (
            datetime.datetime(2024, 2, 1, tzinfo=datetime.UTC),
            None,
            {("February", 200, 1), ("March", 300, 1)},
        ),
        (
            None,
            datetime.datetime(2024, 3, 1, tzinfo=datetime.UTC),
            {("January", 100, 1), ("February", 200, 1)},
        ),
        (
            datetime.datetime(2024, 2, 1, tzinfo=datetime.UTC),
            datetime.datetime(2024, 3, 1, tzinfo=datetime.UTC),
            {("February", 200, 1)},
        ),
    ],
)
def test_get_transactions_in_optional_date_range(
    con: sqlite3.Connection,
    start_date: datetime.datetime | None,
    end_date: datetime.datetime | None,
    expected: set[tuple[str, int, int]],
) -> None:
    transactions = get_transactions_in_date_range(con, "account", start_date, end_date)

    assert {
        (transaction.description, transaction.value_num, transaction.value_denom)
        for transaction in transactions
    } == expected
