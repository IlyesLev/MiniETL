import logging
import os
import re
from pathlib import Path

import snowflake.connector
from snowflake.connector.pandas_tools import write_pandas

logger = logging.getLogger(__name__)


def _format_identifier(identifier):
    if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_$]*", identifier):
        return identifier
    return '"' + identifier.replace('"', '""') + '"'


def get_snowflake_connection():
    project_root = Path(__file__).resolve().parents[3]
    private_key_file = (
        project_root / os.environ["SNOWFLAKE_PRIVATE_KEY_FILE"]
    )

    connection_parameters = {
        "account": os.environ["SNOWFLAKE_ACCOUNT"],
        "user": os.environ["SNOWFLAKE_USER"],
        "warehouse": os.environ["SNOWFLAKE_WAREHOUSE"],
        "database": os.environ["SNOWFLAKE_DATABASE"],
        "schema": os.environ["SNOWFLAKE_SCHEMA"],
        "role": os.environ["SNOWFLAKE_ROLE"],
        "private_key_file": str(private_key_file),
        "private_key_password": os.environ[
            "SNOWFLAKE_PRIVATE_KEY_PASSPHRASE"
        ],
        "enable_server_session_keep_alive_auto_detection": True,
    }

    return snowflake.connector.connect(**connection_parameters)


def load_data(dataframe, destination, load_config):
    schema = destination["schema"]
    table = destination["table"]
    mode = load_config["mode"]

    if mode != "full_refresh":
        raise ValueError(f"Unsupported Snowflake load mode: {mode}")

    logger.info(
        "Loading data into Snowflake: %s.%s",
        schema,
        table,
    )

    if dataframe.empty:
        logger.warning(
            "Source returned zero rows. "
            "Skipping destination replacement."
        )
        return

    dataframe = dataframe.copy()
    dataframe.columns = [
        str(column).upper()
        for column in dataframe.columns
    ]

    connection = get_snowflake_connection()
    try:
        database = os.environ["SNOWFLAKE_DATABASE"]
        with connection.cursor() as cursor:
            cursor.execute(
                "USE SCHEMA "
                f"{_format_identifier(database)}."
                f"{_format_identifier(schema)}"
            )

        success, chunks, rows, output = write_pandas(
            conn=connection,
            df=dataframe,
            table_name=table,
            schema=schema,
            database=database,
            auto_create_table=True,
            overwrite=True,
            quote_identifiers=False,
        )

        if not success:
            raise RuntimeError(f"Snowflake load failed: {output}")

        logger.info(
            "Snowflake load complete: %s rows in %s chunks",
            rows,
            chunks,
        )
    finally:
        connection.close()
