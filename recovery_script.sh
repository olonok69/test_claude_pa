#!/bin/bash
# Recovery and Progress Management Script for Company Classification

set -e

show_usage() {
    echo "Recovery and Progress Management Script"
    echo "====================================="
    echo ""
    echo "Usage: $0 <command> [options]"
    echo ""
    echo "Commands:"
    echo "  status <output_base>     - Show current progress status"
    echo "  resume <input_csv> <output_base> [options] - Resume processing"
    echo "  clean <output_base>      - Clean up temporary files"
    echo "  analyze <output_base>    - Analyze errors and progress"
    echo "  merge <output_base>      - Merge partial results"
    echo ""
    echo "Resume Options:"
    echo "  --batch-size N          - Batch size (default: 5)"
    echo "  --servers TYPE          - Server type (default: google)"
    echo "  --clean-start           - Start fresh, ignore progress"
    echo "  --verbose               - Enable verbose output"
    echo ""
    echo "Examples:"
    echo "  $0 status All_accounts"
    echo "  $0 resume All_Tech_Account_Data.csv All_accounts"
    echo "  $0 resume All_Tech_Account_Data.csv All_accounts --batch-size 3"
    echo "  $0 clean All_accounts"
    echo "  $0 analyze All_accounts"
    echo ""
    exit 1
}

# Function to check if enhanced CLI exists
check_enhanced_cli() {
    if [ ! -f "company_cli.py" ]; then
        echo "❌ Error: company_cli.py not found in current directory"
        echo "   Please run this script from the project root directory"
        exit 1
    fi
}

# Function to show progress status
show_status() {
    local output_base="$1"
    
    echo "📊 Progress Status for: $output_base"
    echo "================================="
    echo ""
    
    # Check for progress file
    if [ -f "${output_base}_progress.pkl" ]; then
        echo "✅ Progress file found: ${output_base}_progress.pkl"
        
        # Try to get stats using Python
        if python3 -c "
import pickle
import sys
try:
    with open('${output_base}_progress.pkl', 'rb') as f:
        data = pickle.load(f)
    
    completed = len(data.get('processed_batches', set()))
    failed = len(data.get('failed_batches', set()))
    total = data.get('total_batches', 0)
    errors = data.get('error_count', 0)
    
    print(f'📈 Progress Statistics:')
    print(f'   Total batches: {total}')
    print(f'   Completed batches: {completed}')
    print(f'   Failed batches: {failed}')
    print(f'   Remaining batches: {total - completed}')
    print(f'   Success rate: {completed/max(1,total)*100:.1f}%')
    print(f'   Total errors: {errors}')
    
    if data.get('start_time'):
        import time
        elapsed = time.time() - data['start_time']
        print(f'   Elapsed time: {elapsed/3600:.1f} hours')
        
        if completed > 0:
            rate = completed / (elapsed / 3600)
            remaining_time = (total - completed) / max(rate, 0.1)
            print(f'   Processing rate: {rate:.1f} batches/hour')
            print(f'   Estimated remaining time: {remaining_time:.1f} hours')
    
except Exception as e:
    print(f'❌ Error reading progress file: {e}')
    sys.exit(1)
" 2>/dev/null; then
            echo ""
        else
            echo "⚠️  Could not parse progress file with Python"
        fi
    else
        echo "❌ No progress file found: ${output_base}_progress.pkl"
        echo "   This might be a fresh start or the process hasn't been run yet"
    fi
    
    # Check for temporary results
    if [ -f "${output_base}_temp_results.json" ]; then
        echo "✅ Temporary results file found: ${output_base}_temp_results.json"
        local temp_size=$(wc -l < "${output_base}_temp_results.json" 2>/dev/null || echo "0")
        echo "   File size: $temp_size lines"
    else
        echo "⚠️  No temporary results file found"
    fi
    
    # Check for error log
    if [ -f "${output_base}_errors.log" ]; then
        echo "⚠️  Error log found: ${output_base}_errors.log"
        local error_lines=$(wc -l < "${output_base}_errors.log" 2>/dev/null || echo "0")
        echo "   Log size: $error_lines lines"
        
        if [ "$error_lines" -gt 0 ]; then
            echo "   Recent errors:"
            tail -n 5 "${output_base}_errors.log" | grep -E "^(Batch|Error)" | head -n 3 | sed 's/^/      /'
        fi
    else
        echo "✅ No error log found (good sign!)"
    fi
    
    # Check for final output files
    echo ""
    echo "📄 Output Files:"
    if [ -f "${output_base}.md" ]; then
        local md_size=$(wc -l < "${output_base}.md" 2>/dev/null || echo "0")
        echo "   ✅ Markdown file: ${output_base}.md ($md_size lines)"
    else
        echo "   ❌ No markdown file found"
    fi
    
    if [ -f "${output_base}.csv" ]; then
        local csv_rows=$(( $(wc -l < "${output_base}.csv" 2>/dev/null || echo "1") - 1 ))
        echo "   ✅ CSV file: ${output_base}.csv ($csv_rows data rows)"
    else
        echo "   ❌ No CSV file found"
    fi
    
    if [ -f "${output_base}.stats.json" ]; then
        echo "   ✅ Statistics file: ${output_base}.stats.json"
    else
        echo "   ❌ No statistics file found"
    fi
    
    echo ""
    echo "💡 Next Steps:"
    if [ -f "${output_base}_progress.pkl" ]; then
        echo "   To resume: $0 resume <input_csv> $output_base"
        echo "   To clean:  $0 clean $output_base"
        echo "   To analyze: $0 analyze $output_base"
    else
        echo "   Run the enhanced CLI tool to start processing"
    fi
}

