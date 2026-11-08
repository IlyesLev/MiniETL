import argparse
import logging
from pathlib import Path
import pandas as pd
import pyodbc
from dotenv import load_dotenv
from mini_etl.config.loader import load_pipeline_config
from mini_etl.destinations import postgresql
from mini_etl.destinations import snowflake


# --------------------------------------------------
# 1. Project configuration
# --------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]

load_dotenv(PROJECT_ROOT / ".env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)


# --------------------------------------------------
# 2. SQL Server connection
# --------------------------------------------------
def get_sqlserver_connection():

    import os

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


# --------------------------------------------------
# 3. Extract data
# --------------------------------------------------
def extract_data(config):
    source = config["source"]
    schema = source["schema"]
    table = source["table"]

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

    connection = get_sqlserver_connection()

    try:
        dataframe = pd.read_sql_query(
            query,
            connection
        )
    finally:
        connection.close()

    logger.info(
        "Extracted %s rows and %s columns",
        len(dataframe),
        len(dataframe.columns)
    )

    return dataframe


# --------------------------------------------------
# 4. Destination router
# --------------------------------------------------
def load_data(dataframe, config):
    destination = config["destination"]
    load_config = config["load"]
    destination_type = destination["type"].lower()
    if destination_type == "postgresql":
        postgresql.load_data(
            dataframe,
            destination,
            load_config
        )

    elif destination_type == "snowflake":
        snowflake.load_data(
            dataframe,
            destination,
            load_config
        )

    else:
        raise ValueError(
            f"Unsupported destination type: "
            f"{destination_type}"
        )


# --------------------------------------------------
# 5. Run pipeline
# --------------------------------------------------
def run_pipeline(pipeline_name: str):
    logger.info(
        "MiniETL pipeline started: %s",
        pipeline_name
    )

    config = load_pipeline_config(pipeline_name)

    dataframe = extract_data(config)
    load_data(dataframe, config)

    logger.info(
        "MiniETL pipeline completed successfully"
    )

def main():
    parser = argparse.ArgumentParser(
        description="Run a MiniETL pipeline."
    )

    parser.add_argument(
        "pipeline_name",
        help="Name of the pipeline configuration to execute."
    )

    args = parser.parse_args()

    run_pipeline(args.pipeline_name)


if __name__ == "__main__":
    main()

