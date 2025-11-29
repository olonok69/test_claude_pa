import argparse
from pathlib import Path

import yaml

from .arc.pre_show.generator import ShowReportGenerator
from .enrich_report import enrich_report


def run_phase_one(profile: dict) -> Path:
    event = profile["event"]
    year = int(profile["year"])
    config_path = profile["config_path"]
    prompt_template = profile["prompt_template"]
    neo4j_profile = profile.get("neo4j_profile", "prod")
    neo4j_database = profile.get("neo4j_database", "neo4j")
    provider = profile.get("provider_phase1", "anthropic")
    model = profile.get("model_phase1")
    temperature = float(profile.get("temperature_phase1", 0.1))
    max_tokens = profile.get("max_tokens_phase1")
    if max_tokens is not None:
        max_tokens = int(max_tokens)
    example_report = profile.get("example_report")

    generator = ShowReportGenerator(
        event_name=event,
        event_year=year,
        config_path=config_path,
        prompt_template_path=prompt_template,
        provider=provider,
        model_name=model,
        temperature=temperature,
        max_tokens=max_tokens,
        neo4j_profile=neo4j_profile,
        neo4j_database=neo4j_database,
        example_report_path=example_report,
        verbose=True,
    )

    try:
        import asyncio

        generator.initialize()
        asyncio.run(generator.generate_and_execute_report())
    finally:
        generator.close()

    # Phase 1 conventionally writes the final report here
    project_root = generator.project_root
    output_path = (
        project_root
        / "deep_agents_reports"
        / "outputs"
        / f"{event.lower()}{year}"
        / "pre_show"
        / f"final_report_{event.lower()}{year}.md"
    )
    return output_path


def run_phase_two(profile: dict, base_report_path: Path) -> Path:
    if not profile.get("enable_enrichment", False):
        return base_report_path

    provider = profile.get("provider_phase2", "anthropic")
    model = profile.get("model_phase2")
    temperature = float(profile.get("temperature_phase2", 0.1))
    max_tokens = profile.get("max_tokens_phase2")
    if max_tokens is not None:
        max_tokens = int(max_tokens)

    enriched_path = base_report_path.with_name(
        base_report_path.stem + "_enriched" + base_report_path.suffix
    )

    enrich_report(
        input_path=base_report_path,
        output_path=enriched_path,
        provider=provider,
        model_name=model,
        temperature=temperature,
        max_tokens=max_tokens,
    )

    return enriched_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Run pre-show reporting pipeline (phase 1 + phase 2).")
    parser.add_argument("--profile", required=True, help="Profile key from reporting_pipeline.yaml (e.g. lva2025)")
    parser.add_argument(
        "--config-file",
        default="deep_agents_reports/config/reporting_pipeline.yaml",
        help="Path to reporting pipeline YAML config",
    )

    args = parser.parse_args()

    config_path = Path(args.config_file).resolve()
    with config_path.open("r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}

    if args.profile not in config:
        raise SystemExit(f"Profile '{args.profile}' not found in {config_path}")

    profile = config[args.profile]

    base_report = run_phase_one(profile)
    if not base_report.exists():
        raise SystemExit(f"Phase 1 did not produce base report at {base_report}")

    enriched = run_phase_two(profile, base_report)

    print(f"Base report: {base_report}")
    if enriched != base_report:
        print(f"Enriched report: {enriched}")


if __name__ == "__main__":
    main()
