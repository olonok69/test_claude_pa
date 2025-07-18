#!/bin/bash
# Script to create the compare_servers.sh script

echo "📝 Creating compare_servers.sh script..."

# Create the compare_servers.sh script
cat > compare_servers.sh << 'EOF'
#!/bin/bash
# Server Comparison Script
# Tests all three server configurations and compares results

set -e

# Function to display usage
show_usage() {
    echo "Usage: $0 <input_csv> <output_directory> [batch_size]"
    echo ""
    echo "This script will test all three server configurations:"
    echo "  - Google Search only"
    echo "  - Perplexity only" 
    echo "  - Both servers combined"
    echo ""
    echo "Arguments:"
    echo "  input_csv        Path to the input CSV file"
    echo "  output_directory Directory for comparison results"
    echo "  batch_size       Number of companies per batch (default: 10)"
    echo ""
    echo "Example:"
    echo "  $0 companies.csv comparison_results 10"
    echo ""
    echo "Output:"
    echo "  - Individual result files for each server configuration"
    echo "  - performance_report.md with detailed comparison"
    echo ""
    exit 1
}

# Function to check if file exists and has content
check_output_file() {
    local file="$1"
    local server_type="$2"
    
    if [ -f "$file" ]; then
        local lines=$(wc -l < "$file" 2>/dev/null || echo "0")
        if [ "$lines" -gt 1 ]; then
            echo "   ✅ $server_type: $((lines - 1)) companies processed"
            return 0
        else
            echo "   ❌ $server_type: No data in output file"
            return 1
        fi
    else
        echo "   ❌ $server_type: Output file not created"
        return 1
    fi
}

# Function to get file size
get_file_size() {
    local file="$1"
    if [ -f "$file" ]; then
        du -h "$file" 2>/dev/null | cut -f1 || echo "unknown"
    else
        echo "missing"
    fi
}

# Check arguments
if [ $# -lt 2 ]; then
    show_usage
fi

INPUT_CSV="$1"
OUTPUT_DIR="$2"
BATCH_SIZE="${3:-10}"

# Validate input file
if [ ! -f "$INPUT_CSV" ]; then
    echo "❌ Error: Input CSV file not found: $INPUT_CSV"
    exit 1
fi

# Validate batch size
if ! [[ "$BATCH_SIZE" =~ ^[0-9]+$ ]] || [ "$BATCH_SIZE" -lt 1 ]; then
    echo "❌ Error: Batch size must be a positive integer, got: $BATCH_SIZE"
    exit 1
fi

# Check if enhanced CLI exists
if [ ! -f "company_cli.py" ]; then
    echo "❌ Error: company_cli.py not found in current directory"
    echo "   Please run this script from the project root directory"
    exit 1
fi

# Create output directory
mkdir -p "$OUTPUT_DIR"

echo "🔍 Starting server comparison for: $INPUT_CSV"
echo "📁 Output directory: $OUTPUT_DIR"
echo "📊 Batch size: $BATCH_SIZE"
echo ""

# Get company count
echo "📋 Analyzing input CSV..."
if command -v python3 &> /dev/null; then
    COMPANY_COUNT=$(python3 -c "
import sys
sys.path.append('.')
try:
    from csv_processor_utility import EnhancedCSVProcessor
    count = EnhancedCSVProcessor.count_valid_companies('$INPUT_CSV')
    print(count)
except ImportError:
    try:
        from csv_processor_utility import CSVProcessor
        count = CSVProcessor.count_valid_companies('$INPUT_CSV')
        print(count)
    except:
        print(0)
except:
    print(0)
")
    
    if [ "$COMPANY_COUNT" -gt 0 ]; then
        TOTAL_BATCHES=$(( (COMPANY_COUNT + BATCH_SIZE - 1) / BATCH_SIZE ))
        echo "   ✅ Found $COMPANY_COUNT valid companies"
        echo "   📊 Will process in $TOTAL_BATCHES batches per server"
        echo ""
    else
        echo "   ❌ No valid companies found in CSV file"
        exit 1
    fi
else
    echo "   ⚠️  Python3 not found, skipping pre-validation"
    echo ""
fi

# Test each server configuration
SERVERS=("google" "perplexity" "both")
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
SUCCESS_COUNT=0
FAILED_SERVERS=()

echo "🧪 Testing server configurations..."
echo "======================================="

for SERVER in "${SERVERS[@]}"; do
    echo "▶️  Testing: $SERVER"
    OUTPUT_BASE="$OUTPUT_DIR/comparison_${TIMESTAMP}_${SERVER}"
    
    # Show what this test requires
    case "$SERVER" in
        "google")
            echo "   📋 Required: GOOGLE_API_KEY, GOOGLE_SEARCH_ENGINE_ID"
            ;;
        "perplexity")
            echo "   📋 Required: PERPLEXITY_API_KEY"
            ;;
        "both")
            echo "   📋 Required: GOOGLE_API_KEY, GOOGLE_SEARCH_ENGINE_ID, PERPLEXITY_API_KEY"
            ;;
    esac
    
    # Run the test
    echo "   🔄 Processing..."
    if python3 company_cli.py --input "$INPUT_CSV" --output "$OUTPUT_BASE" --servers "$SERVER" --batch-size "$BATCH_SIZE" > "${OUTPUT_BASE}_log.txt" 2>&1; then
        # Check if output files were actually created and have content
        if check_output_file "${OUTPUT_BASE}.csv" "$SERVER"; then
            SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
            
            # Show file sizes
            MD_SIZE=$(get_file_size "${OUTPUT_BASE}.md")
            CSV_SIZE=$(get_file_size "${OUTPUT_BASE}.csv")
            echo "   📄 Files: ${OUTPUT_BASE}.md ($MD_SIZE), ${OUTPUT_BASE}.csv ($CSV_SIZE)"
        else
            echo "   ❌ $SERVER: Processing completed but no valid output generated"
            FAILED_SERVERS+=("$SERVER")
        fi
    else
        echo "   ❌ $SERVER: Processing failed"
        FAILED_SERVERS+=("$SERVER")
        
        # Show error details
        if [ -f "${OUTPUT_BASE}_log.txt" ]; then
            echo "   📋 Error details:"
            tail -n 3 "${OUTPUT_BASE}_log.txt" | sed 's/^/      /'
        fi
    fi
    echo ""
