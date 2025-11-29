#!/usr/bin/env python3
"""
Deep Agents TODO List Generator for Pre-Show Reports

Creates atomic TODO lists for comprehensive pre-show report generation using DeepAgents
with built-in middleware tools: write_todos, read_todos, and filesystem tools.

This workflow:
1. Reads the generic prompt template and event configuration
2. Creates atomic TODOs for all 13 report tasks with individual Cypher queries
3. Handles both simple tasks (with query templates) and complex tasks (multiple subtasks)
4. Includes output requirements and sub-agent delegation in each TODO
5. Uses critique sub-agent for quality assurance
"""

import asyncio
import json
import logging
import os
import re
from copy import deepcopy
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from deepagents import SubAgent, create_deep_agent
from deepagents.backends import CompositeBackend
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from neo4j import Driver, GraphDatabase, RoutingControl
from neo4j.exceptions import ClientError, Neo4jError

from ..config import load_event_config, resolve_config_path
from ..env import load_environment
from ..models import ModelSettings, create_chat_model
from .backends import SafeFilesystemBackend
from .manifest import (
    build_prebuilt_todos,
    build_task_manifest,
    build_todo_state_entries,
    collect_existing_artifacts,
    save_prebuilt_todos,
    save_recovery_inventory,
    save_task_manifest,
)
from .prompts import (
    PromptContext,
    build_critique_subagent_prompt,
    build_main_agent_instructions,
    build_neo4j_subagent_prompt,
)

logger = logging.getLogger("deep_agents_todo_generator")

__all__ = ["ShowReportGenerator"]


