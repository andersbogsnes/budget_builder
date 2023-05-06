import pathlib
import sys

import sqlalchemy as sa
import typer
from rich.console import Console
from rich.prompt import Prompt, Confirm
from sqlalchemy.orm import Session

from budget_builder.categorize import ClassificationRepo, render_categories
from budget_builder.data import read_from_file
from budget_builder.db import Base

INPUT_PATH = pathlib.Path(
    "/home/anders/projects/budget_builder/data/Fælleskonto_2022.csv"
)

DB_URL = "sqlite:///test.db"
engine = sa.create_engine(DB_URL)
console = Console()

app = typer.Typer()


@app.callback()
def create_repo(ctx: typer.Context):
    Base.metadata.create_all(engine)
    ctx.obj = ctx.with_resource(Session(engine))


@app.command()
def categorize(ctx: typer.Context, input_file: pathlib.Path):
    repo = ClassificationRepo(ctx.obj)
    parsed_rows = read_from_file(input_file)

    repo.add_expenses(parsed_rows)

    categories = repo.get_categories()
    category_ids = {category.id: category for category in categories}

    while expense := repo.get_uncategorized_expense():
        console.print(expense)
        console.print(render_categories(categories))

        choice: str = Prompt.ask("What category is the item? ", console=console)
        match choice.lower():
            case "new category" | "n":
                new_category_name = Prompt.ask(
                    "What's the category name?", console=console
                )
                is_fixed = Confirm.ask("Is it a fixed cost?", console=console)

                new_category = repo.add_category(new_category_name, is_fixed)
                categories.append(new_category)
                category_ids[new_category.id] = new_category
                repo.set_category(expense.id, new_category)

            case "quit" | "q":
                console.print("Quitting...")
                sys.exit(1)
            case _ as choice if choice.isdigit() and int(choice) in category_ids:
                repo.set_category(expense.id, category_ids[int(choice)])
            case _ as e:
                console.print(f"Invalid selection: {e}")
    console.print("Categorized all expenses")


if __name__ == "__main__":
    app()
