#!/usr/bin/env python3
"""
Session Processor Comparison Script

This script compares the outputs of the old session processor (old_session_processor.py)
and the new generic processor (session_processor.py) to ensure they produce identical results.

Usage:
    python 3_compare_processors.py
"""

import os
import sys
import json
import pandas as pd
import numpy as np
from pathlib import Path
import logging
from datetime import datetime
import hashlib
from typing import Dict, List, Tuple, Any

# Add the current directory to the path to import processors
sys.path.insert(0, os.getcwd())

# Import both processors
try:
    from old_session_processor import SessionProcessor as OldSessionProcessor
    from session_processor import SessionProcessor as NewSessionProcessor
    from utils.config_utils import load_config
    from utils.logging_utils import setup_logging
except ImportError as e:
    print(f"Error importing processors: {e}")
    print("Make sure you have:")
    print("1. old_session_processor.py (renamed from original)")
    print("2. session_processor.py (new generic version)")
    print("3. Both config files in the config/ directory")
    sys.exit(1)


class SessionProcessorComparison:
    """Compare outputs between old and new session processors."""
    
    def __init__(self):
        self.logger = setup_logging(log_file="logs/session_processor_comparison.log")
        self.comparison_results = {}
        self.differences_found = []
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create comparison output directory
        self.comparison_dir = Path("comparison_output_session")
        self.comparison_dir.mkdir(exist_ok=True)
        
        # Create separate output directories for each processor
        self.old_output_dir = self.comparison_dir / "old_processor_output"
        self.new_output_dir = self.comparison_dir / "new_processor_output"
        self.old_output_dir.mkdir(exist_ok=True)
        self.new_output_dir.mkdir(exist_ok=True)
        
        self.logger.info("SessionProcessorComparison initialized")
    
    def run_old_processor_with_config(self, config: Dict) -> OldSessionProcessor:
        """Run the old session processor with provided config."""
        self.logger.info("Running old session processor...")
        
        # Update config to use our comparison output directory
        config_copy = config.copy()
        config_copy["output_dir"] = str(self.old_output_dir)
        
        old_processor = OldSessionProcessor(config_copy)
        old_processor.process()
        self.logger.info("Old session processor completed successfully")
        return old_processor
    
    def run_new_processor_with_config(self, config: Dict) -> NewSessionProcessor:
        """Run the new session processor with provided config."""
        self.logger.info("Running new session processor...")
        
        # Update config to use our comparison output directory
        config_copy = config.copy()
        config_copy["output_dir"] = str(self.new_output_dir)
        
        new_processor = NewSessionProcessor(config_copy)
        new_processor.process()
        self.logger.info("New session processor completed successfully")
        return new_processor
    
    def compare_dataframes(self, df1: pd.DataFrame, df2: pd.DataFrame, name: str) -> Dict:
        """Compare two dataframes and return comparison results."""
        comparison = {
            "name": name,
            "identical": False,
            "shape_match": False,
            "columns_match": False,
            "values_match": False,
            "differences": []
        }
        
        # Check shapes
        if df1.shape == df2.shape:
            comparison["shape_match"] = True
            self.logger.info(f"{name}: Shapes match {df1.shape}")
        else:
            comparison["differences"].append(f"Shape mismatch: {df1.shape} vs {df2.shape}")
            self.logger.warning(f"{name}: Shape mismatch - Old: {df1.shape}, New: {df2.shape}")
        
        # Check columns
        if list(df1.columns) == list(df2.columns):
            comparison["columns_match"] = True
            self.logger.info(f"{name}: Columns match")
        else:
            cols_only_in_old = set(df1.columns) - set(df2.columns)
            cols_only_in_new = set(df2.columns) - set(df1.columns)
            if cols_only_in_old:
                comparison["differences"].append(f"Columns only in old: {cols_only_in_old}")
            if cols_only_in_new:
                comparison["differences"].append(f"Columns only in new: {cols_only_in_new}")
            self.logger.warning(f"{name}: Column mismatch")
        
        # Check values if shapes and columns match
        if comparison["shape_match"] and comparison["columns_match"]:
            # Sort both dataframes by all columns to ensure consistent ordering
            df1_sorted = df1.sort_values(by=list(df1.columns)).reset_index(drop=True)
            df2_sorted = df2.sort_values(by=list(df2.columns)).reset_index(drop=True)
            
            if df1_sorted.equals(df2_sorted):
                comparison["values_match"] = True
                comparison["identical"] = True
                self.logger.info(f"{name}: DataFrames are identical")
            else:
                # Find specific differences
                diff_mask = (df1_sorted != df2_sorted) | (df1_sorted.isna() != df2_sorted.isna())
                diff_locations = np.where(diff_mask)
                num_differences = len(diff_locations[0])
                
                if num_differences > 0:
                    comparison["differences"].append(f"Found {num_differences} cell differences")
                    # Sample a few differences
                    for i in range(min(5, num_differences)):
                        row_idx = diff_locations[0][i]
                        col_idx = diff_locations[1][i]
                        col_name = df1_sorted.columns[col_idx]
                        old_val = df1_sorted.iloc[row_idx, col_idx]
                        new_val = df2_sorted.iloc[row_idx, col_idx]
                        comparison["differences"].append(
                            f"Row {row_idx}, Col '{col_name}': {old_val} -> {new_val}"
                        )
        
        return comparison
    
    def compare_json_files(self, file1: Path, file2: Path, name: str) -> Dict:
        """Compare two JSON files."""
        comparison = {
            "name": name,
            "identical": False,
            "differences": []
        }
        
        try:
            with open(file1, 'r') as f:
                data1 = json.load(f)
            with open(file2, 'r') as f:
                data2 = json.load(f)
            
            # For streams.json, we expect it to be a dictionary
            # We don't compare values as LLM descriptions are non-deterministic
            # Just check that the keys (stream names) match
            if isinstance(data1, dict) and isinstance(data2, dict):
                keys1 = set(data1.keys())
                keys2 = set(data2.keys())
                
                if keys1 == keys2:
                    comparison["identical"] = True
                    self.logger.info(f"{name}: JSON keys match (ignoring LLM-generated values)")
                else:
                    only_in_old = keys1 - keys2
                    only_in_new = keys2 - keys1
                    if only_in_old:
                        comparison["differences"].append(f"Keys only in old: {only_in_old}")
                    if only_in_new:
                        comparison["differences"].append(f"Keys only in new: {only_in_new}")
            else:
                comparison["differences"].append("JSON structure mismatch")
                
        except Exception as e:
            comparison["differences"].append(f"Error comparing JSON: {e}")
            self.logger.error(f"Error comparing {name}: {e}")
        
        return comparison
    
    def compare_files(self, old_dir: Path, new_dir: Path) -> Dict:
        """Compare output files from both processors."""
        file_comparisons = {
            "csv_files": [],
            "json_files": []
        }
        
        # Expected output files
        expected_csv_files = [
            "session_last_filtered_valid_cols_bva.csv",
            "session_last_filtered_valid_cols_lva.csv",
            "session_this_filtered_valid_cols.csv"
        ]
        
        expected_json_files = [
            "streams.json"
        ]
        
        # Compare CSV files
        for csv_file in expected_csv_files:
            old_file = old_dir / "output" / csv_file
            new_file = new_dir / "output" / csv_file
            
            if old_file.exists() and new_file.exists():
                old_df = pd.read_csv(old_file)
                new_df = pd.read_csv(new_file)
                comparison = self.compare_dataframes(old_df, new_df, csv_file)
                file_comparisons["csv_files"].append(comparison)
            else:
                file_comparisons["csv_files"].append({
                    "name": csv_file,
                    "identical": False,
                    "differences": [f"File missing - Old exists: {old_file.exists()}, New exists: {new_file.exists()}"]
                })
        
        # Compare JSON files (only structure, not LLM-generated content)
        for json_file in expected_json_files:
            old_file = old_dir / "output" / json_file
            new_file = new_dir / "output" / json_file
            
            if old_file.exists() and new_file.exists():
                comparison = self.compare_json_files(old_file, new_file, json_file)
                file_comparisons["json_files"].append(comparison)
            else:
                file_comparisons["json_files"].append({
                    "name": json_file,
                    "identical": False,
                    "differences": [f"File missing - Old exists: {old_file.exists()}, New exists: {new_file.exists()}"]
                })
        
        return file_comparisons
    
    def compare_processor_attributes(self, old_processor: OldSessionProcessor, 
                                    new_processor: NewSessionProcessor) -> List[Dict]:
        """Compare key attributes between processors."""
        attribute_comparisons = []
        
        # Key attributes to compare
        attributes_to_compare = [
            'session_this_filtered_valid_cols',
            'session_last_filtered_valid_cols_bva',
            'session_last_filtered_valid_cols_lva',
            'unique_streams',
            'map_vets',
            'titles_to_remove'
        ]
        
        for attr_name in attributes_to_compare:
            comparison = {
                "attribute": attr_name,
                "identical": False,
                "old_exists": hasattr(old_processor, attr_name),
                "new_exists": hasattr(new_processor, attr_name),
                "differences": []
            }
            
            if comparison["old_exists"] and comparison["new_exists"]:
                old_val = getattr(old_processor, attr_name)
                new_val = getattr(new_processor, attr_name)
                
                if isinstance(old_val, pd.DataFrame) and isinstance(new_val, pd.DataFrame):
                    df_comp = self.compare_dataframes(old_val, new_val, f"Attribute: {attr_name}")
                    comparison["identical"] = df_comp["identical"]
                    comparison["differences"] = df_comp["differences"]
                elif isinstance(old_val, (list, dict, set)):
                    if old_val == new_val:
                        comparison["identical"] = True
                    else:
                        comparison["differences"].append(f"Values differ")
                else:
                    if old_val == new_val:
                        comparison["identical"] = True
                    else:
                        comparison["differences"].append(f"Values differ: {old_val} vs {new_val}")
            else:
                if not comparison["old_exists"]:
                    comparison["differences"].append("Missing in old processor")
                if not comparison["new_exists"]:
                    comparison["differences"].append("Missing in new processor")
            
            attribute_comparisons.append(comparison)
        
        return attribute_comparisons
    
    def run_comparison(self, old_config_path: str = "config/config.yaml",
                       new_config_path: str = "config/config_vet.yaml") -> bool:
        """Run full comparison between processors."""
        try:
            self.logger.info("Starting session processor comparison")
            print("🚀 Starting Session Processor Comparison")
            print("=" * 60)
            
            # Load configurations
            print("📁 Loading configurations...")
            old_config = load_config(old_config_path)
            new_config = load_config(new_config_path)
            
            # Run processors
            print("🔄 Running old processor...")
            old_processor = self.run_old_processor_with_config(old_config)
            
            print("🔄 Running new processor...")
            new_processor = self.run_new_processor_with_config(new_config)
            
            # Compare outputs
            print("📊 Comparing outputs...")
            
            # Compare files
            file_comparisons = self.compare_files(self.old_output_dir, self.new_output_dir)
            
            # Compare processor attributes
            attr_comparisons = self.compare_processor_attributes(old_processor, new_processor)
            
            # Compile results
            comparison_data = {
                "timestamp": self.timestamp,
                "old_config": old_config_path,
                "new_config": new_config_path,
                "file_comparisons": file_comparisons,
                "attribute_comparisons": attr_comparisons,
                "summary": {
                    "csv_files_total": len(file_comparisons["csv_files"]),
                    "csv_files_identical": sum(1 for f in file_comparisons["csv_files"] if f["identical"]),
                    "json_files_total": len(file_comparisons["json_files"]),
                    "json_files_identical": sum(1 for f in file_comparisons["json_files"] if f["identical"]),
                    "attr_total": len(attr_comparisons),
                    "attr_identical": sum(1 for a in attr_comparisons if a["identical"])
                }
            }
            
            # Save comparison results
            results_file = self.comparison_dir / f"comparison_results_{self.timestamp}.json"
            with open(results_file, 'w') as f:
                json.dump(comparison_data, f, indent=2, default=str)
            
            # Print summary
            print("\n" + "=" * 60)
            print("📋 COMPARISON SUMMARY")
            print("=" * 60)
            
            summary = comparison_data["summary"]
            print(f"\n📁 CSV Files: {summary['csv_files_identical']}/{summary['csv_files_total']} identical")
            for file_comp in file_comparisons["csv_files"]:
                status = "✅" if file_comp["identical"] else "❌"
                print(f"  {status} {file_comp['name']}")
                if not file_comp["identical"] and file_comp["differences"]:
                    for diff in file_comp["differences"][:3]:  # Show first 3 differences
                        print(f"      - {diff}")
            
            print(f"\n📋 JSON Files: {summary['json_files_identical']}/{summary['json_files_total']} structure match")
            for file_comp in file_comparisons["json_files"]:
                status = "✅" if file_comp["identical"] else "❌"
                print(f"  {status} {file_comp['name']} (comparing keys only, not LLM values)")
            
            print(f"\n🔍 Processor Attributes: {summary['attr_identical']}/{summary['attr_total']} identical")
            for attr_comp in attr_comparisons:
                status = "✅" if attr_comp["identical"] else "❌"
                print(f"  {status} {attr_comp['attribute']}")
                if not attr_comp["identical"] and attr_comp["differences"]:
                    for diff in attr_comp["differences"][:2]:
                        print(f"      - {diff}")
            
            # Overall success
            all_csv_identical = summary['csv_files_identical'] == summary['csv_files_total']
            all_json_structure_ok = summary['json_files_identical'] == summary['json_files_total']
            
            print("\n" + "=" * 60)
            if all_csv_identical and all_json_structure_ok:
                print("🎉 SUCCESS: Processors produce IDENTICAL outputs!")
                print("✅ The new generic session processor is fully compatible.")
            else:
                print("⚠️  WARNING: Some differences found")
                if not all_csv_identical:
                    print("   - CSV outputs have differences")
                if not all_json_structure_ok:
                    print("   - JSON structure has differences")
                print(f"\n📄 Detailed results saved to: {results_file}")
            
            print("=" * 60)
            
            return all_csv_identical and all_json_structure_ok
            
        except Exception as e:
            self.logger.error(f"Comparison failed: {e}", exc_info=True)
            print(f"\n❌ ERROR: Comparison failed - {e}")
            return False


def main():
    """Main function to run the comparison."""
    comparator = SessionProcessorComparison()
    success = comparator.run_comparison()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())