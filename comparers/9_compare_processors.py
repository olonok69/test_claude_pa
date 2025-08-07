#!/usr/bin/env python3
"""
Comparison script for Session Embedding Processors

This script runs both old and new session embedding processors and compares their results.
"""

import os
import sys
import json
from neo4j import GraphDatabase
from dotenv import load_dotenv
import pandas as pd
from pathlib import Path
import tempfile
import shutil

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
    sys.exit(1)


def get_neo4j_embeddings(config, show_name=None):
    """
    Get all session embeddings from Neo4j.
    
    Args:
        config: Configuration dictionary
        show_name: Show name to filter by (optional)
    
    Returns:
        dict: Dictionary of session_id to embedding
    """
    load_dotenv(config["env_file"])
    uri = os.getenv("NEO4J_URI")
    username = os.getenv("NEO4J_USERNAME")
    password = os.getenv("NEO4J_PASSWORD")
    
    driver = GraphDatabase.driver(uri, auth=(username, password))
    
    with driver.session() as session:
        # Build query based on whether we filter by show
        if show_name:
            query = """
            MATCH (s)
            WHERE (s:Sessions_this_year OR s:Sessions_past_year) 
            AND s.show = $show_name
            AND s.embedding IS NOT NULL
            RETURN s.session_id as session_id, s.embedding as embedding
            ORDER BY s.session_id
            """
            result = session.run(query, show_name=show_name)
        else:
            query = """
            MATCH (s)
            WHERE (s:Sessions_this_year OR s:Sessions_past_year)
            AND s.embedding IS NOT NULL
            RETURN s.session_id as session_id, s.embedding as embedding
            ORDER BY s.session_id
            """
            result = session.run(query)
        
        embeddings = {}
        for record in result:
            embeddings[record["session_id"]] = json.loads(record["embedding"])
    
    driver.close()
    return embeddings


def clear_embeddings(config, show_name=None):
    """
    Clear all embeddings from Neo4j sessions.
    
    Args:
        config: Configuration dictionary
        show_name: Show name to filter by (optional)
    """
    load_dotenv(config["env_file"])
    uri = os.getenv("NEO4J_URI")
    username = os.getenv("NEO4J_USERNAME")
    password = os.getenv("NEO4J_PASSWORD")
    
    driver = GraphDatabase.driver(uri, auth=(username, password))
    
    with driver.session() as session:
        if show_name:
            query = """
            MATCH (s)
            WHERE (s:Sessions_this_year OR s:Sessions_past_year)
            AND s.show = $show_name
            REMOVE s.embedding
            """
            session.run(query, show_name=show_name)
        else:
            query = """
            MATCH (s)
            WHERE (s:Sessions_this_year OR s:Sessions_past_year)
            REMOVE s.embedding
            """
            session.run(query)
    
    driver.close()


def compare_embeddings(embeddings1, embeddings2):
    """
    Compare two sets of embeddings.
    
    Args:
        embeddings1: First set of embeddings
        embeddings2: Second set of embeddings
    
    Returns:
        bool: True if embeddings match
    """
    # Check if same number of embeddings
    if len(embeddings1) != len(embeddings2):
        print(f"  Different number of embeddings: {len(embeddings1)} vs {len(embeddings2)}")
        return False
    
    print(f"  Comparing {len(embeddings1)} embeddings...")
    
    # Check if same session IDs
    ids1 = set(embeddings1.keys())
    ids2 = set(embeddings2.keys())
    
    if ids1 != ids2:
        print(f"  ❌ Different session IDs")
        missing_in_2 = ids1 - ids2
        missing_in_1 = ids2 - ids1
        if missing_in_2:
            print(f"     Missing in new: {list(missing_in_2)[:5]}...")
        if missing_in_1:
            print(f"     Missing in old: {list(missing_in_1)[:5]}...")
        return False
    
    # Compare embeddings for each session
    differences = 0
    for session_id in ids1:
        emb1 = embeddings1[session_id]
        emb2 = embeddings2[session_id]
        
        # Compare lengths
        if len(emb1) != len(emb2):
            differences += 1
            if differences <= 3:
                print(f"  ❌ Different embedding length for {session_id}: {len(emb1)} vs {len(emb2)}")
            continue
        
        # Compare values (with small tolerance for floating point)
        for i, (v1, v2) in enumerate(zip(emb1, emb2)):
            if abs(v1 - v2) > 1e-6:
                differences += 1
                if differences <= 3:
                    print(f"  ❌ Different embedding values for {session_id} at index {i}")
                break
    
    if differences > 0:
        print(f"  ❌ Found {differences} sessions with different embeddings")
        return False
    
    print(f"  ✅ All embeddings match perfectly!")
    return True


