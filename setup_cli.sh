#!/bin/bash
# Setup script for Company Classification CLI Tool

set -e

echo "🚀 Setting up Company Classification CLI Tool"
echo "============================================="

# Check if we're in the right directory
if [ ! -d "client" ]; then
    echo "❌ Error: This script should be run from the root directory of the project"
    echo "   (the directory containing the 'client' folder)"
    exit 1
fi

# Check Python version
echo "🐍 Checking Python version..."
python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
echo "   Python version: $python_version"

# Check if required directories exist
echo "📁 Checking project structure..."
required_dirs=("client" "client/services" "client/utils" "client/mcp_servers")
for dir in "${required_dirs[@]}"; do
    if [ ! -d "$dir" ]; then
        echo "❌ Error: Required directory not found: $dir"
        exit 1
    fi
done
echo "   ✅ Project structure is valid"

# Check for environment file
echo "🔐 Checking environment configuration..."
if [ ! -f ".env" ]; then
    echo "   ⚠️  .env file not found, creating template..."
    cat > .env << 'EOF'
# AI Provider Configuration (choose one)
OPENAI_API_KEY=your_openai_api_key_here

# OR Azure OpenAI Configuration
AZURE_API_KEY=your_azure_api_key
AZURE_ENDPOINT=https://your-endpoint.openai.azure.com/
AZURE_DEPLOYMENT=your_deployment_name
AZURE_API_VERSION=2023-12-01-preview

# Google Search Configuration
GOOGLE_API_KEY=your_google_api_key
GOOGLE_SEARCH_ENGINE_ID=your_custom_search_engine_id

# Perplexity Configuration
PERPLEXITY_API_KEY=your_perplexity_api_key
PERPLEXITY_MODEL=sonar

# SSL Configuration (Optional)
SSL_ENABLED=true
EOF
    echo "   📝 Created .env template - please fill in your API keys"
else
    echo "   ✅ .env file found"
fi

# Make CLI scripts executable
echo "🔧 Setting up CLI scripts..."
chmod +x company_cli.py
chmod +x csv_processor_utility.py
echo "   ✅ CLI scripts are now executable"

# Create CLI-specific server configuration
echo "⚙️  Creating CLI server configuration..."
cat > cli_servers_config.json << 'EOF'
{
  "mcpServers": {
    "Google Search": {
      "transport": "sse",
      "url": "http://localhost:8002/sse",
      "timeout": 600,
      "headers": null,
      "sse_read_timeout": 900
    },
    "Perplexity Search": {
      "transport": "sse",
      "url": "http://localhost:8001/sse",
      "timeout": 600,
      "headers": null,
      "sse_read_timeout": 900
    },
    "Company Tagging": {
      "transport": "stdio",
      "command": "python",
      "args": ["-m", "mcp_servers.company_tagging.server"],
      "env": {
        "PERPLEXITY_API_KEY": "${PERPLEXITY_API_KEY}",
        "PERPLEXITY_MODEL": "${PERPLEXITY_MODEL}"
      }
    }
  }
}
EOF
echo "   ✅ Created cli_servers_config.json with localhost URLs"

# Create sample CSV
echo "📊 Creating sample CSV file..."
python3 -c "
import sys
sys.path.append('.')
from csv_processor_utility import CSVProcessor
CSVProcessor.generate_sample_csv('sample_companies.csv', 3)
"

# Create batch processing script
echo "📝 Creating batch processing script..."
python3 -c "
import sys
sys.path.append('.')
from csv_processor_utility import create_batch_script
create_batch_script()
"

# Test the CLI tool structure
echo "🧪 Testing CLI tool structure..."
python3 -c "
import sys
sys.path.append('./client')
try:
    from services.ai_service import create_llm_model
    from services.mcp_service import setup_mcp_client
    from services.chat_service import get_clean_conversation_memory
    print('   ✅ All required modules can be imported')
except ImportError as e:
    print(f'   ❌ Import error: {e}')
    sys.exit(1)
"

echo ""
echo "🎉 Setup completed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Install Python dependencies manually:"
echo "   pip3 install streamlit langchain-openai langchain-mcp-adapters langgraph python-dotenv aiohttp"
echo "   (or pip3 install -r client/requirements.txt if available)"
echo "2. Edit the .env file and add your API keys"
echo "3. Start the MCP servers: docker-compose up mcpserver1 mcpserver2 -d"
echo "4. Test the CLI tool with the sample CSV:"
echo "   python3 company_cli.py --input sample_companies.csv --output results.md"
echo ""
echo "📖 Usage examples:"
echo "   python3 company_cli.py --input companies.csv --output results.md"
echo "   python3 csv_processor_utility.py --validate companies.csv"
echo "   python3 csv_processor_utility.py --preview companies.csv"
echo "   ./batch_process.sh large_companies.csv output_directory"
echo ""
echo "🔧 Available utilities:"
echo "   - company_cli.py: Main classification tool"
echo "   - csv_processor_utility.py: CSV processing utilities"
echo "   - batch_process.sh: Batch processing for large files"
echo "   - sample_companies.csv: Sample data for testing"
echo ""
echo "For more information, run: python3 company_cli.py --help"
