import sqlite3
import sys


def main():
    db_path = sys.argv[1]
    con = sqlite3.connect(db_path)

    cur = con.cursor()

    # Get all accounts
    res = cur.execute("SELECT guid, name, account_type FROM accounts")
    accounts = res.fetchall()

    for account in accounts:
        print(f"Account: {account[1]} ({account[0]}) - Type: {account[2]}")

        res = cur.execute(
            "SELECT guid, tx_guid, value_num, value_denom, quantity_num, quantity_denom FROM splits WHERE account_guid = ?",
            (account[0],),
        )
        splits = res.fetchall()
        for split in splits:
            print(
                f"  Split: {split[0]} - Value: {split[2]}/{split[3]} - Quantity: {split[4]}/{split[5]}"
            )


if __name__ == "__main__":
    main()
