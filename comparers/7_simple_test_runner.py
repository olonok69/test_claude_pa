#!/usr/bin/env python3
"""
Simple Test Runner for Neo4j Specialization Stream Processors

This script runs both Neo4j specialization stream processors and does a quick comparison of key outputs.
"""

import os
import sys
import pandas as pd
from pathlib import Path
import tempfile
import shutil
from neo4j import GraphDatabase
import inspect
from dotenv import load_dotenv

# Add current directory to path
sys.path.insert(0, os.getcwd())

try:
    from old_neo4j_specialization_stream_processor import Neo4jSpecializationStreamProcessor as OldNeo4jSpecializationStreamProcessor
    from neo4j_specialization_stream_processor import Neo4jSpecializationStreamProcessor as NewNeo4jSpecializationStreamProcessor
    from utils.config_utils import load_config
    from utils.logging_utils import setup_logging
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("\nMake sure you have:")
    print("1. old_neo4j_specialization_stream_processor.py")
    print("2. neo4j_specialization_stream_processor.py")
    print("3. config/config.yaml")
    print("4. config/config_vet.yaml")
    print("5. python-dotenv package installed")
    sys.exit(1)


def clear_neo4j_specialization_stream_relationships(config):
    """Clear existing specialization stream relationships from Neo4j"""
    try:
        load_dotenv(config["env_file"])
        uri = os.getenv("NEO4J_URI")
        username = os.getenv("NEO4J_USERNAME")
        password = os.getenv("NEO4J_PASSWORD")
        
        if not all([uri, username, password]):
            raise ValueError("Missing Neo4j credentials")
        
        driver = GraphDatabase.driver(uri, auth=(username, password))
        
        # Get configuration values
        neo4j_config = config.get("neo4j", {})
        show_name = neo4j_config.get("show_name", "unknown")
        node_labels = neo4j_config.get("node_labels", {})
        relationships = neo4j_config.get("relationships", {})
        
        # Get labels and relationship names
        visitor_this_year = node_labels.get("visitor_this_year", "Visitor_this_year")
        visitor_last_year_bva = node_labels.get("visitor_last_year_bva", "Visitor_last_year_bva")
        visitor_last_year_lva = node_labels.get("visitor_last_year_lva", "Visitor_last_year_lva")
        stream_label = node_labels.get("stream", "Stream")
        specialization_rel = relationships.get("specialization_stream", "specialization_to_stream")
        
        print(f"🧹 Clearing specialization stream relationships for show: {show_name}")
        
        with driver.session() as session:
            # Count existing relationships first
            if show_name and show_name != "unknown":
                count_query = f"""
                MATCH (v)-[r:{specialization_rel}]->(s:{stream_label})
                WHERE v.show = $show_name AND s.show = $show_name
                RETURN COUNT(r) AS count
                """
                result = session.run(count_query, show_name=show_name)
            else:
                count_query = f"""
                MATCH ()-[r:{specialization_rel}]->({stream_label})
                RETURN COUNT(r) AS count
                """
                result = session.run(count_query)
            
            initial_count = result.single()["count"]
            print(f"  - Found {initial_count} existing relationships")
            
            # Delete relationships
            if show_name and show_name != "unknown":
                delete_query = f"""
                MATCH (v)-[r:{specialization_rel}]->(s:{stream_label})
                WHERE v.show = $show_name AND s.show = $show_name
                DELETE r
                """
                session.run(delete_query, show_name=show_name)
            else:
                delete_query = f"""
                MATCH ()-[r:{specialization_rel}]->({stream_label})
                DELETE r
                """
                session.run(delete_query)
            
            # Verify deletion
            if show_name and show_name != "unknown":
                result = session.run(count_query, show_name=show_name)
            else:
                result = session.run(count_query)
                
            final_count = result.single()["count"]
            print(f"  - Deleted {initial_count - final_count} relationships, {final_count} remaining")
        
        driver.close()
        print("✅ Specialization stream relationships cleared")
        
    except Exception as e:
        print(f"❌ Error clearing specialization stream relationships: {e}")
        raise