# Function to clean up temporary files
clean_temp_files() {
    local output_base="$1"
    
    echo "🧹 Cleaning temporary files for: $output_base"
    echo "============================================="
    
    local files_to_clean=(
        "${output_base}_progress.pkl"
        "${output_base}_temp_results.json"
        "${output_base}_errors.log"
    )
    
    local cleaned_count=0
    
    for file in "${files_to_clean[@]}"; do
        if [ -f "$file" ]; then
            rm -f "$file"
            echo "   ✅ Removed: $file"
            ((cleaned_count++))
        else
            echo "   ❌ Not found: $file"
        fi
    done
    
    echo ""
    echo "📊 Cleanup Summary:"
    echo "   Files removed: $cleaned_count"
    echo "   Kept final results: ${output_base}.md, ${output_base}.csv, ${output_base}.stats.json"
}

# Function to analyze errors and progress
analyze_progress() {
    local output_base="$1"
    
    echo "🔍 Analyzing progress and errors for: $output_base"
    echo "=============================================="
    echo ""
    
    # Analyze error log
    if [ -f "${output_base}_errors.log" ]; then
        echo "📋 Error Analysis:"
        
        # Count different types of errors
        echo "   Error types found:"
        grep -E "^Error:" "${output_base}_errors.log" | sort | uniq -c | sort -nr | head -5 | while read count error; do
            echo "      $count times: $error"
        done
        
        echo ""
        echo "   Most recent errors:"
        tail -n 10 "${output_base}_errors.log" | grep -E "^(Batch|Error)" | tail -3 | sed 's/^/      /'
        
        # Check for patterns
        echo ""
        echo "   Common error patterns:"
        if grep -q "timeout" "${output_base}_errors.log"; then
            echo "      ⏰ Timeout errors detected - consider reducing batch size"
        fi
        if grep -q "JSON" "${output_base}_errors.log"; then
            echo "      🔧 JSON parsing errors detected - enhanced version should handle these"
        fi
        if grep -q "connection" "${output_base}_errors.log"; then
            echo "      🌐 Connection errors detected - check network/server status"
        fi
        
    else
        echo "✅ No error log found - good sign!"
    fi
    
    # Analyze progress file
    if [ -f "${output_base}_progress.pkl" ]; then
        echo ""
        echo "📊 Progress Analysis:"
        
        python3 -c "
import pickle
import sys
try:
    with open('${output_base}_progress.pkl', 'rb') as f:
        data = pickle.load(f)
    
    processed = data.get('processed_batches', set())
    failed = data.get('failed_batches', set())
    total = data.get('total_batches', 0)
    
    print(f'   Processing efficiency:')
    
    if total > 0:
        success_rate = len(processed) / total * 100
        failure_rate = len(failed) / total * 100
        print(f'      Success rate: {success_rate:.1f}%')
        print(f'      Failure rate: {failure_rate:.1f}%')
        
        if success_rate < 80:
            print('      ⚠️  Low success rate - consider reducing batch size')
        elif success_rate > 95:
            print('      ✅ Excellent success rate!')
        
        # Find gaps in processing
        all_batches = set(range(1, total + 1))
        processed_batches = processed
        missing_batches = all_batches - processed_batches
        
        if missing_batches:
            missing_count = len(missing_batches)
            print(f'      Missing batches: {missing_count}')
            
            if missing_count < 10:
                missing_list = sorted(list(missing_batches))
                print(f'      Missing: {missing_list}')
            
except Exception as e:
    print(f'❌ Error analyzing progress: {e}')
" 2>/dev/null || echo "⚠️  Could not analyze progress file"
    fi
    
    # Check disk space
    echo ""
    echo "💾 Disk Space Check:"
    df -h . | tail -1 | while read filesystem size used avail capacity mounted; do
        echo "   Available space: $avail ($capacity used)"
        
        # Parse capacity percentage
        capacity_num=$(echo "$capacity" | tr -d '%')
        if [ "$capacity_num" -gt 90 ]; then
            echo "   ⚠️  Warning: Low disk space!"
        fi
    done
    
    echo ""
    echo "💡 Recommendations:"
    if [ -f "${output_base}_progress.pkl" ]; then
        echo "   • Resume processing with: $0 resume <input_csv> $output_base"
        echo "   • If many timeouts, try: --batch-size 3"
        echo "   • If JSON errors persist, the enhanced CLI should handle them"
        echo "   • Monitor progress with: $0 status $output_base"
    else
        echo "   • Start processing with the enhanced CLI tool"
    fi
}

