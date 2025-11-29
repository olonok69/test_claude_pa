"""Agent construction utilities for the Deep Agents reporting workflow."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Sequence

from deepagents import SubAgent, create_deep_agent

from .prompts import (
    PromptContext,
    build_main_agent_prompt,
    build_neo4j_subagent_prompt,
    build_planning_subagent_prompt,
    build_quality_subagent_prompt,
    build_report_writer_prompt,
)


@dataclass
class AgentBundle:
    main_agent: Any
    subagents: Sequence[SubAgent]
    neo4j_server_name: str | None
    neo4j_config_source: str | None


def build_agent_bundle(
    model: Any,
    prompt_context: PromptContext,
    neo4j_tools: Sequence[Any],
    neo4j_server_name: str | None,
    neo4j_config_source: str | None,
) -> AgentBundle:
    """Create the main deep agent and supporting subagents."""

    planning_subagent = SubAgent(
        name="planning-specialist",
        description="Decomposes the reporting task into actionable TODOs and keeps them current.",
        prompt=build_planning_subagent_prompt(prompt_context),
    )

    neo4j_subagent = SubAgent(
        name="neo4j-analysis",
        description="Runs Cypher queries via MCP tools and summarises the results for the main agent.",
        prompt=build_neo4j_subagent_prompt(prompt_context),
        tools=[tool.name for tool in neo4j_tools],
    )

    report_writer_subagent = SubAgent(
        name="report-writer",
        description="Transforms consolidated findings into the final executive report.",
        prompt=build_report_writer_prompt(prompt_context),
    )

    quality_subagent = SubAgent(
        name="quality-review",
        description="Provides critical review and improvement suggestions for draft reports.",
        prompt=build_quality_subagent_prompt(prompt_context),
    )

    subagents: List[SubAgent] = [
        planning_subagent,
        neo4j_subagent,
        report_writer_subagent,
        quality_subagent,
    ]

    main_agent = create_deep_agent(
        tools=list(neo4j_tools),
        instructions=build_main_agent_prompt(prompt_context),
        model=model,
        subagents=subagents,
    )

    return AgentBundle(
        main_agent=main_agent,
        subagents=subagents,
        neo4j_server_name=neo4j_server_name,
        neo4j_config_source=neo4j_config_source,
    )
