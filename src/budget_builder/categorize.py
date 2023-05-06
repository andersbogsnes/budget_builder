from dataclasses import dataclass

import sqlalchemy as sa
from rich.align import Align
from rich.console import Group
from rich.rule import Rule
from rich.table import Table
from sqlalchemy.orm import Session

from budget_builder.data import TransactionRow
from budget_builder.models import Category, Expense


def render_categories(categories: list[Category]) -> Group:
    table = Table()
    table.add_column("Id")
    table.add_column("Category")
    table.add_column("Fixed Cost", justify="right")

    for category in categories:
        table.add_row(str(category.id), category.name, str(category.is_fixed_cost))

    return Group(
        Rule("[bold green]Existing Categories"),
        Align(Group(table, "(n) New Category\n(q) Quit"), align="center"),
    )


@dataclass
class ClassificationRepo:
    session: Session

    def add_category(self, category: str, is_fixed_cost: bool = False) -> Category:
        sql = sa.select(Category).where(Category.name == category)
        new_category = Category(name=category, is_fixed_cost=is_fixed_cost)

        if existing_category := self.session.execute(sql).scalar_one_or_none():
            return existing_category
        self.session.add(new_category)
        self.session.commit()
        return new_category

    def get_categories(self) -> list[Category]:
        sql = sa.select(Category)
        return list(self.session.execute(sql).scalars())

    def get_expense_by_name(self, expense_name: str) -> Expense | None:
        sql = sa.select(Expense).filter(Expense.description == expense_name)
        if expense := self.session.execute(sql).scalar_one_or_none():
            return expense

    def _get_existing_hashes(self) -> list[str]:
        sql = sa.select(Expense.md5_hash)
        return list(self.session.execute(sql).scalars())

    def add_expenses(self, expenses: list[TransactionRow]):
        existing_expenses = self._get_existing_hashes()
        expenses = [
            Expense(**expense.dict())
            for expense in expenses
            if expense.md5_hash not in existing_expenses
        ]

        self.session.add_all(expenses)
        self.session.commit()
        return expenses

    def get_uncategorized_expense(self) -> Expense:
        sql = sa.select(Expense).where(Expense.category_id.is_(None)).limit(1)
        return self.session.execute(sql).scalar_one_or_none()

    def set_category(self, expense_id: int, category: Category) -> None:
        if expense := self.session.get(Expense, expense_id):
            sql = (
                sa.update(Expense)
                .where(Expense.description == expense.description)
                .where(Expense.category_id.is_(None))
                .values(category_id=category.id)
            )
            self.session.execute(sql)
            self.session.commit()
