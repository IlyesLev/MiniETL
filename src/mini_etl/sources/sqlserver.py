import os
import pyodbc
import pandas as pd
import logging
from collections.abc import Iterator

logger = logging.getLogger(__name__)


def get_connection():
    trusted = os.getenv(
        "SQLSERVER_TRUSTED_CONNECTION", "true"
    ).lower() == "true"

    connection_string = (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        f"SERVER={os.environ['SQLSERVER_HOST']};"
        f"DATABASE={os.environ['SQLSERVER_DATABASE']};"
        "Encrypt=yes;"
        "TrustServerCertificate=yes;"
    )

    if trusted:
        connection_string += "Trusted_Connection=yes;"
    else:
        connection_string += (
            f"UID={os.environ['SQLSERVER_USERNAME']};"
            f"PWD={os.environ['SQLSERVER_PASSWORD']};"
        )

    return pyodbc.connect(connection_string)


def _extract_table(
    connection,
    schema: str,
    table: str,
) -> pd.DataFrame:
    query = (
        f"SELECT * FROM "
        f"[{schema.replace(']', ']]')}]."
        f"[{table.replace(']', ']]')}]"
    )

    logger.info(
        "Extracting from SQL Server: %s.%s",
        schema,
        table
    )

    dataframe = pd.read_sql_query(query, connection)

    logger.info(
        "Extracted %s rows and %s columns from %s.%s",
        len(dataframe),
        len(dataframe.columns),
        schema,
        table,
    )

    return dataframe


def extract_data(source_config: dict) -> pd.DataFrame:
    """Extract one configured table from SQL Server."""
    connection = get_connection()

    try:
        dataframe = _extract_table(
            connection,
            source_config["schema"],
            source_config["table"],
        )
    finally:
        connection.close()

    return dataframe


def extract_tables(
    source_config: dict,
) -> Iterator[tuple[str, pd.DataFrame]]:
    """Yield each configured or schema-discovered table with its data."""
    schema = source_config["schema"]
    connection = get_connection()

    try:
        if "table" in source_config:
            table_names = [source_config["table"]]
        else:
            table_query = """
                SELECT TABLE_NAME
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_SCHEMA = ?
                  AND TABLE_TYPE = 'BASE TABLE'
                ORDER BY TABLE_NAME
            """
            tables = pd.read_sql_query(
                table_query,
                connection,
                params=[schema],
            )
            table_names = tables["TABLE_NAME"].tolist()

            logger.info(
                "Found %s base tables in SQL Server schema %s",
                len(table_names),
                schema,
            )

        for table_name in table_names:
            yield table_name, _extract_table(
                connection,
                schema,
                table_name,
            )
    finally:
        connection.close()

