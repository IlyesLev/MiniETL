import unittest
from unittest.mock import patch, MagicMock
from mini_etl.main import load_data
from mini_etl.main import load_tables

class TestDestinationRouting(unittest.TestCase):
    def setUp(self):
        self.dataframe = MagicMock()

    @patch("mini_etl.main.postgresql.load_data")
    def test_routes_to_postgresql(self, mock_load):
        config = {
            "destination": {
                "type": "postgresql",
                "schema": "public",
                "table": "authors",
            },
            "load": {
                "mode": "full_refresh"
            }
        }

        load_data(self.dataframe, config)

        mock_load.assert_called_once_with(
            self.dataframe,
            config["destination"],
            config["load"]
        )

    @patch("mini_etl.main.snowflake.load_data")
    def test_routes_to_snowflake(self, mock_load):
        config = {
            "destination": {
                "type": "snowflake",
                "schema": "ANALYTICS",
                "table": "AUTHORS",
            },
            "load": {
                "mode": "full_refresh"
            }
        }

        load_data(self.dataframe, config)

        mock_load.assert_called_once_with(
            self.dataframe,
            config["destination"],
            config["load"]
        )

    def test_unsupported_destination(self):
        config = {
            "destination": {
                "type": "mysql"
            },
            "load": {
                "mode": "full_refresh"
            }
        }

        with self.assertRaisesRegex(
            ValueError,
            "Unsupported destination type: mysql"
        ):
            load_data(self.dataframe, config)


class TestSchemaTableLoading(unittest.TestCase):
    @patch("mini_etl.main.load_data")
    @patch("mini_etl.main.extract_tables")
    def test_loads_each_source_table_into_matching_destination(
        self,
        mock_extract_tables,
        mock_load_data,
    ):
        first_dataframe = MagicMock()
        second_dataframe = MagicMock()

        def table_iterator():
            yield "Author", first_dataframe
            yield "Book", second_dataframe

        mock_extract_tables.return_value = table_iterator()
        config = {
            "source": {"type": "sqlserver", "schema": "dbo"},
            "destination": {"type": "postgresql", "schema": "minietl"},
            "load": {"mode": "full_refresh"},
        }

        load_tables(config)

        self.assertEqual(mock_load_data.call_count, 2)
        mock_load_data.assert_any_call(
            first_dataframe,
            {
                "destination": {
                    "type": "postgresql",
                    "schema": "minietl",
                    "table": "Author",
                },
                "load": {"mode": "full_refresh"},
            },
        )
        mock_load_data.assert_any_call(
            second_dataframe,
            {
                "destination": {
                    "type": "postgresql",
                    "schema": "minietl",
                    "table": "Book",
                },
                "load": {"mode": "full_refresh"},
            },
        )


if __name__ == "__main__":
    unittest.main()
