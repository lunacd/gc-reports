import dataclasses
import sqlite3


@dataclasses.dataclass
class Account:
    guid: str
    name: str
    full_name: list[str]
    account_type: str


type Accounts = dict[str, Account]


def get_accounts(con: sqlite3.Connection) -> Accounts:
    cur = con.cursor()
    cur.execute("SELECT guid, name, account_type, parent_guid FROM accounts")
    raw_accounts = cur.fetchall()

    accounts: Accounts = {}
    raw_account_map: dict[str, tuple[str, str, str | None]] = {
        guid: (name, account_type, parent_guid)
        for guid, name, account_type, parent_guid in raw_accounts
    }

    for guid, _, _, _ in raw_accounts:
        build_account(accounts, raw_account_map, guid)

    return accounts


def build_account(
    accounts: Accounts,
    raw_account_map: dict[str, tuple[str, str, str | None]],
    guid: str,
) -> None:
    """Recursively build the full name of the account and add it to the accounts dictionary"""

    # No actions required, the account has already been built
    if guid in accounts:
        return

    name, account_type, parent_guid = raw_account_map[guid]

    # Root account, no need to build further
    if parent_guid is None or len(parent_guid) == 0:
        accounts[guid] = Account(guid, name, [name], account_type)
        return

    # Build parent account if it hasn't been built yet
    if parent_guid not in accounts:
        build_account(accounts, raw_account_map, parent_guid)

    full_name = accounts[parent_guid].full_name + [name]
    accounts[guid] = Account(guid, name, full_name, account_type)
