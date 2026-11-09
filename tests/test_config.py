
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

from mini_etl.config.loader import load_pipeline_config


class TestLoadPipelineConfig(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_dir = Path(self.temp_dir.name)

        self.valid_config = {
            "pipeline": {
                "name": "test_pipeline",
                "description": "Test pipeline"
            },
            "source": {
                "type": "sqlserver",
                "schema": "dbo",
                "table": "Author"
            },
            "destination": {
                "type": "postgresql",
                "schema": "public",
                "table": "author"
            },
            "load": {
                "mode": "full_refresh"
            }
        }

    def tearDown(self):
        self.temp_dir.cleanup()

    def _write_config(self, name, config):
        config_file = self.config_dir / f"{name}.yaml"
        config_file.write_text(
            yaml.safe_dump(config),
            encoding="utf-8"
        )
        return config_file

    def _load_config(self, name):
        with patch(
            "mini_etl.config.loader.PIPELINE_CONFIG_DIR",
            self.config_dir
        ):
            return load_pipeline_config(name)

    def test_load_valid_config(self):
        self._write_config("test_pipeline", self.valid_config)

        config = self._load_config("test_pipeline")

        self.assertEqual(
            config["pipeline"]["name"],
            "test_pipeline"
        )
        self.assertEqual(
            config["source"]["type"],
            "sqlserver"
        )

    def test_missing_config_file(self):
        with self.assertRaises(FileNotFoundError):
            self._load_config("does_not_exist")

    def test_missing_required_section(self):
        config = {
            "pipeline": {"name": "incomplete_pipeline"},
            "source": {"type": "sqlserver"}
        }

        self._write_config("incomplete_pipeline", config)

        with self.assertRaises(ValueError):
            self._load_config("incomplete_pipeline")

    def test_empty_required_section(self):
        config = self.valid_config.copy()
        config["pipeline"] = {}

        self._write_config("empty_section", config)

        with self.assertRaisesRegex(ValueError, "pipeline"):
            self._load_config("empty_section")

    def test_missing_required_keys(self):
        required_keys = [
            ("pipeline", "name"),
            ("source", "type"),
            ("source", "schema"),
            ("source", "table"),
            ("destination", "type"),
            ("destination", "schema"),
            ("destination", "table"),
            ("load", "mode")
        ]

        for section, key in required_keys:
            with self.subTest(section=section, key=key):
                config = {
                    section_name: values.copy()
                    for section_name, values
                    in self.valid_config.items()
                }

                del config[section][key]

                name = f"missing_{section}_{key}"
                self._write_config(name, config)

                with self.assertRaisesRegex(
                    ValueError,
                    rf"{section}\.{key}"
                ):
                    self._load_config(name)

    def test_empty_required_keys(self):
        required_keys = [
            ("pipeline", "name"),
            ("source", "type"),
            ("source", "schema"),
            ("source", "table"),
            ("destination", "type"),
            ("destination", "schema"),
            ("destination", "table"),
            ("load", "mode")
        ]

        for section, key in required_keys:
            with self.subTest(section=section, key=key):
                config = {
                    section_name: values.copy()
                    for section_name, values
                    in self.valid_config.items()
                }

                config[section][key] = ""

                name = f"empty_{section}_{key}"
                self._write_config(name, config)

                with self.assertRaisesRegex(
                    ValueError,
                    rf"{section}\.{key}"
                ):
                    self._load_config(name)

    def test_invalid_yaml_syntax(self):
        config_file = self.config_dir / "invalid_yaml.yaml"

        config_file.write_text(
            """
pipeline:
  name: test_pipeline
source:
  type: sqlserver
  table: [invalid
""",
            encoding="utf-8"
        )

        with self.assertRaises(Exception):
            self._load_config("invalid_yaml")


if __name__ == "__main__":
    unittest.main()
