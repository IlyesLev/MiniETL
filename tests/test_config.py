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
                "id": 1,
                "name": "test_pipeline",
                "description": "Test pipeline"
            },
            "source": {
                "type": "sqlserver",
                "schema": "dbo"
            },
            "destination": {
                "type": "postgresql",
                "schema": "public"
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

        self.assertEqual(config["pipeline"]["id"], 1)
        self.assertEqual(
            config["pipeline"]["name"],
            "test_pipeline"
        )
        self.assertEqual(config["source"]["type"], "sqlserver")

    def test_rejects_missing_pipeline_id(self):
        config = {
            section: values.copy()
            for section, values in self.valid_config.items()
        }
        del config["pipeline"]["id"]
        self._write_config("missing_pipeline_id", config)

        with self.assertRaisesRegex(ValueError, "pipeline.id"):
            self._load_config("missing_pipeline_id")

    def test_rejects_non_integer_pipeline_id(self):
        for invalid_id in ("1", 1.5, True, 0, 32768):
            with self.subTest(pipeline_id=invalid_id):
                config = {
                    section: values.copy()
                    for section, values in self.valid_config.items()
                }
                config["pipeline"]["id"] = invalid_id
                name = f"invalid_pipeline_id_{str(invalid_id).lower()}"
                self._write_config(name, config)

                with self.assertRaises(ValueError):
                    self._load_config(name)

    def test_missing_config_file(self):
        with self.assertRaises(FileNotFoundError):
            self._load_config("does_not_exist")

    def test_missing_required_section(self):
        config = {
            "pipeline": {"id": 1, "name": "incomplete_pipeline"},
            "source": {"type": "sqlserver"}
        }

        self._write_config("incomplete_pipeline", config)

        with self.assertRaises(ValueError):
            self._load_config("incomplete_pipeline")

    def test_empty_required_section(self):
        config = {
            section: values.copy()
            for section, values in self.valid_config.items()
        }
        config["pipeline"] = {}

        self._write_config("empty_section", config)

        with self.assertRaisesRegex(ValueError, "pipeline"):
            self._load_config("empty_section")

    def test_missing_required_keys(self):
        required_keys = [
            ("pipeline", "name"),
            ("source", "type"),
            ("source", "schema"),
            ("destination", "type"),
            ("destination", "schema"),
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
            ("destination", "type"),
            ("destination", "schema"),
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
  id: 1
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
