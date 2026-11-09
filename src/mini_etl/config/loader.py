
from pathlib import Path

import yaml


# The repository root is four levels above this file.
PROJECT_ROOT = Path(__file__).resolve().parents[3]

PIPELINE_CONFIG_DIR = PROJECT_ROOT / "config" / "pipelines"


def load_pipeline_config(pipeline_name: str) -> dict:
    """
    Load and validate a pipeline configuration from its YAML file.

    Args:
        pipeline_name: Name of the pipeline to load.

    Returns:
        Dictionary containing the validated pipeline configuration.
    """

    config_path = PIPELINE_CONFIG_DIR / f"{pipeline_name}.yaml"

    if not config_path.is_file():
        raise FileNotFoundError(
            f"Pipeline configuration not found: {config_path}"
        )

    with config_path.open("r", encoding="utf-8") as file:
        config = yaml.safe_load(file)

    if not isinstance(config, dict):
        raise ValueError(
            f"Invalid or empty YAML configuration: {config_path}"
        )

    required_sections = ["pipeline", "source", "destination", "load"]

    for section in required_sections:
        if section not in config or not isinstance(config[section], dict):
            raise ValueError(
                f"Missing or invalid '{section}' section "
                f"in {config_path}"
            )

    required_keys = {
        "pipeline": ["name"],
        "source": ["type", "schema", "table"],
        "destination": ["type", "schema", "table"],
        "load": ["mode"],
    }

    for section, keys in required_keys.items():
        for key in keys:
            value = config[section].get(key)

            if not isinstance(value, str) or not value.strip():
                raise ValueError(
                    f"Missing or empty required key "
                    f"'{section}.{key}' in {config_path}"
                )

    return config
