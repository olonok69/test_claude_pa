"""Helper utilities for resolving MCP server configuration.

These helpers centralize discovery of MCP server definitions so both the
workflow and the setup tests can share the same lookup logic.
"""

from __future__ import annotations

import json
import os
import shlex
from builtins import BaseExceptionGroup
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterator, List, cast

from langchain_mcp_adapters.client import Connection

CONFIG_ENV_VAR = "MCP_CONFIG_FILE"
CONFIG_DIR_ENV_VAR = "MCP_CONFIG_DIR"
DEFAULT_CONFIG_FILENAME = "config.json"
def flatten_exception(exc: BaseException) -> List[str]:
    """Flatten nested exception groups into readable messages."""
    if isinstance(exc, BaseExceptionGroup):
        messages: List[str] = []
        for sub_exc in exc.exceptions:
            messages.extend(flatten_exception(sub_exc))
        return messages
    return [f"{exc.__class__.__name__}: {exc}"]


def format_exception(exc: BaseException) -> str:
    """Return a single-line string summarizing possibly grouped exceptions."""
    return "; ".join(flatten_exception(exc))



@dataclass
class MCPConnectionResult:
    """Result of attempting to load an MCP connection definition."""

    connection: Connection | None
    source: Path | None
    error: str | None = None


def _iter_candidate_config_paths() -> Iterator[Path]:
    """Yield plausible locations for the MCP config file."""
    seen: set[Path] = set()

    def _record(path: Path) -> Iterator[Path]:
        resolved = path.expanduser()
        if resolved not in seen:
            seen.add(resolved)
            yield resolved

    # User-specified overrides
    env_file = os.getenv(CONFIG_ENV_VAR)
    if env_file:
        yield from _record(Path(env_file))

    env_dir = os.getenv(CONFIG_DIR_ENV_VAR)
    if env_dir:
        yield from _record(Path(env_dir) / DEFAULT_CONFIG_FILENAME)

    # Platform-specific defaults
    home = Path.home()

    # XDG-style config directories (Linux, WSL)
    xdg_home = Path(os.getenv("XDG_CONFIG_HOME", home / ".config"))
    yield from _record(xdg_home / "mcp" / DEFAULT_CONFIG_FILENAME)

    # Windows roaming profile (APPDATA takes precedence if present)
    appdata = os.getenv("APPDATA")
    if appdata:
        yield from _record(Path(appdata) / "mcp" / DEFAULT_CONFIG_FILENAME)
    yield from _record(home / "AppData" / "Roaming" / "mcp" / DEFAULT_CONFIG_FILENAME)

    # macOS Application Support
    yield from _record(home / "Library" / "Application Support" / "mcp" / DEFAULT_CONFIG_FILENAME)


def _normalize_connection(raw: Dict[str, object]) -> Connection | None:
    """Convert a raw config mapping to an MCP connection dict."""
    connection: Dict[str, object] = dict(raw)

    command = connection.get("command")
    if not isinstance(command, str) or not command.strip():
        return None

    args_value = connection.get("args", [])
    if isinstance(args_value, str):
        args = shlex.split(args_value)
    elif isinstance(args_value, (list, tuple)):
        args = [str(item) for item in args_value]
    else:
        args = []
    connection["args"] = args

    cwd = connection.get("cwd")
    if cwd is not None and not isinstance(cwd, str):
        connection.pop("cwd")

    transport = connection.get("transport")
    if not isinstance(transport, str) or not transport:
        connection["transport"] = "stdio"
    else:
        connection["transport"] = transport

    return connection  # type: ignore[return-value]


def load_mcp_server_connection(server_name: str) -> MCPConnectionResult:
    """Look up a server definition by name in known MCP config locations."""
    for path in _iter_candidate_config_paths():
        try:
            if not path.is_file():
                continue
        except OSError:
            continue

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:  # pragma: no cover - best effort parsing
            return MCPConnectionResult(connection=None, source=path, error=f"Failed to parse MCP config: {exc}")

        servers: Dict[str, object] | None = None
        if isinstance(data, dict):
            if isinstance(data.get("mcpServers"), dict):
                servers = data["mcpServers"]  # type: ignore[assignment]
            elif isinstance(data.get("mcp_servers"), dict):
                servers = data["mcp_servers"]  # type: ignore[assignment]
            elif server_name in data:
                servers = data  # type: ignore[assignment]

        if not servers or server_name not in servers:
            continue

        raw_entry = servers[server_name]
        if not isinstance(raw_entry, dict):
            return MCPConnectionResult(connection=None, source=path, error=f"Invalid MCP entry for '{server_name}'")

        connection = _normalize_connection(raw_entry)
        if connection is None:
            return MCPConnectionResult(connection=None, source=path, error=f"Incomplete MCP config for '{server_name}'")

        return MCPConnectionResult(connection=connection, source=path, error=None)

    return MCPConnectionResult(
        connection=None,
        source=None,
        error=f"Server '{server_name}' not found in MCP config; set {CONFIG_ENV_VAR} or {CONFIG_DIR_ENV_VAR} to override.",
    )
