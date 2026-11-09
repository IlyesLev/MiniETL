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


    @patch("mini_etl.destinations.postgresql.get_postgresql_engine")
    def test_loads_non_empty_dataframe(self, mock_get_engine):
        dataframe = pd.DataFrame({"id": [1], "name": ["Alice"]})

        destination = {
            "schema": "public",
            "table": "authors"
        }

        load_config = {
            "mode": "full_refresh"
        }

        mock_engine = MagicMock()
        mock_connection = MagicMock()

        mock_engine.begin.return_value.__enter__.return_value = mock_connection
        mock_get_engine.return_value = mock_engine

        with patch.object(dataframe, "to_sql") as mock_to_sql:
            postgresql.load_data(
                dataframe,
                destination,
                load_config
            )

        mock_to_sql.assert_called_once_with(
            name="authors",
            con=mock_connection,
            schema="public",
            if_exists="replace",
            index=False,
            chunksize=1000,
            method="multi"
        )

        mock_engine.dispose.assert_called_once()


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
