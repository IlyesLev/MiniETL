import argparse
import logging
from pathlib import Path
from dotenv import load_dotenv
from mini_etl.config.loader import load_pipeline_config
from mini_etl.destinations import postgresql
from mini_etl.destinations import snowflake
from mini_etl.sources.sqlserver import extract_data

# --------------------------------------------------
#  Project configuration
# --------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]

load_dotenv(PROJECT_ROOT / ".env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)


# --------------------------------------------------
#  Destination router
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
#  Run pipeline
# --------------------------------------------------
def run_pipeline(pipeline_name: str):
    logger.info(
        "MiniETL pipeline started: %s",
        pipeline_name
    )

    config = load_pipeline_config(pipeline_name)

    dataframe = extract_data(config["source"])
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

