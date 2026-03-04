"""Workflow orchestration for Deep Agents reporting."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from langchain_core.messages import HumanMessage

from .agents import AgentBundle, build_agent_bundle
from .config import load_event_config, resolve_config_path
from .env import load_environment
from .mcp import MCPManager
from .models import ModelSettings, create_chat_model
from .prompts import PromptContext

logger = logging.getLogger("deep_agents_workflow_v2")


@dataclass
class WorkflowSettings:
    event_name: str
    event_year: int
    config_path: str
    report_type: str = "initial"
    verbose: bool = False
    neo4j_profile: str = "test"
    neo4j_database: Optional[str] = None
    provider: str = "azure"
    model_name: Optional[str] = None
    temperature: float = 1.0


class DeepAgentsReportWorkflow:
    """High-level orchestrator aligning prompts, MCP, and agent execution."""

    def __init__(self, settings: WorkflowSettings):
        self.settings = settings
        self.project_root = load_environment()

        if settings.verbose:
            logging.getLogger().setLevel(logging.DEBUG)
        else:
            logging.getLogger().setLevel(logging.INFO)

        self.config_path = resolve_config_path(settings.config_path, self.project_root)
        self.config: Dict[str, Any] = load_event_config(self.config_path)

        self.model = create_chat_model(
            ModelSettings(
                provider=settings.provider,
                model_name=settings.model_name,
                temperature=settings.temperature,
            )
        )

        self.mcp_manager = MCPManager(
            profile=settings.neo4j_profile,
            explicit_database=settings.neo4j_database,
        )

        self.agent_bundle: Optional[AgentBundle] = None
        self.prompt_context: Optional[PromptContext] = None
        self.data_directory: Optional[Path] = None
        self.report_path: Optional[Path] = None

    def _prepare_run_directories(self) -> None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        reports_root = self.project_root.parent / "reports"
        reports_root.mkdir(parents=True, exist_ok=True)

        self.data_directory = reports_root / f"data_{timestamp}"
        self.data_directory.mkdir(exist_ok=True)

        self.report_path = reports_root / f"report_{self.settings.event_name}_{timestamp}.md"

        self.prompt_context = PromptContext(
            event_name=self.settings.event_name,
            event_year=self.settings.event_year,
            report_type=self.settings.report_type,
            config_path=self.config_path,
            config_data=self.config,
            data_directory=self.data_directory,
            report_stub_path=self.report_path,
        )

    def _build_user_request(self) -> str:
        assert self.prompt_context is not None
        ctx = self.prompt_context
        return (
            f"Generate the {ctx.report_type} ML pipeline report for {ctx.event_name.upper()} {ctx.event_year}. "
            f"Use the event configuration at {ctx.config_path}. Store intermediate Neo4j data in {ctx.data_directory} "
            "and ensure the final markdown report is written to the designated report path."
        )

    async def initialize(self) -> None:
        if self.prompt_context is None:
            self._prepare_run_directories()

        await self.mcp_manager.initialize()
        tools, context = self.mcp_manager.get_first_available_tools()

        if not tools:
            logger.warning("No Neo4j MCP tools discovered; proceeding with filesystem-only workflow.")

        self.agent_bundle = build_agent_bundle(
            model=self.model,
            prompt_context=self.prompt_context,  # type: ignore[arg-type]
            neo4j_tools=tools,
            neo4j_server_name=context.server_name if context else None,
            neo4j_config_source=context.config_source if context else None,
        )

        if context:
            logger.info("Using MCP server %s (config source: %s)", context.server_name, context.config_source)

    async def run(self) -> Path:
        if self.agent_bundle is None:
            await self.initialize()

        assert self.agent_bundle is not None
        assert self.prompt_context is not None

        user_message = self._build_user_request()
        logger.info("Starting Deep Agents run for %s %s", self.settings.event_name, self.settings.event_year)

        result = await self.agent_bundle.main_agent.ainvoke({
            "messages": [HumanMessage(content=user_message)]
        }, config={"recursion_limit": 50})

        final_report = self._capture_final_report(result)

        # Persist artifacts like the research_agent does
        artifacts = self._persist_artifacts(result, user_message, self.data_directory)

        if result.get("todos"):
            logger.debug("Agent managed %d TODO entries", len(result["todos"]))
        if result.get("files"):
            logger.debug("Agent produced %d offloaded files", len(result["files"]))

        logger.info("Workflow finished. Data directory: %s", self.data_directory)

        return final_report

    def _persist_artifacts(
        self,
        result: Dict[str, Any],
        query: str,
        base_dir: Path,
    ) -> Dict[str, Path]:
        """Persist agent artifacts to disk for later inspection, following research_agent pattern."""

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_dir = base_dir / f"artifacts_{timestamp}"
        run_dir.mkdir(parents=True, exist_ok=True)

        artifacts: Dict[str, Path] = {"root": run_dir}

        # Persist agent-managed files
        agent_files = result.get("files") or {}
        if agent_files:
            files_dir = run_dir / "agent_files"
            files_dir.mkdir(parents=True, exist_ok=True)
            used_names: set[str] = set()
            manifest_lines = ["# Agent File Manifest", ""]

            for index, (name, content) in enumerate(agent_files.items(), start=1):
                candidate = Path(name).name or f"agent_file_{index}.txt"
                candidate = self._ensure_unique_filename(candidate, used_names)
                target_path = files_dir / candidate
                file_text = self._normalize_file_content(content)
                target_path.write_text(file_text, encoding="utf-8")
                used_names.add(candidate)
                manifest_lines.append(f"- {candidate} ({len(file_text)} characters)")

            manifest_path = files_dir / "index.md"
            manifest_path.write_text("\n".join(manifest_lines), encoding="utf-8")

            artifacts["agent_files"] = files_dir
            artifacts["agent_files_index"] = manifest_path

        # Persist TODO overview
        todos = result.get("todos") or []
        if todos:
            todo_lines = ["# TODO Overview", ""]
            todo_lines.append("| # | Status | Content |")
            todo_lines.append("|---|--------|---------|")
            status_map = {
                "completed": "completed",
                "in_progress": "in_progress",
                "pending": "pending",
            }
            for idx, todo in enumerate(todos, start=1):
                status = status_map.get(todo.get("status", ""), todo.get("status", "unknown"))
                content = todo.get("content", "").replace("|", "\\|")
                todo_lines.append(f"| {idx} | {status} | {content} |")

            todo_path = run_dir / "todos.md"
            todo_path.write_text("\n".join(todo_lines), encoding="utf-8")
            artifacts["todos"] = todo_path

        return artifacts

    @staticmethod
    def _ensure_unique_filename(candidate: str, used_names: set[str]) -> str:
        """Ensure filenames are unique within the artifact directory."""
        if candidate not in used_names:
            return candidate

        stem = Path(candidate).stem or "file"
        suffix = Path(candidate).suffix
        counter = 1
        unique_name = f"{stem}_{counter}{suffix}"
        while unique_name in used_names:
            counter += 1
            unique_name = f"{stem}_{counter}{suffix}"
        return unique_name

    @staticmethod
    def _normalize_file_content(content: Any) -> str:
        """Normalize agent file payloads into readable text."""
        if content is None:
            return ""

        if isinstance(content, str):
            return content

        if isinstance(content, list):
            return "\n".join(str(item) for item in content)

        if isinstance(content, dict):
            lines: list[str] = []
            primary = content.get("content")
            if isinstance(primary, list):
                lines.append("\n".join(str(item) for item in primary))
            elif isinstance(primary, str):
                lines.append(primary)
            remaining = {k: v for k, v in content.items() if k != "content"}
            if remaining:
                import json
                lines.append("\n---\nMetadata:\n" + json.dumps(remaining, indent=2, ensure_ascii=False))
            return "\n".join(lines).strip()

        return str(content)

    def _capture_final_report(self, result: Dict[str, Any]) -> Path:
        assert self.report_path is not None
        report_path = self.report_path

        if report_path.is_file():
            logger.info("Report already written by agent to %s", report_path)
            return report_path

        messages = result.get("messages") or []
        final_message = messages[-1] if messages else None
        content = ""
        if final_message is not None:
            raw_content = getattr(final_message, "content", "")
            if isinstance(raw_content, list):
                content = "\n\n".join(
                    segment.get("text", "") if isinstance(segment, dict) else str(segment)
                    for segment in raw_content
                )
            else:
                content = str(raw_content)

        if not content.strip():
            content = "Agent did not return content."
            logger.warning("No final content from agent; writing placeholder text.")

        report_path.write_text(content, encoding="utf-8")
        logger.info("Report captured from final message and written to %s", report_path)
        return report_path

    async def close(self) -> None:
        await self.mcp_manager.close()


async def run_workflow(settings: WorkflowSettings) -> Path:
    workflow = DeepAgentsReportWorkflow(settings)
    try:
        report_path = await workflow.run()
        return report_path
    finally:
        await workflow.close()