# Function to merge partial results
merge_results() {
    local output_base="$1"
    
    echo "🔄 Merging partial results for: $output_base"
    echo "======================================="
    
    if [ -f "${output_base}_temp_results.json" ]; then
        echo "✅ Found temporary results file"
        
        # Try to convert temp results to final format
        python3 -c "
import json
import csv
import sys

try:
    with open('${output_base}_temp_results.json', 'r') as f:
        data = json.load(f)
    
    if not data:
        print('❌ No data in temporary results file')
        sys.exit(1)
    
    # Convert to CSV
    csv_path = '${output_base}.csv'
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(data)
    
    print(f'✅ Converted {len(data)} rows to CSV: {csv_path}')
    
    # Create markdown
    if data:
        md_path = '${output_base}.md'
        with open(md_path, 'w', encoding='utf-8') as f:
            header = data[0]
            f.write('|' + '|'.join([''] + header + ['']) + '|\\n')
            
            separator = ['---'] * len(header)
            f.write('|' + '|'.join([''] + separator + ['']) + '|\\n')
            
            for row in data[1:]:
                if len(row) >= len(header):
                    f.write('|' + '|'.join([''] + row[:len(header)] + ['']) + '|\\n')
        
        print(f'✅ Created markdown file: {md_path}')
    
except Exception as e:
    print(f'❌ Error merging results: {e}')
    sys.exit(1)
" 2>/dev/null || echo "❌ Could not merge results"
    else
        echo "❌ No temporary results file found"
    fi
}

# Function to resume processing
resume_processing() {
    local input_csv="$1"
    local output_base="$2"
    shift 2
    
    echo "🔄 Resuming processing..."
    echo "Input CSV: $input_csv"
    echo "Output base: $output_base"
    echo "Additional args: $@"
    echo ""
    
    # Check if input file exists
    if [ ! -f "$input_csv" ]; then
        echo "❌ Error: Input CSV file not found: $input_csv"
        exit 1
    fi
    
    # Run the enhanced CLI tool
    echo "🚀 Starting enhanced CLI tool..."
    python3 company_cli.py --input "$input_csv" --output "$output_base" "$@"
    
    local exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        echo ""
        echo "✅ Processing completed successfully!"
        echo "📄 Check your results:"
        echo "   - ${output_base}.md"
        echo "   - ${output_base}.csv"
        echo "   - ${output_base}.stats.json"
    else
        echo ""
        echo "❌ Processing failed or was interrupted"
        echo "💡 You can resume with: $0 resume $input_csv $output_base"
        echo "📊 Check status with: $0 status $output_base"
    fi
    
    return $exit_code
}

# Main script logic
if [ $# -lt 2 ]; then
    show_usage
fi

command="$1"
shift

check_enhanced_cli

case "$command" in
    "status")
        if [ $# -lt 1 ]; then
            echo "❌ Error: status command requires output_base"
            show_usage
        fi
        show_status "$1"
        ;;
    
    "clean")
        if [ $# -lt 1 ]; then
            echo "❌ Error: clean command requires output_base"
            show_usage
        fi
        clean_temp_files "$1"
        ;;
    
    "analyze")
        if [ $# -lt 1 ]; then
            echo "❌ Error: analyze command requires output_base"
            show_usage
        fi
        analyze_progress "$1"
        ;;
    
    "merge")
        if [ $# -lt 1 ]; then
            echo "❌ Error: merge command requires output_base"
            show_usage
        fi
        merge_results "$1"
        ;;
    
    "resume")
        if [ $# -lt 2 ]; then
            echo "❌ Error: resume command requires input_csv and output_base"
            show_usage
        fi
        resume_processing "$@"
        ;;
    
    *)
        echo "❌ Error: Unknown command: $command"
        show_usage
        ;;
esac