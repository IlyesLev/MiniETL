import os
import logging
from sqlalchemy import create_engine, URL

logger = logging.getLogger(__name__)

def get_postgresql_engine():
    connection_url = URL.create(
        drivername="postgresql+psycopg",
        username=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        host=os.environ["POSTGRES_HOST"],
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        database=os.environ["POSTGRES_DATABASE"],
    )

    return create_engine(
        connection_url,
        pool_pre_ping=True
    )


def load_data(dataframe, destination, load_config):
    schema = destination["schema"]
    table = destination["table"]
    mode = load_config["mode"]

    if mode != "full_refresh":
        raise ValueError(f"Unsupported PostgreSQL load mode: {mode}")

    logger.info(
        "Loading data into PostgreSQL: %s.%s",
        schema,
        table
    )

    if dataframe.empty:
        logger.warning(
            "Source returned zero rows. "
            "Skipping destination replacement."
        )
        return

    engine = get_postgresql_engine()

    try:
        with engine.begin() as connection:

            dataframe.to_sql(
                name=table,
                con=connection,
                schema=schema,
                if_exists="replace",
                index=False,
                chunksize=1000,
                method="multi"
            )

        logger.info(
            "PostgreSQL load complete: %s rows",
            len(dataframe)
        )

    finally:
        engine.dispose()

