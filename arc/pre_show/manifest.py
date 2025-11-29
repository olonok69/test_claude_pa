from __future__ import annotations

import json
import logging
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug or "task"


def _extract_similarity_attributes(config: Dict[str, Any]) -> List[str]:
    rec_cfg = config.get("recommendation", {})
    attributes = rec_cfg.get("similarity_attributes") or {}
    return list(attributes.keys())


def build_task_manifest(
    generator: "ShowReportGnerator",
    processed_template: str,
    config_values: Dict[str, str],
) -> List[Dict[str, Any]]:
    """Parse the resolved template into deterministic task metadata."""

    manifest: List[Dict[str, Any]] = []
    section_outputs: defaultdict[int, List[str]] = defaultdict(list)
    lines = processed_template.splitlines()
    section_number: Optional[int] = None
    section_title = ""
    query_counts: defaultdict[int, int] = defaultdict(int)
    similarity_attributes = _extract_similarity_attributes(generator.config)

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        section_match = re.match(r"^###\s+TASK\s+(\d+):\s+(.+)$", line)
        if section_match:
            section_number = int(section_match.group(1))
            section_title = section_match.group(2).strip()
            i += 1
            continue

        query_match = re.match(r"^\*\*(Query\s+([\d\.]+):\s+(.+))\*\*$", line)
        if query_match and section_number is not None:
            query_label = query_match.group(1)
            query_title = query_match.group(3).strip()
            i += 1

            while i < len(lines) and not lines[i].strip().startswith("```cypher"):
                i += 1

            if i >= len(lines):
                break
            i += 1  # skip ```cypher
            query_lines: List[str] = []
            while i < len(lines) and not lines[i].strip().startswith("```"):
                query_lines.append(lines[i])
                i += 1
            i += 1  # skip closing ```

            raw_cypher = "\n".join(query_lines).strip()
            if not raw_cypher:
                continue

            cypher_variants: List[Dict[str, Any]] = []
            if "[ATTRIBUTE_NAME]" in raw_cypher and similarity_attributes:
                for attribute in similarity_attributes:
                    cypher_variants.append({
                        "cypher": raw_cypher.replace("[ATTRIBUTE_NAME]", attribute),
                        "variant_suffix": attribute,
                    })
            else:
                cypher_variants.append({
                    "cypher": raw_cypher,
                    "variant_suffix": None,
                })

            for variant in cypher_variants:
                cypher_text = variant["cypher"]
                manual_placeholders = sorted(set(re.findall(r"\[([A-Z0-9_]+)\]", cypher_text)))
                manual_placeholders = [
                    placeholder for placeholder in manual_placeholders if placeholder not in config_values
                ]
                query_counts[section_number] += 1
                slug_source = query_title
                if variant.get("variant_suffix"):
                    slug_source = f"{query_title}_{variant['variant_suffix']}"
                slug = _slugify(slug_source)
                output_filename = f"task{section_number:02d}_q{query_counts[section_number]:02d}_{slug}.json"
                output_path = generator.output_dir / output_filename

                manifest.append({
                    "type": "query",
                    "section": section_number,
                    "section_title": section_title,
                    "query_label": query_label,
                    "query_title": query_title,
                    "cypher": cypher_text,
                    "output_file": output_path.as_posix(),
                    "output_file_display": generator._format_agent_path(output_path),
                    "manual_placeholders": manual_placeholders,
                    "variant_suffix": variant.get("variant_suffix"),
                })
                section_outputs[section_number].append(generator._format_agent_path(output_path))
            continue

        i += 1

    for section, outputs in sorted(section_outputs.items()):
        summary_filename = f"task{section:02d}_summary.md"
        summary_path = generator.output_dir / summary_filename
        manifest.append({
            "type": "synthesis",
            "section": section,
            "section_title": f"Task {section:02d} Summary",
            "query_label": f"Task {section:02d} Summary",
            "query_title": f"Summarize outputs for Task {section:02d}",
            "depends_on": outputs,
            "output_file": summary_path.as_posix(),
            "output_file_display": generator._format_agent_path(summary_path),
        })

    final_report_path = generator.output_dir / f"final_report_{generator.event_name.lower()}{generator.event_year}.md"
    final_entry = {
        "type": "final_report",
        "section": 99,
        "section_title": "Comprehensive Report Assembly",
        "query_label": "Final Report",
        "query_title": "Compile final report using the short template structure",
        "depends_on": [task["output_file_display"] for task in manifest if task.get("output_file_display")],
        "output_file": final_report_path.as_posix(),
        "output_file_display": generator._format_agent_path(final_report_path),
        "example_report": generator.example_report_display,
    }
    manifest.append(final_entry)

    return manifest


def save_task_manifest(
    generator: "ShowReportGnerator",
    manifest: List[Dict[str, Any]],
) -> Path:
    manifest_path = generator.artifacts_dir / f"task_manifest_{generator.event_name.lower()}{generator.event_year}.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest_path


