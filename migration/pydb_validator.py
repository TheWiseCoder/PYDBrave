from pypomes_core import (
    validate_format_error, validate_bool
)
from pypomes_db import (
    db_get_engines, db_get_params, db_assert_connection
)
from sqlalchemy.sql.elements import Type

from . import pydb_common, pydb_types


def assert_rdbms_dual(errors: list[str],
                      scheme: dict) -> tuple[str, str]:

    engines: list[str] = db_get_engines()
    source_rdbms: str | None = scheme.get("from-rdbms")
    if source_rdbms not in engines:
        # 142: Invalid value {}: {}
        errors.append(validate_format_error(142, source_rdbms,
                                            "unknown or unconfigured RDBMS engine", "@from-rdbms"))
        source_rdbms = None

    target_rdbms: str | None = scheme.get("to-rdbms")
    if target_rdbms not in engines:
        # 142: Invalid value {}: {}
        errors.append(validate_format_error(142, target_rdbms,
                                            "unknown or unconfigured RDBMS engine", "@to-rdbms"))
        target_rdbms = None

    if source_rdbms and source_rdbms == target_rdbms:
        # 126: {} cannot be assigned for attributes {} at the same time
        errors.append(validate_format_error(126, source_rdbms,
                                            "'from-rdbms' and 'to-rdbms'"))
    if not errors and \
       (source_rdbms != "oracle" or target_rdbms != "postgres"):
        # 101: {}
        errors.append(validate_format_error(101,
                                            "This migration path has not been validated yet. "
                                            "In case of urgency, please email the developer."))
    return source_rdbms, target_rdbms


def assert_migration(errors: list[str],
                     scheme: dict) -> None:

    # validate the migration parameters
    assert_migration_params(errors=errors)

    # validate the migration steps
    assert_migration_steps(errors=errors,
                           scheme=scheme)

    # validate the source and target RDBMS engines
    source_rdbms, target_rdbms = assert_rdbms_dual(errors=errors,
                                                   scheme=scheme)

    # assert the connection parameters for both engines
    if source_rdbms:
        db_assert_connection(errors=errors,
                             engine=source_rdbms)
    if target_rdbms:
        db_assert_connection(errors=errors,
                             engine=target_rdbms)

    # validate the include and exclude tables lists
    if scheme.get("include-tables") and scheme.get("exclude-tables"):
        # 151: "Attributes {} cannot be assigned values at the same time
        errors.append(validate_format_error(151, "'include-tables', 'exclude-tables'"))

    # validate the external columns list
    assert_column_types(errors=errors,
                        scheme=scheme)


def assert_migration_params(errors: list[str]) -> None:

    if pydb_common.MIGRATION_BATCH_SIZE < 1000 or \
       pydb_common.MIGRATION_BATCH_SIZE > 10000000:
        # 151: Invalid value {}: must be in the range {}
        errors.append(validate_format_error(151, pydb_common.MIGRATION_BATCH_SIZE,
                                            [1000, 10000000], "@batch-size"))

    if pydb_common.MIGRATION_CHUNK_SIZE < 1024 or \
       pydb_common.MIGRATION_CHUNK_SIZE > 16777216:
        # 151: Invalid value {}: must be in the range {}
        errors.append(validate_format_error(151, pydb_common.MIGRATION_CHUNK_SIZE,
                                            [1024, 16777216], "@batch-size"))

    if pydb_common.MIGRATION_MAX_PROCESSES < 1 or \
       pydb_common.MIGRATION_MAX_PROCESSES > 1000:
        # 151: Invalid value {}: must be in the range {}
        errors.append(validate_format_error(151, pydb_common.MIGRATION_MAX_PROCESSES,
                                            [1, 100], "@max-processes"))


def assert_migration_steps(errors: list[str],
                           scheme: dict) -> None:

    # retrieve the migration steps
    step_metadata: bool = validate_bool(errors=errors,
                                        scheme=scheme,
                                        attr="migrate-metadata",
                                        required=True)
    step_plaindata: bool = validate_bool(errors=errors,
                                         scheme=scheme,
                                         attr="migrate-plaindata",
                                         required=True)
    step_lobdata: bool = validate_bool(errors=errors,
                                       scheme=scheme,
                                       attr="migrate-lobdata",
                                       required=True)
    # validate them
    err_msg: str | None = None
    if not step_metadata and not step_lobdata and not step_plaindata:
        err_msg = "At least one migration step must be indicated"
    elif step_metadata and step_lobdata and not step_plaindata:
        err_msg = "Migrating the metadata and the LOBs requires migrating the plain data as well"
    if err_msg:
        # 101: {}
        errors.append(validate_format_error(101, err_msg))


def assert_column_types(errors: list[str] | None,
                        scheme: dict) -> dict[str, Type]:

    # initialize the return variable
    result: dict[str, Type] | None = None

    # process the foreign columns list
    foreign_columns: list[dict[str, str]] = scheme.get("external-columns")
    if foreign_columns:
        rdbms: str = scheme.get("to-rdbms")
        result = {}
        for foreign_column in foreign_columns:
            type_name: str = foreign_column.get("column-type")
            column_type: Type = pydb_types.name_to_class(rdbms=rdbms,
                                                         type_name=type_name)
            if column_type:
                result[foreign_column.get("column-name").lower()] = column_type
            elif isinstance(errors, list):
                # 142: Invalid value {}: {}
                errors.append(validate_format_error(142, type_name,
                                                    f"not a valid column type for RDBMS {rdbms}"))

    return result


def get_migration_context(scheme: dict) -> dict:

    # obtain the source RDBMS parameters
    from_rdbms: str = scheme.get("from-rdbms")
    from_params = db_get_params(engine=from_rdbms)
    if isinstance(from_params, dict):
        from_params["rdbms"] = from_rdbms

    # obtain the target RDBMS parameters
    to_rdbms: str = scheme.get("to-rdbms")
    to_params = db_get_params(engine=to_rdbms)
    if isinstance(to_params, dict):
        to_params["rdbms"] = to_rdbms

    # build the return data
    result: dict = {
        "configuration": pydb_common.get_migration_params(),
        "from": from_params,
        "to": to_params
    }

    return result
