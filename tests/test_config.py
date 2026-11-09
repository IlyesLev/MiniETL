import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from mini_etl.config.loader import load_pipeline_config

class TestLoadPipelineConfig(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_dir = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_load_valid_config(self):
        config_content = """
pipeline:
  name: test_pipeline
source:
  type: sqlserver
destination:
  type: postgresql
load:
  mode: full_refresh
"""
        config_file = self.config_dir / "test_pipeline.yaml"
        config_file.write_text(config_content, encoding="utf-8")

        with patch(
            "mini_etl.config.loader.PIPELINE_CONFIG_DIR",
            self.config_dir
        ):
            config = load_pipeline_config("test_pipeline")

        self.assertEqual(config["pipeline"]["name"], "test_pipeline")
        self.assertEqual(config["source"]["type"], "sqlserver")

    def test_missing_config_file(self):
        with patch(
            "mini_etl.config.loader.PIPELINE_CONFIG_DIR",
            self.config_dir
        ):
            with self.assertRaises(FileNotFoundError):
                load_pipeline_config("does_not_exist")

    def test_missing_required_section(self):
        config_content = """
pipeline:
  name: incomplete_pipeline
source:
  type: sqlserver
"""
        config_file = self.config_dir / "incomplete_pipeline.yaml"
        config_file.write_text(config_content, encoding="utf-8")

        with patch(
            "mini_etl.config.loader.PIPELINE_CONFIG_DIR",
            self.config_dir
        ):
            with self.assertRaises(ValueError):
                load_pipeline_config("incomplete_pipeline")


    def test_empty_required_section(self):
        config_content = """
pipeline: {}
source:
  type: sqlserver
  schema: dbo
  table: Author
destination:
  type: postgresql
  schema: public
  table: author
load:
  mode: full_refresh
"""
        config_file = self.config_dir / "empty_section.yaml"
        config_file.write_text(config_content, encoding="utf-8")

        with patch(
            "mini_etl.config.loader.PIPELINE_CONFIG_DIR",
            self.config_dir
        ):
            with self.assertRaisesRegex(ValueError, "pipeline"):
                load_pipeline_config("empty_section")

    def test_missing_required_key(self):
        config_content = """
pipeline:
  name: test_pipeline
source:
  type: sqlserver
  schema: dbo
destination:
  type: postgresql
  schema: public
  table: author
load:
  mode: full_refresh
"""
        config_file = self.config_dir / "missing_key.yaml"
        config_file.write_text(config_content, encoding="utf-8")

        with patch(
            "mini_etl.config.loader.PIPELINE_CONFIG_DIR",
            self.config_dir
        ):
            # The current loader only validates sections.
            # This test documents the missing validation.
            config = load_pipeline_config("missing_key")

        self.assertNotIn("table", config["source"])

    def test_invalid_yaml_syntax(self):
        config_content = """
pipeline:
  name: test_pipeline
source:
  type: sqlserver
  table: [invalid
"""
        config_file = self.config_dir / "invalid_yaml.yaml"
        config_file.write_text(config_content, encoding="utf-8")

        with patch(
            "mini_etl.config.loader.PIPELINE_CONFIG_DIR",
            self.config_dir
        ):
            with self.assertRaises(Exception):
                load_pipeline_config("invalid_yaml")


if __name__ == "__main__":
    unittest.main()

