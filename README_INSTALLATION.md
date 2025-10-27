# Deep Agents ML Report Generation - Installation Guide

## Overview

This document provides complete installation instructions for the Deep Agents workflow that generates ML pipeline analysis reports with Neo4j MCP integration.

## System Requirements

### Python Version
- **Python 3.11 or later** (required for LangGraph compatibility)

Verify your Python version:
```bash
python3 --version
```

### Operating System
- Linux (Ubuntu 24 or later recommended)
- macOS (with Homebrew)
- Windows (with WSL2 recommended)

## Prerequisites

### 1. Package Manager - uv

Install the `uv` package manager for fast, reliable Python package management:

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Update PATH
export PATH="/Users/$USER/.local/bin:$PATH"

# Verify installation
uv --version
```

### 2. Neo4j MCP Server

The workflow requires the Neo4j MCP server to interact with the database:

```bash
# Install neo4j-contrib/mcp-neo4j via npm
npm install -g @neo4j/mcp-neo4j-cypher

# Or using uvx (recommended)
uvx mcp install neo4j
```

**Note:** Ensure the MCP server is configured with your Neo4j credentials. See [Neo4j MCP Configuration](#neo4j-mcp-configuration) below.

### 3. Environment Variables

Create a `.env` file in your project root:

```bash
# Create .env file
touch .env
```

Add required API keys:

```env
# Required for Anthropic Claude models
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Required for Neo4j connections
NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_neo4j_password

# Optional: For tracing and debugging
LANGSMITH_API_KEY=your_langsmith_api_key_here
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=ml-report-deep-agents
```

## Installation Steps

### Step 1: Clone or Copy Files

Ensure you have the following files in your project directory:

```
project/
├── deep_agents_report_workflow.py
├── requirements.txt
├── .env
├── config/
│   ├── config_ecomm.yaml
│   └── config_vet_lva.yaml
├── reports/
│   └── prompts/
│       ├── prompt_initial_run.md
│       ├── prompt_increment_run.md
│       └── prompt_post_show.md
└── README_INSTALLATION.md
```

### Step 2: Create Virtual Environment

Using `uv` to create and manage the virtual environment:

```bash
# Initialize project (if not already done)
uv init

# Sync dependencies (creates venv automatically)
uv sync
```

Alternatively, using standard Python:

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Step 3: Install Dependencies

Create a `requirements.txt` file with the following content:

```txt
# Core Dependencies
langgraph>=0.2.0
langchain>=0.3.0
langchain-anthropic>=0.3.0
langchain-core>=0.3.0

# MCP Integration
langchain-mcp>=0.1.0

# Data Processing
pyyaml>=6.0
pydantic>=2.0

# Neo4j (if direct connection needed)
neo4j>=5.0

# Utilities
python-dotenv>=1.0.0
```

Install using uv:

```bash
uv pip install -r requirements.txt
```

Or using pip:

```bash
pip install -r requirements.txt
```

### Step 4: Install Deep Agents Library

If you need the full Deep Agents training examples:

```bash
# Clone the deep agents repository
git clone https://github.com/langchain-ai/deepagents
cd deepagents

# Install in development mode
uv pip install -e .

# Or with pip
pip install -e .
```

**Note:** For this workflow, the core LangGraph library is sufficient. The Deep Agents repository is optional for learning purposes.

## Neo4j MCP Configuration

### Option 1: Using MCP Config File

Create or edit `~/.config/mcp/config.json`:

```json
{
  "mcpServers": {
    "neo4j-test": {
      "command": "npx",
      "args": [
        "-y",
        "@neo4j/mcp-neo4j-cypher"
      ],
      "env": {
        "NEO4J_URI": "neo4j+s://928872b4.databases.neo4j.io",
        "NEO4J_USERNAME": "neo4j",
        "NEO4J_PASSWORD": "your_password_here"
      }
    },
    "neo4j-prod": {
      "command": "npx",
      "args": [
        "-y",
        "@neo4j/mcp-neo4j-cypher"
      ],
      "env": {
        "NEO4J_URI": "neo4j+s://c32accb7.databases.neo4j.io",
        "NEO4J_USERNAME": "neo4j",
        "NEO4J_PASSWORD": "your_password_here"
      }
    }
  }
}
```

### Option 2: Using Environment Variables

Export Neo4j credentials in your shell:

```bash
export NEO4J_URI="neo4j+s://your-instance.databases.neo4j.io"
export NEO4J_USERNAME="neo4j"
export NEO4J_PASSWORD="your_password"
```

## Verification

### Test Python Installation

```bash
python3 -c "import langgraph; import langchain_anthropic; print('✓ Dependencies installed')"
```

### Test Neo4j MCP Connection

```bash
# Using the workflow script
python deep_agents_report_workflow.py --event test --year 2025 --config config/config_ecomm.yaml --type initial
```

You should see:
```
✓ Connected to Neo4j MCP server: neo4j-test
```

### Test MCP Tools Directly

Create a test script `test_mcp.py`:

```python
from langchain_mcp import MCPToolkit

# Initialize MCP toolkit
toolkit = MCPToolkit(
    server_name="neo4j-test",
    connection_type="stdio"
)

