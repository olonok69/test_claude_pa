import logging
from registration_processor import RegistrationProcessor
from scan_processor import ScanProcessor
from session_processor import SessionProcessor
from neo4j_visitor_processor import Neo4jVisitorProcessor
from neo4j_session_processor import Neo4jSessionProcessor
from neo4j_job_stream_processor import Neo4jJobStreamProcessor
from neo4j_specialization_stream_processor import Neo4jSpecializationStreamProcessor
from neo4j_visitor_relationship_processor import Neo4jVisitorRelationshipProcessor
from session_embedding_processor import SessionEmbeddingProcessor
from session_recommendation_processor import SessionRecommendationProcessor


def run_registration_processing(config):
    """
    Run the registration data processing step.

    Args:
        config: Configuration dictionary

    Returns:
        RegistrationProcessor instance
    """
    reg_processor = RegistrationProcessor(config)
    reg_processor.process()
    return reg_processor


def run_scan_processing(config):
    """
    Run the scan data processing step.

    Args:
        config: Configuration dictionary

    Returns:
        ScanProcessor instance
    """
    scan_processor = ScanProcessor(config)
    scan_processor.process()
    return scan_processor


def run_session_processing(config):
    """
    Run the session data processing step.

    Args:
        config: Configuration dictionary

    Returns:
        SessionProcessor instance
    """
    session_processor = SessionProcessor(config)
    session_processor.process()
    return session_processor


def run_neo4j_processing(config, create_only_new=True, steps_to_run=None):
    """
    Run all Neo4j data processing steps.

    Args:
        config: Configuration dictionary
        create_only_new: If True, only create new nodes if they don't already exist
        steps_to_run: List of step numbers to run (if None, run all enabled steps)

    Returns:
        Dictionary of processor instances
    """
    logger = logging.getLogger(__name__)
    processors = {}

    # Check if specific steps are requested
    run_all = steps_to_run is None

    # Neo4j visitor processor (Step 4)
    if (run_all or 4 in steps_to_run) and config.get("pipeline_steps", {}).get(
        "neo4j_visitor_processing", True
    ):
        logger.info("Starting step 4: Neo4j visitor data processing")
        neo4j_visitor_processor = Neo4jVisitorProcessor(config)
        neo4j_visitor_processor.process(create_only_new=create_only_new)
        processors["neo4j_visitor_processor"] = neo4j_visitor_processor
        logger.info("Completed step 4: Neo4j visitor data processing")
    else:
        logger.info(
            "Skipping step 4: Neo4j visitor data processing (disabled in config or not in selected steps)"
        )

    # Neo4j session processor (Step 5)
    if (run_all or 5 in steps_to_run) and config.get("pipeline_steps", {}).get(
        "neo4j_session_processing", True
    ):
        logger.info("Starting step 5: Neo4j session data processing")
        neo4j_session_processor = Neo4jSessionProcessor(config)
        neo4j_session_processor.process(create_only_new=create_only_new)
        processors["neo4j_session_processor"] = neo4j_session_processor
        logger.info("Completed step 5: Neo4j session data processing")
    else:
        logger.info(
            "Skipping step 5: Neo4j session data processing (disabled in config or not in selected steps)"
        )

    # Neo4j job stream processor (Step 6)
    if (run_all or 6 in steps_to_run) and config.get("pipeline_steps", {}).get(
        "neo4j_job_stream_processing", True
    ):
        logger.info("Starting step 6: Neo4j job to stream relationship processing")
        neo4j_job_stream_processor = Neo4jJobStreamProcessor(config)
        neo4j_job_stream_processor.process(create_only_new=create_only_new)
        processors["neo4j_job_stream_processor"] = neo4j_job_stream_processor
        logger.info("Completed step 6: Neo4j job to stream relationship processing")
    else:
        logger.info(
            "Skipping step 6: Neo4j job to stream relationship processing (disabled in config or not in selected steps)"
        )

    # Neo4j specialization stream processor (Step 7)
    if (run_all or 7 in steps_to_run) and config.get("pipeline_steps", {}).get(
        "neo4j_specialization_stream_processing", True
    ):
        logger.info(
            "Starting step 7: Neo4j specialization to stream relationship processing"
        )
        neo4j_specialization_stream_processor = Neo4jSpecializationStreamProcessor(
            config
        )
        neo4j_specialization_stream_processor.process(create_only_new=create_only_new)
        processors["neo4j_specialization_stream_processor"] = (
            neo4j_specialization_stream_processor
        )
        logger.info(
            "Completed step 7: Neo4j specialization to stream relationship processing"
        )
    else:
        logger.info(
            "Skipping step 7: Neo4j specialization to stream relationship processing (disabled in config or not in selected steps)"
        )

    # Neo4j visitor relationship processor (Step 8)
    if (run_all or 8 in steps_to_run) and config.get("pipeline_steps", {}).get(
        "neo4j_visitor_relationship_processing", True
    ):
        logger.info("Starting step 8: Neo4j visitor relationship processing")
        neo4j_visitor_relationship_processor = Neo4jVisitorRelationshipProcessor(config)
        neo4j_visitor_relationship_processor.process(create_only_new=create_only_new)
        processors["neo4j_visitor_relationship_processor"] = (
            neo4j_visitor_relationship_processor
        )
        logger.info("Completed step 8: Neo4j visitor relationship processing")
    else:
        logger.info(
            "Skipping step 8: Neo4j visitor relationship processing (disabled in config or not in selected steps)"
        )

    # Session embedding processor (Step 9)
    if (run_all or 9 in steps_to_run) and config.get("pipeline_steps", {}).get(
        "session_embedding_processing", True
    ):
        logger.info("Starting step 9: Session embedding processing")
        session_embedding_processor = SessionEmbeddingProcessor(config)
        session_embedding_processor.process(create_only_new=create_only_new)
        processors["session_embedding_processor"] = session_embedding_processor
        logger.info("Completed step 9: Session embedding processing")
    else:
        logger.info(
            "Skipping step 9: Session embedding processing (disabled in config or not in selected steps)"
        )

    # Session recommendation processor (Step 10)
    if (run_all or 10 in steps_to_run) and config.get("pipeline_steps", {}).get(
        "session_recommendation_processing", True
    ):
        logger.info("Starting step 10: Session recommendation processing")
        session_recommendation_processor = SessionRecommendationProcessor(config)
        session_recommendation_processor.process(create_only_new=create_only_new)
        processors["session_recommendation_processor"] = (
            session_recommendation_processor
        )
        logger.info("Completed step 10: Session recommendation processing")
    else:
        logger.info(
            "Skipping step 10: Session recommendation processing (disabled in config or not in selected steps)"
        )

    return processors


def run_session_recommendation_processing(config, create_only_new=True):
    """
    Run session recommendation processing step.

    Args:
        config: Configuration dictionary
        create_only_new: If True, only create new recommendations if they don't already exist

    Returns:
        SessionRecommendationProcessor instance
    """
    logger = logging.getLogger(__name__)
    logger.info("Starting session recommendation processing")

    session_recommendation_processor = SessionRecommendationProcessor(config)
    session_recommendation_processor.process(create_only_new=create_only_new)

    logger.info("Completed session recommendation processing")
    return session_recommendation_processor
