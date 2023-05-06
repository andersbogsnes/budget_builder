import csv
import datetime
import decimal
import hashlib
import pathlib
import typing

from pydantic import BaseModel


class TransactionRow(BaseModel):
    md5_hash: str
    date: datetime.date
    amount: decimal.Decimal
    description: str
    remaining: decimal.Decimal

    def __str__(self):
        return (
            f"Date: {self.date} Amount: {self.amount} Description: {self.description}"
        )


CSVRow = typing.TypedDict(
    "CSVRow",
    {"Bogføringsdato": str, "Beløb": str, "Beskrivelse": str, "Saldo": str},
)


def load_csv(path: pathlib.Path) -> typing.Generator[CSVRow, None, None]:
    with path.open(encoding="utf-8-sig") as f:
        reader = csv.DictReader(
            f,
            delimiter=";",
        )
        yield from reader


def parse_row(row: CSVRow) -> TransactionRow:
    row = {
        "md5_hash": hashlib.md5(
            f"{row['Bogføringsdato'] + row['Beløb'] + row['Beskrivelse'] + row['Saldo']}".encode()
        ).hexdigest(),
        "date": row["Bogføringsdato"].replace("/", "-"),
        "amount": row["Beløb"].replace(",", "."),
        "description": row["Beskrivelse"],
        "remaining": row["Saldo"].replace(",", "."),
    }

    return TransactionRow.parse_obj(row)


def read_from_file(path: pathlib.Path) -> list[TransactionRow]:
    return [parse_row(row) for row in load_csv(path)]
