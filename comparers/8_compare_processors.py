#!/usr/bin/env python3
"""
Compare Neo4j Visitor Relationship Processors

This script compares the output of old_neo4j_visitor_relationship_processor.py 
and neo4j_visitor_relationship_processor.py to ensure they produce identical results.
"""

import os
import sys
import tempfile
from pathlib import Path

# Add current directory to path
sys.path.insert(0, os.getcwd())

try:
    from old_neo4j_visitor_relationship_processor import Neo4jVisitorRelationshipProcessor as OldNeo4jVisitorRelationshipProcessor
    from neo4j_visitor_relationship_processor import Neo4jVisitorRelationshipProcessor as NewNeo4jVisitorRelationshipProcessor
    from utils.config_utils import load_config
    from utils.logging_utils import setup_logging
    from neo4j import GraphDatabase
    from dotenv import load_dotenv
    import inspect
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("\nMake sure you have:")
    print("1. old_neo4j_visitor_relationship_processor.py")
    print("2. neo4j_visitor_relationship_processor.py")
    print("3. config/config_vet.yaml")
    print("4. python-dotenv package installed")
    sys.exit(1)


def clear_neo4j_visitor_relationships(config):
    """Clear existing visitor relationships from Neo4j"""
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
        sessions_past_year = node_labels.get("session_past_year", "Sessions_past_year")
        
        same_visitor_rel = relationships.get("same_visitor", "Same_Visitor")
        attended_session_rel = relationships.get("attended_session", "attended_session")
        
        with driver.session() as session:
            # Clear Same_Visitor relationships
            clear_same_visitor_bva = f"""
            MATCH (v1:{visitor_this_year})-[r:{same_visitor_rel} {{type: 'bva'}}]->(v2:{visitor_last_year_bva})
            WHERE v1.show = $show_name AND v2.show = $show_name
            DELETE r
            """
            result_bva = session.run(clear_same_visitor_bva, show_name=show_name)
            bva_same_deleted = result_bva.consume().counters.relationships_deleted
            
            clear_same_visitor_lva = f"""
            MATCH (v1:{visitor_this_year})-[r:{same_visitor_rel} {{type: 'lva'}}]->(v2:{visitor_last_year_lva})
            WHERE v1.show = $show_name AND v2.show = $show_name
            DELETE r
            """
            result_lva = session.run(clear_same_visitor_lva, show_name=show_name)
            lva_same_deleted = result_lva.consume().counters.relationships_deleted
            
            # Clear attended_session relationships
            clear_attended_bva = f"""
            MATCH (v:{visitor_last_year_bva})-[r:{attended_session_rel}]->(s:{sessions_past_year})
            WHERE v.show = $show_name AND s.show = $show_name
            DELETE r
            """
            result_attended_bva = session.run(clear_attended_bva, show_name=show_name)
            bva_attended_deleted = result_attended_bva.consume().counters.relationships_deleted
            
            clear_attended_lva = f"""
            MATCH (v:{visitor_last_year_lva})-[r:{attended_session_rel}]->(s:{sessions_past_year})
            WHERE v.show = $show_name AND s.show = $show_name
            DELETE r
            """
            result_attended_lva = session.run(clear_attended_lva, show_name=show_name)
            lva_attended_deleted = result_attended_lva.consume().counters.relationships_deleted
        
        driver.close()
        
        total_deleted = bva_same_deleted + lva_same_deleted + bva_attended_deleted + lva_attended_deleted
        print(f"🧹 Cleared {total_deleted} visitor relationships from Neo4j")
        print(f"   - Same_Visitor BVA: {bva_same_deleted}")
        print(f"   - Same_Visitor LVA: {lva_same_deleted}")
        print(f"   - attended_session BVA: {bva_attended_deleted}")
        print(f"   - attended_session LVA: {lva_attended_deleted}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error clearing Neo4j relationships: {str(e)}")
        return False


def get_neo4j_relationship_counts(config):
    """Get current relationship counts in Neo4j"""
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
        sessions_past_year = node_labels.get("session_past_year", "Sessions_past_year")
        
        same_visitor_rel = relationships.get("same_visitor", "Same_Visitor")
        attended_session_rel = relationships.get("attended_session", "attended_session")
        
        with driver.session() as session:
            # Count Same_Visitor BVA relationships
            count_same_bva = session.run(
                f"""
                MATCH (v1:{visitor_this_year})-[r:{same_visitor_rel} {{type: 'bva'}}]->(v2:{visitor_last_year_bva})
                WHERE v1.show = $show_name AND v2.show = $show_name
                RETURN COUNT(r) AS count
                """,
                show_name=show_name
            ).single()["count"]
            
            # Count Same_Visitor LVA relationships
            count_same_lva = session.run(
                f"""
                MATCH (v1:{visitor_this_year})-[r:{same_visitor_rel} {{type: 'lva'}}]->(v2:{visitor_last_year_lva})
                WHERE v1.show = $show_name AND v2.show = $show_name
                RETURN COUNT(r) AS count
                """,
                show_name=show_name
            ).single()["count"]
            
            # Count attended_session BVA relationships
            count_attended_bva = session.run(
                f"""
                MATCH (v:{visitor_last_year_bva})-[r:{attended_session_rel}]->(s:{sessions_past_year})
                WHERE v.show = $show_name AND s.show = $show_name
                RETURN COUNT(r) AS count
                """,
                show_name=show_name
            ).single()["count"]
            
            # Count attended_session LVA relationships
            count_attended_lva = session.run(
                f"""
                MATCH (v:{visitor_last_year_lva})-[r:{attended_session_rel}]->(s:{sessions_past_year})
                WHERE v.show = $show_name AND s.show = $show_name
                RETURN COUNT(r) AS count
                """,
                show_name=show_name
            ).single()["count"]
        
        driver.close()
        
        return {
            "same_visitor_bva": count_same_bva,
            "same_visitor_lva": count_same_lva,
            "attended_session_bva": count_attended_bva,
            "attended_session_lva": count_attended_lva
        }
        
    except Exception as e:
        print(f"❌ Error getting Neo4j relationship counts: {str(e)}")
        return None