def compare_statistics(old_processor, new_processor, show_name):
    """
    Compare statistics from both processors.
    Note: Old processor processes ALL shows, new processor only processes configured show.
    
    Args:
        old_processor: Old processor instance
        new_processor: New processor instance
        show_name: The show being processed by new processor
    
    Returns:
        bool: True if statistics match for the relevant show
    """
    old_stats = old_processor.statistics
    new_stats = new_processor.statistics
    
    print("\n📊 Comparing Statistics:")
    print(f"Note: Old processor includes ALL shows, new processor only '{show_name}'")
    
    match = True
    
    # We expect totals to be different if there are multiple shows
    print(f"\n  Old processor (ALL shows):")
    print(f"    - Total sessions: {old_stats['total_sessions_processed']}")
    print(f"    - Sessions with embeddings: {old_stats['sessions_with_embeddings']}")
    print(f"    - Sessions this year: {old_stats['sessions_by_type']['sessions_this_year']}")
    print(f"    - Sessions past year: {old_stats['sessions_by_type']['sessions_past_year']}")
    
    print(f"\n  New processor ('{show_name}' only):")
    print(f"    - Total sessions: {new_stats['total_sessions_processed']}")
    print(f"    - Sessions with embeddings: {new_stats['sessions_with_embeddings']}")
    print(f"    - Sessions this year: {new_stats['sessions_by_type']['sessions_this_year']}")
    print(f"    - Sessions past year: {new_stats['sessions_by_type']['sessions_past_year']}")
    
    # The key check is that the new processor processed all its sessions successfully
    if new_stats['total_sessions_processed'] == new_stats['sessions_with_embeddings']:
        print(f"\n✅ New processor successfully created embeddings for all {show_name} sessions")
        return True
    else:
        print(f"\n❌ New processor failed to create embeddings for some sessions")
        return False


def main():
    """Main comparison execution."""
    config_file = "config/config_vet.yaml"
    
    print("🔬 Session Embedding Processor Comparison")
    print("=" * 50)
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
    
    print(f"\n🎯 Testing with show: {show_name}")
    
    # Clear existing embeddings
    print("\n🧹 Clearing existing embeddings...")
    clear_embeddings(config, show_name)
    
    # Run OLD processor
    print("\n🔄 Running OLD processor...")
    try:
        old_processor = OldSessionEmbeddingProcessor(config)
        old_processor.process(create_only_new=False)  # Old processor returns None
        print("✅ OLD processor completed successfully")
    except Exception as e:
        print(f"❌ OLD processor error: {e}")
        return False
    
    # Get embeddings from old processor
    print("\n📥 Getting embeddings from OLD processor...")
    old_embeddings_all = get_neo4j_embeddings(config)
    old_embeddings = get_neo4j_embeddings(config, show_name)  # Get only BVA embeddings for fair comparison
    print(f"   Found {len(old_embeddings_all)} total embeddings")
    print(f"   Found {len(old_embeddings)} {show_name} embeddings")
    
    # Clear embeddings again
    print("\n🧹 Clearing embeddings again...")
    clear_embeddings(config, show_name)
    
    # Run NEW processor
    print("\n🔄 Running NEW processor...")
    try:
        new_processor = NewSessionEmbeddingProcessor(config)
        new_result = new_processor.process(create_only_new=False)
        if new_result:
            print("✅ NEW processor completed successfully")
        else:
            print("❌ NEW processor failed")
            return False
    except Exception as e:
        print(f"❌ NEW processor error: {e}")
        return False
    
    # Get embeddings from new processor
    print("\n📥 Getting embeddings from NEW processor...")
    new_embeddings = get_neo4j_embeddings(config, show_name)
    print(f"   Found {len(new_embeddings)} embeddings")
    
    # Compare results
    print("\n🔍 Comparing Results...")
    print("-" * 30)
    
    # Compare embeddings - use BVA-specific embeddings from old processor
    print(f"\n📌 Comparing {show_name} embeddings only:")
    embeddings_match = compare_embeddings(old_embeddings, new_embeddings)
    if embeddings_match:
        print("✅ Embeddings match perfectly!")
    
    # Compare statistics - with understanding that they process different sets
    stats_match = compare_statistics(old_processor, new_processor, show_name)
    
    # Final result
    print("\n" + "=" * 50)
    if embeddings_match and len(old_embeddings) == len(new_embeddings):
        print(f"🎉 SUCCESS: Both processors produce identical results for {show_name} sessions!")
        print(f"  - Old processor: {len(old_embeddings_all)} total embeddings ({len(old_embeddings)} for {show_name})")
        print(f"  - New processor: {len(new_embeddings)} embeddings (correctly filtered to {show_name})")
        return True
    else:
        print("❌ FAILURE: Processors produce different results")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)