"""
Deep Agents Workflow for ML Pipeline Report Generation

This script implements a Deep Agents workflow that:
1. Connects to Neo4j via MCP
2. Reads report generation prompts
3. Analyzes ML pipeline execution data
4. Generates comprehensive markdown reports

Author: Senior Python Developer
Date: 2025
"""

import os
import yaml
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

from langchain_anthropic import ChatAnthropic
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from pydantic import BaseModel, Field

# Import MCP adapter for Neo4j
from langchain_mcp import MCPToolkit


class ReportConfig(BaseModel):
    """Configuration for report generation"""
    event_name: str = Field(description="Event name (e.g., 'ecomm', 'lva')")
    event_year: int = Field(description="Event year")
    config_path: str = Field(description="Path to event config YAML file")
    prompt_type: str = Field(description="Type of report: 'initial', 'increment', or 'post_show'")
    output_dir: str = Field(default="reports", description="Output directory for reports")
    neo4j_mcp_server: str = Field(default="neo4j-test", description="MCP server to use")


class WorkflowState(BaseModel):
    """State management for the workflow"""
    config: ReportConfig
    execution_plan: List[str] = Field(default_factory=list)
    neo4j_queries: List[Dict[str, Any]] = Field(default_factory=list)
    report_sections: Dict[str, str] = Field(default_factory=dict)
    final_report: Optional[str] = None


