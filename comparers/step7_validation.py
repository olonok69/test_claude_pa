#!/usr/bin/env python3
"""
Step 7 Validation Script
Validates that the generic Neo4j Specialization Stream Processor implementation is complete and working.
"""

import os
import sys
from pathlib import Path


def check_file_exists(file_path, description):
    """Check if a file exists and print result."""
    if os.path.exists(file_path):
        print(f"✅ {description}: {file_path}")
        return True
    else:
        print(f"❌ {description}: {file_path} - NOT FOUND")
        return False


def check_import(module_name, file_path):
    """Check if a Python module can be imported."""
    try:
        if file_path:
            sys.path.insert(0, os.path.dirname(file_path))
        __import__(module_name)
        print(f"✅ Python import: {module_name}")
        return True
    except ImportError as e:
        print(f"❌ Python import: {module_name} - {e}")
        return False


def check_config_section(config_path, section_path, description):
    """Check if a config section exists."""
    try:
        import yaml
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Navigate to the section
        current = config
        for key in section_path.split('.'):
            if key in current:
                current = current[key]
            else:
                print(f"❌ Missing config section '{section_path}' in {config_path}")
                return False
        
        print(f"✅ Found config section '{section_path}' in {config_path}")
        return True
    except Exception as e:
        print(f"❌ Error checking config section '{section_path}' in {config_path}: {e}")
        return False


def validate_neo4j_connection():
    """Validate Neo4j connection and database state."""
    try:
        from dotenv import load_dotenv
        from neo4j import GraphDatabase
        
        # Load environment variables
        load_dotenv("keys/.env")
        uri = os.getenv("NEO4J_URI")
        username = os.getenv("NEO4J_USERNAME")
        password = os.getenv("NEO4J_PASSWORD")
        
        if not all([uri, username, password]):
            print("❌ Neo4j credentials not found in .env file")
            return False
        
        # Test connection
        driver = GraphDatabase.driver(uri, auth=(username, password))
        with driver.session() as session:
            result = session.run("MATCH (n) RETURN count(n) AS count")
            count = result.single()["count"]
            print(f"✅ Neo4j connection successful - {count} nodes in database")
        
        driver.close()
        return True
        
    except Exception as e:
        print(f"❌ Neo4j connection failed: {e}")
        return False


def validate_specialization_csv_files():
    """Check for the specialization CSV files."""
    print("\n📋 Checking specialization CSV files:")
    
    # Check for the files in common locations
    files_to_check = [
        "spezialization_to_stream.csv",
        "stream_job_specialism.csv"
    ]
    
    possible_paths = [
        "",  # Current directory
        "data/bva/",
        "data/ecomm/"
    ]
    
    all_found = True
    
    for filename in files_to_check:
        file_found = False
        for path_prefix in possible_paths:
            full_path = path_prefix + filename
            if os.path.exists(full_path):
                file_found = True
                break
        
        if file_found:
            try:
                import pandas as pd
                df = pd.read_csv(full_path)
                
                if filename == "spezialization_to_stream.csv":
                    if "spezialization" not in df.columns:
                        print(f"❌ {filename} missing 'spezialization' column")
                        all_found = False
                        continue
                    print(f"✅ Found {filename} at: {full_path}")
                    print(f"  - Rows: {len(df)}")
                    print(f"  - Columns: {len(df.columns)}")
                    print(f"  - Specializations: {', '.join(df['spezialization'].head(3).tolist())}...")
                
                elif filename == "stream_job_specialism.csv":
                    expected_cols = ["LVE 2024", "2024 BVA", "2025 BVA"]
                    missing_cols = [col for col in expected_cols if col not in df.columns]
                    if missing_cols:
                        print(f"❌ {filename} missing columns: {missing_cols}")
                        all_found = False
                        continue
                    print(f"✅ Found {filename} at: {full_path}")
                    print(f"  - Rows: {len(df)}")
                    print(f"  - Columns: {len(df.columns)}")
                
            except Exception as e:
                print(f"❌ Error reading {filename}: {e}")
                all_found = False
        else:
            print(f"❌ {filename} not found in expected locations")
            all_found = False
    
    return all_found


