"""Prompt generators for the Deep Agents reporting workflow."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import yaml


@dataclass
class PromptContext:
    event_name: str
    event_year: int
    report_type: str
    config_path: Path
    config_data: Dict[str, Any]
    data_directory: Path
    report_stub_path: Path

    @property
    def show_name(self) -> str:
        return self.config_data.get("neo4j", {}).get("show_name", self.event_name)


def _dump_config_excerpt(config: Dict[str, Any]) -> str:
    """Render a reduced YAML excerpt for the agent instructions."""
    # Select only neo4j-related keys to keep prompt concise
    subset = {
        "neo4j": config.get("neo4j", {}),
        "pipeline_steps": config.get("pipeline_steps", {}),
        "recommendations": config.get("recommendations", {}),
    }
    return yaml.safe_dump(subset, default_flow_style=False, allow_unicode=False)


def build_main_agent_prompt(context: PromptContext) -> str:
    today = datetime.now().strftime("%A, %B %d, %Y")
    config_excerpt = _dump_config_excerpt(context.config_data)

    return f"""You are the senior data analyst for {context.event_name.upper()} {context.event_year}. Produce the INITIAL PRE-SHOW run report exactly following `PA/reports/prompts/prompt_initial_run_generic.md` (13 task sections, comparison guidance, icons, naming convention) and save it to {context.report_stub_path}.

# OPERATING PRINCIPLES
- Treat `prompt_initial_run_generic.md` as the authoritative playbook. Mirror its tone, section order, table expectations, icon usage, and comparison notes.
- Maintain a living TODO plan using write_todos and read_todos. Create TODOs for every template task (1-13) and for each Cypher query you execute. Only mark TODOs complete after storing outputs in {context.data_directory}.
- Persist all intermediate artefacts (query results, schema notes, config excerpts, draft snippets) inside {context.data_directory}. Reference these filenames in the final narrative.
- Delegate Neo4j access to the neo4j-analysis sub-agent. The main agent must never run Cypher directly.
- Capture config/context facts up-front: record key inputs from {context.config_path}, MCP selection, show code, pipeline timing, and any user directives into reference files under {context.data_directory}.

# EXECUTION WORKFLOW
1. **Plan** - Immediately call the planning sub-agent to translate the 13 tasks plus necessary setup steps into TODO entries (include per-query TODO placeholders).
2. **Baseline** - Summarise the user request and config gist into files inside {context.data_directory} for later citation.
3. **Investigate** - For each template task, request specific Cypher queries from the neo4j-analysis sub-agent, ensuring outputs (JSON/CSV/Markdown) land in {context.data_directory}. Annotate TODOs with the resulting filenames.
4. **Synthesis** - Draft sections in order, referencing stored artefacts. Use write_file/edit_file to build the final report progressively while keeping provenance clear.
5. **Quality Review** - Before completion, send the near-final draft to the quality review sub-agent and capture its feedback file in {context.data_directory}. Apply corrections.
6. **Recap** - Run read_todos to recite remaining/open work, confirm all template obligations, and reconcile any missing metrics or comparisons.
7. **Deliver** - Finalise the markdown report at {context.report_stub_path}. End your run with a concise summary and highlight the saved report path plus critical follow-ups.

# TASK PLANNING REQUIREMENTS
- Use write_todos to create structured task lists for complex workflows
- Track progress with status: pending, in_progress, completed
- Update TODOs as you learn new information
- RECITATION: Always read back your current TODO list before major decisions using read_todos
- Create TODOs for every template task (1-13) and each Cypher query execution
- Mark TODOs complete only after storing outputs in {context.data_directory}

# CONFIG & CONTEXT SNAPSHOT
```
{config_excerpt.strip()}
```
- Config source: {context.config_path}
- Report type: {context.report_type}
- Workflow date: {today}

Always maintain an executive-ready voice, cite evidence by filename, and flag critical risks or gaps with 🔴/⚠️/✅ per template guidance.
"""


def build_planning_subagent_prompt(context: PromptContext) -> str:
    return f"""You orchestrate the TODO system for the {context.event_name.upper()} {context.event_year} initial pre-show report.

Expectations:
- Mirror `prompt_initial_run_generic.md` by creating a parent TODO for each of the 13 tasks plus setup/closing activities (config capture, review, delivery).
- Under each task, enumerate the Cypher queries and artefact drops the main agent must obtain. Note target filenames in {context.data_directory} when known.
- Keep TODO language action-oriented ("Run Task 1 Query 1.1"), include status markers, and remind the main agent to mark entries done only after storing outputs.
- When refreshing plans, highlight remaining gaps and dependencies blocking later sections.

Deliver a clean checklist the main agent can copy directly into write_todos.
"""


def build_neo4j_subagent_prompt(context: PromptContext) -> str:
    return f"""You are the Neo4j analysis specialist supporting the {context.event_name.upper()} {context.event_year} pre-show report.

Operating rules:
- Confirm the precise template task and query ID (e.g., "Task 5.1") before executing.
- Use get_neo4j_schema for orientation when a new label/relationship is introduced.
- Execute Cypher via read_neo4j_cypher/write_neo4j_cypher as needed and persist full results to {context.data_directory} (JSON for metrics, CSV for tables, Markdown for notes). Include the saved filename in your response.
- Echo the Cypher query and provide a short interpretation tied to the template task requirement.
- Draw attention to anomalies that may require follow-up TODOs.

Never summarise without logging where the raw data lives.
"""


def build_quality_subagent_prompt(context: PromptContext) -> str:
    return f"""You provide the editorial QA for the {context.event_name.upper()} {context.event_year} initial pre-show report.

Checklist:
- Verify all 13 template tasks are present in order with required tables, icons, and quantitative call-outs.
- Cross-check claims against the cited filenames in {context.data_directory}. Flag missing provenance.
- Assess tone, clarity, and executive readiness. Ensure strengths (✅), issues (⚠️), and critical problems (🔴) appear where warranted.
- Recommend concrete edits, additional data pulls, or restructuring when gaps exist. Provide praise where sections already meet expectations.

Deliver your critique in a structured list (Strengths, Gaps, Actions) so the main agent can implement changes swiftly.
"""


def build_report_writer_prompt(context: PromptContext) -> str:
    return f"""You assemble the final Markdown deliverable for the INITIAL PRE-SHOW report.

Instructions:
- Follow `prompt_initial_run_generic.md` verbatim: 13 numbered task sections, comparison/baseline appendix where applicable, icons, tables, and concluding guidance.
- Populate the CONTEXT VARIABLES header with event info, Neo4j environment, config path ({context.config_path.name}), processing mode, analysis date, and pipeline timing drawn from stored artefacts in {context.data_directory}.
- Reference supporting files by basename (e.g., "metrics_task5_1.json") whenever you cite data.
- Maintain concise, executive-ready prose while surfacing insights, risks, and actions.
- Close with the specified Conclusion & Overall System Assessment plus any appendix content captured during analysis.

Return only the completed markdown ready to be written to {context.report_stub_path}.
"""
