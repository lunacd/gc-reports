import dataclasses
import datetime
import pathlib
import sqlite3
import tomllib

import pydantic

from gc_reports.account import Accounts
from gc_reports.algebra import RealNumber
from gc_reports.date_utils import next_month_start
from gc_reports.income_expense import IncomeExpenseCategory, get_categories_by_type
from gc_reports.transaction import (
    get_transactions_in_date_range,
)


class Budget(pydantic.BaseModel):
    budgets: list[BudgetItem]

    @pydantic.computed_field
    @property
    def budget_by_category(self) -> dict[str, list[BudgetItem]]:
        result: dict[str, list[BudgetItem]] = {}
        for budget in self.budgets:
            result.setdefault(budget.category, [])
            result[budget.category].append(budget)
        for category, items in result.items():
            result[category] = sorted(items, key=lambda item: item.effective_date)
        return result


class BudgetItem(pydantic.BaseModel):
    effective_date: datetime.datetime
    category: str
    monthly_budget: int
    max_rollover: int

    @pydantic.field_validator("effective_date", mode="after")
    @classmethod
    def set_local_timezone(cls, value: datetime.datetime):
        return value.replace(tzinfo=datetime.datetime.now().astimezone().tzinfo)

def load_budget(path: pathlib.Path) -> Budget:
    with path.open("br") as f:
        raw = tomllib.load(f)
        return Budget.model_validate(raw)


@dataclasses.dataclass
class BudgetResult:
    rolled_over: RealNumber
    budgeted: RealNumber
    used: RealNumber


def generate_all_budget_stats(
    con: sqlite3.Connection,
    accounts: Accounts,
    budget_path: pathlib.Path,
    start: datetime.datetime,
    end: datetime.datetime,
) -> dict[str, BudgetResult]:
    categories = get_categories_by_type(con, accounts, "EXPENSE")
    budget = load_budget(budget_path)

    result: dict[str, BudgetResult] = {}

    for category in categories:
        budget_result = evaluate_budget_in_date_range(con, budget, category, start, end)
        if budget_result is None:
            continue
        result[category.name] = budget_result

    return result


def evaluate_budget_in_date_range(
    con: sqlite3.Connection,
    budget: Budget,
    category: IncomeExpenseCategory,
    start: datetime.datetime,
    end: datetime.datetime,
) -> BudgetResult | None:
    if category.name not in budget.budget_by_category:
        return None

    budget_items = budget.budget_by_category[category.name]

    if len(budget_items) == 0:
        return None

    # All transactions matter, up to earliest defined budget, because of rollover
    transactions = get_transactions_in_date_range(
        con,
        category.account_guid,
        budget_items[0].effective_date,
        end,
    )

    # Process transactions
    next_month = next_month_start(budget_items[0].effective_date)
    remaining_budget = RealNumber(0, 100)
    in_range = False
    rolled_over = RealNumber(0, 100)
    current_budget_index = 0
    total_budgeted = RealNumber(0, 100)
    used_budget = RealNumber(0, 100)

    for transaction in transactions:
        # Extra processing is needed when:
        # 1. Crossing into the requested range
        # 2. When a new budget comes into effect
        # 3. When we enter a new month
        # The order of processing is important. The best way to figure out this order is to think about what
        # happens when:
        # We request budget status starting July 1st, a new budget comes into effect July 1st, and it's a new
        # month, obviously.
        # Then:
        # 1. The rolled_over amount should not count the budget allowance of July, as that is in the requested range.
        # Hence, in_range processing should happen first.
        # 2. The new policy going into effect on July 1st should affect July budgeting, so that should be processed
        # second.
        # 3. The new month is processed last.

        if not in_range and transaction.post_date > start:
            in_range = True
            rolled_over = remaining_budget

        if (
            current_budget_index + 1 < len(budget_items)
            and transaction.post_date
            > budget_items[current_budget_index + 1].effective_date
        ):
            current_budget_index += 1

        if transaction.post_date > next_month:
            next_month = next_month_start(next_month)
            current_budget = RealNumber(
                budget_items[current_budget_index].monthly_budget, 1
            )
            remaining_budget += current_budget
            if in_range:
                total_budgeted += current_budget

        if transaction.value is not None:
            remaining_budget -= transaction.value
            used_budget += transaction.value

    return BudgetResult(
        rolled_over=rolled_over, budgeted=total_budgeted, used=used_budget
    )
