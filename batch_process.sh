#!/bin/bash
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
