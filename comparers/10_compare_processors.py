#!/usr/bin/env python3
"""
Compare outputs from old and new session recommendation processors.
Tests that the generic processor produces the same results as the old processor.
"""

import sys
import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
import logging
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import configurations
from utils.config_utils import load_config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SessionRecommendationComparator:
    """Compare outputs from old and new session recommendation processors."""
    
    def __init__(self, config_path="config/config.yaml"):
        """Initialize the comparator."""
        self.config = load_config(config_path)
        self.differences = []
        self.stats = {
            "total_visitors_old": 0,
            "total_visitors_new": 0,
            "matching_visitors": 0,
            "different_visitors": 0,
            "total_recommendations_old": 0,
            "total_recommendations_new": 0,
            "matching_recommendations": 0,
            "different_recommendations": 0
        }
    
    def load_recommendation_data(self, file_path):
        """Load recommendation data from JSON file."""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            return data
        except Exception as e:
            logger.error(f"Error loading file {file_path}: {e}")
            return None
    
    def extract_visitor_recommendations(self, data):
        """Extract visitor-recommendation mappings from data."""
        visitor_recs = {}
        
        if isinstance(data, dict) and "recommendations" in data:
            # New format with metadata
            recommendations = data["recommendations"]
        else:
            # Old format - direct list
            recommendations = data if isinstance(data, list) else []
        
        for rec in recommendations:
            if isinstance(rec, dict):
                # Get visitor ID
                visitor_id = None
                if "metadata" in rec and "badge_id" in rec["metadata"]:
                    visitor_id = rec["metadata"]["badge_id"]
                elif "visitor" in rec and "BadgeId" in rec["visitor"]:
                    visitor_id = rec["visitor"]["BadgeId"]
                
                if visitor_id:
                    # Get recommended sessions
                    sessions = []
                    if "filtered_recommendations" in rec:
                        for sess in rec["filtered_recommendations"]:
                            if isinstance(sess, dict):
                                sessions.append(sess.get("session_id", sess))
                            else:
                                sessions.append(sess)
                    
                    visitor_recs[visitor_id] = {
                        "sessions": sessions,
                        "count": len(sessions),
                        "raw_data": rec
                    }
        
        return visitor_recs
    
    def compare_recommendations(self, old_data, new_data):
        """Compare recommendations between old and new processors."""
        # Extract visitor recommendations
        old_recs = self.extract_visitor_recommendations(old_data)
        new_recs = self.extract_visitor_recommendations(new_data)
        
        # Update statistics
        self.stats["total_visitors_old"] = len(old_recs)
        self.stats["total_visitors_new"] = len(new_recs)
        
        # Find common visitors
        old_visitors = set(old_recs.keys())
        new_visitors = set(new_recs.keys())
        common_visitors = old_visitors & new_visitors
        only_old = old_visitors - new_visitors
        only_new = new_visitors - old_visitors
        
        logger.info(f"Common visitors: {len(common_visitors)}")
        logger.info(f"Only in old: {len(only_old)}")
        logger.info(f"Only in new: {len(only_new)}")
        
        # Compare recommendations for common visitors
        for visitor_id in common_visitors:
            old_sessions = set(old_recs[visitor_id]["sessions"])
            new_sessions = set(new_recs[visitor_id]["sessions"])
            
            if old_sessions == new_sessions:
                self.stats["matching_visitors"] += 1
                self.stats["matching_recommendations"] += len(old_sessions)
            else:
                self.stats["different_visitors"] += 1
                common_sessions = old_sessions & new_sessions
                only_old_sessions = old_sessions - new_sessions
                only_new_sessions = new_sessions - old_sessions
                
                self.differences.append({
                    "visitor_id": visitor_id,
                    "old_count": len(old_sessions),
                    "new_count": len(new_sessions),
                    "common_sessions": len(common_sessions),
                    "only_old": list(only_old_sessions)[:5],  # Limit to 5 for readability
                    "only_new": list(only_new_sessions)[:5]
                })
        
        # Count total recommendations
        for visitor_id in old_recs:
            self.stats["total_recommendations_old"] += old_recs[visitor_id]["count"]
        
        for visitor_id in new_recs:
            self.stats["total_recommendations_new"] += new_recs[visitor_id]["count"]
        
        return common_visitors, only_old, only_new
    
    def print_summary(self):
        """Print comparison summary."""
        print("\n" + "="*60)
        print("SESSION RECOMMENDATION COMPARISON SUMMARY")
        print("="*60)
        
        print("\nVisitor Statistics:")
        print(f"  Old processor visitors: {self.stats['total_visitors_old']}")
        print(f"  New processor visitors: {self.stats['total_visitors_new']}")
        print(f"  Matching visitors: {self.stats['matching_visitors']}")
        print(f"  Different visitors: {self.stats['different_visitors']}")
        
        print("\nRecommendation Statistics:")
        print(f"  Total recommendations (old): {self.stats['total_recommendations_old']}")
        print(f"  Total recommendations (new): {self.stats['total_recommendations_new']}")
        
        if self.stats['total_visitors_old'] > 0:
            match_rate = (self.stats['matching_visitors'] / 
                         min(self.stats['total_visitors_old'], self.stats['total_visitors_new'])) * 100
            print(f"\nMatch Rate: {match_rate:.2f}%")
        
        if self.differences:
            print(f"\nFound {len(self.differences)} visitors with different recommendations")
            print("\nSample differences (first 5):")
            for i, diff in enumerate(self.differences[:5]):
                print(f"\n  Visitor {diff['visitor_id']}:")
                print(f"    Old sessions: {diff['old_count']}")
                print(f"    New sessions: {diff['new_count']}")
                print(f"    Common sessions: {diff['common_sessions']}")
                if diff['only_old']:
                    print(f"    Only in old: {diff['only_old']}")
                if diff['only_new']:
                    print(f"    Only in new: {diff['only_new']}")
    
    def save_differences(self, output_file="comparers/differences_step10.json"):
        """Save differences to file for analysis."""
        if self.differences:
            output_data = {
                "timestamp": datetime.now().isoformat(),
                "statistics": self.stats,
                "differences": self.differences
            }
            
            with open(output_file, 'w') as f:
                json.dump(output_data, f, indent=2)
            
            print(f"\nDifferences saved to: {output_file}")