# File I/O tools
@tool
def read_file(file_path: str) -> str:
    """
    Read content from a file.
    
    Args:
        file_path: Path to the file to read
        
    Returns:
        File contents as string
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"


@tool
def write_file(file_path: str, content: str) -> str:
    """
    Write content to a file.
    
    Args:
        file_path: Path to the file to write
        content: Content to write
        
    Returns:
        Success or error message
    """
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Successfully wrote to {file_path}"
    except Exception as e:
        return f"Error writing file: {str(e)}"


@tool
def list_files(directory: str, pattern: str = "*") -> List[str]:
    """
    List files in a directory matching a pattern.
    
    Args:
        directory: Directory path to search
        pattern: Glob pattern to match (default: "*")
        
    Returns:
        List of matching file paths
    """
    try:
        from glob import glob
        path = Path(directory)
        if not path.exists():
            return []
        files = [str(f) for f in path.glob(pattern) if f.is_file()]
        return sorted(files)
    except Exception as e:
        return [f"Error listing files: {str(e)}"]


@tool
def load_yaml_config(config_path: str) -> Dict[str, Any]:
    """
    Load YAML configuration file.
    
    Args:
        config_path: Path to YAML config file
        
    Returns:
        Dictionary containing configuration
    """
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        return {"error": f"Failed to load config: {str(e)}"}


class DeepAgentsReportWorkflow:
    """Main workflow orchestrator using Deep Agents pattern"""
    
    def __init__(self, config: ReportConfig):
        """
        Initialize the workflow.
        
        Args:
            config: Report configuration
        """
        self.config = config
        self.state = WorkflowState(config=config)
        
        # Initialize LLM
        self.llm = ChatAnthropic(
            model="claude-sonnet-4-20250514",
            temperature=0
        )
        
        # Initialize MCP toolkit for Neo4j
        self.neo4j_toolkit = None
        
    def initialize_mcp_connection(self) -> bool:
        """
        Initialize MCP connection to Neo4j server.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Initialize MCPToolkit with stdio connection to neo4j MCP server
            # This assumes mcp-neo4j-cypher is installed and configured
            self.neo4j_toolkit = MCPToolkit(
                server_name=self.config.neo4j_mcp_server,
                connection_type="stdio"
            )
            print(f"✓ Connected to Neo4j MCP server: {self.config.neo4j_mcp_server}")
            return True
        except Exception as e:
            print(f"✗ Failed to connect to Neo4j MCP: {str(e)}")
            return False
    
    def create_planning_agent(self) -> Any:
        """
        Create planning agent that reads prompts and creates execution plan.
        
        Returns:
            LangGraph agent
        """
        system_prompt = """You are a Planning Agent specialized in analyzing ML pipeline report requirements.

Your role is to:
1. Read the report generation prompt
2. Understand the report structure and requirements
3. Create a detailed execution plan (TODO list) for completing the report
4. Identify what data needs to be queried from Neo4j
5. Determine the order of operations

Be thorough and precise in your planning."""

        tools = [read_file, list_files, load_yaml_config]
        
        agent = create_react_agent(
            model=self.llm,
            tools=tools,
            state_modifier=system_prompt
        )
        
        return agent
    
    def create_neo4j_agent(self) -> Any:
        """
        Create Neo4j agent that interacts with the database via MCP.
        
        Returns:
            LangGraph agent with Neo4j MCP tools
        """
        system_prompt = """You are a Neo4j Database Agent specialized in querying graph databases.

Your role is to:
1. Execute Cypher queries against the Neo4j database via MCP
2. Retrieve visitor, session, and recommendation data
3. Calculate metrics and statistics
4. Format query results for report generation

Use the Neo4j MCP tools to interact with the database.
Always verify your queries are correct before executing.
Handle errors gracefully and provide meaningful feedback."""

        # Get Neo4j tools from MCP toolkit
        neo4j_tools = self.neo4j_toolkit.get_tools() if self.neo4j_toolkit else []
        
        # Combine with file tools
        all_tools = neo4j_tools + [read_file, write_file]
        
        agent = create_react_agent(
            model=self.llm,
            tools=all_tools,
            state_modifier=system_prompt
        )
        
        return agent
    
    def create_report_writer_agent(self) -> Any:
        """
        Create report writer agent that generates markdown reports.
        
        Returns:
            LangGraph agent
        """
        system_prompt = """You are a Report Writer Agent specialized in creating comprehensive analysis reports.

Your role is to:
1. Synthesize data from Neo4j queries
2. Apply the report structure from the prompt
3. Generate well-formatted markdown sections
4. Include tables, metrics, and insights
5. Follow the exact format specified in the prompt

Create professional, data-driven reports with clear insights.
Use markdown formatting extensively (headers, tables, bold, lists).
Be precise with numbers and calculations."""

        tools = [write_file, read_file, load_yaml_config]
        
        agent = create_react_agent(
            model=self.llm,
            tools=tools,
            state_modifier=system_prompt
        )
        
        return agent
    
    def get_prompt_path(self) -> str:
        """
        Get the appropriate prompt file path based on report type.
        
        Returns:
            Path to prompt file
        """
        prompt_files = {
            'initial': 'reports/prompts/prompt_initial_run.md',
            'increment': 'reports/prompts/prompt_increment_run.md',
            'post_show': 'reports/prompts/prompt_post_show.md'
        }
        return prompt_files.get(self.config.prompt_type, prompt_files['initial'])
    
    def run_planning_phase(self) -> List[str]:
        """
        Execute planning phase to create execution plan.
        
        Returns:
            List of execution steps
        """
        print("\n" + "="*80)
        print("PHASE 1: PLANNING")
        print("="*80)
        
        planning_agent = self.create_planning_agent()
        prompt_path = self.get_prompt_path()
        
        planning_prompt = f"""Analyze the report generation requirements and create an execution plan.

1. Read the prompt file: {prompt_path}
2. Read the config file: {self.config.config_path}
3. List any previous reports in the reports directory
4. Create a detailed TODO list for generating this report

The report is for {self.config.event_name} {self.config.event_year}.
Report type: {self.config.prompt_type}

Provide the execution plan as a numbered list of specific tasks."""

        result = planning_agent.invoke({"messages": [HumanMessage(content=planning_prompt)]})
        
        # Extract plan from final message
        final_message = result["messages"][-1].content
        print("\n📋 Execution Plan Created:")
        print(final_message)
        
        # Parse plan into list (simple split by lines starting with numbers)
        plan_lines = [line.strip() for line in final_message.split('\n') 
                     if line.strip() and any(line.strip().startswith(str(i)) for i in range(1, 100))]
        
        self.state.execution_plan = plan_lines
        return plan_lines
    
    def run_data_collection_phase(self) -> Dict[str, Any]:
        """
        Execute data collection phase using Neo4j agent.
        
        Returns:
            Dictionary containing collected data
        """
        print("\n" + "="*80)
        print("PHASE 2: DATA COLLECTION")
        print("="*80)
        
        if not self.neo4j_toolkit:
            print("⚠ Warning: Neo4j MCP not initialized. Skipping data collection.")
            return {}
        
        neo4j_agent = self.create_neo4j_agent()
        
        data_collection_prompt = f"""Collect all necessary data from Neo4j for the report.

Based on the execution plan, query the database for:
1. Total visitors (Visitor_this_year nodes)
2. Returning vs new visitor counts
3. Recommendation statistics (IS_RECOMMENDED relationships)
4. Session coverage metrics
5. Top recommended sessions
6. Visitor demographics and attributes
7. Any other metrics specified in the prompt

Event: {self.config.event_name} {self.config.event_year}
Report type: {self.config.prompt_type}

Execute the necessary Cypher queries and save results to a temporary file for the report writer."""

        result = neo4j_agent.invoke({"messages": [HumanMessage(content=data_collection_prompt)]})
        
        print("\n📊 Data Collection Completed")
        return {"status": "completed", "result": result["messages"][-1].content}
    
    def run_report_generation_phase(self) -> str:
        """
        Execute report generation phase.
        
        Returns:
            Path to generated report file
        """
        print("\n" + "="*80)
        print("PHASE 3: REPORT GENERATION")
        print("="*80)
        
        report_writer = self.create_report_writer_agent()
        prompt_path = self.get_prompt_path()
        
        # Determine output filename
        timestamp = datetime.now().strftime("%d%m%Y")
        output_filename = f"report_{self.config.event_name}_{timestamp}.md"
        output_path = os.path.join(self.config.output_dir, output_filename)
        
        report_generation_prompt = f"""Generate the complete report based on the prompt and collected data.

1. Read the prompt template: {prompt_path}
2. Read collected data from previous phase
3. Read configuration: {self.config.config_path}
4. Generate the complete report following the prompt structure
5. Save the report to: {output_path}

Event: {self.config.event_name} {self.config.event_year}
Report type: {self.config.prompt_type}

Ensure the report includes:
- All required sections from the prompt
- Proper markdown formatting
- Tables with data
- Metrics and statistics
- Insights and recommendations

Generate the complete, professional report now."""

        result = report_writer.invoke({"messages": [HumanMessage(content=report_generation_prompt)]})
        
        print(f"\n📄 Report Generated: {output_path}")
        self.state.final_report = output_path
        
        return output_path
    
    def run(self) -> str:
        """
        Execute the complete workflow.
        
        Returns:
            Path to generated report
        """
        print("\n" + "="*80)
        print(f"DEEP AGENTS REPORT WORKFLOW")
        print(f"Event: {self.config.event_name} {self.config.event_year}")
        print(f"Report Type: {self.config.prompt_type}")
        print("="*80)
        
        # Initialize MCP connection
        if not self.initialize_mcp_connection():
            print("\n⚠ Warning: Proceeding without Neo4j MCP connection")
        
        # Phase 1: Planning
        self.run_planning_phase()
        
        # Phase 2: Data Collection
        self.run_data_collection_phase()
        
        # Phase 3: Report Generation
        report_path = self.run_report_generation_phase()
        
        print("\n" + "="*80)
        print("✓ WORKFLOW COMPLETED SUCCESSFULLY")
        print("="*80)
        print(f"\nGenerated Report: {report_path}")
        
        return report_path


