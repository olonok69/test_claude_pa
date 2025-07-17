# Company Classification CLI Tool

A command-line interface for classifying companies using the existing MCP (Model Context Protocol) server infrastructure. This tool reuses the same functionality available in the Streamlit application to classify companies from CSV files using AI-powered research and taxonomy matching.

## 🚀 Features

- **Reuses Existing Infrastructure**: Leverages the same MCP servers and AI models used in the Streamlit application
- **CSV Processing**: Processes company data from CSV files with the expected column structure
- **Batch Processing**: Handles large CSV files by splitting them into manageable batches
- **Multi-Engine Search**: Uses both Google Search and Perplexity AI for comprehensive research
- **Taxonomy Matching**: Matches companies to exact industry/product pairs from the established taxonomy
- **Automated Research**: Systematically researches each company using domain, trading name, and company name
- **Markdown Output**: Generates results in markdown table format for easy viewing and processing

## 📋 Prerequisites

- Python 3.11+
- All dependencies from the main Streamlit application
- Environment variables configured (same as Streamlit app)
- Access to Google Search, Perplexity, and Company Tagging MCP servers

## 🛠️ Installation

1. **Run the setup script**:
   ```bash
   chmod +x setup_cli.sh
   ./setup_cli.sh
   ```

2. **Configure environment variables**:
   Edit the `.env` file with your API keys:
   ```env
   # AI Provider (choose one)
   OPENAI_API_KEY=your_openai_api_key_here
   # OR
   AZURE_API_KEY=your_azure_api_key
   AZURE_ENDPOINT=https://your-endpoint.openai.azure.com/
   AZURE_DEPLOYMENT=your_deployment_name
   AZURE_API_VERSION=2023-12-01-preview
   
   # Google Search
   GOOGLE_API_KEY=your_google_api_key
   GOOGLE_SEARCH_ENGINE_ID=your_custom_search_engine_id
   
   # Perplexity
   PERPLEXITY_API_KEY=your_perplexity_api_key
   PERPLEXITY_MODEL=sonar
   ```

3. **Start the MCP servers**:
   ```bash
   # In the main project directory
   docker-compose up mcpserver1 mcpserver2 -d
   ```

## 📊 CSV Input Format

Your CSV file must contain these columns:

| Column | Description | Required |
|--------|-------------|----------|
| `CASEACCID` | Case/Account ID | Optional |
| `Account Name` | Company name | **Required** |
| `Trading Name` | Trading name | Optional |
| `Domain` | Company domain | Optional |
| `Industry` | Industry classification | Optional |
| `Product/Service Type` | Product/service type | Optional |
| `Event` | Trade show events | Optional |

### Example CSV Structure:
```csv
CASEACCID,Account Name,Trading Name,Domain,Industry,Product/Service Type,Event
CASE001,GMV,GMV,gmv.com,,"100 Optical; ADAS and Autonomous Vehicle Technology Expo Europe"
CASE002,IQVIA,IQVIA,iqvia.com,,"100 Optical; Best Practice; Big Data Expo"
CASE003,Keepler,Keepler,keepler.io,,"100 Optical; Best Practice; Big Data Expo"
```

## 🎯 Usage

### Basic Usage

```bash
# Classify companies from CSV
python3 company_cli.py --input companies.csv --output results.md

# With verbose output
python3 company_cli.py --input companies.csv --output results.md --verbose

# With custom configuration
python3 company_cli.py --input companies.csv --output results.md --config custom_config.json
```

### CSV Processing Utilities

```bash
# Validate CSV structure
python3 csv_processor_utility.py --validate companies.csv

# Preview CSV contents
python3 csv_processor_utility.py --preview companies.csv

# Generate sample CSV
python3 csv_processor_utility.py --generate-sample test_companies.csv

# Split large CSV into batches
python3 csv_processor_utility.py --split large_companies.csv --batch-size 10

# Convert markdown results to CSV
python3 csv_processor_utility.py --to-csv results.md --output results.csv

# Merge multiple result files
python3 csv_processor_utility.py --merge result1.md result2.md --output final_results.md
```

### Batch Processing

For large CSV files, use the batch processing script:

```bash
# Process large CSV in batches
./batch_process.sh large_companies.csv output_directory

# This will:
# 1. Split the CSV into batches of 10 companies each
# 2. Process each batch separately
# 3. Merge all results into final_results.md and final_results.csv
```

## 📤 Output Format

The tool generates a markdown table with the following structure:

```markdown
| Company Name | Trading Name | Tech Industry 1 | Tech Product 1 | Tech Industry 2 | Tech Product 2 | Tech Industry 3 | Tech Product 3 | Tech Industry 4 | Tech Product 4 |
|--------------|--------------|-----------------|----------------|-----------------|----------------|-----------------|----------------|-----------------|----------------|
| GMV | GMV | Cloud and AI Infrastructure Services | Cloud Security Solutions | IT Infrastructure & Hardware | Semiconductor Technologies | | | | |
| IQVIA | IQVIA | AI & ML Platforms | Applications & AI Tools | Data Management | Data Analytics & Integration | | | | |
| Keepler | Keepler | AI & ML Platforms | Applications & AI Tools | Data Science & Processing | Analytics Platforms | | | | |
```

