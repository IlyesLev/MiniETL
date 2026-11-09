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


    @patch("mini_etl.destinations.snowflake.write_pandas")
    @patch("mini_etl.destinations.snowflake.get_snowflake_connection")
    def test_loads_non_empty_dataframe(
        self,
        mock_get_connection,
        mock_write_pandas
    ):
        dataframe = pd.DataFrame({
            "id": [1],
            "name": ["Alice"]
        })

        destination = {
            "schema": "ANALYTICS",
            "table": "AUTHORS"
        }

        load_config = {
            "mode": "full_refresh"
        }

        mock_connection = MagicMock()
        mock_get_connection.return_value = mock_connection

        mock_write_pandas.return_value = (
            True,
            1,
            1,
            "Successfully loaded"
        )

        with patch.dict(
            "os.environ",
            {"SNOWFLAKE_DATABASE": "TEST_DB"}
        ):
            snowflake.load_data(
                dataframe,
                destination,
                load_config
            )

        mock_get_connection.assert_called_once()

        mock_write_pandas.assert_called_once()

        call_kwargs = mock_write_pandas.call_args.kwargs

        self.assertEqual(
            list(call_kwargs["df"].columns),
            ["ID", "NAME"]
        )

        self.assertEqual(
            call_kwargs["table_name"],
            "AUTHORS"
        )

        self.assertEqual(
            call_kwargs["schema"],
            "ANALYTICS"
        )

        self.assertEqual(
            call_kwargs["database"],
            "TEST_DB"
        )

        self.assertTrue(call_kwargs["overwrite"])
        self.assertTrue(call_kwargs["auto_create_table"])
        self.assertFalse(call_kwargs["quote_identifiers"])

        mock_connection.cursor.assert_called_once()
        mock_connection.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
