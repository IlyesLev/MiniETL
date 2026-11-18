import argparse
import logging
from contextlib import closing
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

from mini_etl.config.loader import load_pipeline_config
from mini_etl.destinations import postgresql
from mini_etl.destinations import snowflake
from mini_etl.metadata.metadata import (
    create_metadata_engine,
    create_session_factory,
)
from mini_etl.metadata.repository import PipelineRunRepository
from mini_etl.sources.sqlserver import extract_tables


# --------------------------------------------------
# Project configuration
# --------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]

load_dotenv(PROJECT_ROOT / ".env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)


# --------------------------------------------------
# Destination router
# --------------------------------------------------
def load_data(
    dataframe: pd.DataFrame,
    config: dict
) -> None:
    """Route extracted data to the configured destination."""

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


def load_tables(config: dict) -> None:
    """Extract and load each configured or discovered source table."""
    with closing(extract_tables(config["source"])) as tables:
        for source_table, dataframe in tables:
            destination = config["destination"].copy()
            destination.setdefault("table", source_table)
            load_data(
                dataframe,
                {
                    "destination": destination,
                    "load": config["load"],
                },
            )


# --------------------------------------------------
# Run pipeline
# --------------------------------------------------
def run_pipeline(pipeline_name: str) -> None:
    config = load_pipeline_config(pipeline_name)
    pipeline_id = config["pipeline"]["id"]

    logger.info(
        "MiniETL pipeline started: %s (id=%s)",
        pipeline_name,
        pipeline_id
    )

    metadata_engine = create_metadata_engine()

    try:
        session_factory = create_session_factory(metadata_engine)

        with session_factory() as session:
            repository = PipelineRunRepository(session)

            # Commit the run record before extraction/loading starts.
            # This ensures a later ETL failure cannot roll back the record.
            with session.begin():
                run = repository.create_run(pipeline_id)
                run_id = run.id

            try:
                load_tables(config)

            except Exception as exc:
                with session.begin():
                    repository.mark_failed(run_id, str(exc))

                logger.exception(
                    "MiniETL pipeline failed: %s",
                    pipeline_name
                )
                raise

            else:
                with session.begin():
                    repository.mark_succeeded(run_id)

                logger.info(
                    "MiniETL pipeline completed successfully: %s",
                    pipeline_name
                )

    finally:
        metadata_engine.dispose()


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
