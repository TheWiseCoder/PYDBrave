from logging import Logger
from pypomes_db import db_get_params


def build_connection_string() -> str:

    params: dict = db_get_params("postgres")
    return (
        f"mssql+pyodbc://{params.get('user')}:"
        f"{params.get('pwd')}@{params.get('host')}:"
        f"{params.get('port')}/{params.get('name')}?driver={params.get('driver')}"
    )


def build_bulk_select_stmt(schema: str,
                           table: str,
                           columns: str,
                           offset: int,
                           batch_size: int) -> str:
    return (
        f"SELECT {columns} "
        f"FROM {schema}.{table} "
        f"ORDER BY rowid "
        f"OFFSET {offset} ROWS FETCH NEXT {batch_size} ROWS ONLY"
    )


def build_bulk_insert_stmt(schema: str,
                           table: str,
                           columns: str) -> str:

    values: list[str] = [", %s"] * len(columns)
    return (
        f"INSERT INTO {schema}.{table} "
        f"({columns}) "
        f"VALUES({values[2:]})"
    )


def disable_restrictions(_errors: list[str], _logger: Logger) -> None:

    pass
