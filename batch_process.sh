#!/bin/bash
# Enhanced Batch Processing Script with Server Selection
# Supports Google, Perplexity, or both MCP servers

set -e

# Default values
DEFAULT_BATCH_SIZE=10
DEFAULT_SERVERS="both"

# Function to display usage
show_usage() {
    echo "Usage: $0 <input_csv> <output_directory> [batch_size] [servers]"
    echo ""
    echo "Arguments:"
    echo "  input_csv        Path to the input CSV file"
    echo "  output_directory Directory for output files"
    echo "  batch_size       Number of companies per batch (default: $DEFAULT_BATCH_SIZE)"
    echo "  servers          MCP servers to use: 'google', 'perplexity', or 'both' (default: $DEFAULT_SERVERS)"
    echo ""
    echo "Examples:"
    echo "  # Use both servers (default)"
    echo "  $0 companies.csv results"
    echo ""
    echo "  # Use only Google Search"
    echo "  $0 companies.csv results 10 google"
    echo ""
    echo "  # Use only Perplexity"
    echo "  $0 companies.csv results 5 perplexity"
    echo ""
    echo "  # Use both servers with custom batch size"
    echo "  $0 companies.csv results 15 both"
    echo ""
    echo "Server Options:"
    echo "  google      - Use only Google Search MCP server"
    echo "  perplexity  - Use only Perplexity MCP server"
    echo "  both        - Use both Google and Perplexity servers (recommended)"
    echo ""
    exit 1
}

# Function to validate servers argument
validate_servers() {
    local servers="$1"
    case "$servers" in
        "google"|"perplexity"|"both")
            return 0
            ;;
        *)
            echo "❌ Error: Invalid servers option '$servers'"
            echo "   Valid options: google, perplexity, both"
            return 1
            ;;
    esac
}

# Function to get server description
get_server_description() {
    local servers="$1"
    case "$servers" in
        "google")
            echo "Google Search only"
            ;;
        "perplexity")
            echo "Perplexity AI only"
            ;;
        "both")
            echo "Google Search + Perplexity AI"
            ;;
        *)
            echo "Unknown"
            ;;
    esac
}

