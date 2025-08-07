#!/usr/bin/env python3
"""
Simple Test Runner for Session Embedding Processors

This script runs both session embedding processors and does a quick comparison of key outputs.
"""

import os
import sys
import json
from neo4j import GraphDatabase
from dotenv import load_dotenv

# Add current directory to path
sys.path.insert(0, os.getcwd())

try:
    from old_session_embedding_processor import SessionEmbeddingProcessor as OldSessionEmbeddingProcessor
    from session_embedding_processor import SessionEmbeddingProcessor as NewSessionEmbeddingProcessor
    from utils.config_utils import load_config
    from utils.logging_utils import setup_logging
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("\nMake sure you have:")
    print("1. old_session_embedding_processor.py")
    print("2. session_embedding_processor.py")
    print("3. config/config_vet.yaml")
    print("4. sentence-transformers package installed")
    sys.exit(1)


def get_embedding_count(config, show_name=None):
    """Get count of sessions with embeddings from Neo4j."""
    try:
        load_dotenv(config["env_file"])
        uri = os.getenv("NEO4J_URI")
        username = os.getenv("NEO4J_USERNAME")
        password = os.getenv("NEO4J_PASSWORD")
        
        if not all([uri, username, password]):
            print("❌ Missing Neo4j credentials")
            return None
        
        driver = GraphDatabase.driver(uri, auth=(username, password))
        
        with driver.session() as session:
            if show_name:
                query = """
                MATCH (s)
                WHERE (s:Sessions_this_year OR s:Sessions_past_year)
                AND s.show = $show_name
                AND s.embedding IS NOT NULL
                RETURN count(s) as count
                """
                result = session.run(query, show_name=show_name)
            else:
                # Count ALL sessions with embeddings
                query = """
                MATCH (s)
                WHERE (s:Sessions_this_year OR s:Sessions_past_year)
                AND s.embedding IS NOT NULL
                RETURN count(s) as count
                """
                result = session.run(query)
            
            count = result.single()["count"]
        
        driver.close()
        return count
    except Exception as e:
        print(f"❌ Error counting embeddings: {e}")
        return None


def clear_embeddings(config, show_name=None):
    """Clear all embeddings from Neo4j sessions."""
    try:
        load_dotenv(config["env_file"])
        uri = os.getenv("NEO4J_URI")
        username = os.getenv("NEO4J_USERNAME")
        password = os.getenv("NEO4J_PASSWORD")
        
        if not all([uri, username, password]):
            raise ValueError("Missing Neo4j credentials")
        
        driver = GraphDatabase.driver(uri, auth=(username, password))
        
        with driver.session() as session:
            if show_name:
                query = """
                MATCH (s)
                WHERE (s:Sessions_this_year OR s:Sessions_past_year)
                AND s.show = $show_name
                REMOVE s.embedding
                RETURN count(s) as count
                """
                result = session.run(query, show_name=show_name)
            else:
                query = """
                MATCH (s)
                WHERE (s:Sessions_this_year OR s:Sessions_past_year)
                REMOVE s.embedding
                RETURN count(s) as count
                """
                result = session.run(query)
            
            count = result.single()["count"]
            print(f"  Cleared embeddings from {count} sessions")
        
        driver.close()
        return True
    except Exception as e:
        print(f"❌ Error clearing embeddings: {e}")
        return False


def compare_statistics(old_processor, new_processor):
    """Compare basic statistics from both processors."""
    print("\n📊 Quick Statistics Comparison:")
    
    old_stats = old_processor.statistics
    new_stats = new_processor.statistics
    
    match = True
    
    # Total sessions
    old_total = old_stats["total_sessions_processed"]
    new_total = new_stats["total_sessions_processed"]
    if old_total == new_total:
        print(f"  ✅ Total sessions: {old_total}")
    else:
        print(f"  ❌ Total sessions: OLD={old_total}, NEW={new_total}")
        match = False
    
    # Sessions with embeddings
    old_emb = old_stats["sessions_with_embeddings"]
    new_emb = new_stats["sessions_with_embeddings"]
    if old_emb == new_emb:
        print(f"  ✅ Sessions with embeddings: {old_emb}")
    else:
        print(f"  ❌ Sessions with embeddings: OLD={old_emb}, NEW={new_emb}")
        match = False
    
    # Sessions with stream descriptions
    old_stream = old_stats["sessions_with_stream_descriptions"]
    new_stream = new_stats["sessions_with_stream_descriptions"]
    if old_stream == new_stream:
        print(f"  ✅ Sessions with stream descriptions: {old_stream}")
    else:
        print(f"  ❌ Sessions with stream descriptions: OLD={old_stream}, NEW={new_stream}")
        match = False
    
    return match