class ShowReportGenerator:
    """Generates comprehensive atomic TODO lists for Deep Agents reports."""

    def __init__(
        self,
        event_name: str,
        event_year: int,
        config_path: str,
        prompt_template_path: str,
        provider: str = "azure",
        model_name: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
        neo4j_profile: str = "test",
        neo4j_database: str = "neo4j",
        example_report_path: Optional[str] = None,
        verbose: bool = False,
    ) -> None:
        self.project_root = load_environment()
        self.workspace_dir = self.project_root / "deep_agents_reports"
        load_dotenv()

        self.event_name = event_name
        self.event_year = event_year
        self.preloaded_todo_state: List[Dict[str, Any]] = []
        self.expected_todo_contents: List[str] = []
        self.prebuilt_todos_display: Optional[str] = None
        self.prebuilt_todo_total: int = 0
        self.agent: Optional[SubAgent] = None

        base_fs_backend = SafeFilesystemBackend(
            root_dir=str(self.project_root),
            virtual_mode=True,
        )
        self.memory_backend_root = self.project_root / "deep_agents_reports" / "memory"
        self.memory_backend_root.mkdir(parents=True, exist_ok=True)
        self.memory_backend = SafeFilesystemBackend(
            root_dir=str(self.memory_backend_root),
            virtual_mode=True,
        )
        self.memory_namespace = f"{self.event_name.lower()}{self.event_year}"
        self.memory_output_dir_path = self.memory_backend_root / self.memory_namespace / "pre_show"
        self.memory_output_dir_path.mkdir(parents=True, exist_ok=True)
        self.memory_output_dir_display = f"/memories/{self.memory_namespace}/pre_show"

        self.backend_factory = lambda runtime: CompositeBackend(  # noqa: E731
            default=base_fs_backend,
            routes={"/memories/": self.memory_backend},
        )

        os.environ["NEO4J_DATABASE"] = neo4j_database
        self.neo4j_database = neo4j_database

        if verbose:
            logging.getLogger().setLevel(logging.DEBUG)
        else:
            logging.getLogger().setLevel(logging.INFO)

        self.config_path = resolve_config_path(config_path, self.project_root)
        self.prompt_template_path = Path(prompt_template_path).resolve()
        self.config: Dict[str, Any] = load_event_config(self.config_path)
        self.config_path_display = self._format_agent_path(self.config_path)
        self.prompt_template_display = self._format_agent_path(self.prompt_template_path)
        self.agent_protocol_path = self.workspace_dir / "docs" / "pre_show_agent_protocol.md"
        self.agent_protocol_display = (
            self._format_agent_path(self.agent_protocol_path)
            if self.agent_protocol_path.exists()
            else None
        )

        if not self.prompt_template_path.exists():
            raise FileNotFoundError(f"Prompt template not found: {self.prompt_template_path}")
        self.prompt_template = self.prompt_template_path.read_text(encoding="utf-8")
        self.example_report_path = self._resolve_example_report_path(example_report_path)
        self.example_report_display = (
            self._format_agent_path(self.example_report_path)
            if self.example_report_path
            else None
        )

        provider_name = (provider or "").lower()
        if provider_name == "azure":
            default_max_tokens = 16384
        elif provider_name == "anthropic":
            default_max_tokens = 8192
        else:
            default_max_tokens = 4096

        self.model_max_tokens = max_tokens if max_tokens is not None else default_max_tokens

        self.model_settings = ModelSettings(
            provider=provider,
            model_name=model_name,
            temperature=temperature,
            max_tokens=self.model_max_tokens,
        )

        self.max_todo_plan_attempts = 3
        self.required_todo_count = 13
        self.max_read_rows = 500
        self.preview_rows = 50

        self.neo4j_profile = neo4j_profile
        self.neo4j_driver = self._initialize_neo4j_driver(neo4j_profile)

        self.reports_dir = self.workspace_dir / "reports"
        self.artifacts_dir = self.reports_dir / "artifacts"
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)

        self.output_dir = (
            self.project_root
            / "deep_agents_reports"
            / "outputs"
            / f"{self.event_name.lower()}{self.event_year}"
            / "pre_show"
        )
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.schema_path = self.output_dir / f"neo4j_schema_{self.event_name.lower()}{self.event_year}.json"
        self.output_dir_display = self._format_agent_path(self.output_dir)
        self.schema_path_display = self._format_agent_path(self.schema_path)

        neo4j_cfg = self.config.get("neo4j", {})
        node_labels = neo4j_cfg.get("node_labels", {})
        relationships = neo4j_cfg.get("relationships", {})
        self.show_code = neo4j_cfg.get("show_name", self.event_name.lower())

        visitor_label = node_labels.get("visitor_this_year", "Visitor_this_year")
        session_label = node_labels.get("session_this_year", "Sessions_this_year")
        stream_label = node_labels.get("stream", "Stream")
        recommendation_rel = relationships.get("is_recommended", "IS_RECOMMENDED")

        self.label_aliases = {
            "Visitor": visitor_label,
            "Visitors": visitor_label,
            "Session": session_label,
            "Sessions": session_label,
            "Stream": stream_label,
        }
        self.relationship_aliases = {
            "RECOMMENDS": recommendation_rel,
            "RECOMMENDED": recommendation_rel,
            "IS_RECOMMENDED": recommendation_rel,
        }

        self.visitor_label = visitor_label
        self.session_label = session_label
        self.stream_label = stream_label
        self.recommendation_relationship = recommendation_rel

        self.label_alias_lookup = {alias.lower(): target for alias, target in self.label_aliases.items()}
        self.relationship_alias_lookup = {alias.upper(): target for alias, target in self.relationship_aliases.items()}

        self.model = create_chat_model(self.model_settings)

        if hasattr(self.model, "max_tokens"):
            self.model.max_tokens = self.model_max_tokens
        if hasattr(self.model, "model_kwargs"):
            self.model.model_kwargs["max_tokens"] = self.model_max_tokens

    def _format_agent_path(self, path: Path) -> str:
        target = Path(path)
        if not target.is_absolute():
            target = (self.project_root / target).resolve()
        try:
            relative = target.relative_to(self.project_root)
            return f"/{relative.as_posix()}"
        except ValueError:
            return f"/{target.as_posix()}"

    def _resolve_example_report_path(self, example_report_path: Optional[str]) -> Optional[Path]:
        if not example_report_path:
            return None
        candidate = Path(example_report_path)
        if not candidate.is_absolute():
            candidate = (self.project_root / candidate).resolve()
        return candidate if candidate.exists() else None

    def _auto_save_agent_artifact(self, prefix: str, data: Any, extension: str = "json") -> Tuple[Path, str]:
        """Persist query results to the output directory for agent consumption."""

        safe_prefix = re.sub(r"[^a-zA-Z0-9_-]", "_", prefix).strip("_") or "agent_file"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        token = uuid.uuid4().hex[:6]
        filename = f"{safe_prefix}_{timestamp}_{token}.{extension}"
        target_path = self.output_dir / filename

        if extension == "json":
            serialized = json.dumps(data, indent=2, default=str)
        else:
            serialized = str(data)

        target_path.write_text(serialized, encoding="utf-8")
        self._mirror_to_memory(target_path.name, serialized)

        return target_path, self._format_agent_path(target_path)

    def _mirror_to_memory(self, filename: str, content: str) -> None:
        """Persist a copy of agent artifacts to the /memories namespace for recovery."""

        try:
            memory_target = self.memory_output_dir_path / filename
            memory_target.parent.mkdir(parents=True, exist_ok=True)
            memory_target.write_text(content, encoding="utf-8")
        except Exception as exc:  # pragma: no cover - best effort safeguard
            logger.warning("Failed to mirror %s to memory backend: %s", filename, exc)

    def _initialize_neo4j_driver(self, profile: str) -> Driver:
        """
        Initialize Neo4j driver directly using environment variables.
        Similar to MCP server initialization but without the MCP layer.
        """
        # Load Neo4j connection details from environment
        neo4j_uri = os.getenv(f"NEO4J_URI_{profile.upper()}")
        neo4j_user = os.getenv("NEO4J_USERNAME", "neo4j")  # Default to neo4j if not specified
        neo4j_password = os.getenv(f"NEO4J_PASSWORD_{profile.upper()}")

        if not all([neo4j_uri, neo4j_user, neo4j_password]):
            raise ValueError(f"Missing Neo4j {profile} environment variables. Required: NEO4J_URI_{profile.upper()}, NEO4J_USERNAME (optional, defaults to 'neo4j'), NEO4J_PASSWORD_{profile.upper()}")

        driver = GraphDatabase.driver(
            neo4j_uri,
            auth=(neo4j_user, neo4j_password),
        )

        return driver

    def _extract_config_values(self) -> Dict[str, str]:
        """
        Extract all placeholder values from the config file based on the prompt template mappings.
        """
        values = {}

        # Basic event information
        values['SHOW_CODE'] = self.config.get('neo4j', {}).get('show_name', self.config.get('event', {}).get('name', 'unknown'))
        values['EVENT_NAME'] = self.config.get('event', {}).get('main_event_name', self.config.get('event', {}).get('name', 'Unknown Event'))
        values['MODE'] = self.config.get('mode', 'personal_agendas')

        # Database and environment
        values['ENVIRONMENT'] = 'Production'  # Default, can be overridden
        values['DATABASE_CONNECTION'] = f"neo4j-{self.neo4j_profile}" if hasattr(self, 'neo4j_profile') else 'neo4j-test'

        # File paths
        values['CONFIG_FILE_PATH'] = str(self.config_path)

        # Current date and timing
        values['CURRENT_DATE'] = datetime.now().strftime('%Y-%m-%d')
        values['PIPELINE_RUN_DATE'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Placeholder
        values['DURATION'] = 'Unknown'  # Placeholder

        # Recommendation settings
        rec_config = self.config.get('recommendation', {})
        values['MAX_RECOMMENDATIONS'] = str(rec_config.get('max_recommendations', 10))
        values['MIN_SIMILARITY_SCORE'] = str(rec_config.get('min_similarity_score', 0.3))
        values['SIMILAR_VISITORS_COUNT'] = str(rec_config.get('similar_visitors_count', 3))
        values['FILTERING_ENABLED'] = str(rec_config.get('enable_filtering', False)).lower()

        # Similarity attributes (for dynamic query generation)
        similarity_attrs = rec_config.get('similarity_attributes', {})
        values['ATTRIBUTE_NAMES'] = ', '.join(f'"{attr}"' for attr in similarity_attrs.keys())

        return values

    def _replace_placeholders_in_template(self, template: str, values: Dict[str, str]) -> str:
        """
        Replace all placeholders in the template with actual config values.
        """
        result = template
        for placeholder, value in values.items():
            result = result.replace(f'[{placeholder}]', value)
        return result

    def initialize(self) -> None:
        """Initialize Neo4j driver connection."""
        print("Initializing Neo4j driver...")
        # Test the connection
        self.neo4j_driver.verify_connectivity()
        print("Neo4j driver initialized successfully")

        # Now create the agent with initialized Neo4j tools
        self.agent = self._create_agent()

    def close(self) -> None:
        """Clean up resources."""
        self.neo4j_driver.close()

    def _create_agent(self):
        """
        Create the deep agent with sub-agents and direct Neo4j tools.

        Uses DeepAgents middleware:
        - write_todos: Task planning and TODO management
        - read_todos: TODO status checking and recitation
        - Filesystem tools: ls, read_file, write_file, edit_file for context offloading
        - task tool: Sub-agent delegation for context isolation
        - Direct Neo4j tools: get_neo4j_schema, read_neo4j_cypher, write_neo4j_cypher
        """
        prompt_ctx = PromptContext(
            event_name=self.event_name,
            event_year=self.event_year,
            output_dir_display=self.output_dir_display,
            schema_path_display=self.schema_path_display,
            memory_output_dir_display=self.memory_output_dir_display,
            example_report_display=self.example_report_display,
            current_date=datetime.now().strftime("%A, %B %d, %Y"),
        )

        # Define neo4j-analysis sub-agent for database queries
        neo4j_subagent = SubAgent(
            name="neo4j-analysis",
            description=(
                "Provides Cypher queries for database operations. "
                "Use this sub-agent to generate appropriate queries for Neo4j database tasks."
            ),
            system_prompt=build_neo4j_subagent_prompt(prompt_ctx),
        )

        # Define critique sub-agent for quality assurance
        critique_subagent = SubAgent(
            name="critique-agent",
            description=(
                "Delegate TODO output review to this critical analyst. "
                "Use to identify gaps, verify quality, and suggest improvements. "
                "Provide the TODO execution results to review for quality assurance."
            ),
            system_prompt=build_critique_subagent_prompt(),
            tools=[],  # No additional tools needed for critique
        )

        # Create the main deep agent with all capabilities
        # DeepAgents automatically provides:
        # - write_todos tool (TASK PLANNING)
        # - read_todos tool (TODO recitation)
        # - File system tools: ls, read_file, write_file, edit_file (CONTEXT OFFLOADING)
        # - task tool for delegating to sub-agents (CONTEXT ISOLATION)
        # Direct Neo4j tools for database access
        tools = [
            self.get_neo4j_schema,
            self.read_neo4j_cypher,
            self.write_neo4j_cypher,
        ]

        print(f"Creating DeepAgent with {len(tools)} direct Neo4j tools...")
        agent = create_deep_agent(
            model=self.model,
            tools=tools,  # Direct Neo4j tools
            backend=self.backend_factory,
            system_prompt=build_main_agent_instructions(prompt_ctx),
            subagents=[neo4j_subagent, critique_subagent],
        )
        print("DeepAgent created successfully")
        return agent

    def get_neo4j_schema(self) -> str:
        """
        Get Neo4j database schema using APOC plugin.
        This requires that the APOC plugin is installed and enabled.
        """
        get_schema_query = """
        CALL apoc.meta.schema();
        """

        def clean_schema(schema: dict) -> dict:
            cleaned = {}

            for key, entry in schema.items():
                new_entry = {"type": entry["type"]}
                if "count" in entry:
                    new_entry["count"] = entry["count"]

                labels = entry.get("labels", [])
                if labels:
                    new_entry["labels"] = labels

                props = entry.get("properties", {})
                clean_props = {}
                for pname, pinfo in props.items():
                    cp = {}
                    if "indexed" in pinfo:
                        cp["indexed"] = pinfo["indexed"]
                    if "type" in pinfo:
                        cp["type"] = pinfo["type"]
                    if cp:
                        clean_props[pname] = cp
                if clean_props:
                    new_entry["properties"] = clean_props

                if entry.get("relationships"):
                    rels_out = {}
                    for rel_name, rel in entry["relationships"].items():
                        cr = {}
                        if "direction" in rel:
                            cr["direction"] = rel["direction"]
                        rlabels = rel.get("labels", [])
                        if rlabels:
                            cr["labels"] = rlabels
                        rprops = rel.get("properties", {})
                        clean_rprops = {}
                        for rpname, rpinfo in rprops.items():
                            crp = {}
                            if "indexed" in rpinfo:
                                crp["indexed"] = rpinfo["indexed"]
                            if "type" in rpinfo:
                                crp["type"] = rpinfo["type"]
                            if crp:
                                clean_rprops[rpname] = crp
                        if clean_rprops:
                            cr["properties"] = clean_rprops
                        if cr:
                            rels_out[rel_name] = cr
                    if rels_out:
                        new_entry["relationships"] = rels_out

                cleaned[key] = new_entry

            return cleaned

        try:
            with self.neo4j_driver.session(database=self.neo4j_database) as session:
                result = session.run(get_schema_query)
                record = result.single()
                schema = record["value"] if record else {}

            logger.debug(f"Read query returned schema data")

            schema_clean = clean_schema(schema)
            schema_clean_str = json.dumps(schema_clean, default=str, indent=2)

            return schema_clean_str

        except ClientError as e:
            if "Neo.ClientError.Procedure.ProcedureNotFound" in str(e):
                raise ValueError(
                    "Neo4j Client Error: This instance of Neo4j does not have the APOC plugin installed. Please install and enable the APOC plugin to use the get_neo4j_schema tool."
                )
            else:
                raise ValueError(f"Neo4j Client Error: {e}")

        except Neo4jError as e:
            raise ValueError(f"Neo4j Error: {e}")

        except Exception as e:
            logger.error(f"Error retrieving Neo4j database schema: {e}")
            raise ValueError(f"Unexpected Error: {e}")

    def read_neo4j_cypher(self, query: str, params: Optional[Dict[str, Any]] = None) -> str:
        """
        Execute a read Cypher query on the neo4j database.
        """
        if not query.strip():
            raise ValueError("Query cannot be empty")

        # Check if it's a write query
        if re.search(r"\b(MERGE|CREATE|SET|DELETE|REMOVE|ADD)\b", query, re.IGNORECASE):
            raise ValueError("Only MATCH queries are allowed for read operations")

        query = self._normalize_cypher_identifiers(query)
        # Fix common Cypher syntax issues that sub-agents might generate
        query = self._fix_cypher_syntax(query)

        try:
            with self.neo4j_driver.session(database=self.neo4j_database) as session:
                result = session.run(query, parameters=params or {})
                records: List[Dict[str, Any]] = []
                truncated = False

                for record in result:
                    if len(records) < self.max_read_rows:
                        records.append(dict(record))
                    else:
                        truncated = True
                        break

                result.consume()

            preview_rows = records[: self.preview_rows]
            payload: Dict[str, Any] = {
                "rows": records,
                "rows_count": len(records),
                "preview": preview_rows,
                "truncated": truncated,
            }

            logger.debug(
                "Read query returned %s rows (truncated=%s)",
                len(records),
                truncated,
            )

            return json.dumps(payload, default=str, indent=2)

        except Neo4jError as e:
            logger.error(f"Neo4j Error executing read query: {e}\n{query}\n{params}")
            raise ValueError(f"Neo4j Error: {e}\nQuery: {query}")

        except Exception as e:
            logger.error(f"Error executing read query: {e}\n{query}\n{params}")
            raise ValueError(f"Error: {e}\nQuery: {query}")

    def _fix_cypher_syntax(self, query: str) -> str:
        """
        Fix common Cypher syntax issues that AI agents might generate.
        """
        # Fix the specific issue with aggregation expressions referencing variables
        # from previous WITH clauses that are not grouping keys
        if (
            'rec_count' in query
            and 'count(DISTINCT total)' in query
            and 'toFloat(rec_count)' in query
            and 'max_concentration_percentage' in query
        ):
            show_literal = (self.show_code or self.event_name.lower()).replace("'", "\\'")
            visitor_label = self.visitor_label or 'Visitor_this_year'
            session_label = self.session_label or 'Sessions_this_year'
            recommendation_rel = self.recommendation_relationship or 'IS_RECOMMENDED'
            query = (
                f"MATCH (total:{visitor_label})\n"
                f"WHERE total.show = '{show_literal}'\n"
                "WITH count(total) as total_visitors\n"
                f"MATCH (v:{visitor_label})-[:{recommendation_rel}]->(s:{session_label})\n"
                f"WHERE v.show = '{show_literal}' AND s.show = '{show_literal}'\n"
                "WITH total_visitors, s, count(DISTINCT v) as rec_count\n"
                "RETURN s.title as most_recommended_session, toFloat(rec_count) / total_visitors * 100 as max_concentration_percentage\n"
                "ORDER BY max_concentration_percentage DESC\n"
                "LIMIT 1"
            )

        # Fix undefined variable 'theatre' in sessions by theatre query
        if "RETURN {metric:'sessions_by_theatre', key: theatre, value: count} AS result;" in query:
            query = query.replace(
                "MATCH (s:Sessions_this_year)\nWITH count(s) AS total\nRETURN {metric:'sessions_by_theatre', key: theatre, value: count} AS result;",
                "MATCH (s:Sessions_this_year)\nWITH s.theatre as theatre, count(s) as count\nRETURN {metric:'sessions_by_theatre', key: theatre, value: count} AS result;"
            )

        # Fix malformed geographic distribution query
        if 'RETURN count(*) AS c' in query and ')),2) AS pct' in query:
            query = query.replace(
                'RETURN count(*) AS c)),2) AS pct\nORDER BY count DESC',
                'RETURN v.country as country, count(*) as count\nORDER BY count DESC'
            )

        if 'count(DISTINCT s) as total_sessions_recommended' in query:
            visitor_label = self.visitor_label or 'Visitor_this_year'
            session_label = self.session_label or 'Sessions_this_year'
            recommendation_rel = self.recommendation_relationship or 'IS_RECOMMENDED'
            show_literal = (self.show_code or self.event_name.lower()).replace("'", "\\'")
            query = (
                f"MATCH (v:{visitor_label})-[:{recommendation_rel}]->(s:{session_label})\n"
                f"WHERE v.show = '{show_literal}' AND s.show = '{show_literal}'\n"
                "RETURN count(DISTINCT s) as total_sessions_recommended"
            )

        # Normalize mis-typed demographic property names (agent sometimes drops the leading "you_")
        query = query.replace(
            "are_you_a_please_select_the_most_appropriate_option",
            "you_are_a_please_select_the_most_appropriate_option",
        )

        # Fix double RETURN statements - remove all but the last one
        if query.count('RETURN') > 1:
            parts = query.split('RETURN')
            # Keep everything before the first RETURN, then only the last RETURN part
            query = parts[0] + 'RETURN' + parts[-1]

        # Rewrite nested aggregate patterns like avg(size(collect(r))) using
        # the canonical template for average recommendations per visitor
        query = self._rewrite_nested_avg_collect(query)

        size_pattern = re.compile(
            r"size\(\((?P<var>[a-zA-Z0-9_]+)\)-\[:(?P<rel>[A-Z_]+)]->\(\)\)",
            re.IGNORECASE,
        )

        def size_replacement(match: re.Match) -> str:
            var = match.group('var')
            rel = match.group('rel').upper()
            return f"count {{ ({var})-[:{rel}]->(:{self.label_alias_lookup.get('sessions', self.session_label)}) }}"

        query = size_pattern.sub(size_replacement, query)

        # Handle other common syntax issues
        lines = query.strip().split('\n')
        fixed_lines = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Fix common issues
            # Remove trailing commas before ORDER BY
            if line.upper().startswith('ORDER BY'):
                # Check if previous line ends with comma
                if fixed_lines and fixed_lines[-1].endswith(','):
                    fixed_lines[-1] = fixed_lines[-1].rstrip(',')

            fixed_lines.append(line)

        return '\n'.join(fixed_lines)

    def _normalize_cypher_identifiers(self, query: str) -> str:
        """Map generic labels/relationships to the configured Neo4j schema."""

        def replace_label(match: re.Match) -> str:
            label = match.group(1)
            replacement = self.label_alias_lookup.get(label.lower())
            if not replacement or replacement.lower() == label.lower():
                return match.group(0)
            return f":{replacement}"

        # Avoid matching relationship definitions by excluding colon instances that follow '['
        label_pattern = re.compile(r"(?<!\[):\s*`?([A-Za-z_][A-Za-z0-9_]*)`?", re.IGNORECASE)
        query = label_pattern.sub(replace_label, query)

        def replace_relationship(match: re.Match) -> str:
            rel = match.group(1)
            replacement = self.relationship_alias_lookup.get(rel.upper())
            if not replacement or replacement.upper() == rel.upper():
                return match.group(0)
            return match.group(0).replace(rel, replacement, 1)

        rel_pattern = re.compile(r"\[\s*:\s*`?([A-Za-z_][A-Za-z0-9_]*)`?", re.IGNORECASE)
        query = rel_pattern.sub(replace_relationship, query)

        return query

    def _rewrite_nested_avg_collect(self, query: str) -> str:
        """Rewrite known nested aggregate patterns into template-compliant Cypher."""

        if "avg(size(collect(" not in query.lower():
            return query

        lowered_query = query.lower()
        if "avg_recommendations_per_visitor" not in lowered_query and "avg_recs_per_visitor" not in lowered_query:
            return query

        show_literal = (self.show_code or "unknown").replace("'", "\\'")
        visitor_label = self.visitor_label or 'Visitor_this_year'
        session_label = self.session_label or 'Sessions_this_year'
        recommendation_rel = self.recommendation_relationship or 'IS_RECOMMENDED'

        rewritten_query = (
            f"MATCH (v:{visitor_label})\n"
            f"WHERE v.show = '{show_literal}'\n"
            f"OPTIONAL MATCH (v)-[r:{recommendation_rel}]->(s:{session_label})\n"
            f"WHERE s.show = '{show_literal}'\n"
            f"WITH v, count(r) AS rec_count\n"
            f"RETURN avg(rec_count) AS avg_recommendations_per_visitor"
        )

        return rewritten_query

    def write_neo4j_cypher(self, query: str, params: Optional[Dict[str, Any]] = None) -> str:
        """
        Execute a write Cypher query on the neo4j database.
        """
        if not query.strip():
            raise ValueError("Query cannot be empty")

        # Check if it's actually a write query
        if not re.search(r"\b(MERGE|CREATE|SET|DELETE|REMOVE|ADD)\b", query, re.IGNORECASE):
            logger.warning(
                "write_neo4j_cypher received a read-only query; automatically routing to read_neo4j_cypher."
            )
            return self.read_neo4j_cypher(query, params)

        query = self._normalize_cypher_identifiers(query)
        query = self._fix_cypher_syntax(query)

        try:
            with self.neo4j_driver.session(database=self.neo4j_database) as session:
                result = session.run(query, parameters=params or {})
                summary = result.consume()

            counters_json_str = json.dumps(summary.counters.__dict__, default=str, indent=2)

            logger.debug(f"Write query affected {counters_json_str}")

            return counters_json_str

        except Neo4jError as e:
            logger.error(f"Neo4j Error executing write query: {e}\n{query}\n{params}")
            raise ValueError(f"Neo4j Error: {e}\nQuery: {query}")

        except Exception as e:
            logger.error(f"Error executing write query: {e}\n{query}\n{params}")
            raise ValueError(f"Error: {e}\nQuery: {query}")

    def _is_valid_todo_plan(self, todos: List[Dict[str, Any]]) -> bool:
        """Verify the agent retained the canonical TODO list before execution."""
        if not todos:
            return False

        if self._todos_match_preloaded(todos):
            return True

        # Fallback to legacy heuristic only if we were unable to preload the plan
        if not self.expected_todo_contents:
            return len(todos) >= self.required_todo_count

        return False

    def _todos_match_preloaded(self, todos: List[Dict[str, Any]]) -> bool:
        """Check if the returned TODO list matches the canonical manifest order."""
        if not self.expected_todo_contents:
            return False

        if len(todos) != len(self.expected_todo_contents):
            return False

        for todo, expected in zip(todos, self.expected_todo_contents):
            if self._todo_lookup_key(todo.get("content")) != self._todo_lookup_key(expected):
                return False

            if self._normalize_todo_content(todo.get("content")) != self._normalize_todo_content(expected):
                return False

        return True

    def _align_todos_with_manifest(
        self,
        todos: List[Dict[str, Any]],
    ) -> Tuple[List[Dict[str, Any]], bool]:
        """Realign TODO payloads to match the manifest-defined ordering."""

        if not self.preloaded_todo_state:
            return todos, False

        if not todos:
            return deepcopy(self.preloaded_todo_state), True

        lookup: Dict[str, Dict[str, Any]] = {}
        for todo in todos:
            key = self._todo_lookup_key(todo.get("content"))
            if not key or key in lookup:
                continue
            lookup[key] = todo

        reconciled: List[Dict[str, Any]] = []
        changed = False

        for template in self.preloaded_todo_state:
            expected_content = template.get("content", "")
            key = self._todo_lookup_key(expected_content)
            matched = lookup.get(key)

            if matched:
                merged = dict(matched)
                merged["content"] = expected_content
                merged["status"] = merged.get("status") or template.get("status", "pending")
                reconciled.append(merged)
                if self._normalize_todo_content(matched.get("content")) != self._normalize_todo_content(expected_content):
                    changed = True
            else:
                reconciled.append({
                    "content": expected_content,
                    "status": template.get("status", "pending"),
                })
                changed = True

        if len(reconciled) != len(todos):
            changed = True

        return reconciled, changed

    def _build_retry_instruction(self, todos: List[Dict[str, Any]], attempt: int) -> str:
        """Create explicit guidance for the agent when re-planning TODOs."""
        preview_items = [
            (todo.get("content") or "").strip()
            for todo in todos[:5]
        ]
        preview_text = " | ".join(filter(None, preview_items)) or "(no content captured)"
        expected_total = self.prebuilt_todo_total or self.required_todo_count
        directives = [
            "\n\n## Retry Directive\n",
            f"Attempt #{attempt} overwrote the canonical {expected_total}-item TODO list with: {preview_text}.\n",
            "You must not invent a new plan—only update statuses on the existing entries.\n",
            "- Call `read_todos`; if the contents differ from `TODO 01` through the final `TODO`, stop immediately.\n",
        ]
        if self.prebuilt_todos_display:
            directives.append(
                f"- If `read_todos` reports fewer than {expected_total} entries, reopen the markdown plan via "
                f"`read_file(\"{self.prebuilt_todos_display}\")` and reapply the exact TODO text in batches (10 items max per `write_todos` call).\n"
            )
        directives.append(
            "- Resume work only after the middleware shows the full canonical count with identical labels."
        )
        return "".join(directives)

    async def generate_and_execute_report(self) -> Dict[str, Any]:
        """
        Generate TODO list and execute all tasks in a continuous workflow until completion.

        This follows the research_agent.py pattern of single continuous execution.
        """
        schema_path = self._prepare_schema_file()

        # Extract config values and replace placeholders in template
        config_values = self._extract_config_values()
        processed_template = self._replace_placeholders_in_template(self.prompt_template, config_values)

        # Save the processed template and supporting assets
        processed_template_path = self.artifacts_dir / f"processed_prompt_{self.event_name.lower()}{self.event_year}.md"
        processed_template_path.write_text(processed_template, encoding='utf-8')
        processed_template_display = self._format_agent_path(processed_template_path)
        schema_display = self._format_agent_path(schema_path)

        manifest = build_task_manifest(self, processed_template, config_values)
        manifest_path = save_task_manifest(self, manifest)
        manifest_display = self._format_agent_path(manifest_path)
        prebuilt_todos = build_prebuilt_todos(manifest)
        prebuilt_todos_path = save_prebuilt_todos(self, prebuilt_todos)
        prebuilt_todos_display = self._format_agent_path(prebuilt_todos_path)
        prebuilt_todo_total = len(prebuilt_todos)
        self.required_todo_count = prebuilt_todo_total
        self.preloaded_todo_state = build_todo_state_entries(manifest)
        self.expected_todo_contents = [entry["content"] for entry in self.preloaded_todo_state]
        self.prebuilt_todos_display = prebuilt_todos_display
        self.prebuilt_todo_total = prebuilt_todo_total
        recovered_artifacts = collect_existing_artifacts(self, manifest)
        recovery_inventory_display = save_recovery_inventory(self, recovered_artifacts)
        final_report_display = next(
            (task["output_file_display"] for task in manifest if task["type"] == "final_report"),
            self.output_dir_display,
        )

        core_config_section = (
            "## Core Configuration Reminders\n"
            f"- Open the processed prompt template via `read_file(\"{processed_template_display}\")` when you need exact wording or placeholder guidance.\n"
            f"- Use `read_file(\"{self.config_path_display}\")` whenever you need SHOW_CODE, filtering flags, or similarity attributes—do not rely on cached values.\n"
            f"- Schema reference: `read_file(\"{schema_display}\")` before every Cypher draft to avoid invalid labels.\n"
        )

        if self.example_report_display:
            example_report_line = "- Example report for tone/structure: " + self.example_report_display + "\n"
            final_template_line = (
                f"- Before drafting the final markdown, open {self.example_report_display} and mirror its exact heading order: metadata header block → Executive Summary → Key Metrics Overview table → Strengths → Areas for Improvement → Critical Issues → Section 1 (Event Overview & Visitor Registration) → Section 2 (Visitor Demographics & Segmentation) → Report Metadata → END OF REPORT.\n"
                f"- Keep the same section titles, numbering, and closing marker; only update the numbers and narrative with CPCN {self.event_year} data.\n"
                "- Do not insert extra callouts such as 'Data Sources' or inline file-path bullet lists in any section.\n"
            )
        else:
            example_report_line = ""
            final_template_line = ""
        final_chat_line = (
            "- Final chat response must stay concise: confirm completion and list the saved file paths (final report + summaries + README). Do not restate the report contents or execution trace.\n"
        )
        protocol_line = (
            f"- Detailed execution / recovery checklist: {self.agent_protocol_display}\n"
            if self.agent_protocol_display
            else ""
        )

        base_user_message = (
            f"You must execute the {self.event_name.upper()} {self.event_year} pre-show workflow using the prebuilt TODO plan. All prerequisite artifacts already exist in the repository—do **not** regenerate any templates or manifests.\n\n"
            "## Resources (paths already include the leading `/` required by the FilesystemMiddleware)\n"
            f"- Task manifest (JSON with every query/output): {manifest_display}\n"
            f"- Prebuilt TODO plan (use `read_file` when you need verbatim Cypher or instructions): {prebuilt_todos_display}\n"
            f"- Resolved prompt template: {processed_template_display}\n"
            f"- Full configuration YAML: {self.config_path_display}\n"
            f"- Schema snapshot: {schema_display}\n"
            + example_report_line
            + final_template_line
            + f"- Output directory for ALL files: {self.output_dir_display}\n"
            + f"- Long-term memory namespace (persists across runs): {self.memory_output_dir_display}\n"
            + (f"- Recovery inventory of existing artifacts: {recovery_inventory_display}\n" if recovery_inventory_display else "")
            + protocol_line
            + "- Use filesystem tools exactly as described by DeepAgents middleware: every path you pass to `ls`, `read_file`, `write_file`, etc. must keep the leading `/` and stays sandboxed under the repository root provided by the backend.\n"
            + "- Bulk updates always use `write_file(path, new_content)`; `edit_file` is forbidden and will throw an error.\n\n"
            + core_config_section
            + "\n## TODO Bootstrapping\n"
            + f"- The prebuilt plan has **{prebuilt_todo_total}** entries stored in `{prebuilt_todos_display}`. Immediately open it and load TODO 01-10 via `write_todos`, confirm with `read_todos`, then append the next batches (≤10 items each) until all entries exist.\n"
            + f"- If the TODO count ever differs from {prebuilt_todo_total}, halt, reload the missing entries from the markdown file, and continue only when `read_todos` shows the full canonical set.\n"
            + f"- When you need the exact Cypher or instructions, call `read_file(\"{prebuilt_todos_display}\")` instead of pasting the text back into chat.\n"
            + "\n## Key Execution Reminders\n"
            + "- Reference the protocol document for recovery steps, synthesis order, and report assembly expectations.\n"
            + f"- Mirror every saved artifact under both {self.output_dir_display} and {self.memory_output_dir_display}.\n"
            + "- Use `write_file` immediately after each Neo4j call to persist the JSON payload returned by the tool, then run `ls` on both directories to confirm the file exists before marking the TODO complete, and cite those exact paths in your notes.\n"
            + ("- When compiling the final markdown, reproduce the sections, tables, and tone from the provided short template verbatim (only substitute CPCN metrics).\n" if self.example_report_display else "")
            + f"- The final TODO must assemble `{final_report_display}` citing the saved files; do not end the run while any TODO remains pending.\n"
            + final_chat_line
        )

        logger.info(f"Generating and executing complete pre-show report for {self.event_name} {self.event_year}")
        result: Dict[str, Any] = {}
        todos: List[Dict[str, Any]] = []
        retry_suffix = ""
        for attempt in range(1, self.max_todo_plan_attempts + 1):
            composed_message = base_user_message + retry_suffix
            invoke_payload: Dict[str, Any] = {
                "messages": [HumanMessage(content=composed_message)]
            }

            result = await self.agent.ainvoke(invoke_payload)

            todos = result.get("todos") or []
            todos, was_reconciled = self._align_todos_with_manifest(todos)
            if was_reconciled:
                result["todos"] = todos
            if self._is_valid_todo_plan(todos):
                break

            self._persist_artifacts(result)
            if attempt == self.max_todo_plan_attempts:
                raise RuntimeError(
                    "TODO plan invalid after multiple attempts. Ensure DeepAgents produces granular Neo4j query tasks before execution."
                )

            retry_suffix = self._build_retry_instruction(todos, attempt)
            logger.warning(
                "Retrying TODO planning (attempt %s/%s) due to insufficient granularity",
                attempt,
                self.max_todo_plan_attempts,
            )
            await asyncio.sleep(0)

        if len(todos) != self.required_todo_count:
            self._persist_artifacts(result)
            raise RuntimeError(
                f"Agent loaded {len(todos)} TODOs but the plan contains {self.required_todo_count}. Reload the plan in batches and ensure the counts match before execution."
            )

        incomplete_todos = [
            {
                "index": idx + 1,
                "status": todo.get("status", "unknown"),
                "content": todo.get("content", "")
            }
            for idx, todo in enumerate(todos)
            if todo.get("status") != "completed"
        ]

        if incomplete_todos:
            self._persist_artifacts(result)
            summary = ", ".join(
                f"#{todo['index']} ({todo['status']}): {todo['content']}"[:200]
                for todo in incomplete_todos
            )
            raise RuntimeError(
                "DeepAgents halted with incomplete TODOs. Incomplete items: " + summary
            )

        # Validate that real files landed in the output directory even if DeepAgents
        # does not surface them via the `files` payload (some providers omit this).
        if not any(self.output_dir.glob("*")):
            self._persist_artifacts(result)
            raise RuntimeError(
                f"No artifacts were saved under {self.output_dir_display}. Ensure `write_file` is used for every task."
            )

        return result

    def _prepare_schema_file(self, force_refresh: bool = True) -> Path:
        """Retrieve the Neo4j schema via APOC and persist it for agents to consume."""

        if force_refresh or not self.schema_path.exists():
            schema_json = self.get_neo4j_schema()
            self.schema_path.write_text(schema_json, encoding='utf-8')
            self.schema_path_display = self._format_agent_path(self.schema_path)
        return self.schema_path

    def _persist_artifacts(self, result: Dict[str, Any]) -> Dict[str, Path]:
        """
        Persist the TODO list and artifacts to disk, following research_agent pattern.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_dir = self.artifacts_dir / f"todo_generation_{timestamp}"
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

            # Also save as JSON for programmatic access
            todos_json_path = run_dir / "todos.json"
            with open(todos_json_path, 'w') as f:
                json.dump(todos, f, indent=2)
            artifacts["todos_json"] = todos_json_path

        # Persist final response
        final_message = None
        messages = result.get("messages") or []
        if messages:
            final_message = messages[-1]

        response_content = ""
        if final_message is not None:
            content = getattr(final_message, "content", "")
            if isinstance(content, list):
                response_content = "\n\n".join(
                    segment.get("text", "") if isinstance(segment, dict) else str(segment)
                    for segment in content
                )
            else:
                response_content = str(content)

        if response_content:
            response_path = run_dir / "agent_response.md"
            response_path.write_text(response_content, encoding="utf-8")
            artifacts["response"] = response_path
            print(f"Agent response saved to: {response_path}")
        else:
            print("No agent response content found")

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

    @staticmethod
    def _normalize_todo_content(content: Optional[str]) -> str:
        if not content:
            return ""
        collapsed = re.sub(r"\s+", " ", content).strip()
        return collapsed

    @staticmethod
    def _todo_lookup_key(content: Optional[str]) -> str:
        if not content:
            return ""
        match = re.search(r"todo\s*(\d+)", content, re.IGNORECASE)
        if match:
            return f"num-{int(match.group(1)):02d}"
        return "text-" + ShowReportGenerator._normalize_todo_content(content).lower()


