import pathlib

import sqlalchemy as sa
import typer
from rich.console import Console
from rich.prompt import Prompt
from sqlalchemy.orm import Session

from budget_builder.categorize import Base, ClassificationRepo
from budget_builder.data import load_csv, parse_row

INPUT_PATH = pathlib.Path(
    "/home/anders/projects/budget_builder/data/Fælleskonto_2022.csv"
)

DB_URL = "sqlite:///test.db"
engine = sa.create_engine(DB_URL)
console = Console()

app = typer.Typer()
category = typer.Typer()
categorize = typer.Typer()

def create_repo(ctx: typer.Context):
    with Session(engine) as session:
        ctx

app.add_typer(category, name="category")
app.add_typer(categorize, name="categorize")

@category.command()
def add(name: str, is_fixed: bool = False):
    pass


@categorize.command()
def categorize():
    rows = load_csv(INPUT_PATH)
    parsed_rows = map(parse_row, rows)

    Base.metadata.create_all(engine)

    with Session(engine) as session:
        repo = ClassificationRepo(session)
        repo.add_expenses(list(parsed_rows))

        uncategorized = repo.get_uncategorized_expenses()
        categories = repo.get_existing_categories()
        existing_categories = {category.name: category for category in categories}
        for expense in uncategorized:
            console.print(f"Amount: {expense.amount}")
            console.print(f"Description: {expense.description}")
            choice = Prompt.ask("What category is the item?",
                                console=console,
                                choices=list(existing_categories))
            repo.categorize(expense.id, existing_categories[choice])


if __name__ == "__main__":
    categorize()