def main():
    """Main test execution."""
    config_file = "config/config_vet.yaml"
    
    print("🧪 Simple Session Embedding Processor Test")
    print(f"📁 Config: {config_file}")
    
    # Load configuration
    try:
        config = load_config(config_file)
        show_name = config.get("neo4j", {}).get("show_name", "bva")
    except Exception as e:
        print(f"❌ Failed to load config: {e}")
        return False
    
    # Setup logging
    setup_logging(log_file="data_processing.log")
    
    print(f"🎯 Testing with show: {show_name}")
    
    # Clear existing embeddings - clear ALL to ensure clean state
    print("\n🧹 Clearing ALL existing embeddings...")
    if not clear_embeddings(config):  # Clear all, not just show-specific
        return False
    
    # Test OLD processor
    print("\n🔄 Testing OLD processor...")
    try:
        old_processor = OldSessionEmbeddingProcessor(config)
        old_processor.process(create_only_new=False)  # Old processor returns None, not boolean
        print("✅ OLD processor completed")
    except Exception as e:
        print(f"❌ OLD processor error: {e}")
        return False
    
    # Get count after old processor (all sessions)
    old_count_total = get_embedding_count(config)  # Total count
    old_count_bva = get_embedding_count(config, show_name)  # BVA only count
    print(f"📊 OLD processor created {old_count_total} total embeddings")
    print(f"   - {old_count_bva} for '{show_name}' sessions")
    if old_count_total > old_count_bva:
        print(f"   - {old_count_total - old_count_bva} for other shows")
    
    # Clear embeddings again - clear ALL embeddings
    print("\n🧹 Clearing ALL embeddings again...")
    if not clear_embeddings(config):  # Clear all, not just show-specific
        return False
    
    # Test NEW processor
    print("\n🔄 Testing NEW processor...")
    try:
        new_processor = NewSessionEmbeddingProcessor(config)
        new_result = new_processor.process(create_only_new=False)
        if new_result:
            print("✅ NEW processor completed")
        else:
            # This should fail if there was an issue
            print("❌ NEW processor returned False")
            return False
    except Exception as e:
        print(f"❌ NEW processor error: {e}")
        return False
    
    # Get count after new processor
    new_count = get_embedding_count(config, show_name)
    print(f"📊 NEW processor created {new_count} embeddings")
    
    # Quick comparison
    # Note: The old processor processes ALL sessions, while the new processor 
    # only processes sessions for the configured show (bva)
    
    print(f"\n📝 Note: The generic processor correctly filters by show.")
    print(f"  - Old processor: Processes ALL sessions (no show filtering)")
    print(f"  - New processor: Only processes '{show_name}' sessions")
    
    # Compare BVA sessions specifically
    bva_counts_match = old_count_bva == new_count
    
    print(f"\n🎯 Test Results:")
    print(f"  - Old processor total embeddings: {old_count_total}")
    print(f"  - Old processor '{show_name}' embeddings: {old_count_bva}")
    print(f"  - New processor '{show_name}' embeddings: {new_count}")
    print(f"  - BVA embeddings match: {'✅' if bva_counts_match else '❌'}")
    
    # The real test is whether both processors created the same number of embeddings
    # for BVA sessions specifically
    if bva_counts_match and new_count > 0:
        print(f"\n🎉 SUCCESS: New processor correctly processed all '{show_name}' sessions!")
        print(f"  - Both processors created {new_count} embeddings for '{show_name}' sessions")
        print(f"  - The generic processor correctly filters by show")
        return True
    else:
        print(f"\n❌ FAILURE: Processors created different numbers of embeddings for '{show_name}' sessions!")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)