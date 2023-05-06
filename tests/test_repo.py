import datetime
import decimal
import hashlib

import pytest
import sqlalchemy as sa
from sqlalchemy.orm import Session

from budget_builder.categorize import ClassificationRepo
from budget_builder.data import TransactionRow
from budget_builder.db import Base
from budget_builder.models import Category, Expense


@pytest.fixture()
def db_url() -> str:
    return "sqlite:///:memory:"


@pytest.fixture()
def session(db_url: str) -> Session:
    engine = sa.create_engine(db_url)
    with Session(engine) as session:
        yield session


@pytest.fixture()
def repo(session: Session) -> ClassificationRepo:
    repo = ClassificationRepo(session)
    Base.metadata.create_all(session.bind)
    return repo


@pytest.fixture()
def new_category(repo: ClassificationRepo) -> Category:
    return repo.add_category('Groceries')


@pytest.fixture()
def transactions() -> list[TransactionRow]:
    return [
        TransactionRow(
            md5_hash=hashlib.md5("expense1".encode()).hexdigest(),
            date=datetime.date(year=2022, month=4, day=11),
            description="Cleaning Angel",
            amount=decimal.Decimal("-1787.50"),
            remaining=decimal.Decimal("10000")
        ),
        TransactionRow(
            md5_hash=hashlib.md5("expense2".encode()).hexdigest(),
            date=datetime.date(year=2022, month=4, day=11),
            description="Babysitter",
            amount=decimal.Decimal("570.0"),
            remaining=decimal.Decimal("1000")
        ),
        TransactionRow(
            md5_hash=hashlib.md5("expense3".encode()).hexdigest(),
            date=datetime.date(year=2022, month=5, day=6),
            description="Babysitter",
            amount=decimal.Decimal("-600"),
            remaining=decimal.Decimal('120000')
        )
    ]


@pytest.fixture()
def new_expenses(repo: ClassificationRepo, transactions: list[TransactionRow]) -> Expense:
    return repo.add_expenses(transactions)


def test_can_add_new_category(new_category: Category):
    assert new_category


def test_can_get_all_categories(repo: ClassificationRepo, new_category: Category):
    result = repo.get_categories()
    assert result[0].id == new_category.id


def test_can_add_new_category_with_existing_name(new_category: Category, repo: ClassificationRepo):
    result = repo.add_category(new_category.name)
    assert result.id == new_category.id


@pytest.mark.usefixtures("new_expenses")
def test_get_expenses_without_category_correctly_returns_one_expense_without_a_category(
        repo: ClassificationRepo):
    result = repo.get_uncategorized_expense()
    assert result.category is None


def test_can_categorize_expense(new_expenses: list[Expense],
                                repo: ClassificationRepo,
                                new_category: Category,
                                session: Session):
    expense_id = new_expenses[0].id
    repo.set_category(expense_id, new_category)

    result = session.get(Expense, expense_id)
    assert result.category.id == new_category.id


def test_categorizing_one_categorizes_all(new_expenses: list[Expense],
                                          repo: ClassificationRepo,
                                          new_category: Category,
                                          session: Session):
    expense = new_expenses[1]
    repo.set_category(expense.id, new_category)

    sql = (sa.select(sa.func.count(Expense.id))
           .where(Expense.category_id.is_(None))
           .where(Expense.description == expense.description))
    result = session.execute(sql).scalar_one()
    assert result == 0
