# Deep Agents ML Report Workflow - Implementation Guide

## Overview

This guide provides comprehensive instructions for implementing and using the Deep Agents workflow to generate ML pipeline analysis reports with Neo4j MCP integration.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Workflow Components](#workflow-components)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Running the Workflow](#running-the-workflow)
6. [Understanding the Output](#understanding-the-output)
7. [Troubleshooting](#troubleshooting)
8. [Advanced Usage](#advanced-usage)
9. [Best Practices](#best-practices)

---

## Architecture Overview

### Deep Agents Pattern

The workflow implements the Deep Agents pattern with three specialized agents:

```
┌─────────────────────────────────────────────────────────┐
│                   ORCHESTRATOR                          │
│            (DeepAgentsReportWorkflow)                   │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
   ┌────▼───┐   ┌───▼────┐  ┌────▼──────┐
   │Planning│   │ Neo4j  │  │  Report   │
   │ Agent  │   │ Agent  │  │  Writer   │
   └────────┘   └────────┘  └───────────┘
        │            │            │
        │            │            │
   Reads Prompts  Queries DB  Generates MD
   Creates Plan   Via MCP     Formatted Reports
```

### Agent Responsibilities

**Planning Agent:**
- Reads report generation prompts
- Analyzes requirements
- Creates detailed execution plan (TODO list)
- Identifies data needs

**Neo4j Agent:**
- Connects to Neo4j via MCP stdio
- Executes Cypher queries
- Retrieves visitor and session data
- Calculates metrics

**Report Writer Agent:**
- Synthesizes collected data
- Generates markdown reports
- Follows prompt structure precisely
- Formats tables and visualizations

### Neo4j MCP Integration

```
Workflow → MCP Adapter → Neo4j MCP Server → Neo4j Database
           (langchain-mcp)  (mcp-neo4j-cypher)  (Graph DB)
```

The workflow uses **langchain-mcp-adapters** to convert MCP tools into LangChain tools that agents can use.

---

## Workflow Components

### Core Files

```
deep_agents_report_workflow.py  # Main workflow orchestrator
requirements.txt                 # Python dependencies  
test_setup.py                    # Validation tests
examples_usage.py                # Usage examples
README_INSTALLATION.md           # Installation guide
```

### Configuration Files

```
config/
├── config_ecomm.yaml           # ECOMM event configuration
├── config_vet_lva.yaml         # LVA veterinary event
├── config_vet_bva.yaml         # BVA veterinary event
└── config_cpcn.yaml            # CPCN pharmacy event
```

### Report Templates (Prompts)

```
reports/prompts/
├── prompt_initial_run.md       # First-time report generation
├── prompt_increment_run.md     # Incremental updates
├── prompt_post_show.md         # Post-event analysis
└── reference.md                # Quick reference guide
```

---

## Installation

### Step 1: Install Package Manager

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="/Users/$USER/.local/bin:$PATH"
```

### Step 2: Clone/Copy Files

Ensure all workflow files are in your project directory.

### Step 3: Install Python Dependencies

```bash
# Using uv (recommended)
uv pip install -r requirements.txt

# Or using pip
pip install -r requirements.txt
```

### Step 4: Install Neo4j MCP Server

```bash
# Install via npm
npm install -g @neo4j/mcp-neo4j-cypher

# Or via uvx
uvx mcp install neo4j
```

### Step 5: Configure Environment

Create `.env` file:

```env
ANTHROPIC_API_KEY=your_key_here
NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password
```

### Step 6: Configure MCP Server

Create/edit `~/.config/mcp/config.json`:

```json
{
  "mcpServers": {
    "neo4j-test": {
      "command": "npx",
      "args": ["-y", "@neo4j/mcp-neo4j-cypher"],
      "env": {
        "NEO4J_URI": "neo4j+s://928872b4.databases.neo4j.io",
        "NEO4J_USERNAME": "neo4j",
        "NEO4J_PASSWORD": "your_password"
      }
    },
    "neo4j-prod": {
      "command": "npx",
      "args": ["-y", "@neo4j/mcp-neo4j-cypher"],
      "env": {
        "NEO4J_URI": "neo4j+s://c32accb7.databases.neo4j.io",
        "NEO4J_USERNAME": "neo4j",
        "NEO4J_PASSWORD": "your_password"
      }
    }
  }
}
```

### Step 7: Verify Installation

```bash
python test_setup.py
```

Expected output:
```
✓ All tests passed! You're ready to run the workflow.
```

---

## Configuration

### Event Configuration Files

Each event requires a YAML configuration file with:

```yaml
event:
  name: "ecomm"
  year: 2025
  
recommendation:
  min_similarity_score: 0.5
  max_recommendations: 20
  similarity_attributes:
    what_is_your_job_role: 0.6
    what_is_your_industry: 1.0
    
neo4j:
  uri: "neo4j+s://..."
  username: "neo4j"
  password: ""
  show_name: "ecomm"
  node_labels:
    visitor_this_year: "Visitor_this_year"
    session_this_year: "Sessions_this_year"
```

### Neo4j Database Requirements

**Required Nodes:**
- `Visitor_this_year` - Current year registrations
- `Sessions_this_year` - Current year sessions
- `Visitor_last_year_bva` - Previous main event
- `Visitor_last_year_lva` - Previous secondary event
- `Stream` - Session categories

**Required Relationships:**
- `IS_RECOMMENDED` - Recommendations generated by ML pipeline
- `Same_Visitor` - Links current to past attendees
- `attended_session` - Past year attendance

**Post-Show Only:**
- `assisted_this_year` - Actual attendance from badge scans

### Verify Neo4j Data

```cypher
// Check visitor counts
MATCH (v:Visitor_this_year)
RETURN COUNT(v) as total_visitors

// Check recommendations
MATCH ()-[r:IS_RECOMMENDED]->()
RETURN COUNT(r) as total_recommendations

// Check sessions
MATCH (s:Sessions_this_year)
RETURN COUNT(s) as total_sessions
```

---

## Running the Workflow

### Command Line Interface

**Generate Initial Report:**
```bash
python deep_agents_report_workflow.py \
    --event ecomm \
    --year 2025 \
    --config config/config_ecomm.yaml \
    --type initial
```

**Generate Incremental Report:**
```bash
python deep_agents_report_workflow.py \
    --event ecomm \
    --year 2025 \
    --config config/config_ecomm.yaml \
    --type increment
```

**Generate Post-Show Analysis:**
```bash
python deep_agents_report_workflow.py \
    --event ecomm \
    --year 2025 \
    --config config/config_ecomm.yaml \
    --type post_show
```

### Python API

```python
from deep_agents_report_workflow import DeepAgentsReportWorkflow, ReportConfig

# Configure
config = ReportConfig(
    event_name="ecomm",
    event_year=2025,
    config_path="config/config_ecomm.yaml",
    prompt_type="initial",
    output_dir="reports",
    neo4j_mcp_server="neo4j-test"
)

# Run workflow
workflow = DeepAgentsReportWorkflow(config)
report_path = workflow.run()

print(f"Report generated: {report_path}")
```

### Workflow Phases

The workflow executes in three phases:

**Phase 1: Planning**
- Reads prompt template
- Analyzes requirements
- Creates execution plan
- Outputs: TODO list

**Phase 2: Data Collection**
- Connects to Neo4j via MCP
- Executes Cypher queries
- Retrieves metrics
- Outputs: Data files

**Phase 3: Report Generation**
- Synthesizes data
- Applies report structure
- Generates markdown
- Outputs: Final report

---

## Understanding the Output

### Report File Naming

Reports are saved with this naming convention:

```
reports/report_{event}_{DDMMYYYY}.md
```

Examples:
- `report_ecomm_20082025.md` - ECOMM report from Aug 20, 2025
- `report_lva_23092025.md` - LVA report from Sep 23, 2025

### Report Structure

**Initial Run Report Sections:**
1. Executive Summary
2. Visitor Demographics and Retention
3. Data Completeness and Quality
4. Recommendation System Analysis
5. Attribute Correlations and Patterns
6. System Performance Issues
7. Recommendations for Improvement
8. Conclusion

**Incremental Run Report Sections:**
1. Executive Summary (with comparisons)
2. Progressive Demographics Analysis
3. Progressive Recommendation Performance
4. Sessions Never Recommended Tracking
5. Key Insights from Progressive Analysis
6. Recommendations Building on Previous Analysis
7. Growth Rate and Scaling Analysis
8. Conclusion (three-period summary)

**Post-Show Analysis Sections:**
1. Executive Summary (performance assessment)
2. Complete Visitor Journey
3. Recommendation System Performance
4. Pre-Show Predictions vs Post-Show Reality
5. Show-Specific Breakdown
6. Critical Issues Deep Dive
7. What Worked Well
8. Root Cause Analysis
9. Actionable Recommendations for Next Event
10. Success Metrics for Next Event

### Key Metrics in Reports

- **Total Visitors**: Number of registered attendees
- **Returning %**: Percentage who attended previous events
- **Total Recommendations**: Number of session recommendations generated
- **Coverage %**: Percentage of sessions with recommendations
- **Concentration %**: Top session recommended to X% of visitors
- **Hit Rate**: % of visitors who attended ≥1 recommended session
- **Conversion Rate**: % of recommendations that resulted in attendance

---

## Troubleshooting

### Common Issues

**Issue: "ModuleNotFoundError: No module named 'langgraph'"**

Solution:
```bash
uv pip install --force-reinstall langgraph langchain-anthropic langchain-mcp
```

**Issue: "MCP connection failed"**

Solutions:
1. Verify MCP server is installed:
   ```bash
   npx @neo4j/mcp-neo4j-cypher --version
   ```

2. Check MCP config file:
   ```bash
   cat ~/.config/mcp/config.json
   ```

3. Test Neo4j connection:
   ```bash
   python -c "from neo4j import GraphDatabase; driver = GraphDatabase.driver('neo4j+s://uri', auth=('neo4j', 'pass')); driver.verify_connectivity(); print('Connected')"
   ```

**Issue: "No recommendations found in database"**

Solution:
1. Verify ML pipeline has run
2. Check Neo4j for `IS_RECOMMENDED` relationships:
   ```cypher
   MATCH ()-[r:IS_RECOMMENDED]->()
   RETURN COUNT(r)
   ```

**Issue: "Report file empty or incomplete"**

Solutions:
1. Check workflow logs for errors
2. Verify all three phases completed
3. Ensure prompt files are accessible
4. Check output directory permissions

### Debug Mode

Add debug logging to the workflow:

```python
import logging

logging.basicConfig(level=logging.DEBUG)

workflow = DeepAgentsReportWorkflow(config)
workflow.run()
```

---

## Advanced Usage

### Custom Agent Behavior

Modify agent system prompts:

```python
def create_custom_planning_agent(self):
    system_prompt = """Custom planning instructions here"""
    
    tools = [read_file, list_files, load_yaml_config]
    
    return create_react_agent(
        model=self.llm,
        tools=tools,
        state_modifier=system_prompt
    )
```

### Multiple Event Batch Processing

```python
from deep_agents_report_workflow import DeepAgentsReportWorkflow, ReportConfig

events = ["ecomm", "lva", "bva"]
reports = []

for event in events:
    config = ReportConfig(
        event_name=event,
        event_year=2025,
        config_path=f"config/config_{event}.yaml",
        prompt_type="initial"
    )
    
    workflow = DeepAgentsReportWorkflow(config)
    report_path = workflow.run()
    reports.append(report_path)
```

### Custom Neo4j Queries

Add custom queries to the Neo4j agent:

```python
@tool
def custom_neo4j_query(query: str) -> Dict[str, Any]:
    """Execute custom Cypher query"""
    # Implementation here
    pass
```

### Using Different LLM Models

```python
from langchain_anthropic import ChatAnthropic

# Use Claude Opus for more complex reasoning
workflow.llm = ChatAnthropic(
    model="claude-opus-4-20250514",
    temperature=0.1
)
```

---

## Best Practices

### 1. Version Control

Commit generated reports to version control:

```bash
git add reports/report_*.md
git commit -m "Add report for ECOMM 2025-08-20"
```

### 2. Report Review Workflow

1. Generate report
2. Review metrics and insights
3. Validate against Neo4j data
4. Implement recommendations
5. Document changes in config
6. Re-run pipeline
7. Generate incremental report

### 3. Neo4j Data Quality

Before generating reports:
- Verify all nodes and relationships exist
- Check for data completeness
- Validate recommendation counts
- Ensure timestamps are correct

### 4. Configuration Management

- Keep separate configs per event
- Version control config files
- Document configuration changes
- Use descriptive commit messages

### 5. Testing Strategy

Test workflow components independently:

```bash
# Test dependencies
python test_setup.py

# Test planning phase only
python -c "from deep_agents_report_workflow import *; workflow = DeepAgentsReportWorkflow(config); workflow.run_planning_phase()"

# Test with sample data
python deep_agents_report_workflow.py --event test --year 2025 --config config/config_ecomm.yaml --type initial
```

### 6. Error Handling

Implement robust error handling:

```python
try:
    workflow = DeepAgentsReportWorkflow(config)
    report_path = workflow.run()
except Exception as e:
    logging.error(f"Workflow failed: {e}")
    # Implement recovery logic
```

### 7. Performance Optimization

- Use batch queries for large datasets
- Cache frequently accessed data
- Limit agent tool calls when possible
- Monitor token usage

### 8. Security

- Never commit `.env` file
- Use environment variables for credentials
- Restrict Neo4j database access
- Audit agent actions in production

---

## Workflow Decision Tree

```
START
  ↓
Is this the first time running recommendations?
  ├─ YES → Use prompt_initial_run.md
  │         Generate baseline report
  │         Analyze data quality
  │         Identify initial issues
  │
  └─ NO → Has the event occurred?
          ├─ YES → Use prompt_post_show.md
          │         Generate post-show analysis
          │         Compare predictions vs reality
          │         Calculate hit rates
          │         Root cause analysis
          │
          └─ NO → Use prompt_increment_run.md
                   Generate incremental report
                   Compare to previous runs
                   Track implementation
                   Analyze trends
```

---

## Integration with ML Pipeline

### Workflow Integration Points

```
ML Pipeline Execution
  ↓
[Generate Recommendations]
  ↓
[Write to Neo4j]
  ↓
[Trigger Deep Agents Workflow] ← You are here
  ↓
[Generate Report]
  ↓
[Review & Implement]
  ↓
[Update Configuration]
  ↓
[Re-run ML Pipeline]
```

### Automated Workflow Trigger

```python
# In your ML pipeline
def run_ml_pipeline(event, config_path):
    # 1. Run recommendation generation
    generate_recommendations(event, config_path)
    
    # 2. Write to Neo4j
    write_to_neo4j(recommendations)
    
    # 3. Trigger report generation
    from deep_agents_report_workflow import DeepAgentsReportWorkflow, ReportConfig
    
    report_config = ReportConfig(
        event_name=event,
        event_year=2025,
        config_path=config_path,
        prompt_type="initial"
    )
    
    workflow = DeepAgentsReportWorkflow(report_config)
    report_path = workflow.run()
    
    return report_path
```

---

## Next Steps

1. **Complete Installation** - Follow [README_INSTALLATION.md](README_INSTALLATION.md)
2. **Run Tests** - Execute `python test_setup.py`
3. **Review Examples** - Study `examples_usage.py`
4. **Generate First Report** - Run workflow with your event data
5. **Review Output** - Analyze generated report
6. **Implement Recommendations** - Update configuration
7. **Iterate** - Generate incremental reports

---

## Support and Resources

- **LangGraph Documentation**: https://langchain-ai.github.io/langgraph/
- **Deep Agents Course**: https://academy.langchain.com/courses/deep-research-with-langgraph
- **Neo4j MCP**: https://github.com/neo4j-contrib/mcp-neo4j
- **MCP Protocol**: https://modelcontextprotocol.io/
- **LangChain MCP Adapters**: https://github.com/langchain-ai/langchain-mcp-adapters

---

**Implementation Guide Complete**

You now have all the information needed to implement and use the Deep Agents ML Report Workflow. Start with installation, then proceed through the examples to generate your first report.