# Get available tools
tools = toolkit.get_tools()
print(f"✓ Found {len(tools)} Neo4j MCP tools")
for tool in tools:
    print(f"  - {tool.name}")
```

Run the test:

```bash
python test_mcp.py
```

Expected output:
```
✓ Found 3 Neo4j MCP tools
  - neo4j-test:get_neo4j_schema
  - neo4j-test:read_neo4j_cypher
  - neo4j-test:write_neo4j_cypher
```

## Usage

### Basic Usage

Generate an initial report:

```bash
python deep_agents_report_workflow.py \
    --event ecomm \
    --year 2025 \
    --config config/config_ecomm.yaml \
    --type initial \
    --output-dir reports
```

Generate an incremental report:

```bash
python deep_agents_report_workflow.py \
    --event ecomm \
    --year 2025 \
    --config config/config_ecomm.yaml \
    --type increment \
    --output-dir reports
```

Generate a post-show analysis:

```bash
python deep_agents_report_workflow.py \
    --event ecomm \
    --year 2025 \
    --config config/config_ecomm.yaml \
    --type post_show \
    --output-dir reports
```

### Using Different Neo4j Servers

```bash
# Use production server
python deep_agents_report_workflow.py \
    --event lva \
    --year 2025 \
    --config config/config_vet_lva.yaml \
    --type initial \
    --neo4j-server neo4j-prod
```

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'langgraph'"

**Solution:**
```bash
# Reinstall dependencies
uv pip install --force-reinstall langgraph langchain-anthropic
```

### Issue: "MCP connection failed"

**Solution:**
1. Verify Neo4j MCP server is installed:
   ```bash
   npx @neo4j/mcp-neo4j-cypher --version
   ```

2. Check MCP config file exists:
   ```bash
   cat ~/.config/mcp/config.json
   ```

3. Test Neo4j connection directly:
   ```bash
   # Install neo4j driver
   pip install neo4j
   
   # Test connection
   python -c "from neo4j import GraphDatabase; driver = GraphDatabase.driver('neo4j+s://your-uri', auth=('neo4j', 'password')); driver.verify_connectivity(); print('✓ Connected')"
   ```

### Issue: "ANTHROPIC_API_KEY not found"

**Solution:**
```bash
# Verify .env file exists and is loaded
cat .env | grep ANTHROPIC_API_KEY

# Export manually if needed
export ANTHROPIC_API_KEY="your_key_here"
```

### Issue: "Permission denied" on script execution

**Solution:**
```bash
# Make script executable
chmod +x deep_agents_report_workflow.py

# Run with python explicitly
python deep_agents_report_workflow.py --help
```

## Advanced Configuration

### Custom LLM Models

Edit the script to use different models:

```python
# In DeepAgentsReportWorkflow.__init__
self.llm = ChatAnthropic(
    model="claude-opus-4-20250514",  # Use Opus for more complex reasoning
    temperature=0
)
```

### Parallel Agent Execution

For faster processing, modify to use async:

```python
import asyncio
from langgraph.prebuilt import create_react_agent

# Convert agents to async
async def run_async():
    # Run planning and data collection in parallel
    planning_task = asyncio.create_task(run_planning_phase())
    data_task = asyncio.create_task(run_data_collection_phase())
    
    await asyncio.gather(planning_task, data_task)
```

### Custom Agent Prompts

Modify agent system prompts in the `create_*_agent()` methods for specialized behavior.

## Next Steps

1. **Read the Example Reports:** Review `reports/report_ecomm_20082025.md` and `reports/report_lva_23092025.md`
2. **Understand Prompts:** Study the prompt files in `reports/prompts/`
3. **Test with Your Data:** Run the workflow with your event configuration
4. **Customize:** Adapt agent prompts and workflow logic for your specific needs

## Support and Resources

- **LangGraph Documentation:** https://langchain-ai.github.io/langgraph/
- **Deep Agents Course:** https://academy.langchain.com/courses/deep-research-with-langgraph
- **Neo4j MCP:** https://github.com/neo4j-contrib/mcp-neo4j
- **MCP Protocol:** https://github.com/langchain-ai/langchain-mcp-adapters

## Project Structure

```
project/
├── deep_agents_report_workflow.py      # Main workflow script
├── requirements.txt                     # Python dependencies
├── README_INSTALLATION.md               # This file
├── .env                                 # Environment variables
├── config/                              # Event configurations
│   ├── config_ecomm.yaml
│   ├── config_vet_lva.yaml
│   ├── config_vet_bva.yaml
│   └── config_cpcn.yaml
├── reports/                             # Generated reports
│   ├── prompts/                         # Report generation prompts
│   │   ├── prompt_initial_run.md
│   │   ├── prompt_increment_run.md
│   │   ├── prompt_post_show.md
│   │   └── reference.md
│   └── deep_agents/                     # Training examples (optional)
│       ├── notebooks/
│       └── src/
└── data/                                # ML pipeline data
    ├── ecomm/
    ├── lva/
    └── bva/
```

## License

This workflow implementation follows the patterns from the LangChain Deep Agents course and is intended for educational and internal use.

---

**Installation complete!** You're ready to generate ML pipeline reports using Deep Agents.
