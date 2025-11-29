#!/usr/bin/env python3
"""CLI entrypoint for the Deep Agents pre-show workflow."""

import argparse
import asyncio

from arc.pre_show.generator import ShowReportGenerator


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Deep Agents TODO Workflow for Pre-Show Reports")
    parser.add_argument("--event", required=True, help="Event name (e.g., CPCN)")
    parser.add_argument("--year", type=int, required=True, help="Event year (e.g., 2025)")
    parser.add_argument("--config", required=True, help="Path to config file")
    parser.add_argument("--prompt-template", required=True, help="Path to generic prompt template")
    parser.add_argument(
        "--provider",
        default="azure",
        choices=["azure", "openai", "anthropic"],
        help="LLM provider",
    )
    parser.add_argument("--model", dest="model_name", default="gpt-5-mini", help="Model name")
    parser.add_argument("--temperature", type=float, default=0.0, help="Model temperature")
    parser.add_argument("--neo4j-profile", default="test", choices=["dev", "test", "prod"], help="Neo4j profile")
    parser.add_argument("--neo4j-database", default="neo4j", help="Neo4j database name")
    parser.add_argument(
        "--example-report",
        dest="example_report",
        help="Optional path to a reference report used for tone/structure guidance",
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    return parser


async def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    generator = ShowReportGenerator(
        event_name=args.event,
        event_year=args.year,
        config_path=args.config,
        prompt_template_path=args.prompt_template,
        provider=args.provider,
        model_name=args.model_name,
        temperature=args.temperature,
        neo4j_profile=args.neo4j_profile,
        neo4j_database=args.neo4j_database,
        example_report_path=args.example_report,
        verbose=args.verbose,
    )

    try:
        generator.initialize()
        print(f"🤖 Generating and executing complete pre-show report for {args.event.upper()} {args.year}")
        print("=" * 60)

        result = await generator.generate_and_execute_report()
        operation = "generation and execution"

        artifacts = generator._persist_artifacts(result)

        todos = result.get("todos", [])
        if todos:
            print(f"\n✅ {len(todos)} TODO items processed")
            print("\n📋 TODO Status Summary:")
            print("-" * 50)
            status_counts = {}
            for todo in todos:
                status = todo.get("status", "unknown")
                status_counts[status] = status_counts.get(status, 0) + 1

            for status, count in status_counts.items():
                print(f"  {status}: {count} items")

        print("\n💾 Artifacts saved:")
        if "todos" in artifacts:
            print(f"  - TODO list: {artifacts['todos']}")
        if "todos_json" in artifacts:
            print(f"  - TODO JSON: {artifacts['todos_json']}")
        if "response" in artifacts:
            print(f"  - Agent response: {artifacts['response']}")
        if "agent_files" in artifacts:
            print(f"  - Agent files: {artifacts['agent_files']}")

        print(f"\n🎯 Report {operation} complete for {args.event.upper()} {args.year}")
    finally:
        generator.close()


if __name__ == "__main__":
    asyncio.run(main())