def compare_neo4j_nodes(config):
    """Compare Neo4j nodes and relationships after processing"""
    try:
        load_dotenv(config["env_file"])
        uri = os.getenv("NEO4J_URI")
        username = os.getenv("NEO4J_USERNAME")
        password = os.getenv("NEO4J_PASSWORD")
        
        if not all([uri, username, password]):
            raise ValueError("Missing Neo4j credentials")
        
        driver = GraphDatabase.driver(uri, auth=(username, password))
        
        # Get configuration values
        neo4j_config = config.get("neo4j", {})
        show_name = neo4j_config.get("show_name", "unknown")
        node_labels = neo4j_config.get("node_labels", {})
        relationships = neo4j_config.get("relationships", {})
        
        # Get labels and relationship names
        visitor_this_year = node_labels.get("visitor_this_year", "Visitor_this_year")
        visitor_last_year_bva = node_labels.get("visitor_last_year_bva", "Visitor_last_year_bva")
        visitor_last_year_lva = node_labels.get("visitor_last_year_lva", "Visitor_last_year_lva")
        stream_label = node_labels.get("stream", "Stream")
        specialization_rel = relationships.get("specialization_stream", "specialization_to_stream")
        
        with driver.session() as session:
            # Count nodes by type
            node_counts = {}
            for label in [visitor_this_year, visitor_last_year_bva, visitor_last_year_lva, stream_label]:
                if show_name and show_name != "unknown":
                    result = session.run(f"MATCH (n:{label}) WHERE n.show = $show_name RETURN COUNT(n) AS count", 
                                       show_name=show_name)
                else:
                    result = session.run(f"MATCH (n:{label}) RETURN COUNT(n) AS count")
                node_counts[label] = result.single()["count"]
            
            # Count relationships
            relationship_counts = {}
            if show_name and show_name != "unknown":
                result = session.run(f"""
                    MATCH (v)-[r:{specialization_rel}]->(s:{stream_label})
                    WHERE v.show = $show_name AND s.show = $show_name
                    RETURN COUNT(r) AS count
                """, show_name=show_name)
            else:
                result = session.run(f"MATCH ()-[r:{specialization_rel}]->({stream_label}) RETURN COUNT(r) AS count")
            relationship_counts[specialization_rel] = result.single()["count"]
            
            # Get show distribution
            show_distribution = {}
            if show_name and show_name != "unknown":
                result = session.run(f"""
                    MATCH (v)-[r:{specialization_rel}]->(s:{stream_label})
                    WHERE v.show = $show_name AND s.show = $show_name
                    RETURN v.show as show, COUNT(r) as count
                """, show_name=show_name)
            else:
                result = session.run(f"""
                    MATCH (v)-[r:{specialization_rel}]->({stream_label})
                    RETURN COALESCE(v.show, 'no_show') as show, COUNT(r) as count
                """)
            
            for record in result:
                show_distribution[record["show"]] = record["count"]
            
            # Validation checks
            validation_passed = True
            
            # Check that we have the expected structure
            visitors_total = (node_counts.get(visitor_this_year, 0) + 
                            node_counts.get(visitor_last_year_bva, 0) + 
                            node_counts.get(visitor_last_year_lva, 0))
            streams_count = node_counts.get(stream_label, 0)
            relationships_count = relationship_counts.get(specialization_rel, 0)
            
            print(f"\n📊 Database Health Check:")
            print(f"  - Total visitor nodes: {visitors_total}")
            print(f"  - Stream nodes: {streams_count} {'✅' if streams_count > 0 else '❌ Missing'}")
            print(f"  - {specialization_rel} relationships: {relationships_count} {'✅' if relationships_count > 0 else '❌ Missing'}")
            
            # The processor should create relationships between visitors and streams
            if streams_count > 0 and relationships_count > 0:
                print("  ✅ Complete specialization-stream graph structure created")
                validation_passed = True
            else:
                print("  ❌ Graph structure incomplete")
                validation_passed = False
            
            # Return the structured data
            return {
                "node_counts": node_counts,
                "relationship_counts": relationship_counts,
                "show_distribution": show_distribution,
                "validation_passed": validation_passed
            }
            
    except Exception as e:
        print(f"❌ Error comparing Neo4j nodes: {e}")
        return None
    finally:
        if 'driver' in locals():
            driver.close()


