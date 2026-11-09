from pathlib import Path
import yaml

# The repository root is four levels above this file.
PROJECT_ROOT = Path(__file__).resolve().parents[3]

PIPELINE_CONFIG_DIR = PROJECT_ROOT / "config" / "pipelines"


def load_pipeline_config(pipeline_name: str) -> dict:
    """
    Load a pipeline configuration from its YAML file.

    Args:
        pipeline_name: Name of the pipeline to load.

    Returns:
        Dictionary containing the pipeline configuration.
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
        if not isinstance(config.get(section), dict) or not config[section]:
            raise ValueError(
                f"Missing or invalid '{section}' section "
                f"in {config_path}"
            )

    return config
