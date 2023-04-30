import datetime
import decimal

import sqlalchemy as sa
from rich.panel import Panel
from rich.text import Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from budget_builder.db import Base


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True)
    is_fixed_cost: Mapped[bool]

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

    def __rich__(self) -> Panel:
        return Panel(
            Text(f"Description: {self.description}\nAmount: {self.amount:,.2f}", justify='center'))