# Check arguments
if [ $# -lt 2 ]; then
    show_usage
fi

INPUT_CSV="$1"
OUTPUT_DIR="$2"
BATCH_SIZE="${3:-$DEFAULT_BATCH_SIZE}"
SERVERS="${4:-$DEFAULT_SERVERS}"

# Validate input file
if [ ! -f "$INPUT_CSV" ]; then
    echo "❌ Error: Input CSV file not found: $INPUT_CSV"
    exit 1
fi

# Validate servers option
if ! validate_servers "$SERVERS"; then
    exit 1
fi

# Validate batch size
if ! [[ "$BATCH_SIZE" =~ ^[0-9]+$ ]] || [ "$BATCH_SIZE" -lt 1 ]; then
    echo "❌ Error: Batch size must be a positive integer, got: $BATCH_SIZE"
    exit 1
fi

# Create output directory
mkdir -p "$OUTPUT_DIR"

echo "🚀 Starting Enhanced Batch Processing"
echo "======================================="
echo "📁 Input CSV: $INPUT_CSV"
echo "📁 Output Directory: $OUTPUT_DIR"
echo "📊 Batch Size: $BATCH_SIZE"
echo "🔧 Servers: $SERVERS ($(get_server_description "$SERVERS"))"
echo ""

# Check if the enhanced CLI exists
if [ ! -f "company_cli.py" ]; then
    echo "❌ Error: company_cli.py not found in current directory"
    echo "   Please run this script from the project root directory"
    exit 1
fi

# Get company count information
echo "📋 Analyzing input CSV..."
if command -v python3 &> /dev/null; then
    COMPANY_COUNT=$(python3 -c "
import sys
sys.path.append('.')
from csv_processor_utility import CSVProcessor
try:
    count = CSVProcessor.count_valid_companies('$INPUT_CSV')
    print(count)
except:
    print(0)
")
    
    if [ "$COMPANY_COUNT" -gt 0 ]; then
        TOTAL_BATCHES=$(( (COMPANY_COUNT + BATCH_SIZE - 1) / BATCH_SIZE ))
        echo "   ✅ Found $COMPANY_COUNT valid companies"
        echo "   📊 Will process in $TOTAL_BATCHES batches"
    else
        echo "   ❌ No valid companies found in CSV file"
        exit 1
    fi
else
    echo "   ⚠️  Python3 not found, skipping pre-validation"
fi

echo ""

# Run the enhanced classification
echo "🔄 Starting company classification..."
OUTPUT_BASE="$OUTPUT_DIR/results_$(date +%Y%m%d_%H%M%S)_${SERVERS}"

# Build the command
CMD="python3 company_cli.py --input \"$INPUT_CSV\" --output \"$OUTPUT_BASE\" --batch-size $BATCH_SIZE --servers $SERVERS"

# Add verbose flag if DEBUG environment variable is set
if [ -n "$DEBUG" ]; then
    CMD="$CMD --verbose"
fi

echo "💻 Running command: $CMD"
echo ""

# Execute the command
if eval $CMD; then
    echo ""
    echo "✅ Batch processing completed successfully!"
    echo ""
    echo "📄 Output files created:"
    
    # Check and report on output files
    MD_FILE="${OUTPUT_BASE}.md"
    CSV_FILE="${OUTPUT_BASE}.csv"
    
    if [ -f "$MD_FILE" ]; then
        MD_LINES=$(wc -l < "$MD_FILE" 2>/dev/null || echo "0")
        echo "   📝 Markdown: $MD_FILE ($MD_LINES lines)"
    fi
    
    if [ -f "$CSV_FILE" ]; then
        CSV_ROWS=$(( $(wc -l < "$CSV_FILE" 2>/dev/null || echo "1") - 1 ))
        echo "   📊 CSV: $CSV_FILE ($CSV_ROWS data rows)"
    fi
    
    echo ""
    echo "🔧 Server Configuration Used:"
    echo "   $(get_server_description "$SERVERS")"
    echo ""
    echo "📊 Processing Statistics:"
    echo "   Total companies processed: $COMPANY_COUNT"
    echo "   Batch size used: $BATCH_SIZE"
    echo "   Total batches: $TOTAL_BATCHES"
    echo ""
    
    # Show file sizes
    if [ -f "$MD_FILE" ]; then
        MD_SIZE=$(du -h "$MD_FILE" 2>/dev/null | cut -f1 || echo "unknown")
        echo "   Markdown file size: $MD_SIZE"
    fi
    
    if [ -f "$CSV_FILE" ]; then
        CSV_SIZE=$(du -h "$CSV_FILE" 2>/dev/null | cut -f1 || echo "unknown")
        echo "   CSV file size: $CSV_SIZE"
    fi
    
    echo ""
    echo "🎉 Ready for analysis! Files are in: $OUTPUT_DIR"
    
else
    echo ""
    echo "❌ Batch processing failed!"
    echo ""
    echo "🔍 Troubleshooting tips:"
    echo "   1. Check that your .env file contains the required API keys"
    echo "   2. Ensure MCP servers are running (if using Docker)"
    echo "   3. Verify the CSV file format matches the expected structure"
    echo "   4. Try running with DEBUG=1 for verbose output:"
    echo "      DEBUG=1 $0 $INPUT_CSV $OUTPUT_DIR $BATCH_SIZE $SERVERS"
    echo ""
    echo "📋 Required environment variables by server:"
    case "$SERVERS" in
        "google")
            echo "   - GOOGLE_API_KEY"
            echo "   - GOOGLE_SEARCH_ENGINE_ID"
            echo "   - OPENAI_API_KEY or Azure OpenAI credentials"
            ;;
        "perplexity")
            echo "   - PERPLEXITY_API_KEY"
            echo "   - OPENAI_API_KEY or Azure OpenAI credentials"
            ;;
        "both")
            echo "   - GOOGLE_API_KEY"
            echo "   - GOOGLE_SEARCH_ENGINE_ID"
            echo "   - PERPLEXITY_API_KEY"
            echo "   - OPENAI_API_KEY or Azure OpenAI credentials"
            ;;
    esac
    
    exit 1
fi