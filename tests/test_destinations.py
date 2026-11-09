import unittest
from unittest.mock import MagicMock, patch
import pandas as pd
from mini_etl.destinations import postgresql
from mini_etl.destinations import snowflake

class TestPostgreSQLDestination(unittest.TestCase):
    @patch("mini_etl.destinations.postgresql.get_postgresql_engine")
    def test_empty_dataframe_skips_loading(self, mock_engine):
        dataframe = pd.DataFrame()

        destination = {
            "schema": "public",
            "table": "authors"
        }

        load_config = {
            "mode": "full_refresh"
        }

        postgresql.load_data(
            dataframe,
            destination,
            load_config
        )

        mock_engine.assert_not_called()

class TestSnowflakeDestination(unittest.TestCase):

    @patch("mini_etl.destinations.snowflake.get_snowflake_connection")
    def test_empty_dataframe_skips_loading(self, mock_connection):
        dataframe = pd.DataFrame()

        destination = {
            "schema": "ANALYTICS",
            "table": "AUTHORS"
        }

        load_config = {
            "mode": "full_refresh"
        }

        snowflake.load_data(
            dataframe,
            destination,
            load_config
        )

        mock_connection.assert_not_called()


if __name__ == "__main__":
    unittest.main()