def validate_step7_implementation():
    """Validate all Step 7 implementation components."""
    print("🔍 Validating Step 7 Implementation")
    print("=" * 50)
    
    all_checks_passed = True
    
    # Check main processor file
    print("\n📁 Checking Core Files:")
    all_checks_passed &= check_file_exists("neo4j_specialization_stream_processor.py", "Neo4j Specialization Stream Processor")
    all_checks_passed &= check_file_exists("old_neo4j_specialization_stream_processor.py", "Old Neo4j Specialization Stream Processor")
    
    # Check comparison tools
    print("\n🔧 Checking Comparison Tools:")
    all_checks_passed &= check_file_exists("comparers/7_compare_processors.py", "Comparison Tool")
    all_checks_passed &= check_file_exists("comparers/7_simple_test_runner.py", "Simple Test Runner")
    
    # Check configuration files
    print("\n⚙️  Checking Configuration Files:")
    all_checks_passed &= check_file_exists("config/config_vet.yaml", "BVA Config")
    all_checks_passed &= check_file_exists("config/config_ecomm.yaml", "ECOMM Config")
    all_checks_passed &= check_file_exists("config/config.yaml", "Legacy Config")
    
    # Check configuration sections
    print("\n📋 Checking Configuration Sections:")
    all_checks_passed &= check_config_section("config/config_vet.yaml", "neo4j.show_name", "Show Name in BVA")
    all_checks_passed &= check_config_section("config/config_ecomm.yaml", "neo4j.show_name", "Show Name in ECOMM")
    all_checks_passed &= check_config_section("config/config_vet.yaml", "neo4j.specialization_stream_mapping", "Specialization Stream Config in BVA")
    all_checks_passed &= check_config_section("config/config_ecomm.yaml", "neo4j.specialization_stream_mapping", "Specialization Stream Config in ECOMM")
    
    # Check required utility files
    print("\n🛠️  Checking Utility Files:")
    all_checks_passed &= check_file_exists("utils/config_utils.py", "Config Utils")
    all_checks_passed &= check_file_exists("utils/logging_utils.py", "Logging Utils")
    all_checks_passed &= check_file_exists("utils/summary_utils.py", "Summary Utils")
    all_checks_passed &= check_file_exists("pipeline.py", "Pipeline")
    all_checks_passed &= check_file_exists("main.py", "Main Script")
    
    # Check Python imports
    print("\n🐍 Checking Python Imports:")
    if os.path.exists("neo4j_specialization_stream_processor.py"):
        all_checks_passed &= check_import("neo4j_specialization_stream_processor", "neo4j_specialization_stream_processor.py")
    
    if os.path.exists("comparers/7_compare_processors.py"):
        sys.path.insert(0, "comparers")
        all_checks_passed &= check_import("7_compare_processors", "comparers/7_compare_processors.py")
    
    # Check Neo4j dependency
    print("\n🗄️  Checking Dependencies:")
    try:
        import neo4j
        print("✅ Neo4j driver installed")
    except ImportError:
        print("❌ Neo4j driver not installed - run: pip install neo4j")
        all_checks_passed = False
    
    try:
        import pandas
        print("✅ Pandas installed")
    except ImportError:
        print("❌ Pandas not installed - run: pip install pandas")
        all_checks_passed = False
    
    try:
        import yaml
        print("✅ PyYAML installed")
    except ImportError:
        print("❌ PyYAML not installed - run: pip install pyyaml")
        all_checks_passed = False
    
    # Check CSV files
    all_checks_passed &= validate_specialization_csv_files()
    
    # Check Neo4j connection and database state
    print("\n🗄️  Checking Neo4j Database:")
    all_checks_passed &= validate_neo4j_connection()
    
    # Final result
    print(f"\n{'='*50}")
    if all_checks_passed:
        print("🎉 SUCCESS: Step 7 implementation is complete and ready!")
        print("\nNext steps:")
        print("1. Run: cd comparers && python 7_simple_test_runner.py")
        print("2. Run: cd comparers && python 7_compare_processors.py")
        print("3. Test: python main.py --config config/config_vet.yaml --only-steps 7")
        print("4. Test: python main.py --config config/config_ecomm.yaml --only-steps 7")
    else:
        print("❌ FAILURE: Some components are missing or invalid!")
        print("\nPlease address the issues above before proceeding.")
    
    return all_checks_passed


if __name__ == "__main__":
    validate_step7_implementation()