import unittest
from unittest.mock import MagicMock, patch

import pandas as pd

from mini_etl.sources.sqlserver import extract_tables


class TestSQLServerSource(unittest.TestCase):
    @patch("mini_etl.sources.sqlserver.pd.read_sql_query")
    @patch("mini_etl.sources.sqlserver.get_connection")
    def test_extracts_each_base_table_in_schema(
        self,
        mock_get_connection,
        mock_read_sql_query,
    ):
        connection = MagicMock()
        mock_get_connection.return_value = connection
        author_data = pd.DataFrame({"id": [1]})
        book_data = pd.DataFrame({"id": [2]})
        mock_read_sql_query.side_effect = [
            pd.DataFrame({"TABLE_NAME": ["Author", "Book]Entry"]}),
            author_data,
            book_data,
        ]

        tables = list(extract_tables({"schema": "dbo"}))

        self.assertEqual(
            tables,
            [("Author", author_data), ("Book]Entry", book_data)],
        )
        discovery_query = mock_read_sql_query.call_args_list[0]
        self.assertIn("INFORMATION_SCHEMA.TABLES", discovery_query.args[0])
        self.assertEqual(discovery_query.kwargs["params"], ["dbo"])
        self.assertIn(
            "[dbo].[Author]",
            mock_read_sql_query.call_args_list[1].args[0],
        )
        self.assertIn(
            "[dbo].[Book]]Entry]",
            mock_read_sql_query.call_args_list[2].args[0],
        )
        connection.close.assert_called_once()

    @patch("mini_etl.sources.sqlserver.pd.read_sql_query")
    @patch("mini_etl.sources.sqlserver.get_connection")
    def test_extracts_only_explicitly_configured_table(
        self,
        mock_get_connection,
        mock_read_sql_query,
    ):
        connection = MagicMock()
        mock_get_connection.return_value = connection
        dataframe = pd.DataFrame({"id": [1]})
        mock_read_sql_query.return_value = dataframe

        tables = list(
            extract_tables({"schema": "dbo", "table": "Author"})
        )

        self.assertEqual(tables, [("Author", dataframe)])
        mock_read_sql_query.assert_called_once()
        self.assertNotIn(
            "INFORMATION_SCHEMA",
            mock_read_sql_query.call_args.args[0],
        )
        connection.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()