done

echo "📊 Comparison Summary:"
echo "======================"
echo "✅ Successful configurations: $SUCCESS_COUNT/3"
echo "❌ Failed configurations: ${#FAILED_SERVERS[@]}/3"

if [ ${#FAILED_SERVERS[@]} -gt 0 ]; then
    echo "📋 Failed servers: ${FAILED_SERVERS[*]}"
fi

# Generate comparison report if we have at least one success
if [ "$SUCCESS_COUNT" -gt 0 ]; then
    echo ""
    echo "📊 Generating comparison report..."
    
    # Try to generate report using enhanced processor
    if python3 -c "
import sys
sys.path.append('.')
try:
    from csv_processor_utility import EnhancedCSVProcessor
    EnhancedCSVProcessor.generate_server_performance_report('$OUTPUT_DIR', '$OUTPUT_DIR/performance_report.md')
    print('✅ Enhanced report generated')
except ImportError:
    print('⚠️  Enhanced processor not available')
    sys.exit(1)
except Exception as e:
    print(f'❌ Report generation failed: {e}')
    sys.exit(1)
" 2>/dev/null; then
        echo "   📄 Performance report: $OUTPUT_DIR/performance_report.md"
    else
        # Create basic report manually
        echo "   📝 Creating basic comparison report..."
        cat > "$OUTPUT_DIR/performance_report.md" << EOF
# Server Performance Comparison Report
Generated on: $(date)

## Summary
- Input file: $INPUT_CSV
- Companies processed: $COMPANY_COUNT
- Batch size: $BATCH_SIZE
- Successful configurations: $SUCCESS_COUNT/3

## Results by Server

EOF
        
        for SERVER in "${SERVERS[@]}"; do
            CSV_FILE="$OUTPUT_DIR/comparison_${TIMESTAMP}_${SERVER}.csv"
            if [ -f "$CSV_FILE" ]; then
                ROWS=$(( $(wc -l < "$CSV_FILE" 2>/dev/null || echo "1") - 1 ))
                cat >> "$OUTPUT_DIR/performance_report.md" << EOF
### $SERVER Server
- Status: ✅ Success
- Companies processed: $ROWS
- Output file: $(basename "$CSV_FILE")

EOF
            else
                cat >> "$OUTPUT_DIR/performance_report.md" << EOF
### $SERVER Server
- Status: ❌ Failed
- Error: Processing failed or no output generated

EOF
            fi
        done
        
        echo "   📄 Basic report created: $OUTPUT_DIR/performance_report.md"
    fi
else
    echo ""
    echo "❌ No successful configurations - cannot generate comparison report"
fi

echo ""
echo "📁 All results available in: $OUTPUT_DIR"
echo "📋 Files created:"
ls -la "$OUTPUT_DIR" | grep -E "\.(csv|md|txt)$" | while read -r line; do
    echo "   $line"
done

echo ""
if [ "$SUCCESS_COUNT" -eq 3 ]; then
    echo "🎉 All server configurations tested successfully!"
    echo "📊 Check the performance report to see which configuration works best for your data"
elif [ "$SUCCESS_COUNT" -gt 0 ]; then
    echo "⚠️  Some server configurations failed"
    echo "🔍 Check your .env file and ensure all required API keys are set"
    echo "📋 Failed servers may be missing required environment variables"
else
    echo "❌ All server configurations failed"
    echo "🔍 Troubleshooting steps:"
    echo "   1. Check your .env file contains the required API keys"
    echo "   2. Ensure MCP servers are running (docker-compose up -d)"
    echo "   3. Verify CSV file format is correct"
    echo "   4. Check log files in $OUTPUT_DIR for detailed error information"
fi

echo ""
echo "🔧 To run individual tests:"
echo "   python3 company_cli.py --input $INPUT_CSV --output test_google --servers google"
echo "   python3 company_cli.py --input $INPUT_CSV --output test_perplexity --servers perplexity"
echo "   python3 company_cli.py --input $INPUT_CSV --output test_both --servers both"

exit 0
EOF

# Make the script executable
chmod +x compare_servers.sh

echo "✅ compare_servers.sh created successfully!"
echo ""
echo "Usage: ./compare_servers.sh <input_csv> <output_directory> [batch_size]"
echo ""
echo "Example:"
echo "  ./compare_servers.sh sample_companies.csv comparison_results 10"