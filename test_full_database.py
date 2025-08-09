#!/usr/bin/env python3
"""
Full Database Test for Session Recommendation Processors

This script tests ALL visitors in the database to ensure the old and new
processors produce identical results.

Usage:
    python test_full_database.py [--sample N] [--batch-size B]
"""

import os
import sys
import json
import argparse
import pandas as pd
from pathlib import Path
import logging
from datetime import datetime
import time
from typing import Dict, List, Tuple
import csv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from old_session_recommendation_processor import SessionRecommendationProcessor as OldProcessor
    from session_recommendation_processor import SessionRecommendationProcessor as NewProcessor
    from utils.config_utils import load_config
    from utils.logging_utils import setup_logging
    from neo4j import GraphDatabase
except ImportError as e:
    print(f"Error importing required modules: {e}")
    sys.exit(1)


class FullDatabaseTester:
    """Test ALL visitors in the database with both processors."""
    
    def __init__(self):
        self.logger = setup_logging(log_file="logs/full_database_test.log")
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create output directory
        self.output_dir = Path("full_database_test_output")
        self.output_dir.mkdir(exist_ok=True)
        
        # Statistics
        self.stats = {
            "total_visitors": 0,
            "processed": 0,
            "matches": 0,
            "mismatches": 0,
            "errors": 0,
            "returning_visitors": 0,
            "new_visitors": 0,
            "returning_matches": 0,
            "new_matches": 0,
            "processing_time": 0
        }
        
        self.mismatched_visitors = []
        self.error_visitors = []
        
        self.logger.info("FullDatabaseTester initialized")
    
    def get_all_visitors(self, config: dict, sample_size: int = None) -> List[Dict]:
        """Get all visitors from the database."""
        neo4j_config = config.get("neo4j", {})
        uri = neo4j_config.get("uri")
        username = neo4j_config.get("username")
        password = neo4j_config.get("password")
        
        visitors = []
        
        try:
            with GraphDatabase.driver(uri, auth=(username, password)) as driver:
                with driver.session() as session:
                    # Get all visitors or a sample
                    if sample_size:
                        query = """
                        MATCH (v:Visitor_this_year)
                        WITH v, rand() as r
                        ORDER BY r
                        LIMIT $limit
                        RETURN v.BadgeId as badge_id,
                               v.assist_year_before as assist_year_before,
                               v.job_role as job_role,
                               v.what_type_does_your_practice_specialise_in as practice_type
                        """
                        result = session.run(query, limit=sample_size)
                    else:
                        query = """
                        MATCH (v:Visitor_this_year)
                        RETURN v.BadgeId as badge_id,
                               v.assist_year_before as assist_year_before,
                               v.job_role as job_role,
                               v.what_type_does_your_practice_specialise_in as practice_type
                        ORDER BY v.BadgeId
                        """
                        result = session.run(query)
                    
                    for record in result:
                        visitors.append(dict(record))
                    
                    self.logger.info(f"Retrieved {len(visitors)} visitors from database")
                    
        except Exception as e:
            self.logger.error(f"Error getting visitors: {e}")
            
        return visitors
    
    def process_visitor_batch(self, visitors_batch: List[Dict], old_processor, new_processor, config: dict) -> Tuple[int, int]:
        """Process a batch of visitors and compare results."""
        matches = 0
        mismatches = 0
        
        neo4j_config = config.get("neo4j", {})
        uri = neo4j_config.get("uri")
        username = neo4j_config.get("username")
        password = neo4j_config.get("password")
        
        for visitor in visitors_batch:
            badge_id = visitor["badge_id"]
            is_returning = visitor.get("assist_year_before") == "1"
            
            try:
                # Get recommendations from old processor
                recommendation_config = old_processor.config.get("recommendation", {})
                min_score = recommendation_config.get("min_similarity_score", 0.3)
                max_recs = recommendation_config.get("max_recommendations", 10)
                num_similar = recommendation_config.get("similar_visitors_count", 3)
                
                old_recs = old_processor.recommend_sessions_optimized(
                    badge_id=badge_id,
                    min_score=min_score,
                    max_recommendations=max_recs,
                    num_similar_visitors=num_similar,
                )
                
                # Get visitor info for filtering
                visitor_obj = {}
                with GraphDatabase.driver(uri, auth=(username, password)) as driver:
                    with driver.session() as session:
                        visitor_query = """
                        MATCH (v:Visitor_this_year {BadgeId: $visitor_id})
                        RETURN v
                        """
                        result = session.run(visitor_query, visitor_id=badge_id)
                        record = result.single()
                        if record:
                            visitor_obj = dict(record["v"])
                
                # Apply filtering for old processor
                old_filtered, old_rules = old_processor.filter_sessions(visitor_obj, old_recs) if visitor_obj else (old_recs, [])
                
                # Get recommendations from new processor
                new_recs = []
                new_filtered = []
                with GraphDatabase.driver(uri, auth=(username, password)) as driver:
                    with driver.session() as neo4j_session:
                        visitor_info = neo4j_session.execute_read(
                            new_processor.get_visitor_info, visitor_id=badge_id
                        )
                        
                        if visitor_info:
                            new_recs = new_processor.get_recommendations_for_visitor(
                                session=neo4j_session,
                                badge_id=badge_id,
                                num_similar_visitors=new_processor.similar_visitors_count,
                                min_score=new_processor.min_similarity_score,
                                max_recommendations=new_processor.max_recommendations,
                            )
                            
                            new_filtered, new_rules = new_processor.filter_sessions(
                                visitor_info["visitor"], new_recs
                            )
                
                # Compare results
                old_ids = set(r["session_id"] for r in old_filtered)
                new_ids = set(r["session_id"] for r in new_filtered)
                
                if old_ids == new_ids and len(old_filtered) == len(new_filtered):
                    matches += 1
                    if is_returning:
                        self.stats["returning_matches"] += 1
                    else:
                        self.stats["new_matches"] += 1
                else:
                    mismatches += 1
                    self.mismatched_visitors.append({
                        "badge_id": badge_id,
                        "is_returning": is_returning,
                        "old_count": len(old_filtered),
                        "new_count": len(new_filtered),
                        "only_in_old": list(old_ids - new_ids),
                        "only_in_new": list(new_ids - old_ids)
                    })
                    
            except Exception as e:
                self.logger.error(f"Error processing {badge_id}: {e}")
                self.error_visitors.append({
                    "badge_id": badge_id,
                    "error": str(e)
                })
                self.stats["errors"] += 1
        
        return matches, mismatches
    
    def run_full_test(self, config_path: str, sample_size: int = None, batch_size: int = 100):
        """Run full database test."""
        print("\n" + "="*80)
        print("FULL DATABASE TEST FOR SESSION RECOMMENDATIONS")
        print("="*80)
        
        start_time = time.time()
        
        # Load configuration
        config = load_config(config_path)
        self.logger.info(f"Loaded configuration from {config_path}")
        
        # Get all visitors
        print("\n📊 Retrieving visitors from database...")
        visitors = self.get_all_visitors(config, sample_size)
        self.stats["total_visitors"] = len(visitors)
        
        # Count returning vs new
        self.stats["returning_visitors"] = sum(1 for v in visitors if v.get("assist_year_before") == "1")
        self.stats["new_visitors"] = self.stats["total_visitors"] - self.stats["returning_visitors"]
        
        print(f"Found {self.stats['total_visitors']} visitors:")
        print(f"  - Returning (assist_year_before='1'): {self.stats['returning_visitors']}")
        print(f"  - New (assist_year_before='0' or NULL): {self.stats['new_visitors']}")
        
        # Create processors
        print("\n🔧 Initializing processors...")
        old_processor = OldProcessor(config)
        new_processor = NewProcessor(config)
        print("✅ Both processors initialized")
        
        # Process in batches
        print(f"\n🚀 Processing visitors in batches of {batch_size}...")
        
        for i in range(0, len(visitors), batch_size):
            batch = visitors[i:i+batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(visitors) + batch_size - 1) // batch_size
            
            print(f"  Processing batch {batch_num}/{total_batches} ({len(batch)} visitors)...", end="")
            
            matches, mismatches = self.process_visitor_batch(batch, old_processor, new_processor, config)
            
            self.stats["matches"] += matches
            self.stats["mismatches"] += mismatches
            self.stats["processed"] += len(batch)
            
            print(f" ✓ ({matches} matches, {mismatches} mismatches)")
            
            # Show progress
            if self.stats["processed"] % 500 == 0:
                elapsed = time.time() - start_time
                rate = self.stats["processed"] / elapsed
                remaining = (self.stats["total_visitors"] - self.stats["processed"]) / rate
                print(f"  Progress: {self.stats['processed']}/{self.stats['total_visitors']} "
                      f"({self.stats['processed']*100/self.stats['total_visitors']:.1f}%) "
                      f"- Est. remaining: {remaining:.1f}s")
        
        self.stats["processing_time"] = time.time() - start_time
        
        # Save detailed results
        self.save_results()
        
        # Print summary
        self.print_summary()
        
        return self.stats["mismatches"] == 0
    
    def save_results(self):
        """Save detailed test results."""
        # Save statistics
        stats_file = self.output_dir / f"test_stats_{self.timestamp}.json"
        with open(stats_file, "w") as f:
            json.dump(self.stats, f, indent=2)
        
        # Save mismatched visitors
        if self.mismatched_visitors:
            mismatch_file = self.output_dir / f"mismatched_visitors_{self.timestamp}.csv"
            df = pd.DataFrame(self.mismatched_visitors)
            df.to_csv(mismatch_file, index=False)
            self.logger.info(f"Saved {len(self.mismatched_visitors)} mismatched visitors to {mismatch_file}")
        
        # Save error visitors
        if self.error_visitors:
            error_file = self.output_dir / f"error_visitors_{self.timestamp}.csv"
            df = pd.DataFrame(self.error_visitors)
            df.to_csv(error_file, index=False)
            self.logger.info(f"Saved {len(self.error_visitors)} error visitors to {error_file}")
    
    def print_summary(self):
        """Print test summary."""
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        
        print(f"\n📊 Overall Statistics:")
        print(f"  Total visitors: {self.stats['total_visitors']}")
        print(f"  Processed: {self.stats['processed']}")
        print(f"  Matches: {self.stats['matches']} ({self.stats['matches']*100/max(1,self.stats['processed']):.1f}%)")
        print(f"  Mismatches: {self.stats['mismatches']} ({self.stats['mismatches']*100/max(1,self.stats['processed']):.1f}%)")
        print(f"  Errors: {self.stats['errors']}")
        
        print(f"\n📈 By Visitor Type:")
        print(f"  Returning visitors: {self.stats['returning_visitors']}")
        print(f"    - Matches: {self.stats['returning_matches']} ({self.stats['returning_matches']*100/max(1,self.stats['returning_visitors']):.1f}%)")
        print(f"  New visitors: {self.stats['new_visitors']}")
        print(f"    - Matches: {self.stats['new_matches']} ({self.stats['new_matches']*100/max(1,self.stats['new_visitors']):.1f}%)")
        
        print(f"\n⏱️ Performance:")
        print(f"  Total processing time: {self.stats['processing_time']:.2f}s")
        print(f"  Average per visitor: {self.stats['processing_time']/max(1,self.stats['processed'])*1000:.2f}ms")
        
        if self.stats['mismatches'] == 0:
            print("\n✅ SUCCESS: All visitors have identical recommendations!")
        else:
            print(f"\n⚠️ WARNING: {self.stats['mismatches']} visitors have different recommendations")
            print(f"Check mismatched_visitors_{self.timestamp}.csv for details")


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Test session recommendation processors with full database"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config/config_vet.yaml",
        help="Path to configuration file"
    )
    parser.add_argument(
        "--sample",
        type=int,
        help="Test with a random sample of N visitors instead of all"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Process visitors in batches of this size"
    )
    
    args = parser.parse_args()
    
    tester = FullDatabaseTester()
    
    try:
        success = tester.run_full_test(
            config_path=args.config,
            sample_size=args.sample,
            batch_size=args.batch_size
        )
        
        if success:
            print("\n🎉 ALL TESTS PASSED!")
            sys.exit(0)
        else:
            print("\n⚠️ Some tests failed. Check output files for details.")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()