def compare_statistics(old_processor, new_processor):
    """Compare the statistics from both processors."""
    print("\n📊 Comparing Statistics...")
    
    comparisons = []
    
    # Check if both processors have statistics
    if not hasattr(old_processor, "statistics") or not hasattr(new_processor, "statistics"):
        print("❌ One or both processors don't have statistics attribute")
        return False
    
    old_stats = old_processor.statistics
    new_stats = new_processor.statistics
    
    # Compare relationship statistics
    relationship_types = ["same_visitor_bva", "same_visitor_lva", "attended_session_bva", "attended_session_lva"]
    stat_types = ["relationships_created", "relationships_skipped", "relationships_failed"]
    
    for stat_type in stat_types:
        print(f"\n  {stat_type}:")
        for rel_type in relationship_types:
            old_value = old_stats.get(stat_type, {}).get(rel_type, 0)
            new_value = new_stats.get(stat_type, {}).get(rel_type, 0)
            
            print(f"    - {rel_type}: Old={old_value}, New={new_value}")
            
            if old_value == new_value:
                print(f"      ✅ Match")
                comparisons.append(True)
            else:
                print(f"      ❌ Mismatch")
                comparisons.append(False)
    
    return all(comparisons)


def compare_neo4j_state(old_config, new_config):
    """Compare the Neo4j database state after both processors."""
    print("\n🔍 Comparing Neo4j State...")
    
    # Get counts from both configurations (should be the same, but let's be thorough)
    old_counts = get_neo4j_relationship_counts(old_config)
    new_counts = get_neo4j_relationship_counts(new_config)
    
    if old_counts is None or new_counts is None:
        print("❌ Failed to get relationship counts")
        return False
    
    comparisons = []
    
    for relationship_type in ["same_visitor_bva", "same_visitor_lva", "attended_session_bva", "attended_session_lva"]:
        old_count = old_counts.get(relationship_type, 0)
        new_count = new_counts.get(relationship_type, 0)
        
        print(f"  - {relationship_type}: Old={old_count}, New={new_count}")
        
        if old_count == new_count:
            print(f"    ✅ Match")
            comparisons.append(True)
        else:
            print(f"    ❌ Mismatch")
            comparisons.append(False)
    
    return all(comparisons)


def run_comparison(config_path="config/config_vet.yaml"):
    """Run the full comparison between old and new processors."""
    print(f"🔄 Neo4j Visitor Relationship Processor Comparison")
    print(f"📁 Using config: {config_path}")
    
    # Load config
    try:
        config = load_config(config_path)
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        return False
    
    # Setup logging
    setup_logging(log_file="data_processing.log")
    
    print(f"🧹 Clearing existing visitor relationships...")
    if not clear_neo4j_visitor_relationships(config):
        return False
    
    print(f"\n🔄 Step 1: Running OLD processor...")
    
    try:
        old_processor = OldNeo4jVisitorRelationshipProcessor(config)
        old_processor.process(create_only_new=False)
        print(f"✅ OLD processor completed successfully")
    except Exception as e:
        print(f"❌ OLD processor failed: {e}")
        return False
    
    # Get counts after old processor
    old_counts = get_neo4j_relationship_counts(config)
    
    print(f"\n🧹 Clearing relationships again...")
    if not clear_neo4j_visitor_relationships(config):
        return False
    
    print(f"\n🔄 Step 2: Running NEW processor...")
    
    try:
        new_processor = NewNeo4jVisitorRelationshipProcessor(config)
        new_processor.process(create_only_new=False)
        print(f"✅ NEW processor completed successfully")
    except Exception as e:
        print(f"❌ NEW processor failed: {e}")
        return False
    
    # Get counts after new processor
    new_counts = get_neo4j_relationship_counts(config)
    
    print(f"\n📊 Results Summary:")
    print(f"OLD processor Neo4j counts: {old_counts}")
    print(f"NEW processor Neo4j counts: {new_counts}")
    
    # Compare statistics
    stats_match = compare_statistics(old_processor, new_processor)
    
    # Compare Neo4j state
    neo4j_match = old_counts == new_counts if old_counts and new_counts else False
    
    print(f"\n🎯 Final Results:")
    print(f"  - Statistics match: {'✅ Yes' if stats_match else '❌ No'}")
    print(f"  - Neo4j state match: {'✅ Yes' if neo4j_match else '❌ No'}")
    
    if stats_match and neo4j_match:
        print(f"\n🎉 SUCCESS: Both processors produce identical results!")
        return True
    else:
        print(f"\n❌ FAILURE: Processors produce different results!")
        return False


if __name__ == "__main__":
    success = run_comparison()
    sys.exit(0 if success else 1)