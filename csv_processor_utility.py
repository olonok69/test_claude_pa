"""
CSV Processor Utility Functions - Updated for Batch Processing
Additional utilities for the Company Classification CLI Tool
"""

import csv
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import re

class CSVProcessor:
    """Utility class for processing CSV files and handling batch operations."""
    
    @staticmethod
    def validate_csv_structure(csv_path: str) -> Tuple[bool, List[str]]:
        """Validate CSV structure and return status and missing columns."""
        required_columns = ['Account Name', 'Trading Name', 'Domain', 'Event']
        
        if not os.path.exists(csv_path):
            return False, [f"File not found: {csv_path}"]
        
        try:
            with open(csv_path, 'r', encoding='utf-8', newline='') as csvfile:
                sample = csvfile.read(1024)
                csvfile.seek(0)
                sniffer = csv.Sniffer()
                delimiter = sniffer.sniff(sample).delimiter
                
                reader = csv.DictReader(csvfile, delimiter=delimiter)
                headers = reader.fieldnames
                
                if not headers:
                    return False, ["No headers found in CSV"]
                
                # Check for required columns
                missing_columns = []
                for col in required_columns:
                    if col not in headers:
                        missing_columns.append(col)
                
                if missing_columns:
                    return False, missing_columns
                
                return True, []
                
        except Exception as e:
            return False, [f"Error reading CSV: {e}"]
    
    @staticmethod
    def count_valid_companies(csv_path: str) -> int:
        """Count valid companies in CSV file."""
        try:
            with open(csv_path, 'r', encoding='utf-8', newline='') as csvfile:
                sample = csvfile.read(1024)
                csvfile.seek(0)
                sniffer = csv.Sniffer()
                delimiter = sniffer.sniff(sample).delimiter
                
                reader = csv.DictReader(csvfile, delimiter=delimiter)
                
                count = 0
                for row in reader:
                    cleaned_row = {k.strip(): v.strip() if v else "" for k, v in row.items()}
                    if cleaned_row.get('Account Name'):
                        count += 1
                
                return count
                
        except Exception as e:
            return 0
    
    @staticmethod
    def merge_csv_results(result_files: List[str], output_path: str):
        """Merge multiple CSV result files into one."""
        try:
            all_rows = []
            header_added = False
            
            for result_file in result_files:
                if os.path.exists(result_file) and result_file.endswith('.csv'):
                    with open(result_file, 'r', encoding='utf-8', newline='') as f:
                        reader = csv.reader(f)
                        rows = list(reader)
                        
                        if rows:
                            if not header_added:
                                # Add header from first file
                                all_rows.append(rows[0])
                                header_added = True
                            
                            # Add data rows (skip header)
                            if len(rows) > 1:
                                all_rows.extend(rows[1:])
            
            # Write merged results
            if all_rows:
                with open(output_path, 'w', encoding='utf-8', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerows(all_rows)
                
                print(f"✅ Merged {len(result_files)} CSV files into {output_path}")
                print(f"   Total rows (including header): {len(all_rows)}")
            else:
                print("❌ No valid CSV data found to merge")
            
        except Exception as e:
            raise ValueError(f"Error merging CSV results: {e}")
    
    @staticmethod
    def merge_markdown_results(result_files: List[str], output_path: str):
        """Merge multiple markdown result files into one."""
        try:
            all_tables = []
            header_added = False
            
            for result_file in result_files:
                if os.path.exists(result_file) and result_file.endswith('.md'):
                    with open(result_file, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                        if content and "|" in content:
                            lines = content.split('\n')
                            
                            if not header_added:
                                # Add everything from first file
                                all_tables.extend(lines)
                                header_added = True
                            else:
                                # Skip header and separator for subsequent files
                                data_start = 0
                                for i, line in enumerate(lines):
                                    if "|" in line and "Company Name" in line:
                                        data_start = i + 2  # Skip header and separator
                                        break
                                if data_start < len(lines):
                                    all_tables.extend(lines[data_start:])
            
            # Write merged results
            if all_tables:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(all_tables))
                
                print(f"✅ Merged {len(result_files)} markdown files into {output_path}")
            else:
                print("❌ No valid markdown data found to merge")
            
        except Exception as e:
            raise ValueError(f"Error merging markdown results: {e}")
    
    @staticmethod
    def convert_markdown_to_csv(markdown_path: str, csv_path: str):
        """Convert markdown table results to CSV format."""
        try:
            with open(markdown_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.strip().split('\n')
            csv_rows = []
            
            for line in lines:
                if "|" in line and line.strip():
                    # Parse markdown table row
                    columns = [col.strip() for col in line.split('|')]
                    # Remove empty first/last columns from markdown formatting
                    if columns and not columns[0]:
                        columns = columns[1:]
                    if columns and not columns[-1]:
                        columns = columns[:-1]
                    
                    # Skip separator lines
                    if columns and not all(col == '' or '-' in col for col in columns):
                        csv_rows.append(columns)
            
            if csv_rows:
                with open(csv_path, 'w', encoding='utf-8', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerows(csv_rows)
                
                print(f"✅ Converted markdown to CSV: {csv_path}")
                print(f"   Rows converted: {len(csv_rows)}")
            else:
                raise ValueError("No valid table data found in markdown")
                
        except Exception as e:
            raise ValueError(f"Error converting markdown to CSV: {e}")
    
    @staticmethod
    def validate_output_results(base_path: str) -> Dict[str, bool]:
        """Validate that both MD and CSV output files exist and have content."""
        results = {}
        
        md_path = Path(base_path).with_suffix('.md')
        csv_path = Path(base_path).with_suffix('.csv')
        
        # Check markdown file
        if md_path.exists():
            try:
                with open(md_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                results['markdown_exists'] = bool(content and "|" in content)
            except:
                results['markdown_exists'] = False
        else:
            results['markdown_exists'] = False
        
        # Check CSV file
        if csv_path.exists():
            try:
                with open(csv_path, 'r', encoding='utf-8', newline='') as f:
                    reader = csv.reader(f)
                    rows = list(reader)
                results['csv_exists'] = bool(rows and len(rows) > 1)  # Header + at least one data row
                results['csv_row_count'] = len(rows) - 1 if rows else 0  # Exclude header
            except:
                results['csv_exists'] = False
                results['csv_row_count'] = 0
        else:
            results['csv_exists'] = False
            results['csv_row_count'] = 0
        
        return results
    
    @staticmethod
    def calculate_batch_info(total_companies: int, batch_size: int) -> Dict[str, int]:
        """Calculate batch processing information."""
        total_batches = (total_companies + batch_size - 1) // batch_size  # Ceiling division
        
        return {
            'total_companies': total_companies,
            'batch_size': batch_size,
            'total_batches': total_batches,
            'last_batch_size': total_companies % batch_size or batch_size
        }
    
    @staticmethod
    def generate_sample_csv(output_path: str, num_samples: int = 10):
        """Generate a sample CSV file with the expected structure."""
        sample_data = [
            {
                'CASEACCID': 'CASE001',
                'Account Name': 'GMV',
                'Trading Name': 'GMV',
                'Domain': 'gmv.com',
                'Industry': '',
                'Product/Service Type': '',
                'Event': 'Cloud Security London; Big Data Expo'
            },
            {
                'CASEACCID': 'CASE002',
                'Account Name': 'IQVIA',
                'Trading Name': 'IQVIA',
                'Domain': 'iqvia.com',
                'Industry': '',
                'Product/Service Type': '',
                'Event': 'Big Data Expo; Digital Health Intelligence Networks'
            },
            {
                'CASEACCID': 'CASE003',
                'Account Name': 'Keepler',
                'Trading Name': 'Keepler',
                'Domain': 'keepler.io',
                'Industry': '',
                'Product/Service Type': '',
                'Event': 'Big Data Expo; Cloud Security London'
            },
            {
                'CASEACCID': 'CASE004',
                'Account Name': 'Microsoft',
                'Trading Name': 'Microsoft',
                'Domain': 'microsoft.com',
                'Industry': '',
                'Product/Service Type': '',
                'Event': 'Cloud and AI Infrastructure; DevOps Live'
            },
            {
                'CASEACCID': 'CASE005',
                'Account Name': 'Amazon Web Services',
                'Trading Name': 'AWS',
                'Domain': 'aws.amazon.com',
                'Industry': '',
                'Product/Service Type': '',
                'Event': 'Cloud and AI Infrastructure; Data Centre World'
            },
            {
                'CASEACCID': 'CASE006',
                'Account Name': 'NVIDIA Corporation',
                'Trading Name': 'NVIDIA',
                'Domain': 'nvidia.com',
                'Industry': '',
                'Product/Service Type': '',
                'Event': 'Big Data and AI World; Cloud and AI Infrastructure'
            },
            {
                'CASEACCID': 'CASE007',
                'Account Name': 'Palantir Technologies',
                'Trading Name': 'Palantir',
                'Domain': 'palantir.com',
                'Industry': '',
                'Product/Service Type': '',
                'Event': 'Big Data and AI World; Cloud and Cyber Security Expo'
            },
            {
                'CASEACCID': 'CASE008',
                'Account Name': 'Snowflake Inc.',
                'Trading Name': 'Snowflake',
                'Domain': 'snowflake.com',
                'Industry': '',
                'Product/Service Type': '',
                'Event': 'Big Data and AI World; Cloud and AI Infrastructure'
            },
            {
                'CASEACCID': 'CASE009',
                'Account Name': 'HashiCorp',
                'Trading Name': 'HashiCorp',
                'Domain': 'hashicorp.com',
                'Industry': '',
                'Product/Service Type': '',
                'Event': 'DevOps Live; Cloud and Cyber Security Expo'
            },
            {
                'CASEACCID': 'CASE010',
                'Account Name': 'Datadog',
                'Trading Name': 'Datadog',
                'Domain': 'datadoghq.com',
                'Industry': '',
                'Product/Service Type': '',
                'Event': 'DevOps Live; Cloud and AI Infrastructure'
            }
        ]
        
        # Limit to requested number of samples
        sample_data = sample_data[:num_samples]
        
        try:
            with open(output_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=sample_data[0].keys())
                writer.writeheader()
                writer.writerows(sample_data)
            
            print(f"✅ Generated sample CSV with {len(sample_data)} companies: {output_path}")
            
        except Exception as e:
            raise ValueError(f"Error generating sample CSV: {e}")


def create_batch_script():
    """Create a batch processing script for large CSV files."""
    batch_script = """#!/bin/bash
# Batch processing script for company classification

if [ $# -lt 2 ]; then
    echo "Usage: $0 <input_csv> <output_base_name> [batch_size]"
    echo "Example: $0 companies.csv results 10"
    exit 1
fi

INPUT_CSV="$1"
OUTPUT_BASE="$2"
BATCH_SIZE="${3:-10}"

echo "🚀 Starting batch processing..."
echo "   Input: $INPUT_CSV"
echo "   Output base: $OUTPUT_BASE"
echo "   Batch size: $BATCH_SIZE"

# Run the classification with batch processing
python3 company_cli.py --input "$INPUT_CSV" --output "$OUTPUT_BASE" --batch-size "$BATCH_SIZE"

# Check if processing was successful
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Batch processing completed successfully!"
    echo "📄 Output files created:"
    echo "   - ${OUTPUT_BASE}.md (Markdown table)"
    echo "   - ${OUTPUT_BASE}.csv (CSV format)"
    
    # Show file sizes
    if [ -f "${OUTPUT_BASE}.md" ]; then
        MD_SIZE=$(wc -l < "${OUTPUT_BASE}.md")
        echo "   - Markdown file: $MD_SIZE lines"
    fi
    
    if [ -f "${OUTPUT_BASE}.csv" ]; then
        CSV_SIZE=$(tail -n +2 "${OUTPUT_BASE}.csv" | wc -l)
        echo "   - CSV file: $CSV_SIZE data rows"
    fi
else
    echo "❌ Batch processing failed!"
    exit 1
fi
"""
    
    with open('batch_process.sh', 'w') as f:
        f.write(batch_script)
    
    os.chmod('batch_process.sh', 0o755)
    print("✅ Created batch processing script: batch_process.sh")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="CSV Processing Utilities")
    parser.add_argument("--validate", help="Validate CSV structure")
    parser.add_argument("--count", help="Count valid companies in CSV")
    parser.add_argument("--batch-info", help="Calculate batch processing info for CSV")
    parser.add_argument("--batch-size", type=int, default=10, help="Batch size for calculations")
    parser.add_argument("--generate-sample", help="Generate sample CSV file")
    parser.add_argument("--sample-size", type=int, default=10, help="Number of sample companies")
    parser.add_argument("--merge-csv", nargs='+', help="Merge multiple CSV result files")
    parser.add_argument("--merge-md", nargs='+', help="Merge multiple markdown result files")
    parser.add_argument("--output", help="Output file path")
    parser.add_argument("--to-csv", help="Convert markdown results to CSV")
    parser.add_argument("--validate-output", help="Validate output files exist and have content")
    parser.add_argument("--create-batch-script", action="store_true", help="Create batch processing script")
    
    args = parser.parse_args()
    
    try:
        if args.validate:
            valid, issues = CSVProcessor.validate_csv_structure(args.validate)
            if valid:
                print("✅ CSV structure is valid")
            else:
                print(f"❌ CSV validation failed: {issues}")
        
        elif args.count:
            count = CSVProcessor.count_valid_companies(args.count)
            print(f"📊 Valid companies in file: {count}")
        
        elif args.batch_info:
            count = CSVProcessor.count_valid_companies(args.batch_info)
            if count > 0:
                info = CSVProcessor.calculate_batch_info(count, args.batch_size)
                print(f"📊 Batch Processing Info:")
                print(f"   Total companies: {info['total_companies']}")
                print(f"   Batch size: {info['batch_size']}")
                print(f"   Total batches: {info['total_batches']}")
                print(f"   Last batch size: {info['last_batch_size']}")
            else:
                print("❌ No valid companies found in CSV")
        
        elif args.generate_sample:
            CSVProcessor.generate_sample_csv(args.generate_sample, args.sample_size)
        
        elif args.merge_csv:
            if not args.output:
                print("❌ --output is required for merging CSV files")
                sys.exit(1)
            CSVProcessor.merge_csv_results(args.merge_csv, args.output)
        
        elif args.merge_md:
            if not args.output:
                print("❌ --output is required for merging markdown files")
                sys.exit(1)
            CSVProcessor.merge_markdown_results(args.merge_md, args.output)
        
        elif args.to_csv:
            if not args.output:
                print("❌ --output is required for CSV conversion")
                sys.exit(1)
            CSVProcessor.convert_markdown_to_csv(args.to_csv, args.output)
        
        elif args.validate_output:
            results = CSVProcessor.validate_output_results(args.validate_output)
            print(f"📄 Output Validation Results:")
            print(f"   Markdown file exists: {'✅' if results['markdown_exists'] else '❌'}")
            print(f"   CSV file exists: {'✅' if results['csv_exists'] else '❌'}")
            print(f"   CSV rows processed: {results['csv_row_count']}")
        
        elif args.create_batch_script:
            create_batch_script()
        
        else:
            parser.print_help()
    
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)