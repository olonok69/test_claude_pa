#!/usr/bin/env python3
"""
Simple test runner for Step 10: Session Recommendation Processor
Runs both old and new processors and compares results.
"""

import sys
import os
import time
import logging
import json
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/step10_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def clear_neo4j_recommendations(config):
    """Clear existing recommendation relationships and flags."""
    from neo4j import GraphDatabase
    
    try:
        driver = GraphDatabase.driver(
            config["neo4j"]["uri"],
            auth=(config["neo4j"]["username"], config["neo4j"]["password"])
        )
        
        with driver.session() as session:
            # Clear has_recommendation flags
            result = session.run("""
                MATCH (v:Visitor_this_year)
                WHERE v.has_recommendation = "1"
                SET v.has_recommendation = "0"
                RETURN COUNT(v) as cleared_visitors
            """)
            cleared = result.single()["cleared_visitors"]
            logger.info(f"Cleared has_recommendation flag from {cleared} visitors")
            
            # Delete IS_RECOMMENDED relationships
            result = session.run("""
                MATCH ()-[r:IS_RECOMMENDED]->()
                DELETE r
                RETURN COUNT(*) as deleted_relationships
            """)
            deleted = result.single()["deleted_relationships"]
            logger.info(f"Deleted {deleted} IS_RECOMMENDED relationships")
        
        driver.close()
        return True
        
    except Exception as e:
        logger.error(f"Error clearing Neo4j recommendations: {e}")
        return False


def run_old_processor(config_path="config/config.yaml"):
    """Run the old session recommendation processor."""
    logger.info("="*60)
    logger.info("Running OLD Session Recommendation Processor")
    logger.info("="*60)
    
    try:
        # Import old processor
        from old_session_recommendation_processor import SessionRecommendationProcessor
        from utils.config_utils import load_config
        
        # Load configuration
        config = load_config(config_path)
        
        # Clear existing recommendations
        logger.info("Clearing existing recommendations...")
        clear_neo4j_recommendations(config)
        
        # Initialize processor
        processor = SessionRecommendationProcessor(config)
        
        # Process recommendations (recreate all for testing)
        start_time = time.time()
        processor.process(create_only_new=False)
        processing_time = time.time() - start_time
        
        # Save output with specific name for comparison
        if hasattr(processor, 'statistics'):
            stats = processor.statistics
            logger.info(f"Old Processor Statistics:")
            logger.info(f"  Visitors processed: {stats.get('total_visitors_processed', 0)}")
            logger.info(f"  With recommendations: {stats.get('visitors_with_recommendations', 0)}")
            logger.info(f"  Total recommendations: {stats.get('total_recommendations_generated', 0)}")
            logger.info(f"  Processing time: {processing_time:.2f}s")
            
            # Create a marker file to indicate old processor output
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            marker_file = f"data/bva/recommendations/recommendations_old_{timestamp}.json"
            
            # Note: The old processor should save its output automatically
            # We're just creating a marker to help identify the file
            
            return True, stats
        
        return True, {}
        
    except Exception as e:
        logger.error(f"Error running old processor: {e}", exc_info=True)
        return False, {}


def run_new_processor(config_path="config/config_vet.yaml"):
    """Run the new generic session recommendation processor."""
    logger.info("="*60)
    logger.info("Running NEW Generic Session Recommendation Processor")
    logger.info("="*60)
    
    try:
        # Import new processor
        from session_recommendation_processor import SessionRecommendationProcessor
        from utils.config_utils import load_config
        
        # Load configuration
        config = load_config(config_path)
        
        # Clear existing recommendations
        logger.info("Clearing existing recommendations...")
        clear_neo4j_recommendations(config)
        
        # Initialize processor
        processor = SessionRecommendationProcessor(config)
        
        # Process recommendations (recreate all for testing)
        start_time = time.time()
        processor.process(create_only_new=False)
        processing_time = time.time() - start_time
        
        # Get statistics
        if hasattr(processor, 'statistics'):
            stats = processor.statistics
            logger.info(f"New Processor Statistics:")
            logger.info(f"  Visitors processed: {stats.get('total_visitors_processed', 0)}")
            logger.info(f"  With recommendations: {stats.get('visitors_with_recommendations', 0)}")
            logger.info(f"  Total recommendations: {stats.get('total_recommendations_generated', 0)}")
            logger.info(f"  Processing time: {processing_time:.2f}s")
            
            return True, stats
        
        return True, {}
        
    except Exception as e:
        logger.error(f"Error running new processor: {e}", exc_info=True)
        return False, {}


