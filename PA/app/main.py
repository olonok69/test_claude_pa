import argparse
from utils.logging_utils import setup_logging
from utils.config_utils import load_config
from utils.summary_utils import generate_and_save_summary
from pipeline import (
    run_registration_processing,
    run_scan_processing,
    run_session_processing,
    run_neo4j_processing,
    run_session_recommendation_processing,
)

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Process and upload data to Neo4j.")
    parser.add_argument(
        "--recreate-all",
        action="store_true",
        help="Recreate all nodes, even if they already exist in Neo4j",
    )
    parser.add_argument(
        "--skip-neo4j", action="store_true", help="Skip Neo4j upload steps"
    )
    parser.add_argument(
        "--only-steps",
        type=str,
        help="Comma-separated list of step numbers to run (e.g., '1,3,4')",
    )
    parser.add_argument(
        "--only-recommendations",
        action="store_true",
        help="Only run session recommendation processing (step 10)",
    )
    args = parser.parse_args()

    # Get create_only_new from config, but allow command line to override
    # Set up logging first to load config
    logger = setup_logging(log_file="logs/data_processing.log")
    config = load_config("config/config.yaml")

    # If --recreate-all is specified, create_only_new is False
    # Otherwise, use the value from config (default True)
    if args.recreate_all:
        create_only_new = False
    else:
        create_only_new = config.get("create_only_new", True)

    logger.info(f"Running with create_only_new={create_only_new}")

    try:
        # Load the configuration
        config = load_config("config/config.yaml")

        # Determine which steps to run
        steps_to_run = []
        if args.only_steps:
            steps_to_run = [int(step.strip()) for step in args.only_steps.split(",")]

        # If only recommendations flag is set, only run step 10
        if args.only_recommendations:
            logger.info("Running only session recommendation processing (step 10)")
            processors = {
                "session_recommendation_processor": run_session_recommendation_processing(
                    config, create_only_new
                )
            }
            generate_and_save_summary(processors, skip_neo4j=True)
            logger.info("Session recommendation processing completed successfully")
            exit(0)

        processors = {}

        # Step 1: Registration data processing
        if not steps_to_run or 1 in steps_to_run:
            if config.get("pipeline_steps", {}).get("registration_processing", True):
                logger.info("Starting step 1: Registration data processing")
                processors["reg_processor"] = run_registration_processing(config)
                logger.info("Completed step 1: Registration data processing")
            else:
                logger.info(
                    "Skipping step 1: Registration data processing (disabled in config)"
                )

        # Step 2: Scan data processing
        if not steps_to_run or 2 in steps_to_run:
            if config.get("pipeline_steps", {}).get("scan_processing", True):
                logger.info("Starting step 2: Scan data processing")
                processors["scan_processor"] = run_scan_processing(config)
                logger.info("Completed step 2: Scan data processing")
            else:
                logger.info(
                    "Skipping step 2: Scan data processing (disabled in config)"
                )

        # Step 3: Session data processing
        if not steps_to_run or 3 in steps_to_run:
            if config.get("pipeline_steps", {}).get("session_processing", True):
                logger.info("Starting step 3: Session data processing")
                processors["session_processor"] = run_session_processing(config)
                logger.info("Completed step 3: Session data processing")
            else:
                logger.info(
                    "Skipping step 3: Session data processing (disabled in config)"
                )

        # Neo4j processing steps (optional with --skip-neo4j flag)
        if not args.skip_neo4j:
            # Check if any Neo4j steps are enabled
            neo4j_steps_enabled = any(
                [
                    config.get("pipeline_steps", {}).get(
                        "neo4j_visitor_processing", True
                    ),
                    config.get("pipeline_steps", {}).get(
                        "neo4j_session_processing", True
                    ),
                    config.get("pipeline_steps", {}).get(
                        "neo4j_job_stream_processing", True
                    ),
                    config.get("pipeline_steps", {}).get(
                        "neo4j_specialization_stream_processing", True
                    ),
                    config.get("pipeline_steps", {}).get(
                        "neo4j_visitor_relationship_processing", True
                    ),
                    config.get("pipeline_steps", {}).get(
                        "session_embedding_processing", True
                    ),
                    config.get("pipeline_steps", {}).get(
                        "session_recommendation_processing", True
                    ),
                ]
            )

            # Check which specific Neo4j steps should run based on configuration and command line
            neo4j_steps_to_run = steps_to_run
            if not steps_to_run:
                # If no specific steps are requested, include all steps that are enabled in config
                neo4j_steps_to_run = []
                if config.get("pipeline_steps", {}).get(
                    "neo4j_visitor_processing", True
                ):
                    neo4j_steps_to_run.append(4)
                if config.get("pipeline_steps", {}).get(
                    "neo4j_session_processing", True
                ):
                    neo4j_steps_to_run.append(5)
                if config.get("pipeline_steps", {}).get(
                    "neo4j_job_stream_processing", True
                ):
                    neo4j_steps_to_run.append(6)
                if config.get("pipeline_steps", {}).get(
                    "neo4j_specialization_stream_processing", True
                ):
                    neo4j_steps_to_run.append(7)
                if config.get("pipeline_steps", {}).get(
                    "neo4j_visitor_relationship_processing", True
                ):
                    neo4j_steps_to_run.append(8)
                if config.get("pipeline_steps", {}).get(
                    "session_embedding_processing", True
                ):
                    neo4j_steps_to_run.append(9)
                if config.get("pipeline_steps", {}).get(
                    "session_recommendation_processing", True
                ):
                    neo4j_steps_to_run.append(10)

            if neo4j_steps_enabled and neo4j_steps_to_run:
                logger.info("Starting Neo4j data processing")
                neo4j_processors = run_neo4j_processing(
                    config, create_only_new, neo4j_steps_to_run
                )
                processors.update(neo4j_processors)
                logger.info("Completed Neo4j data processing")
            else:
                logger.info(
                    "Skipping Neo4j processing (all Neo4j steps disabled in config or not in selected steps)"
                )

        # Generate and save summary statistics
        logger.info("Generating summary statistics")
        generate_and_save_summary(processors, args.skip_neo4j)
        logger.info("Data processing and analysis completed successfully")

    except Exception as e:
        logger.error(f"Error in data processing: {e}", exc_info=True)
        print(f"Error: {e}")
        print("See logs/data_processing.log for details")
