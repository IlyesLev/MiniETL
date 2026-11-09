import unittest
from unittest.mock import patch, MagicMock
from mini_etl.main import load_data

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


if __name__ == "__main__":
    unittest.main()