def run_test():
    """Run the complete test."""
    print("🚀 Starting Neo4j Specialization Stream Processor Comparison Test")
    print("=" * 70)
    
    # Setup logging
    logger = setup_logging(log_file="logs/simple_test_7_fixed.log")
    
    try:
        # Load configurations
        print("📁 Loading configurations...")
        old_config = load_config("config/config.yaml")
        new_config = load_config("config/config_vet.yaml")
        
        # Clear existing specialization data
        clear_neo4j_specialization_stream_relationships(new_config)
        
        # Run old processor
        print("\n🔄 Running OLD Neo4j Specialization Stream Processor...")
        old_processor = OldNeo4jSpecializationStreamProcessor(old_config)
        old_stats = old_processor.process(create_only_new=False)
        print("✅ Old processor completed")
        
        # Capture state after old processor
        print("\n📊 Capturing Neo4j state after OLD processor...")
        old_db_state = compare_neo4j_nodes(old_config)
        
        # Clear data again before running new processor
        clear_neo4j_specialization_stream_relationships(new_config)
        
        # Run new processor
        print("\n🔄 Running NEW Neo4j Specialization Stream Processor...")
        new_processor = NewNeo4jSpecializationStreamProcessor(new_config)
        new_stats = new_processor.process(create_only_new=False)
        print("✅ New processor completed")
        
        # Capture state after new processor
        print("\n📊 Capturing Neo4j state after NEW processor...")
        new_db_state = compare_neo4j_nodes(new_config)
        
        # Compare results
        print("\n🔍 COMPARISON RESULTS")
        print("=" * 50)
        
        # Compare statistics
        print("📈 Processor Statistics:")
        if old_stats and new_stats:
            stats_to_compare = [
                "specializations_processed", "specializations_mapped", 
                "stream_matches_found", "visitor_nodes_processed"
            ]
            
            for stat in stats_to_compare:
                old_val = old_stats.get(stat, 0)
                new_val = new_stats.get(stat, 0)
                
                # Handle nested dictionaries (like visitor_nodes_processed)
                if isinstance(old_val, dict) and isinstance(new_val, dict):
                    print(f"  {stat}:")
                    for key in set(old_val.keys()) | set(new_val.keys()):
                        old_subval = old_val.get(key, 0)
                        new_subval = new_val.get(key, 0)
                        status = "✅" if old_subval == new_subval else "❌"
                        print(f"    {key}: {status} Old: {old_subval}, New: {new_subval}")
                else:
                    status = "✅" if old_val == new_val else "❌"
                    print(f"  {stat}: {status} Old: {old_val}, New: {new_val}")
            
            # Compare relationship creation stats
            old_created = old_stats.get("relationships_created", {}).get("total", 0)
            new_created = new_stats.get("relationships_created", {}).get("total", 0)
            status = "✅" if old_created == new_created else "❌"
            print(f"  relationships_created: {status} Old: {old_created}, New: {new_created}")
        
        # Compare Neo4j states
        print("\n🗄️ Neo4j Database States:")
        if old_db_state and new_db_state:
            old_rels = old_db_state.get("relationship_counts", {})
            new_rels = new_db_state.get("relationship_counts", {})
            
            for rel_type in set(old_rels.keys()) | set(new_rels.keys()):
                old_count = old_rels.get(rel_type, 0)
                new_count = new_rels.get(rel_type, 0)
                status = "✅" if old_count == new_count else "❌"
                print(f"  {rel_type}: {status} Old: {old_count}, New: {new_count}")
            
            # Check validation status
            old_valid = old_db_state.get("validation_passed", False)
            new_valid = new_db_state.get("validation_passed", False)
            val_status = "✅" if old_valid and new_valid else "❌"
            print(f"  Database validation: {val_status} Old: {old_valid}, New: {new_valid}")
        
        # Overall assessment
        print("\n🎯 OVERALL ASSESSMENT")
        print("=" * 30)
        
        # Check if results match
        results_match = True
        if old_stats and new_stats and old_db_state and new_db_state:
            # Check key statistics match
            key_stats_match = (
                old_stats.get("specializations_processed", 0) == new_stats.get("specializations_processed", 0) and
                old_stats.get("relationships_created", {}).get("total", 0) == new_stats.get("relationships_created", {}).get("total", 0)
            )
            
            # Check Neo4j states match
            specialization_rel = new_config.get("neo4j", {}).get("relationships", {}).get("specialization_stream", "specialization_to_stream")
            neo4j_states_match = (
                old_db_state.get("relationship_counts", {}).get(specialization_rel, 0) == 
                new_db_state.get("relationship_counts", {}).get(specialization_rel, 0)
            )
            
            results_match = key_stats_match and neo4j_states_match
        
        if results_match:
            print("✅ SUCCESS: Both processors produce identical results!")
            print("✅ The new generic processor works correctly.")
            print("✅ Safe to replace the old processor.")
        else:
            print("❌ FAILURE: Processors produce different results!")
            print("❌ Investigation needed before replacing the old processor.")
        
        # Summary
        print(f"\n📋 Summary:")
        if new_db_state:
            specialization_rel = new_config.get("neo4j", {}).get("relationships", {}).get("specialization_stream", "specialization_to_stream")
            print(f"  - Total relationships created: {new_db_state.get('relationship_counts', {}).get(specialization_rel, 0)}")
            print(f"  - Show distribution: {new_db_state.get('show_distribution', {})}")
        
        if new_stats:
            print(f"  - Specializations processed: {new_stats.get('specializations_processed', 0)}")
            print(f"  - Stream matches found: {new_stats.get('stream_matches_found', 0)}")
        
        return results_match
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        logger.error(f"Test failed: {e}", exc_info=True)
        return False


def main():
    """Main function"""
    print("Neo4j Specialization Stream Processor Simple Test")
    print("=" * 55)
    
    success = run_test()
    
    if success:
        print("\n🎉 Test completed successfully!")
        print("➡️  Next: Run the full comparison with 'python comparers/7_compare_processors.py'")
        sys.exit(0)
    else:
        print("\n💥 Test failed!")
        print("➡️  Check the logs and fix issues before proceeding")
        sys.exit(1)


if __name__ == "__main__":
    main()