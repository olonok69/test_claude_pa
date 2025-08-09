#!/usr/bin/env python3
"""
Focused Test Runner for Session Recommendation Processor (BVA Only)

This script tests specific visitors with both old and new processors
to verify they produce exactly the same recommendations.

Tests 3 returning visitors (assist_year_before='1') and 3 new visitors (assist_year_before='0')

Usage:
    python 10_simple_test_runner.py
"""

import os
import sys
import json
import argparse
from pathlib import Path
import logging
from datetime import datetime
from typing import Dict, List, Set, Tuple
import time

# Add parent directory to path to import processors
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from old_session_recommendation_processor import SessionRecommendationProcessor as OldProcessor
    from session_recommendation_processor import SessionRecommendationProcessor as NewProcessor
    from utils.config_utils import load_config
    from utils.logging_utils import setup_logging
    from neo4j import GraphDatabase
except ImportError as e:
    print(f"Error importing required modules: {e}")
    print("Make sure you have:")
    print("1. old_session_recommendation_processor.py")
    print("2. session_recommendation_processor.py")
    print("3. utils/config_utils.py and utils/logging_utils.py")
    sys.exit(1)


class FocusedTestRunner:
    """Test runner that compares specific visitors between old and new processors."""
    
    def __init__(self):
        self.logger = setup_logging(log_file="logs/focused_recommendation_test.log")
        self.test_results = {}
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create test output directory
        self.test_output_dir = Path("focused_test_output")
        self.test_output_dir.mkdir(exist_ok=True)
        
        # HARDCODED TEST VISITORS FROM DATABASE
        # These are actual visitors from the database with known characteristics
        self.returning_visitors = [
            "GIY5RHT",  # Other (please specify), Small Animal;Mixed
            "6ZNCI83",  # Vet Nurse, Mixed
            "3QRQTLJ"   # Vet/Vet Surgeon, Mixed
        ]
        
        self.new_visitors = [
            "4ZTU822",  # Student, Small Animal
            "DE6TRR7",  # Student, Small Animal
            "MRVEZSE"   # Student, NA
        ]
        
        self.logger.info("FocusedTestRunner initialized with hardcoded test visitors")
        self.logger.info(f"Returning visitors (assist_year_before='1'): {self.returning_visitors}")
        self.logger.info(f"New visitors (assist_year_before='0'): {self.new_visitors}")
    
    def get_visitor_details(self, badge_id: str, config: dict) -> dict:
        """Get visitor details from database."""
        neo4j_config = config.get("neo4j", {})
        uri = neo4j_config.get("uri")
        username = neo4j_config.get("username")
        password = neo4j_config.get("password")
        
        visitor_details = {}
        
        try:
            with GraphDatabase.driver(uri, auth=(username, password)) as driver:
                with driver.session() as session:
                    query = """
                    MATCH (v:Visitor_this_year {BadgeId: $badge_id})
                    RETURN v.BadgeId as badge_id,
                           v.job_role as job_role,
                           v.what_type_does_your_practice_specialise_in as practice_type,
                           v.assist_year_before as assist_year_before,
                           v.organisation_type as org_type,
                           v.Country as country
                    """
                    result = session.run(query, badge_id=badge_id)
                    record = result.single()
                    if record:
                        visitor_details = dict(record)
                        
        except Exception as e:
            self.logger.error(f"Error getting visitor details for {badge_id}: {e}")
            
        return visitor_details
    
    def get_recommendations_for_visitor(self, processor, badge_id: str, config: dict) -> Dict:
        """Get recommendations for a specific visitor using the given processor."""
        
        # Check if this is the old processor (uses different method names)
        is_old_processor = hasattr(processor, 'recommend_sessions_optimized')
        
        if is_old_processor:
            # Old processor uses recommend_sessions_optimized which returns raw recommendations
            try:
                # Old processor gets these from config, not as instance attributes
                recommendation_config = processor.config.get("recommendation", {})
                min_score = recommendation_config.get("min_similarity_score", 0.3)
                max_recs = recommendation_config.get("max_recommendations", 10)
                num_similar = recommendation_config.get("similar_visitors_count", 3)
                
                # The old processor's method returns the recommendations directly
                raw_recommendations = processor.recommend_sessions_optimized(
                    badge_id=badge_id,
                    min_score=min_score,
                    max_recommendations=max_recs,
                    num_similar_visitors=num_similar,
                )
                
                # Get visitor info for filtering
                neo4j_config = config.get("neo4j", {})
                uri = neo4j_config.get("uri")
                username = neo4j_config.get("username")
                password = neo4j_config.get("password")
                
                visitor = {}
                with GraphDatabase.driver(uri, auth=(username, password)) as driver:
                    with driver.session() as session:
                        # Get visitor info using direct query
                        visitor_query = """
                        MATCH (v:Visitor_this_year {BadgeId: $visitor_id})
                        RETURN v
                        """
                        result = session.run(visitor_query, visitor_id=badge_id)
                        record = result.single()
                        if record:
                            visitor = dict(record["v"])
                
                # Apply filtering using the processor's filter_sessions method
                filtered_recommendations = []
                rules_applied = []
                
                if visitor and raw_recommendations:
                    filtered_recommendations, rules_applied = processor.filter_sessions(
                        visitor, raw_recommendations
                    )
                elif raw_recommendations:
                    # If no visitor found but have recommendations, use raw
                    filtered_recommendations = raw_recommendations
                    
                return {
                    "visitor": visitor if visitor else {},
                    "raw_recommendations": raw_recommendations if raw_recommendations else [],
                    "filtered_recommendations": filtered_recommendations if filtered_recommendations else [],
                    "rules_applied": rules_applied if rules_applied else []
                }
                
            except Exception as e:
                self.logger.error(f"Error getting recommendations from old processor for {badge_id}: {e}", exc_info=True)
                return {
                    "visitor": {},
                    "raw_recommendations": [],
                    "filtered_recommendations": [],
                    "rules_applied": []
                }
        else:
            # New processor - use the method structure with Neo4j session
            neo4j_config = config.get("neo4j", {})
            uri = neo4j_config.get("uri")
            username = neo4j_config.get("username")
            password = neo4j_config.get("password")
            
            recommendations = []
            visitor_info = None
            visitor = {}
            filtered_recommendations = []
            rules_applied = []
            
            try:
                with GraphDatabase.driver(uri, auth=(username, password)) as driver:
                    with driver.session() as neo4j_session:
                        # Get visitor info
                        visitor_info = neo4j_session.execute_read(
                            processor.get_visitor_info, visitor_id=badge_id
                        )
                        
                        if visitor_info:
                            visitor = visitor_info.get("visitor", {})
                            # Get recommendations - note this is the method that exists in new processor
                            recommendations = processor.get_recommendations_for_visitor(
                                session=neo4j_session,
                                badge_id=badge_id,
                                num_similar_visitors=processor.similar_visitors_count,
                                min_score=processor.min_similarity_score,
                                max_recommendations=processor.max_recommendations,
                            )
                            
                            # Apply filtering
                            filtered_recommendations, rules_applied = processor.filter_sessions(
                                visitor, recommendations
                            )
                        else:
                            self.logger.warning(f"Visitor {badge_id} not found in new processor")
                            
            except Exception as e:
                self.logger.error(f"Error getting recommendations from new processor for {badge_id}: {e}", exc_info=True)
            
            return {
                "visitor": visitor if visitor else {},
                "raw_recommendations": recommendations if recommendations else [],
                "filtered_recommendations": filtered_recommendations if filtered_recommendations else [],
                "rules_applied": rules_applied if rules_applied else []
            }
    
    def compare_recommendations(self, old_recs: Dict, new_recs: Dict, visitor_id: str) -> Dict:
        """Compare recommendations from old and new processors."""
        comparison = {
            "visitor_id": visitor_id,
            "matches": True,
            "differences": []
        }
        
        # Compare raw recommendations
        old_raw = old_recs.get("raw_recommendations", [])
        new_raw = new_recs.get("raw_recommendations", [])
        
        old_raw_ids = [r["session_id"] for r in old_raw]
        new_raw_ids = [r["session_id"] for r in new_raw]
        
        if set(old_raw_ids) != set(new_raw_ids):
            comparison["matches"] = False
            only_old = set(old_raw_ids) - set(new_raw_ids)
            only_new = set(new_raw_ids) - set(old_raw_ids)
            if only_old:
                comparison["differences"].append(f"Raw sessions only in old: {only_old}")
            if only_new:
                comparison["differences"].append(f"Raw sessions only in new: {only_new}")
        
        # Compare filtered recommendations
        old_filtered = old_recs.get("filtered_recommendations", [])
        new_filtered = new_recs.get("filtered_recommendations", [])
        
        old_filtered_ids = [r["session_id"] for r in old_filtered]
        new_filtered_ids = [r["session_id"] for r in new_filtered]
        
        if old_filtered_ids != new_filtered_ids:
            comparison["matches"] = False
            comparison["differences"].append(f"Filtered order differs")
            
            if set(old_filtered_ids) != set(new_filtered_ids):
                only_old = set(old_filtered_ids) - set(new_filtered_ids)
                only_new = set(new_filtered_ids) - set(old_filtered_ids)
                if only_old:
                    comparison["differences"].append(f"Filtered sessions only in old: {only_old}")
                if only_new:
                    comparison["differences"].append(f"Filtered sessions only in new: {only_new}")
        
        # Compare similarity scores for matching sessions
        for old_rec in old_filtered:
            for new_rec in new_filtered:
                if old_rec["session_id"] == new_rec["session_id"]:
                    old_sim = old_rec.get("similarity", 0)
                    new_sim = new_rec.get("similarity", 0)
                    if abs(old_sim - new_sim) > 0.001:  # Allow small floating point differences
                        comparison["matches"] = False
                        comparison["differences"].append(
                            f"Similarity differs for {old_rec['session_id']}: old={old_sim:.4f}, new={new_sim:.4f}"
                        )
        
        # Compare rules applied
        old_rules = set(old_recs.get("rules_applied", []))
        new_rules = set(new_recs.get("rules_applied", []))
        
        if old_rules != new_rules:
            comparison["matches"] = False
            comparison["differences"].append(f"Rules differ: old={old_rules}, new={new_rules}")
        
        # Store detailed results
        comparison["old_count"] = len(old_filtered)
        comparison["new_count"] = len(new_filtered)
        comparison["old_sessions"] = old_filtered_ids[:5]  # First 5 for display
        comparison["new_sessions"] = new_filtered_ids[:5]  # First 5 for display
        
        return comparison
    
    def test_with_config(self, config_path: str, test_name: str) -> bool:
        """Test both processors with specific hardcoded visitors and compare results."""
        self.logger.info(f"\n{'='*80}")
        self.logger.info(f"Testing {test_name} Configuration with hardcoded visitors")
        self.logger.info(f"{'='*80}")
        
        try:
            # Load configuration
            config = load_config(config_path)
            self.logger.info(f"✅ Loaded configuration from {config_path}")
            
            # Use hardcoded test visitors
            all_test_visitors = self.returning_visitors + self.new_visitors
            
            self.logger.info(f"\nTesting with {len(self.returning_visitors)} returning and {len(self.new_visitors)} new visitors")
            
            # Create processor instances
            self.logger.info("\nCreating processor instances...")
            old_processor = OldProcessor(config)
            new_processor = NewProcessor(config)
            self.logger.info("✅ Both processors created successfully")
            
            # Test each visitor
            all_match = True
            detailed_results = []
            
            for visitor_type, visitor_list in [("RETURNING", self.returning_visitors), ("NEW", self.new_visitors)]:
                self.logger.info(f"\n{'-'*60}")
                self.logger.info(f"Testing {visitor_type} Visitors (assist_year_before='{'1' if visitor_type == 'RETURNING' else '0'}')")
                self.logger.info(f"{'-'*60}")
                
                for badge_id in visitor_list:
                    # Get visitor details from database
                    visitor_details = self.get_visitor_details(badge_id, config)
                    
                    self.logger.info(f"\nProcessing visitor {badge_id}...")
                    self.logger.info(f"  Details: {visitor_details}")
                    
                    # Get recommendations from old processor
                    old_start = time.time()
                    old_recs = self.get_recommendations_for_visitor(old_processor, badge_id, config)
                    old_time = time.time() - old_start
                    
                    # Get recommendations from new processor
                    new_start = time.time()
                    new_recs = self.get_recommendations_for_visitor(new_processor, badge_id, config)
                    new_time = time.time() - new_start
                    
                    # Compare results
                    comparison = self.compare_recommendations(old_recs, new_recs, badge_id)
                    
                    # Display results
                    # Get visitor data - prefer from the successful processor
                    visitor = old_recs.get("visitor") or new_recs.get("visitor") or {}
                    job_role = visitor.get("job_role", "N/A") if visitor else "N/A"
                    practice = visitor.get("what_type_does_your_practice_specialise_in", "N/A") if visitor else "N/A"
                    
                    self.logger.info(f"  Visitor: {badge_id}")
                    self.logger.info(f"  Type: {visitor_type}")
                    self.logger.info(f"  Assist Year Before: {'1' if visitor_type == 'RETURNING' else '0'}")
                    self.logger.info(f"  Job Role: {job_role}")
                    self.logger.info(f"  Practice: {practice}")
                    self.logger.info(f"  Old Processor: {comparison['old_count']} recommendations in {old_time:.2f}s")
                    self.logger.info(f"  New Processor: {comparison['new_count']} recommendations in {new_time:.2f}s")
                    
                    if comparison["matches"]:
                        self.logger.info(f"  ✅ MATCH - Identical recommendations!")
                    else:
                        self.logger.warning(f"  ❌ MISMATCH - Differences found:")
                        for diff in comparison["differences"]:
                            self.logger.warning(f"     - {diff}")
                        all_match = False
                    
                    # Show first few recommendations
                    if comparison["old_sessions"] or comparison["new_sessions"]:
                        self.logger.info(f"  First sessions (old): {comparison['old_sessions']}")
                        self.logger.info(f"  First sessions (new): {comparison['new_sessions']}")
                    
                    # Store detailed results
                    detailed_results.append({
                        "visitor_id": badge_id,
                        "visitor_type": visitor_type,
                        "assist_year_before": "1" if visitor_type == "RETURNING" else "0",
                        "job_role": job_role,
                        "practice": practice,
                        "comparison": comparison,
                        "old_time": old_time,
                        "new_time": new_time
                    })
            
            # Save detailed results
            self.test_results[test_name] = {
                "success": all_match,
                "timestamp": self.timestamp,
                "num_visitors_tested": len(all_test_visitors),
                "detailed_results": detailed_results
            }
            
            # Print summary
            self.logger.info(f"\n{'='*60}")
            self.logger.info(f"Summary for {test_name}")
            self.logger.info(f"{'='*60}")
            
            matching = sum(1 for r in detailed_results if r["comparison"]["matches"])
            mismatching = len(detailed_results) - matching
            
            self.logger.info(f"Total visitors tested: {len(detailed_results)}")
            self.logger.info(f"  Returning visitors (assist_year_before='1'): {len(self.returning_visitors)}")
            self.logger.info(f"  New visitors (assist_year_before='0'): {len(self.new_visitors)}")
            self.logger.info(f"Matching results: {matching}")
            self.logger.info(f"Mismatching results: {mismatching}")
            
            if all_match:
                self.logger.info(f"\n✅ SUCCESS: All {len(detailed_results)} visitors have identical recommendations!")
            else:
                self.logger.warning(f"\n⚠️ WARNING: {mismatching} visitors have different recommendations")
                # Show which visitors had mismatches
                mismatched_visitors = [r["visitor_id"] for r in detailed_results if not r["comparison"]["matches"]]
                self.logger.warning(f"Mismatched visitors: {mismatched_visitors}")
            
            return all_match
            
        except Exception as e:
            self.logger.error(f"Error testing {test_name}: {e}", exc_info=True)
            self.test_results[test_name] = {
                "success": False,
                "error": str(e)
            }
            return False
    
    def save_detailed_report(self):
        """Save detailed comparison report."""
        report_file = self.test_output_dir / f"focused_comparison_{self.timestamp}.json"
        
        with open(report_file, 'w') as f:
            json.dump(self.test_results, f, indent=2, default=str)
        
        self.logger.info(f"\nDetailed report saved to {report_file}")
        
        # Also save a summary CSV for easy review
        summary_file = self.test_output_dir / f"focused_summary_{self.timestamp}.csv"
        
        with open(summary_file, 'w') as f:
            f.write("Config,Visitor ID,Type,Job Role,Match,Old Count,New Count,Differences\n")
            
            for config_name, results in self.test_results.items():
                if "detailed_results" in results:
                    for visitor_result in results["detailed_results"]:
                        visitor_id = visitor_result["visitor_id"]
                        visitor_type = visitor_result["visitor_type"]
                        job_role = visitor_result.get("job_role", "N/A")
                        comparison = visitor_result["comparison"]
                        match = "Yes" if comparison["matches"] else "No"
                        old_count = comparison["old_count"]
                        new_count = comparison["new_count"]
                        differences = "; ".join(comparison.get("differences", []))
                        
                        f.write(f"{config_name},{visitor_id},{visitor_type},{job_role},{match},{old_count},{new_count},{differences}\n")
        
        self.logger.info(f"Summary CSV saved to {summary_file}")
        
        return report_file, summary_file


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Compare old and new recommendation processors with hardcoded test visitors"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config/config_vet.yaml",
        help="Path to configuration file (default: config/config_vet.yaml)"
    )
    
    args = parser.parse_args()
    
    print("\n" + "="*80)
    print("FOCUSED RECOMMENDATION PROCESSOR COMPARISON")
    print("="*80)
    print("\nThis tool tests specific hardcoded visitors from the database:")
    print("- 3 returning visitors (assist_year_before='1'): GIY5RHT, 6ZNCI83, 3QRQTLJ")
    print("- 3 new visitors (assist_year_before='0'): 4ZTU822, DE6TRR7, MRVEZSE")
    print("\nThese visitors verify both use cases for recommendations.\n")
    
    runner = FocusedTestRunner()
    
    try:
        # Test with the specified configuration (NO args.num_visitors!)
        config_path = args.config if args.config else "config/config_vet.yaml"
        config_name = Path(config_path).stem
        success = runner.test_with_config(config_path, config_name)  # ONLY 2 parameters!
        
        # Save reports
        report_file, summary_file = runner.save_detailed_report()
        
        # Print final summary
        print(f"\n{'='*80}")
        print("FINAL SUMMARY")
        print(f"{'='*80}")
        
        for test_name, results in runner.test_results.items():
            if results.get("success", False):
                print(f"✅ {test_name}: ALL VISITORS MATCH")
                if "detailed_results" in results:
                    # Show breakdown by visitor type
                    returning_matches = sum(1 for r in results["detailed_results"] 
                                          if r["visitor_type"] == "RETURNING" and r["comparison"]["matches"])
                    new_matches = sum(1 for r in results["detailed_results"] 
                                    if r["visitor_type"] == "NEW" and r["comparison"]["matches"])
                    print(f"   - Returning visitors: {returning_matches}/3 matched")
                    print(f"   - New visitors: {new_matches}/3 matched")
            else:
                if "error" in results:
                    print(f"❌ {test_name}: ERROR - {results['error']}")
                else:
                    print(f"❌ {test_name}: MISMATCHES FOUND")
                    if "detailed_results" in results:
                        mismatches = [r for r in results["detailed_results"] if not r["comparison"]["matches"]]
                        if mismatches:
                            print(f"   Mismatching visitors:")
                            for m in mismatches:
                                print(f"     - {m['visitor_id']} ({m['visitor_type']}, {m.get('job_role', 'N/A')})")
        
        print(f"\nDetailed report: {report_file}")
        print(f"Summary CSV: {summary_file}")
        
        if success:
            print("\n🎉 SUCCESS: All tested visitors have identical recommendations!")
            print("The new generic processor produces exactly the same results as the old one.")
            print("\nBoth cases verified:")
            print("  ✓ Returning visitors (assist_year_before='1') - use their own past sessions")
            print("  ✓ New visitors (assist_year_before='0') - find similar visitors' sessions")
            sys.exit(0)
        else:
            print("\n⚠️ WARNING: Some visitors have different recommendations.")
            print("Please review the detailed report to identify the issues.")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()