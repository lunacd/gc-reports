import dataclasses
import datetime
import sqlite3

from gc_reports.algebra import RealNumber


@dataclasses.dataclass
class Transaction:
    post_date: datetime.datetime
    description: str
    value_num: int | None
    value_denom: int | None

    @property
    def value(self) -> RealNumber | None:
        if self.value_num is None or self.value_denom is None:
            return None
        return RealNumber(self.value_num, self.value_denom)


def get_transactions_in_date_range(
    con: sqlite3.Connection,
    account_guid: str,
    start_datetime: datetime.datetime | None,
    end_datetime: datetime.datetime | None,
) -> list[Transaction]:
    """
    Get transactions for a specific account within an optional date range.
    The date range is inclusive of the start datetime and exclusive of the end datetime.
    """

    cur = con.cursor()
    query = """
        SELECT t.post_date, t.description, s.value_num, s.value_denom
        FROM transactions AS t
        JOIN splits AS s ON t.guid = s.tx_guid
        JOIN accounts AS a ON s.account_guid = a.guid
        WHERE a.guid = ?
        """
    parameters = [account_guid]

    if start_datetime is not None:
        query += " AND t.post_date >= ?"
        parameters.append(start_datetime.astimezone(datetime.UTC).strftime("%Y-%m-%d %H:%M:%S"))
    if end_datetime is not None:
        query += " AND t.post_date < ?"
        parameters.append(end_datetime.astimezone(datetime.UTC).strftime("%Y-%m-%d %H:%M:%S"))

    res = cur.execute(query, parameters)
    return [
        Transaction(
            post_date=datetime.datetime.fromisoformat(transaction[0]).replace(tzinfo=datetime.UTC),
            description=transaction[1],
            value_num=transaction[2],
            value_denom=transaction[3],
        )
        for transaction in res.fetchall()
    ]


def get_transaction_date_range(
    con: sqlite3.Connection,
) -> tuple[datetime.datetime | None, datetime.datetime | None]:
    cur = con.cursor()
    res = cur.execute("SELECT MIN(post_date), MAX(post_date) FROM transactions")
    min_date_stamp, max_date_stamp = res.fetchone()
    min_date = (
        datetime.datetime.strptime(min_date_stamp, "%Y-%m-%d %H:%M:%S").replace(
            tzinfo=datetime.UTC
        )
        if min_date_stamp is not None
        else None
    )
    max_date = (
        datetime.datetime.strptime(max_date_stamp, "%Y-%m-%d %H:%M:%S").replace(
            tzinfo=datetime.UTC
        )
        if max_date_stamp is not None
        else None
    )
    return min_date, max_date
