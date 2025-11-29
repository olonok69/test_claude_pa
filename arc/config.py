"""Configuration loaders for Deep Agents reporting workflow."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import yaml


class ConfigLoaderError(FileNotFoundError):
    """Raised when the workflow configuration cannot be located."""


def resolve_config_path(raw_path: str, project_root: Path) -> Path:
    """Resolve a configuration path with fallbacks into the repo structure."""

    candidate_paths: List[Path] = []
    supplied = Path(raw_path)

    if supplied.is_absolute():
        candidate_paths.append(supplied)
    else:
        candidate_paths.extend(
            [
                Path.cwd() / supplied,
                project_root / supplied,
                project_root / "config" / supplied,
                (project_root / "deep_agents_reports" / supplied),
                (project_root / "deep_agents_reports" / "config" / supplied),
                (project_root.parent / "config" / supplied),  # PA/config
            ]
        )

    for candidate in candidate_paths:
        if candidate.is_file():
            return candidate.resolve()

    search_list = ", ".join(str(path.resolve()) for path in candidate_paths)
    raise ConfigLoaderError(
        f"Unable to locate configuration file '{raw_path}'. Checked: {search_list}"
    )


def load_event_config(config_path: Path) -> Dict[str, Any]:
    """Load the YAML event configuration."""

    with config_path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}
