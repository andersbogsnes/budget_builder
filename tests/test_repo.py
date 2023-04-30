import datetime
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
            amount=-1787.50,
        ),
        TransactionRow(
            md5_hash=hashlib.md5("expense2".encode()).hexdigest(),
            date=datetime.date(year=2022, month=4, day=11),
            description="Babysitter",
            amount=-570.0,
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
def test_get_expenses_without_category_returns_all_expenses(repo: ClassificationRepo,
                                                            transactions: list[TransactionRow]):
    result = repo.get_uncategorized_expenses()
    assert len(result) == len(transactions)


def test_can_categorize_expense(new_expenses: list[Expense],
                                repo: ClassificationRepo,
                                new_category: Category,
                                session: Session):
    expense_id = new_expenses[0].id
    repo.set_category(expense_id, new_category)

    result = session.get(Expense, expense_id)
    assert result.category.id == new_category.id


def test_categorizing_one_categorizes_all():
    # TODO: Finish this test
    pass
