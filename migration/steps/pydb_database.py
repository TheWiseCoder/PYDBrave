from logging import Logger, DEBUG
from pypomes_db import db_get_param, db_execute
from typing import Any

from migration import pydb_common


def create_schema(errors: list[str],
                  schema: str,
                  rdbms: str,
                  logger: Logger) -> None:

    if rdbms == "oracle":
        stmt: str = f"CREATE USER {schema} IDENTIFIED BY {schema}"
    else:
        user: str = db_get_param(key="user",
                                 engine=rdbms)
        stmt = f"CREATE SCHEMA {schema} AUTHORIZATION {user}"
    db_execute(errors=errors,
               exc_stmt=stmt,
               engine=rdbms,
               logger=logger)


def drop_table(errors: list[str],
               table_name: str,
               rdbms: str,
               logger: Logger) -> None:

    # build drop statement
    if rdbms == "oracle":
        # oracle has no 'IF EXISTS' clause
        drop_stmt: str = \
            (f"BEGIN\n"
             f"  EXECUTE IMMEDIATE 'DROP TABLE {table_name} CASCADE CONSTRAINTS'\n;"
             "EXCEPTION\n"
             "  WHEN OTHERS THEN NULL;"
             "END\n;"
             "/")
    else:
        drop_stmt: str = f"DROP TABLE IF EXISTS {table_name} CASCADE"

    # drop the table
    db_execute(errors=errors,
               exc_stmt=drop_stmt,
               engine=rdbms,
               logger=logger)


def drop_view(errors: list[str],
              view_name: str,
              rdbms: str,
              logger: Logger) -> None:

    # build drop statement
    if rdbms == "oracle":
        # oracle has no 'IF EXISTS' clause
        drop_stmt: str = \
            (f"BEGIN\n"
             f"  EXECUTE IMMEDIATE 'DROP VIEW {view_name}'\n;"
             "EXCEPTION\n"
             "  WHEN OTHERS THEN NULL;"
             "END\n;"
             "/")
    else:
        drop_stmt: str = f"DROP VIEW IF EXISTS {view_name}"

    # drop the view
    db_execute(errors=errors,
               exc_stmt=drop_stmt,
               engine=rdbms,
               logger=logger)


def disable_session_restrictions(errors: list[str],
                                 rdbms: str,
                                 conn: Any,
                                 logger: Logger) -> None:

    # disable session restrictions to speed-up bulk copy
    match rdbms:
        case "mysql":
            pass
        case "oracle":
            pass
        case "postgres":
            db_execute(errors=errors,
                       exc_stmt="SET SESSION_REPLICATION_ROLE TO REPLICA",
                       engine="postgres",
                       connection=conn,
                       logger=logger)
        case "sqlserver":
            pass

    pydb_common.log(logger=logger,
                    level=DEBUG,
                    msg=f"RDBMS {rdbms}, disabled session restrictions to speed-up bulk copying")


def restore_session_restrictions(errors: list[str],
                                 rdbms: str,
                                 conn: Any,
                                 logger: Logger) -> None:

    # restore session restrictions delaying bulk copy
    match rdbms:
        case "mysql":
            pass
        case "oracle":
            pass
        case "postgres":
            db_execute(errors=errors,
                       exc_stmt="SET SESSION_REPLICATION_ROLE TO DEFAULT",
                       engine="postgres",
                       connection=conn,
                       logger=logger)
        case "sqlserver":
            pass

    pydb_common.log(logger=logger,
                    level=DEBUG,
                    msg=f"RDBMS {rdbms}, restored session restrictions delaying bulk copying")
