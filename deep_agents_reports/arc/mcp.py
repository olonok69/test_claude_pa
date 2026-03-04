"""MCP client management for the Deep Agents reporting workflow."""

from __future__ import annotations

import os
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from langchain_mcp_adapters.client import MultiServerMCPClient

from .mcp_utils import load_mcp_server_connection

logger = logging.getLogger("deep_agents_workflow_v2.mcp")


@dataclass
class MCPServerContext:
    server_name: str
    config_source: Optional[str]
    tools: list


@dataclass
class MCPManager:
    profile: str
    explicit_database: Optional[str]
    clients: Dict[str, MultiServerMCPClient] = field(default_factory=dict)
    server_context: Dict[str, MCPServerContext] = field(default_factory=dict)

    def _resolve_env_overrides(self, server_name: str) -> Dict[str, str]:
        profile_suffix = server_name.split("-", 1)[-1].upper()
        username = os.getenv("NEO4J_USERNAME", "neo4j")
        uri = (
            os.getenv(f"NEO4J_URI_{profile_suffix}")
            or os.getenv("NEO4J_URI")
        )
        password = (
            os.getenv(f"NEO4J_PASSWORD_{profile_suffix}")
            or os.getenv("NEO4J_PASSWORD")
            or ""
        )
        database = (
            os.getenv(f"NEO4J_DATABASE_{profile_suffix}")
            or self.explicit_database
            or os.getenv("NEO4J_DATABASE")
            or "neo4j"
        )

        overrides: Dict[str, str] = {"NEO4J_USERNAME": username, "NEO4J_DATABASE": database}
        if uri:
            overrides["NEO4J_URI"] = uri
        if password:
            overrides["NEO4J_PASSWORD"] = password
        return overrides

    async def initialize(self) -> None:
        preferred_server = f"neo4j-{self.profile.lower()}"
        candidates: List[str] = [preferred_server]
        for fallback in ("neo4j-test", "neo4j-prod", "neo4j-dev"):
            if fallback not in candidates:
                candidates.append(fallback)

        for candidate in candidates:
            if candidate in self.clients:
                continue

            result = load_mcp_server_connection(candidate)
            if result.connection is None:
                logger.warning(
                    "MCP configuration for %s not available (%s)",
                    candidate,
                    result.error or "not found",
                )
                continue

            connection_dict = dict(result.connection)
            env_config = dict(connection_dict.get("env", {}))
            env_config.update(self._resolve_env_overrides(candidate))
            connection_dict["env"] = env_config

            try:
                client = MultiServerMCPClient({candidate: connection_dict})
                tools = await client.get_tools()
                self.clients[candidate] = client
                self.server_context[candidate] = MCPServerContext(
                    server_name=candidate,
                    config_source=str(result.source) if result.source else None,
                    tools=tools,
                )
                logger.info(
                    "Initialized MCP client for %s (config: %s, tools: %d)",
                    candidate,
                    self.server_context[candidate].config_source,
                    len(tools),
                )
            except Exception as exc:  # pragma: no cover - runtime issues
                logger.warning("Failed to initialize MCP client for %s: %s", candidate, exc)

        if not self.clients:
            raise RuntimeError("No MCP Neo4j clients could be initialized. Check MCP configuration and environment variables.")

    async def close(self) -> None:
        for client in self.clients.values():
            try:
                await client.__aexit__(None, None, None)
            except Exception:  # pragma: no cover - best-effort cleanup
                pass

    def get_first_available_tools(self) -> tuple[list, Optional[MCPServerContext]]:
        for server_name, context in self.server_context.items():
            if context.tools:
                return context.tools, context
        return [], None
