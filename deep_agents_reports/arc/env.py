"""Environment helpers for the Deep Agents reporting workflow."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


def load_environment() -> Path:
    """Load project-level and workflow-specific environment variables.

    Returns:
        Path to the project root derived from the current file hierarchy.
    """

    project_root = Path(__file__).resolve().parents[2]

    # Load root-level .env if present
    load_dotenv()

    # Load workflow-specific .env without overriding existing values.
    # Prefer current flattened layout, then legacy nested layout.
    workflow_env_candidates = [
        project_root / ".env",
        project_root / "deep_agents_reports" / ".env",
    ]
    workflow_env = None
    for candidate in workflow_env_candidates:
        if candidate.is_file():
            load_dotenv(dotenv_path=candidate, override=False)
            workflow_env = candidate
            break

    # Ensure the MCP configuration path is absolute and defaults to the project config
    default_candidates = [
        project_root / ".config" / "mcp" / "config.json",
        project_root / "deep_agents_reports" / ".config" / "mcp" / "config.json",
    ]
    default_mcp_config = next((path for path in default_candidates if path.is_file()), default_candidates[0])
    current_mcp_config = os.getenv("MCP_CONFIG_FILE")
    if current_mcp_config:
        mcp_path = Path(current_mcp_config)
        if not mcp_path.is_absolute():
            candidate_paths = [project_root / mcp_path]
            if workflow_env is not None:
                candidate_paths.append(workflow_env.parent / mcp_path)
            for candidate in candidate_paths:
                resolved = candidate.resolve()
                if resolved.is_file():
                    os.environ["MCP_CONFIG_FILE"] = str(resolved)
                    break
            else:
                os.environ["MCP_CONFIG_FILE"] = str(default_mcp_config)
    else:
        os.environ["MCP_CONFIG_FILE"] = str(default_mcp_config)

    return project_root