def main():
    """Main entry point for the workflow"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Deep Agents workflow for ML pipeline report generation"
    )
    parser.add_argument(
        "--event",
        required=True,
        help="Event name (e.g., 'ecomm', 'lva')"
    )
    parser.add_argument(
        "--year",
        type=int,
        required=True,
        help="Event year"
    )
    parser.add_argument(
        "--config",
        required=True,
        help="Path to event config YAML file"
    )
    parser.add_argument(
        "--type",
        choices=['initial', 'increment', 'post_show'],
        default='initial',
        help="Type of report to generate"
    )
    parser.add_argument(
        "--output-dir",
        default="reports",
        help="Output directory for reports"
    )
    parser.add_argument(
        "--neo4j-server",
        default="neo4j-test",
        help="Neo4j MCP server name"
    )
    
    args = parser.parse_args()
    
    # Create configuration
    config = ReportConfig(
        event_name=args.event,
        event_year=args.year,
        config_path=args.config,
        prompt_type=args.type,
        output_dir=args.output_dir,
        neo4j_mcp_server=args.neo4j_server
    )
    
    # Create and run workflow
    workflow = DeepAgentsReportWorkflow(config)
    report_path = workflow.run()
    
    print(f"\n✓ Report generated successfully: {report_path}")


if __name__ == "__main__":
    main()