def build_prebuilt_todos(manifest: List[Dict[str, Any]]) -> List[str]:
    todos: List[str] = []
    for index, task in enumerate(manifest, start=1):
        base = f"TODO {index:02d}: {task['query_title']}"
        if task["type"] == "query":
            manual_note = ""
            if task.get("manual_placeholders"):
                placeholders = ", ".join(task["manual_placeholders"])
                manual_note = f"\n- Before executing, replace placeholders ({placeholders}) with concrete values based on previously saved files or config."

            todo_text = (
                f"{base}\n"
                f"- Execute the Cypher below using `read_neo4j_cypher` and save the complete result set to `{task['output_file_display']}` immediately.\n"
                f"- Never summarize in memory—persist first, then cite the saved file."
                f"{manual_note}\n"
                f"```cypher\n{task['cypher']}\n```"
            )
            todos.append(todo_text)
        elif task["type"] == "synthesis":
            source_list = task.get("depends_on") or []
            sources = "\n  - ".join(source_list) if source_list else "(no source files recorded)"
            todo_text = (
                f"{base}\n"
                f"- Read the following files and produce a markdown summary saved to `{task['output_file_display']}`:\n  - {sources}\n"
                "- Highlight key metrics, anomalies, and cite the source files explicitly."
            )
            todos.append(todo_text)
        elif task["type"] == "final_report":
            example_note = (
                f"Refer to the example report at `{task['example_report']}` for tone and structure."
                if task.get("example_report")
                else "Follow the template structure for tone and layout."
            )
            source_list = task.get("depends_on") or []
            sources = "\n  - ".join(source_list) if source_list else "(no source files recorded)"
            todo_text = (
                f"{base}\n"
                f"- Assemble the final report using the synthesized section files below, saving the final output to `{task['output_file_display']}`:\n  - {sources}\n"
                f"- {example_note}\n"
                "- Ensure every cited metric links back to a saved file."
            )
            todos.append(todo_text)

    return todos


def save_prebuilt_todos(
    generator: "ShowReportGnerator",
    todos: List[str],
) -> Path:
    plan_path = generator.artifacts_dir / f"prebuilt_todos_{generator.event_name.lower()}{generator.event_year}.md"
    lines = ["# Prebuilt TODO Plan", ""]
    for todo in todos:
        lines.append(todo)
        lines.append("")
    plan_path.write_text("\n".join(lines), encoding="utf-8")
    return plan_path


def build_todo_state_entries(manifest: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Create concise TODO entries that reference manifest metadata."""

    todo_state: List[Dict[str, Any]] = []
    for index, task in enumerate(manifest, start=1):
        title = task.get("query_title") or task.get("section_title") or f"Task {index}"
        output_path = task.get("output_file_display")
        task_type = task.get("type", "task")
        summary = f"TODO {index:02d}: {title} ({task_type})"
        if output_path:
            summary += f" → save to {output_path}"
        todo_state.append({"content": summary, "status": "pending"})
    return todo_state


def collect_existing_artifacts(
    generator: "ShowReportGnerator",
    manifest: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Detect artifacts already present on disk or in /memories for recovery."""

    recovered: List[Dict[str, Any]] = []
    for index, task in enumerate(manifest, start=1):
        filename = Path(task["output_file"]).name
        local_path = generator.output_dir / filename
        memory_path = generator.memory_output_dir_path / filename
        local_exists = local_path.exists()
        memory_exists = memory_path.exists()

        if local_exists and not memory_exists:
            try:
                memory_path.parent.mkdir(parents=True, exist_ok=True)
                memory_path.write_text(local_path.read_text(encoding="utf-8"), encoding="utf-8")
                memory_exists = True
            except Exception as exc:  # pragma: no cover - best effort fallback
                logger.warning(
                    "Failed to backfill %s into memory namespace: %s",
                    filename,
                    exc,
                )
        if not (local_exists or memory_exists):
            continue

        recovered.append({
            "index": index,
            "title": task.get("query_title", f"Task {index}"),
            "local_path": generator._format_agent_path(local_path) if local_exists else None,
            "memory_path": f"{generator.memory_output_dir_display}/{filename}" if memory_exists else None,
        })

    return recovered


def save_recovery_inventory(
    generator: "ShowReportGnerator",
    recovered: List[Dict[str, Any]],
) -> Optional[str]:
    """Persist a markdown summary of recovered artifacts for the agent to review."""

    if not recovered:
        return None

    inventory_path = generator.artifacts_dir / f"recovery_inventory_{generator.event_name.lower()}{generator.event_year}.md"
    lines = ["# Recovered Artifacts", "", "| # | Task | Local File | Memory File |", "|---|------|-----------|-------------|"]

    for item in recovered:
        local_path = item.get("local_path") or "(missing)"
        memory_path = item.get("memory_path") or "(missing)"
        lines.append(
            f"| {item['index']:02d} | {item['title']} | {local_path} | {memory_path} |"
        )

    inventory_path.write_text("\n".join(lines), encoding="utf-8")
    return generator._format_agent_path(inventory_path)
