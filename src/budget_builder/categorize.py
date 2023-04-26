import contextlib
import datetime
import decimal
from dataclasses import dataclass
from functools import cached_property

import sqlalchemy as sa
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, Session

from budget_builder.data import TransactionRow


class Base(DeclarativeBase):
    pass


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True)
    is_fixed_cost: Mapped[int]

    expenses: Mapped[list["Expense"]] = relationship(
        "Expense", back_populates="category"
    )


class Expense(Base):
    __tablename__ = "expenses"

    id: Mapped[int] = mapped_column(primary_key=True)
    md5_hash: Mapped[str] = mapped_column(unique=True)
    date: Mapped[datetime.date]
    amount: Mapped[decimal.Decimal]
    description: Mapped[str]
    category_id: Mapped[int | None] = mapped_column(sa.ForeignKey("categories.id"))

    category: Mapped[Category] = relationship(
        "Category", back_populates="expenses", lazy="selectin"
    )


@dataclass
class ClassificationRepo:
    db_url: str

    @cached_property
    def engine(self):
        return sa.create_engine(self.db_url)

    @contextlib.contextmanager
    def session(self):
        with Session(self.engine, expire_on_commit=False) as session:
            yield session

    def add_category(self, category: str, is_fixed_cost: bool = False) -> Category:
        sql = sa.select(Category).where(Category.name == category)
        new_category = Category(name=category, is_fixed_cost=is_fixed_cost)

        with self.session() as session:
            if existing_category := session.execute(sql).scalar_one_or_none():
                return existing_category
            session.add(new_category)
            session.commit()
            return new_category

    def get_existing_categories(self) -> list[Category]:
        sql = sa.select(Category)
        with self.session() as session:
            return list(session.execute(sql).scalars())

    def _get_existing_hashes(self) -> list[str]:
        sql = sa.select(Expense.md5_hash)
        with self.session() as session:
            return list(session.execute(sql).scalars())

    def add_expenses(self, expenses: list[TransactionRow]):
        existing_expenses = self._get_existing_hashes()
        expenses = [
            Expense(
                md5_hash=expense.md5_hash,
                date=expense.date,
                amount=expense.amount,
                description=expense.description,
            )
            for expense in expenses
            if expense.md5_hash not in existing_expenses
        ]

        with self.session() as session:
            session.add_all(expenses)
            session.commit()
        return expenses

    def get_uncategorized_expenses(self) -> list[Expense]:
        sql = sa.select(Expense).where(Expense.category_id.is_(None))
        with self.session() as session:
            return list(session.execute(sql).scalars())

    def categorize(self, expense_id: int, category: Category) -> None:
        with self.session() as session:
            if expense := session.get(Expense, expense_id):
                expense.category = category
                session.commit()
