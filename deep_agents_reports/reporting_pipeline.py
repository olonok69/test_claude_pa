"""
Reporting Pipeline Runner

Supports both pre-show (personal_agendas) and post-show (post_analysis) report generation.

Usage:
    Pre-show report:
        python reporting_pipeline.py --profile lva2025
    
    Post-show report:
        python reporting_pipeline.py --profile lva2025_post
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Optional

import yaml

try:
    from .arc.pre_show.generator import ShowReportGenerator
    from .enrich_report import enrich_report
except ImportError:  # Script execution fallback
    from arc.pre_show.generator import ShowReportGenerator
    from enrich_report import enrich_report

logger = logging.getLogger(__name__)


def resolve_project_path(raw_path: str, project_root: Path) -> Path:
    """Resolve profile paths with compatibility for legacy deep_agents_reports prefixes."""
    candidate = Path(raw_path)
    if candidate.is_absolute():
        return candidate.resolve()

    stripped = candidate
    if candidate.parts and candidate.parts[0] == "deep_agents_reports":
        stripped = Path(*candidate.parts[1:])

    candidates = [
        Path.cwd() / candidate,
        Path.cwd() / stripped,
        project_root / candidate,
        project_root / stripped,
        project_root / "deep_agents_reports" / candidate,
        project_root / "deep_agents_reports" / stripped,
    ]

    for path in candidates:
        resolved = path.resolve()
        if resolved.exists():
            return resolved

    return (project_root / stripped).resolve()


def determine_report_type(profile: dict) -> str:
    """
    Determine the report type from the profile configuration.
    
    Returns:
        'pre_show' or 'post_show' based on profile settings.
    """
    # Explicit report_type takes precedence
    if "report_type" in profile:
        return profile["report_type"]
    
    # Infer from mode
    mode = profile.get("mode", "personal_agendas")
    if mode == "post_analysis":
        return "post_show"
    
    return "pre_show"


def get_output_subdirectory(report_type: str) -> str:
    """Get the output subdirectory based on report type."""
    return "post_show" if report_type == "post_show" else "pre_show"


def run_phase_one(profile: dict) -> Path:
    """
    Execute Phase 1: Generate the base report using ShowReportGenerator.
    
    This phase supports both pre-show and post-show report generation.
    The generator uses the appropriate prompt template based on the profile configuration.
    
    Args:
        profile: Configuration profile from reporting_pipeline.yaml
        
    Returns:
        Path to the generated base report.
    """
    event = profile["event"]
    year = int(profile["year"])
    project_root = Path(__file__).resolve().parent
    config_path = str(resolve_project_path(profile["config_path"], project_root))
    prompt_template = str(resolve_project_path(profile["prompt_template"], project_root))
    neo4j_profile = profile.get("neo4j_profile", "prod")
    neo4j_database = profile.get("neo4j_database", "neo4j")
    provider = profile.get("provider_phase1", "anthropic")
    model = profile.get("model_phase1")
    temperature = float(profile.get("temperature_phase1", 0.1))
    max_tokens = profile.get("max_tokens_phase1")
    if max_tokens is not None:
        max_tokens = int(max_tokens)
    
    # Example report for style reference
    example_report = profile.get("example_report")
    if example_report:
        example_report = str(resolve_project_path(example_report, project_root))
    
    # Pre-show report reference (for post-show comparison)
    pre_show_report = profile.get("pre_show_report")
    if pre_show_report:
        pre_show_report = str(resolve_project_path(pre_show_report, project_root))
    
    report_type = determine_report_type(profile)
    
    logger.info(f"Starting Phase 1 for {event.upper()} {year} ({report_type} report)")
    logger.info(f"Using prompt template: {prompt_template}")
    logger.info(f"Using config: {config_path}")
    
    if pre_show_report:
        logger.info(f"Pre-show report reference: {pre_show_report}")

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
        pre_show_report_path=pre_show_report,  # Pass pre-show report for post-analysis
        report_type=report_type,
        verbose=True,
    )

    try:
        import asyncio

        generator.initialize()
        asyncio.run(generator.generate_and_execute_report())
    finally:
        generator.close()

    # Determine output path based on report type
    project_root = generator.project_root
    output_subdir = get_output_subdirectory(report_type)
    report_suffix = "post_show" if report_type == "post_show" else "pre_show"
    
    output_path = (
        project_root
        / "outputs"
        / f"{event.lower()}{year}"
        / output_subdir
        / f"final_report_{event.lower()}{year}_{report_suffix}.md"
    )
    
    logger.info(f"Phase 1 complete. Base report: {output_path}")
    return output_path


def run_phase_two(profile: dict, base_report_path: Path) -> Path:
    """
    Execute Phase 2: Enrich the base report with LLM-powered polishing.
    
    Args:
        profile: Configuration profile from reporting_pipeline.yaml
        base_report_path: Path to the base report from Phase 1
        
    Returns:
        Path to the enriched report (or base report if enrichment is disabled).
    """
    if not profile.get("enable_enrichment", False):
        logger.info("Phase 2 enrichment disabled. Returning base report.")
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

    report_type = determine_report_type(profile)
    logger.info(f"Starting Phase 2 enrichment for {report_type} report")
    logger.info(f"Using model: {provider}/{model}")

    enrich_report(
        input_path=base_report_path,
        output_path=enriched_path,
        provider=provider,
        model_name=model,
        temperature=temperature,
        max_tokens=max_tokens,
    )

    logger.info(f"Phase 2 complete. Enriched report: {enriched_path}")
    return enriched_path


def validate_profile(profile: dict, profile_name: str) -> None:
    """
    Validate that a profile has all required fields.
    
    Args:
        profile: Configuration profile dictionary
        profile_name: Name of the profile for error messages
        
    Raises:
        ValueError: If required fields are missing.
    """
    required_fields = ["event", "year", "config_path", "prompt_template"]
    missing = [f for f in required_fields if f not in profile]
    
    if missing:
        raise ValueError(
            f"Profile '{profile_name}' is missing required fields: {', '.join(missing)}"
        )
    
    report_type = determine_report_type(profile)
    
    # Validate prompt template exists
    project_root = Path(__file__).resolve().parent
    prompt_path = resolve_project_path(profile["prompt_template"], project_root)
    if not prompt_path.is_absolute():
        # Will be resolved relative to project root later
        pass
    
    # For post-show reports, validate pre_show_report if provided
    if report_type == "post_show":
        pre_show_report = profile.get("pre_show_report")
        if pre_show_report:
            logger.info(f"Post-show report will reference pre-show report: {pre_show_report}")


def main() -> None:
    """Main entry point for the reporting pipeline."""
    parser = argparse.ArgumentParser(
        description="Run pre-show or post-show reporting pipeline.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Generate pre-show report for LVA 2025
    python reporting_pipeline.py --profile lva2025
    
    # Generate post-show report for LVA 2025
    python reporting_pipeline.py --profile lva2025_post
    
    # Generate post-show report for ECOMM 2025
    python reporting_pipeline.py --profile ecomm2025_post
        """
    )
    parser.add_argument(
        "--profile", 
        required=True, 
        help="Profile key from reporting_pipeline.yaml (e.g., lva2025, lva2025_post)"
    )
    parser.add_argument(
        "--config-file",
        default="config/reporting_pipeline.yaml",
        help="Path to reporting pipeline YAML config",
    )
    parser.add_argument(
        "--skip-enrichment",
        action="store_true",
        help="Skip Phase 2 enrichment even if enabled in profile",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Load configuration
    config_path = Path(args.config_file).resolve()
    if not config_path.exists():
        raise SystemExit(f"Configuration file not found: {config_path}")
    
    with config_path.open("r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}

    if args.profile not in config:
        available = ", ".join(sorted(config.keys()))
        raise SystemExit(
            f"Profile '{args.profile}' not found in {config_path}\n"
            f"Available profiles: {available}"
        )

    profile = config[args.profile]
    
    # Validate profile
    validate_profile(profile, args.profile)
    
    # Override enrichment if requested
    if args.skip_enrichment:
        profile["enable_enrichment"] = False

    report_type = determine_report_type(profile)
    logger.info(f"=" * 60)
    logger.info(f"Starting {report_type.upper().replace('_', '-')} report generation")
    logger.info(f"Profile: {args.profile}")
    logger.info(f"Event: {profile['event'].upper()} {profile['year']}")
    logger.info(f"=" * 60)

    # Execute Phase 1
    base_report = run_phase_one(profile)
    if not base_report.exists():
        raise SystemExit(f"Phase 1 did not produce base report at {base_report}")

    # Execute Phase 2
    enriched = run_phase_two(profile, base_report)

    # Print summary
    print("\n" + "=" * 60)
    print(f"Report generation complete!")
    print(f"Report type: {report_type.replace('_', '-').upper()}")
    print(f"Base report: {base_report}")
    if enriched != base_report:
        print(f"Enriched report: {enriched}")
    print("=" * 60)


if __name__ == "__main__":
    main()