## 🔧 How It Works

The CLI tool follows the same systematic process as the Streamlit application:

1. **Setup Phase**:
   - Initializes MCP client connections to Google Search, Perplexity, and Company Tagging servers
   - Creates AI agent with LangChain and React framework
   - Validates environment configuration

2. **CSV Processing**:
   - Reads and validates CSV file structure
   - Formats company data for analysis
   - Handles missing fields gracefully

3. **Company Classification**:
   - Uses the same company tagging prompt from the MCP server
   - Systematically researches each company using:
     - `search_show_categories` tool (gets complete taxonomy)
     - `google-search` tool (searches company domain/name)
     - `perplexity_search_web` tool (AI-powered research)
   - Matches findings to exact taxonomy pairs
   - Generates structured markdown output

4. **Output Generation**:
   - Saves results to specified output file
   - Can convert to CSV format for further processing

## 📁 File Structure

```
project_root/
├── company_cli.py              # Main CLI tool
├── csv_processor_utility.py    # CSV processing utilities
├── setup_cli.sh               # Setup script
├── batch_process.sh           # Batch processing script
├── sample_companies.csv       # Sample data
├── client/                    # Existing Streamlit app
│   ├── services/             # Reused service modules
│   │   ├── ai_service.py
│   │   ├── mcp_service.py
│   │   └── chat_service.py
│   ├── utils/                # Reused utility modules
│   ├── mcp_servers/          # MCP server definitions
│   └── config.py             # Configuration
└── .env                      # Environment variables
```

## 🔍 Available MCP Tools

The CLI tool uses the same MCP tools as the Streamlit application:

### Google Search Tools
- `google-search`: Web search with configurable result counts
- `read-webpage`: Clean webpage content extraction
- `clear-cache`: Cache management
- `cache-stats`: Performance monitoring

### Perplexity AI Tools
- `perplexity_search_web`: AI-powered web search
- `perplexity_advanced_search`: Advanced search with custom parameters
- `search_show_categories`: Category taxonomy access
- `clear_api_cache`: Cache management
- `get_cache_stats`: Performance monitoring

### Company Tagging Tools
- `search_show_categories`: Access to trade show taxonomy
- Embedded stdio MCP server for specialized workflows

## 🐛 Troubleshooting

### Common Issues

1. **Environment Variables Not Set**:
   ```bash
   # Check if .env file exists and has correct values
   cat .env
   
   # Verify environment variables are loaded
   python3 -c "import os; print(os.getenv('OPENAI_API_KEY'))"
   ```

2. **MCP Servers Not Running**:
   ```bash
   # Check if MCP servers are running
   docker-compose ps
   
   # Start MCP servers
   docker-compose up mcpserver1 mcpserver2 -d
   ```

3. **CSV Format Issues**:
   ```bash
   # Validate CSV structure
   python3 csv_processor_utility.py --validate your_file.csv
   
   # Preview CSV contents
   python3 csv_processor_utility.py --preview your_file.csv
   ```

4. **Import Errors**:
   ```bash
   # Check Python path
   python3 -c "import sys; print(sys.path)"
   
   # Verify project structure
   ls -la client/services/
   ```

### Debug Mode

Run with verbose output for debugging:
```bash
python3 company_cli.py --input companies.csv --output results.md --verbose
```

## 📊 Performance Considerations

- **Batch Size**: For large files, use batch processing with 10-20 companies per batch
- **API Limits**: Monitor API usage for Google Search and Perplexity
- **Caching**: MCP servers include intelligent caching to reduce API calls
- **Memory**: Large CSV files are processed in batches to manage memory usage

## 🔒 Security

- Environment variables are loaded securely
- API keys are not logged or exposed
- All communication uses the existing MCP server security model
- Same authentication and authorization as the Streamlit application

## 📈 Monitoring

- **Tool Execution**: Verbose mode shows all tool calls and results
- **Error Handling**: Comprehensive error messages with context
- **Progress Tracking**: Real-time progress updates during processing
- **Cache Statistics**: Monitor cache hit rates and performance

## 🤝 Contributing

To extend the CLI tool:

1. Add new functionality to existing service modules in `client/services/`
2. Create new utility functions in `client/utils/`
3. Extend the CSVProcessor class for new file processing features
4. Update the CLI argument parser for new options

## 📄 License

This CLI tool inherits the same license as the main Streamlit application.

---

**Version**: 1.0.0  
**Compatibility**: Python 3.11+, Same MCP servers as Streamlit app  
**Dependencies**: Reuses all dependencies from the main application  
**Architecture**: Leverages existing MCP infrastructure with command-line interface