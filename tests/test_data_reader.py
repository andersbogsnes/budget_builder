import pathlib
import textwrap
from typing import Generator

import pytest

from budget_builder.data import load_csv, CSVRow, parse_row, TransactionRow


@pytest.fixture()
def raw_data() -> str:
    return textwrap.dedent(
        """\
    Bogføringsdato;Beløb;Afsender;Modtager;Navn;Beskrivelse;Saldo;Valuta;Afstemt
    2022/08/29;-25,00;6297395627;;;1155 ATP EJENDOMME;97139,36;DKK;
    2022/08/29;40385,60;;6297395627;;Lønoverførsel;97164,36;DKK;
    2022/08/26;800,00;;6297395627;;Kopper;56778,76;DKK;
    2022/08/26;-168,91;6297395627;;;Gorillas Technologie;55978,76;DKK;
    2022/08/26;-35,00;6297395627;;;1155 ATP EJENDOMME;56147,67;DKK;
    2022/08/26;-25,00;6297395627;;;1155 ATP EJENDOMME;56182,67;DKK;
    2022/08/26;-15,00;6297395627;;;1155 ATP EJENDOMME;56207,67;DKK;""")


@pytest.fixture()
def csv_file(tmp_path: pathlib.Path, raw_data: str):
    tmp_path.with_suffix(".csv").write_text(raw_data)
    return tmp_path.with_suffix(".csv")


@pytest.fixture()
def data_generator(csv_file: pathlib.Path) -> Generator[CSVRow, None, None]:
    return load_csv(csv_file)


@pytest.fixture()
def parsed_rows(data_generator: Generator[CSVRow, None, None]) -> Generator[
    TransactionRow, None, None]:
    return (parse_row(row) for row in data_generator)


@pytest.fixture()
def loaded_data(parsed_rows: Generator[TransactionRow, None, None]) -> list[TransactionRow]:
    return list(parsed_rows)


def test_load_csv_has_correct_headers(parsed_rows: Generator[TransactionRow, None, None]):
    assert list(next(parsed_rows).dict().keys()) == ["md5_hash", "date", "amount", "description"]


def test_load_csv_contains_correct_number_of_lines(loaded_data: list[TransactionRow],
                                                   raw_data: str):
    """Expect loaded data to have same number of lines as loaded data minus the header row"""
    assert len(loaded_data) == len(raw_data.split("\n")) - 1


def test_payload_has_correct_description(loaded_data: list[TransactionRow], raw_data: str):
    """Expect loaded_data to correctly map to the definition in the raw data"""
    expected = raw_data.splitlines()[1].split(";")[-4]
    assert loaded_data[0].description == expected


def test_each_row_has_different_md5_hash(loaded_data: list[TransactionRow]):
    result = {row.md5_hash for row in loaded_data}
    assert len(result) == len(loaded_data)
