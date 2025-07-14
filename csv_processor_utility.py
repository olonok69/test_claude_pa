"""
CSV Processor Utility Functions
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
    def preview_csv(csv_path: str, num_rows: int = 5) -> Dict:
        """Preview the first few rows of a CSV file."""
        try:
            with open(csv_path, 'r', encoding='utf-8', newline='') as csvfile:
                sample = csvfile.read(1024)
                csvfile.seek(0)
                sniffer = csv.Sniffer()
                delimiter = sniffer.sniff(sample).delimiter
                
                reader = csv.DictReader(csvfile, delimiter=delimiter)
                
                preview_data = {
                    'headers': reader.fieldnames,
                    'delimiter': delimiter,
                    'rows': []
                }
                
                for i, row in enumerate(reader):
                    if i >= num_rows:
                        break
                    preview_data['rows'].append(row)
                
                return preview_data
                
        except Exception as e:
            return {'error': f"Error previewing CSV: {e}"}
    
    @staticmethod
    def split_csv_into_batches(csv_path: str, batch_size: int = 10) -> List[str]:
        """Split a large CSV file into smaller batches for processing."""
        batch_files = []
        
        try:
            with open(csv_path, 'r', encoding='utf-8', newline='') as csvfile:
                sample = csvfile.read(1024)
                csvfile.seek(0)
                sniffer = csv.Sniffer()
                delimiter = sniffer.sniff(sample).delimiter
                
                reader = csv.DictReader(csvfile, delimiter=delimiter)
                headers = reader.fieldnames
                
                batch_num = 1
                current_batch = []
                
                for row in reader:
                    current_batch.append(row)
                    
                    if len(current_batch) >= batch_size:
                        # Save current batch
                        batch_filename = f"batch_{batch_num}_{Path(csv_path).stem}.csv"
                        batch_path = Path(csv_path).parent / batch_filename
                        
                        with open(batch_path, 'w', encoding='utf-8', newline='') as batch_file:
                            writer = csv.DictWriter(batch_file, fieldnames=headers, delimiter=delimiter)
                            writer.writeheader()
                            writer.writerows(current_batch)
                        
                        batch_files.append(str(batch_path))
                        current_batch = []
                        batch_num += 1
                
                # Save remaining rows
                if current_batch:
                    batch_filename = f"batch_{batch_num}_{Path(csv_path).stem}.csv"
                    batch_path = Path(csv_path).parent / batch_filename
                    
                    with open(batch_path, 'w', encoding='utf-8', newline='') as batch_file:
                        writer = csv.DictWriter(batch_file, fieldnames=headers, delimiter=delimiter)
                        writer.writeheader()
                        writer.writerows(current_batch)
                    
                    batch_files.append(str(batch_path))
                
                return batch_files
                
        except Exception as e:
            raise ValueError(f"Error splitting CSV into batches: {e}")
    
    @staticmethod
    def merge_markdown_results(result_files: List[str], output_path: str):
        """Merge multiple markdown result files into one."""
        try:
            all_tables = []
            
            for result_file in result_files:
                if os.path.exists(result_file):
                    with open(result_file, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                        if content and "|" in content:
                            lines = content.split('\n')
                            # Skip header for subsequent files
                            if all_tables:
                                # Find the first data row (skip header and separator)
                                data_start = 0
                                for i, line in enumerate(lines):
                                    if "|" in line and "Company Name" in line:
                                        data_start = i + 2  # Skip header and separator
                                        break
                                if data_start < len(lines):
                                    all_tables.extend(lines[data_start:])
                            else:
                                all_tables.extend(lines)
            
            # Write merged results
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(all_tables))
            
            print(f"✅ Merged {len(result_files)} result files into {output_path}")
            
        except Exception as e:
            raise ValueError(f"Error merging results: {e}")
    
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
            else:
                raise ValueError("No valid table data found in markdown")
                
        except Exception as e:
            raise ValueError(f"Error converting markdown to CSV: {e}")
    
    @staticmethod
    def generate_sample_csv(output_path: str, num_samples: int = 3):
        """Generate a sample CSV file with the expected structure."""
        sample_data = [
            {
                'CASEACCID': 'CASE001',
                'Account Name': 'GMV',
                'Trading Name': 'GMV',
                'Domain': 'gmv.com',
                'Industry': '',
                'Product/Service Type': '',
                'Event': '100 Optical; ADAS and Autonomous Vehicle Technology Expo Europe; ADAS and Autonomous Vehicle Technology Expo USA; Cloud Security London'
            },
            {
                'CASEACCID': 'CASE002',
                'Account Name': 'IQVIA',
                'Trading Name': 'IQVIA',
                'Domain': 'iqvia.com',
                'Industry': '',
                'Product/Service Type': '',
                'Event': '100 Optical; Best Practice; Big Data Expo; Clinical Pharmacy Congress; Digital Health Intelligence Networks; Genomics and Precision Medicine Expo; Oncology Professional Care'
            },
            {
                'CASEACCID': 'CASE003',
                'Account Name': 'Keepler',
                'Trading Name': 'Keepler',
                'Domain': 'keepler.io',
                'Industry': '',
                'Product/Service Type': '',
                'Event': '100 Optical; Best Practice; Big Data Expo; Clinical Pharmacy Congress; Digital Health Intelligence Networks; Genomics and Precision Medicine Expo; Oncology Professional Care'
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

if [ $# -ne 2 ]; then
    echo "Usage: $0 <input_csv> <output_directory>"
    exit 1
fi

INPUT_CSV="$1"
OUTPUT_DIR="$2"
BATCH_SIZE=10

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Run the batch processing
python -c "
import sys
sys.path.append('.')
from csv_processor_utility import CSVProcessor

# Split CSV into batches
csv_path = '$INPUT_CSV'
batch_files = CSVProcessor.split_csv_into_batches(csv_path, $BATCH_SIZE)

print(f'Created {len(batch_files)} batch files')
for i, batch_file in enumerate(batch_files):
    print(f'Batch {i+1}: {batch_file}')
"

# Process each batch
for batch_file in batch_*.csv; do
    if [ -f "$batch_file" ]; then
        echo "Processing $batch_file..."
        python company_cli.py --input "$batch_file" --output "$OUTPUT_DIR/result_$batch_file.md"
    fi
done

# Merge results
python -c "
import glob
import sys
sys.path.append('.')
from csv_processor_utility import CSVProcessor

result_files = glob.glob('$OUTPUT_DIR/result_*.md')
if result_files:
    CSVProcessor.merge_markdown_results(result_files, '$OUTPUT_DIR/final_results.md')
    CSVProcessor.convert_markdown_to_csv('$OUTPUT_DIR/final_results.md', '$OUTPUT_DIR/final_results.csv')
    print('Batch processing complete!')
"

# Clean up batch files
rm -f batch_*.csv
"""
    
    with open('batch_process.sh', 'w') as f:
        f.write(batch_script)
    
    os.chmod('batch_process.sh', 0o755)
    print("✅ Created batch processing script: batch_process.sh")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="CSV Processing Utilities")
    parser.add_argument("--validate", help="Validate CSV structure")
    parser.add_argument("--preview", help="Preview CSV file")
    parser.add_argument("--generate-sample", help="Generate sample CSV file")
    parser.add_argument("--split", help="Split CSV into batches")
    parser.add_argument("--batch-size", type=int, default=10, help="Batch size for splitting")
    parser.add_argument("--merge", nargs='+', help="Merge multiple result files")
    parser.add_argument("--output", help="Output file path")
    parser.add_argument("--to-csv", help="Convert markdown results to CSV")
    parser.add_argument("--create-batch-script", action="store_true", help="Create batch processing script")
    
    args = parser.parse_args()
    
    try:
        if args.validate:
            valid, issues = CSVProcessor.validate_csv_structure(args.validate)
            if valid:
                print("✅ CSV structure is valid")
            else:
                print(f"❌ CSV validation failed: {issues}")
        
        elif args.preview:
            preview = CSVProcessor.preview_csv(args.preview)
            if 'error' in preview:
                print(f"❌ {preview['error']}")
            else:
                print(f"Headers: {preview['headers']}")
                print(f"Delimiter: '{preview['delimiter']}'")
                print("Sample rows:")
                for i, row in enumerate(preview['rows']):
                    print(f"  Row {i+1}: {row}")
        
        elif args.generate_sample:
            CSVProcessor.generate_sample_csv(args.generate_sample)
        
        elif args.split:
            batch_files = CSVProcessor.split_csv_into_batches(args.split, args.batch_size)
            print(f"✅ Created {len(batch_files)} batch files")
            for batch_file in batch_files:
                print(f"  - {batch_file}")
        
        elif args.merge:
            if not args.output:
                print("❌ --output is required for merging")
                sys.exit(1)
            CSVProcessor.merge_markdown_results(args.merge, args.output)
        
        elif args.to_csv:
            if not args.output:
                print("❌ --output is required for CSV conversion")
                sys.exit(1)
            CSVProcessor.convert_markdown_to_csv(args.to_csv, args.output)
        
        elif args.create_batch_script:
            create_batch_script()
        
        else:
            parser.print_help()
    
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)