import os
import pyodbc
import pandas as pd
import logging

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


def extract_data(source_config: dict) -> pd.DataFrame:
    schema = source_config["schema"]
    table = source_config["table"]

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

    connection = get_connection()

    try:
        dataframe = pd.read_sql_query(query, connection)
    finally:
        connection.close()

    logger.info(
        "Extracted %s rows and %s columns",
        len(dataframe),
        len(dataframe.columns)
    )

    return dataframe

