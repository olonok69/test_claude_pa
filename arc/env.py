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

    # Load the deep_agents_reports specific .env without overriding existing values
    workflow_env = project_root / "deep_agents_reports" / ".env"
    if workflow_env.is_file():
        load_dotenv(dotenv_path=workflow_env, override=False)

    # Ensure the MCP configuration path is absolute and defaults to the project config
    default_mcp_config = project_root / "deep_agents_reports" / ".config" / "mcp" / "config.json"
    current_mcp_config = os.getenv("MCP_CONFIG_FILE")
    if current_mcp_config:
        mcp_path = Path(current_mcp_config)
        if not mcp_path.is_absolute():
            candidate_paths = [project_root / mcp_path, Path(workflow_env.parent) / mcp_path]
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