def main():
    """Main comparison function."""
    print("Starting Session Recommendation Processor Comparison")
    print("="*60)
    
    # Initialize comparator
    comparator = SessionRecommendationComparator("config/config.yaml")
    
    # Define file paths for old and new outputs
    # You'll need to update these based on actual output locations
    old_output_pattern = "data/bva/recommendations/recommendations_old_*.json"
    new_output_pattern = "data/bva/recommendations/recommendations_bva_*.json"
    
    # Find the most recent files
    from glob import glob
    
    old_files = sorted(glob(old_output_pattern))
    new_files = sorted(glob(new_output_pattern))
    
    if not old_files:
        print(f"No old processor output files found matching: {old_output_pattern}")
        print("Please run the old processor first to generate baseline data.")
        return 1
    
    if not new_files:
        print(f"No new processor output files found matching: {new_output_pattern}")
        print("Please run the new processor first to generate comparison data.")
        return 1
    
    # Use the most recent files
    old_file = old_files[-1]
    new_file = new_files[-1]
    
    print(f"\nComparing:")
    print(f"  Old: {old_file}")
    print(f"  New: {new_file}")
    
    # Load data
    old_data = comparator.load_recommendation_data(old_file)
    new_data = comparator.load_recommendation_data(new_file)
    
    if not old_data or not new_data:
        print("Error loading recommendation data")
        return 1
    
    # Compare recommendations
    common, only_old, only_new = comparator.compare_recommendations(old_data, new_data)
    
    # Print summary
    comparator.print_summary()
    
    # Save differences if any
    if comparator.differences:
        comparator.save_differences()
    
    # Return success/failure based on match rate
    if comparator.stats['total_visitors_old'] > 0:
        match_rate = (comparator.stats['matching_visitors'] / 
                     min(comparator.stats['total_visitors_old'], 
                         comparator.stats['total_visitors_new'])) * 100
        if match_rate >= 95:
            print("\n✅ SUCCESS: Processors produce equivalent results (≥95% match)")
            return 0
        else:
            print(f"\n⚠️ WARNING: Match rate is {match_rate:.2f}% (expected ≥95%)")
            return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())