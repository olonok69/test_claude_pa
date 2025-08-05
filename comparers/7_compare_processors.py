#!/usr/bin/env python3
"""
Comparison Tool for Neo4j Specialization Stream Processors

This script compares the output of the old and new Neo4j specialization stream processors,
including Neo4j database state comparison.
"""

import os
import sys
import json
import logging
import tempfile
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
from neo4j import GraphDatabase
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
    sys.exit(1)


class Neo4jSpecializationStreamProcessorComparison:
    """Comprehensive comparison of Neo4j specialization stream processors"""

    def __init__(self):
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.comparison_dir = Path("comparisons") / "neo4j_specialization_stream"
        self.comparison_dir.mkdir(parents=True, exist_ok=True)
        
        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Create temporary directories for outputs
        self.temp_dir = Path(tempfile.mkdtemp())
        self.old_output_dir = self.temp_dir / "old_output"
        self.new_output_dir = self.temp_dir / "new_output"
        self.old_output_dir.mkdir(exist_ok=True)
        self.new_output_dir.mkdir(exist_ok=True)

    def __del__(self):
        """Clean up temporary directories"""
        if hasattr(self, 'temp_dir') and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def clear_neo4j_specialization_stream_relationships(self, config):
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

    def run_old_processor_with_config(self, config):
        """Run the old processor with given configuration"""
        try:
            print("🔄 Running OLD Neo4j Specialization Stream Processor...")
            old_processor = OldNeo4jSpecializationStreamProcessor(config)
            old_stats = old_processor.process(create_only_new=False)
            print(f"✅ Old processor completed - Created {old_stats.get('relationships_created', {}).get('total', 0)} relationships")
            return old_processor
        except Exception as e:
            self.logger.error(f"Error running old processor: {e}")
            raise

    def run_new_processor_with_config(self, config):
        """Run the new processor with given configuration"""
        try:
            print("🔄 Running NEW Neo4j Specialization Stream Processor...")
            new_processor = NewNeo4jSpecializationStreamProcessor(config)
            new_stats = new_processor.process(create_only_new=False)
            print(f"✅ New processor completed - Created {new_stats.get('relationships_created', {}).get('total', 0)} relationships")
            return new_processor
        except Exception as e:
            self.logger.error(f"Error running new processor: {e}")
            raise

    def compare_neo4j_relationships(self, config) -> Dict[str, Any]:
        """Compare specialization stream relationships in Neo4j"""
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
                # Count total relationships
                if show_name and show_name != "unknown":
                    total_query = f"""
                    MATCH (v)-[r:{specialization_rel}]->(s:{stream_label})
                    WHERE v.show = $show_name AND s.show = $show_name
                    RETURN COUNT(r) AS count
                    """
                    result = session.run(total_query, show_name=show_name)
                else:
                    total_query = f"""
                    MATCH ()-[r:{specialization_rel}]->({stream_label})
                    RETURN COUNT(r) AS count
                    """
                    result = session.run(total_query)
                
                total_relationships = result.single()["count"]
                
                # Count unique visitor types with relationships
                visitor_counts = {}
                for visitor_label in [visitor_this_year, visitor_last_year_bva, visitor_last_year_lva]:
                    if show_name and show_name != "unknown":
                        visitor_query = f"""
                        MATCH (v:{visitor_label})-[r:{specialization_rel}]->(s:{stream_label})
                        WHERE v.show = $show_name AND s.show = $show_name
                        RETURN COUNT(DISTINCT v) AS count
                        """
                        result = session.run(visitor_query, show_name=show_name)
                    else:
                        visitor_query = f"""
                        MATCH (v:{visitor_label})-[r:{specialization_rel}]->({stream_label})
                        RETURN COUNT(DISTINCT v) AS count
                        """
                        result = session.run(visitor_query)
                    
                    visitor_counts[visitor_label] = result.single()["count"]
                
                # Count unique streams
                if show_name and show_name != "unknown":
                    stream_query = f"""
                    MATCH (v)-[r:{specialization_rel}]->(s:{stream_label})
                    WHERE v.show = $show_name AND s.show = $show_name
                    RETURN COUNT(DISTINCT s) AS count
                    """
                    result = session.run(stream_query, show_name=show_name)
                else:
                    stream_query = f"""
                    MATCH ()-[r:{specialization_rel}]->(s:{stream_label})
                    RETURN COUNT(DISTINCT s) AS count
                    """
                    result = session.run(stream_query)
                
                unique_streams = result.single()["count"]
                
                # Get sample relationships for verification
                if show_name and show_name != "unknown":
                    sample_query = f"""
                    MATCH (v)-[r:{specialization_rel}]->(s:{stream_label})
                    WHERE v.show = $show_name AND s.show = $show_name
                    RETURN v.BadgeId as visitor_id, s.stream as stream_name
                    LIMIT 5
                    """
                    result = session.run(sample_query, show_name=show_name)
                else:
                    sample_query = f"""
                    MATCH (v)-[r:{specialization_rel}]->(s:{stream_label})
                    RETURN v.BadgeId as visitor_id, s.stream as stream_name
                    LIMIT 5
                    """
                    result = session.run(sample_query)
                
                sample_relationships = [
                    {"visitor_id": record["visitor_id"], "stream_name": record["stream_name"]}
                    for record in result
                ]
                
                comparison_result = {
                    "total_relationships": total_relationships,
                    "visitor_counts": visitor_counts,
                    "unique_streams": unique_streams,
                    "sample_relationships": sample_relationships,
                    "show_name": show_name
                }
                
                self.logger.info(f"Neo4j state: {total_relationships} relationships, {unique_streams} streams")
                return comparison_result
                
        except Exception as e:
            self.logger.error(f"Error comparing Neo4j relationships: {e}")
            return {"error": str(e)}
        finally:
            if 'driver' in locals():
                driver.close()

    def compare_processor_statistics(self, old_processor, new_processor) -> Dict[str, Any]:
        """Compare the statistics from both processors"""
        try:
            old_stats = old_processor.statistics if hasattr(old_processor, 'statistics') else {}
            new_stats = new_processor.statistics if hasattr(new_processor, 'statistics') else {}
            
            comparison = {}
            
            # Compare key statistics
            key_stats = [
                "initial_count", "final_count", "specializations_processed", 
                "specializations_mapped", "stream_matches_found"
            ]
            
            for stat in key_stats:
                old_val = old_stats.get(stat, 0)
                new_val = new_stats.get(stat, 0)
                comparison[stat] = {
                    "old": old_val,
                    "new": new_val,
                    "identical": old_val == new_val,
                    "difference": new_val - old_val
                }
            
            # Compare nested statistics
            nested_stats = ["visitor_nodes_processed", "relationships_created", "relationships_skipped", "relationships_failed"]
            for stat in nested_stats:
                if stat in old_stats and stat in new_stats:
                    if isinstance(old_stats[stat], dict) and isinstance(new_stats[stat], dict):
                        comparison[stat] = {}
                        all_keys = set(old_stats[stat].keys()) | set(new_stats[stat].keys())
                        for key in all_keys:
                            old_val = old_stats[stat].get(key, 0)
                            new_val = new_stats[stat].get(key, 0)
                            comparison[stat][key] = {
                                "old": old_val,
                                "new": new_val,
                                "identical": old_val == new_val,
                                "difference": new_val - old_val
                            }
                    else:
                        old_val = old_stats[stat]
                        new_val = new_stats[stat]
                        comparison[stat] = {
                            "old": old_val,
                            "new": new_val,
                            "identical": old_val == new_val,
                            "difference": new_val - old_val
                        }
            
            return comparison
            
        except Exception as e:
            self.logger.error(f"Error comparing processor statistics: {e}")
            return {"error": str(e)}

    def generate_report(self, old_config_path: str, new_config_path: str, 
                       stats_comparison: Dict[str, Any], 
                       neo4j_state: Dict[str, Any]) -> str:
        """Generate a detailed comparison report"""
        report = f"""# Neo4j Specialization Stream Processor Comparison Report

## Test Configuration
- **Timestamp**: {self.timestamp}
- **Old Config**: {old_config_path}
- **New Config**: {new_config_path}
- **Show**: {neo4j_state.get('show_name', 'unknown')}

## Summary
- **Total Relationships Created**: {neo4j_state.get('total_relationships', 0)}
- **Unique Streams Connected**: {neo4j_state.get('unique_streams', 0)}
- **Visitor Types Processed**: {len(neo4j_state.get('visitor_counts', {}))}

## Processor Statistics Comparison
"""

        if "error" not in stats_comparison:
            identical_count = 0
            total_count = 0
            
            for stat_name, comparison in stats_comparison.items():
                if isinstance(comparison, dict) and "identical" in comparison:
                    total_count += 1
                    if comparison["identical"]:
                        identical_count += 1
                    
                    status = "✅ IDENTICAL" if comparison["identical"] else "❌ DIFFERENT"
                    report += f"\n### {stat_name.replace('_', ' ').title()} {status}\n"
                    report += f"- Old: {comparison['old']}\n"
                    report += f"- New: {comparison['new']}\n"
                    if not comparison["identical"]:
                        report += f"- Difference: {comparison['difference']}\n"
                
                elif isinstance(comparison, dict):
                    report += f"\n### {stat_name.replace('_', ' ').title()}\n"
                    for key, comp in comparison.items():
                        if isinstance(comp, dict) and "identical" in comp:
                            total_count += 1
                            if comp["identical"]:
                                identical_count += 1
                            
                            status = "✅" if comp["identical"] else "❌"
                            report += f"- {key}: {status} Old: {comp['old']}, New: {comp['new']}\n"
            
            report += f"\n**Statistics Match Rate**: {identical_count}/{total_count} ({100*identical_count/total_count if total_count > 0 else 0:.1f}%)\n"
        else:
            report += f"\n❌ **Error in statistics comparison**: {stats_comparison['error']}\n"

        # Neo4j State Details
        report += "\n## Neo4j Database State\n"
        if "error" not in neo4j_state:
            visitor_counts = neo4j_state.get('visitor_counts', {})
            for visitor_type, count in visitor_counts.items():
                report += f"- **{visitor_type}**: {count} visitors with relationships\n"
            
            report += f"\n### Sample Relationships\n"
            for rel in neo4j_state.get('sample_relationships', [])[:5]:
                report += f"- Visitor {rel['visitor_id']} → Stream '{rel['stream_name']}'\n"
        else:
            report += f"❌ **Error accessing Neo4j**: {neo4j_state['error']}\n"

        # Recommendations
        report += "\n## Recommendations\n"
        if "error" not in stats_comparison and neo4j_state.get('total_relationships', 0) > 0:
            identical_stats = sum(1 for comp in stats_comparison.values() 
                                if isinstance(comp, dict) and comp.get("identical", False))
            total_stats = len([comp for comp in stats_comparison.values() 
                             if isinstance(comp, dict) and "identical" in comp])
            
            if identical_stats == total_stats:
                report += "✅ **PASS**: Both processors produce identical results. Safe to use the new generic processor.\n"
            else:
                report += "⚠️ **REVIEW NEEDED**: Processors produce different results. Investigation required.\n"
        else:
            report += "❌ **FAILED**: Unable to complete comparison due to errors.\n"

        return report

    def run_comparison(self, old_config_path: str = "config/config.yaml", 
                      new_config_path: str = "config/config_vet.yaml") -> bool:
        """Run the complete comparison between old and new processors"""
        try:
            print("🚀 Starting Neo4j Specialization Stream Processor Comparison")
            print("=" * 80)
            
            # Load configurations
            print("📁 Loading configurations...")
            old_config = load_config(old_config_path)
            new_config = load_config(new_config_path)
            
            # Clear existing relationships before testing
            print("🧹 Clearing existing specialization stream relationships...")
            self.clear_neo4j_specialization_stream_relationships(new_config)
            
            # Run old processor
            print("🔄 Running old processor...")
            old_processor = self.run_old_processor_with_config(old_config)
            
            # Compare Neo4j state after old processor
            print("📊 Capturing Neo4j state after old processor...")
            old_neo4j_state = self.compare_neo4j_relationships(old_config)
            
            # Clear relationships again
            print("🧹 Clearing relationships for new processor test...")
            self.clear_neo4j_specialization_stream_relationships(new_config)
            
            # Run new processor
            print("🔄 Running new processor...")
            new_processor = self.run_new_processor_with_config(new_config)
            
            # Compare Neo4j state after new processor
            print("📊 Capturing Neo4j state after new processor...")
            new_neo4j_state = self.compare_neo4j_relationships(new_config)
            
            # Compare processor statistics
            print("📈 Comparing processor statistics...")
            stats_comparison = self.compare_processor_statistics(old_processor, new_processor)
            
            # Compare final Neo4j states (should be identical if processors work the same)
            print("🔍 Comparing final Neo4j states...")
            neo4j_states_identical = (
                old_neo4j_state.get("total_relationships", 0) == new_neo4j_state.get("total_relationships", 0) and
                old_neo4j_state.get("unique_streams", 0) == new_neo4j_state.get("unique_streams", 0)
            )
            
            # Generate report
            print("📝 Generating comparison report...")
            report = self.generate_report(old_config_path, new_config_path, stats_comparison, new_neo4j_state)
            
            # Save report
            report_path = self.comparison_dir / f"comparison_report_{self.timestamp}.md"
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report)
            
            # Save detailed comparison data
            comparison_data = {
                "timestamp": self.timestamp,
                "old_config": old_config_path,
                "new_config": new_config_path,
                "statistics_comparison": stats_comparison,
                "old_neo4j_state": old_neo4j_state,
                "new_neo4j_state": new_neo4j_state,
                "neo4j_states_identical": neo4j_states_identical,
                "summary": {
                    "stats_identical": sum(1 for comp in stats_comparison.values() if comp.get("identical", False)) if "error" not in stats_comparison else 0,
                    "stats_total": len(stats_comparison) if "error" not in stats_comparison else 0,
                    "neo4j_relationships": new_neo4j_state.get("total_relationships", 0),
                    "test_passed": neo4j_states_identical and "error" not in stats_comparison
                }
            }
            
            comparison_data_path = self.comparison_dir / f"comparison_data_{self.timestamp}.json"
            with open(comparison_data_path, 'w', encoding='utf-8') as f:
                json.dump(comparison_data, f, indent=2, default=str, ensure_ascii=False)
            
            # Print summary
            print(f"\n{'='*80}")
            print("📋 COMPARISON SUMMARY")
            print(f"📄 Report saved: {report_path}")
            print(f"💾 Data saved: {comparison_data_path}")
            
            if comparison_data["summary"]["test_passed"]:
                print("✅ TEST PASSED: Both processors produce identical results!")
            else:
                print("❌ TEST FAILED: Processors produce different results or errors occurred!")
            
            print(f"📊 Relationships created: {new_neo4j_state.get('total_relationships', 0)}")
            print(f"🎯 Streams connected: {new_neo4j_state.get('unique_streams', 0)}")
            
            return comparison_data["summary"]["test_passed"]
            
        except Exception as e:
            self.logger.error(f"Comparison failed: {e}")
            print(f"❌ Comparison failed: {e}")
            return False


def main():
    """Main function to run the comparison"""
    comparison = Neo4jSpecializationStreamProcessorComparison()
    
    # You can customize these paths if needed
    old_config_path = "config/config.yaml"
    new_config_path = "config/config_vet.yaml"
    
    success = comparison.run_comparison(old_config_path, new_config_path)
    
    if success:
        print("\n🎉 Comparison completed successfully!")
        sys.exit(0)
    else:
        print("\n💥 Comparison failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()