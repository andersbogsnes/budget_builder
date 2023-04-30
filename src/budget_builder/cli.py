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
def categorize(ctx: typer.Context):
    repo = ClassificationRepo(ctx.obj)
    parsed_rows = read_from_file(INPUT_PATH)

    repo.add_expenses(parsed_rows)

    categories = repo.get_categories()
    category_ids = {category.id: category for category in categories}

    for expense in repo.get_uncategorized_expenses():
        console.print(expense)
        console.print(render_categories(categories))

        while True:
            choice: str = Prompt.ask("What category is the item? ",
                                     console=console)
            match choice.lower():
                case "new category" | "n":
                    new_category_name = Prompt.ask("What's the category name?", console=console)
                    is_fixed = Confirm.ask("Is it a fixed cost?", console=console)

                    new_category = repo.add_category(new_category_name, is_fixed)
                    categories.append(new_category)
                    category_ids[new_category.id] = new_category
                    break

                case "quit" | "q":
                    console.print("Quitting...")
                    sys.exit(1)
                case _ as choice if choice.isdigit() and int(choice) in category_ids:
                    repo.set_category(expense.id, category_ids[int(choice)])
                    break
                case _ as e:
                    console.print(f"Invalid selection: {e}")


if __name__ == "__main__":
    app()