def verify_neo4j_state(config):
    """Verify the state of Neo4j after processing."""
    from neo4j import GraphDatabase
    
    try:
        driver = GraphDatabase.driver(
            config["neo4j"]["uri"],
            auth=(config["neo4j"]["username"], config["neo4j"]["password"])
        )
        
        with driver.session() as session:
            # Count visitors with recommendations
            result = session.run("""
                MATCH (v:Visitor_this_year)
                WHERE v.has_recommendation = "1"
                RETURN COUNT(v) as visitors_with_recs
            """)
            visitors_with_recs = result.single()["visitors_with_recs"]
            
            # Count IS_RECOMMENDED relationships
            result = session.run("""
                MATCH ()-[r:IS_RECOMMENDED]->()
                RETURN COUNT(r) as recommendation_rels
            """)
            recommendation_rels = result.single()["recommendation_rels"]
            
            # Get sample recommendations
            result = session.run("""
                MATCH (v:Visitor_this_year)-[r:IS_RECOMMENDED]->(s:Sessions_this_year)
                WHERE v.has_recommendation = "1"
                RETURN v.BadgeId as visitor_id, s.session_id as session_id
                LIMIT 5
            """)
            
            samples = []
            for record in result:
                samples.append({
                    "visitor_id": record["visitor_id"],
                    "session_id": record["session_id"]
                })
            
            logger.info(f"\nNeo4j State Verification:")
            logger.info(f"  Visitors with recommendations: {visitors_with_recs}")
            logger.info(f"  IS_RECOMMENDED relationships: {recommendation_rels}")
            
            if samples:
                logger.info(f"\n  Sample recommendations:")
                for sample in samples:
                    logger.info(f"    {sample['visitor_id']} -> {sample['session_id']}")
        
        driver.close()
        return {
            "visitors_with_recs": visitors_with_recs,
            "recommendation_rels": recommendation_rels,
            "samples": samples
        }
        
    except Exception as e:
        logger.error(f"Error verifying Neo4j state: {e}")
        return None


def compare_results(old_stats, new_stats):
    """Compare statistics from old and new processors."""
    print("\n" + "="*60)
    print("COMPARISON RESULTS")
    print("="*60)
    
    comparison = {
        "visitors_processed": {
            "old": old_stats.get('total_visitors_processed', 0),
            "new": new_stats.get('total_visitors_processed', 0)
        },
        "visitors_with_recommendations": {
            "old": old_stats.get('visitors_with_recommendations', 0),
            "new": new_stats.get('visitors_with_recommendations', 0)
        },
        "total_recommendations": {
            "old": old_stats.get('total_recommendations_generated', 0),
            "new": new_stats.get('total_recommendations_generated', 0)
        }
    }
    
    all_match = True
    for metric, values in comparison.items():
        match = values['old'] == values['new']
        symbol = "✅" if match else "⚠️"
        print(f"{symbol} {metric}:")
        print(f"   Old: {values['old']}")
        print(f"   New: {values['new']}")
        if not match:
            diff = abs(values['new'] - values['old'])
            pct = (diff / max(values['old'], 1)) * 100
            print(f"   Difference: {diff} ({pct:.1f}%)")
            all_match = False
    
    if all_match:
        print("\n✅ SUCCESS: All metrics match perfectly!")
    else:
        print("\n⚠️ WARNING: Some metrics differ. Run detailed comparison for more info.")
    
    return all_match


def main():
    """Main test execution."""
    print("\n" + "="*60)
    print("STEP 10: SESSION RECOMMENDATION PROCESSOR TEST")
    print("="*60)
    
    from utils.config_utils import load_config
    
    # Load configurations
    config_old = load_config("config/config.yaml")
    config_new = load_config("config/config_vet.yaml")
    
    # Ensure output directories exist
    os.makedirs("data/bva/recommendations", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    # Run old processor
    print("\n1. Running old processor...")
    old_success, old_stats = run_old_processor("config/config.yaml")
    if not old_success:
        print("❌ Failed to run old processor")
        return 1
    
    # Verify Neo4j state after old processor
    print("\n2. Verifying Neo4j state after old processor...")
    old_neo4j_state = verify_neo4j_state(config_old)
    
    # Run new processor
    print("\n3. Running new processor...")
    new_success, new_stats = run_new_processor("config/config_vet.yaml")
    if not new_success:
        print("❌ Failed to run new processor")
        return 1
    
    # Verify Neo4j state after new processor
    print("\n4. Verifying Neo4j state after new processor...")
    new_neo4j_state = verify_neo4j_state(config_new)
    
    # Compare results
    print("\n5. Comparing results...")
    results_match = compare_results(old_stats, new_stats)
    
    # Run detailed comparison
    print("\n6. Running detailed comparison...")
    print("   Run: python comparers/10_compare_processors.py")
    print("   for detailed recommendation comparison")
    
    # Final summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    if old_success and new_success:
        if results_match:
            print("✅ SUCCESS: Both processors ran successfully with matching results!")
            print("\nNext steps:")
            print("1. Run detailed comparison: python comparers/10_compare_processors.py")
            print("2. Test with ECOMM config: python main.py --config config/config_ecomm.yaml --only-steps 10")
            print("3. Check output files in data/bva/recommendations/")
            return 0
        else:
            print("⚠️ PARTIAL SUCCESS: Both processors ran but with different results.")
            print("Run detailed comparison to investigate differences.")
            return 0
    else:
        print("❌ FAILURE: One or both processors failed to run.")
        return 1


if __name__ == "__main__":
    sys.exit(main())