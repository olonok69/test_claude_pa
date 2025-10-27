"""
Example Usage Scripts for Deep Agents ML Report Workflow

This file contains example commands and use cases for running the workflow.

Author: Senior Python Developer
Date: 2025
"""

# ==============================================================================
# EXAMPLE 1: Generate Initial Report for ECOMM Event
# ==============================================================================

"""
First-time report generation for the ECOMM event.

This generates the initial pre-show report analyzing:
- Visitor demographics
- Recommendation coverage
- Data quality
- System configuration
"""

# Command line:
# python deep_agents_report_workflow.py \
#     --event ecomm \
#     --year 2025 \
#     --config config/config_ecomm.yaml \
#     --type initial \
#     --output-dir reports

# Python API:
if __name__ == "__main__":
    from deep_agents_report_workflow import DeepAgentsReportWorkflow, ReportConfig
    
    config = ReportConfig(
        event_name="ecomm",
        event_year=2025,
        config_path="config/config_ecomm.yaml",
        prompt_type="initial",
        output_dir="reports",
        neo4j_mcp_server="neo4j-test"
    )
    
    workflow = DeepAgentsReportWorkflow(config)
    report_path = workflow.run()
    print(f"✓ Report generated: {report_path}")


# ==============================================================================
# EXAMPLE 2: Generate Incremental Report (New Visitors Added)
# ==============================================================================

"""
Incremental report after new visitors have registered.

This generates a progressive analysis comparing:
- Current vs previous runs
- Implementation tracking of recommendations
- Trend analysis
"""

# Command line:
# python deep_agents_report_workflow.py \
#     --event ecomm \
#     --year 2025 \
#     --config config/config_ecomm.yaml \
#     --type increment \
#     --output-dir reports

# Python API:
def generate_increment_report():
    from deep_agents_report_workflow import DeepAgentsReportWorkflow, ReportConfig
    
    config = ReportConfig(
        event_name="ecomm",
        event_year=2025,
        config_path="config/config_ecomm.yaml",
        prompt_type="increment",
        output_dir="reports",
        neo4j_mcp_server="neo4j-test"
    )
    
    workflow = DeepAgentsReportWorkflow(config)
    return workflow.run()


# ==============================================================================
# EXAMPLE 3: Generate Post-Show Analysis
# ==============================================================================

"""
Post-event comprehensive analysis.

This requires:
- Badge scan data processed
- `assisted_this_year` relationships in Neo4j
- All previous pre-show reports available

Analyzes:
- Recommendation hit rates
- Actual vs predicted attendance
- Root cause analysis
- Success metrics
"""

# Command line:
# python deep_agents_report_workflow.py \
#     --event ecomm \
#     --year 2025 \
#     --config config/config_ecomm.yaml \
#     --type post_show \
#     --output-dir reports

# Python API:
def generate_post_show_report():
    from deep_agents_report_workflow import DeepAgentsReportWorkflow, ReportConfig
    
    config = ReportConfig(
        event_name="ecomm",
        event_year=2025,
        config_path="config/config_ecomm.yaml",
        prompt_type="post_show",
        output_dir="reports",
        neo4j_mcp_server="neo4j-test"
    )
    
    workflow = DeepAgentsReportWorkflow(config)
    return workflow.run()


# ==============================================================================
# EXAMPLE 4: LVA Event Reports
# ==============================================================================

"""
Generate reports for the LVA veterinary event.
"""

# Initial report
# python deep_agents_report_workflow.py \
#     --event lva \
#     --year 2025 \
#     --config config/config_vet_lva.yaml \
#     --type initial \
#     --neo4j-server neo4j-prod


# ==============================================================================
# EXAMPLE 5: BVA Event Reports
# ==============================================================================

"""
Generate reports for the BVA veterinary event.
"""

# Initial report
# python deep_agents_report_workflow.py \
#     --event bva \
#     --year 2025 \
#     --config config/config_vet_bva.yaml \
#     --type initial \
#     --neo4j-server neo4j-prod


# ==============================================================================
# EXAMPLE 6: Custom Output Directory
# ==============================================================================

"""
Save reports to a custom location.
"""

# python deep_agents_report_workflow.py \
#     --event ecomm \
#     --year 2025 \
#     --config config/config_ecomm.yaml \
#     --type initial \
#     --output-dir /custom/path/reports


# ==============================================================================
# EXAMPLE 7: Batch Processing Multiple Events
# ==============================================================================

def batch_generate_reports():
    """
    Generate reports for multiple events in sequence.
    """
    from deep_agents_report_workflow import DeepAgentsReportWorkflow, ReportConfig
    
    events = [
        {
            "name": "ecomm",
            "config": "config/config_ecomm.yaml",
            "server": "neo4j-test"
        },
        {
            "name": "lva",
            "config": "config/config_vet_lva.yaml",
            "server": "neo4j-prod"
        },
        {
            "name": "bva",
            "config": "config/config_vet_bva.yaml",
            "server": "neo4j-prod"
        },
    ]
    
    reports = []
    
    for event in events:
        config = ReportConfig(
            event_name=event["name"],
            event_year=2025,
            config_path=event["config"],
            prompt_type="initial",
            output_dir="reports",
            neo4j_mcp_server=event["server"]
        )
        
        workflow = DeepAgentsReportWorkflow(config)
        report_path = workflow.run()
        reports.append(report_path)
        
        print(f"✓ Generated report for {event['name']}: {report_path}")
    
    return reports


# ==============================================================================
# EXAMPLE 8: Programmatic Workflow with Custom Agent Behavior
# ==============================================================================

def custom_workflow_example():
    """
    Example of customizing the workflow programmatically.
    """
    from deep_agents_report_workflow import DeepAgentsReportWorkflow, ReportConfig
    from langchain_anthropic import ChatAnthropic
    
    config = ReportConfig(
        event_name="ecomm",
        event_year=2025,
        config_path="config/config_ecomm.yaml",
        prompt_type="initial",
        output_dir="reports",
        neo4j_mcp_server="neo4j-test"
    )
    
    workflow = DeepAgentsReportWorkflow(config)
    
    # Custom LLM configuration
    workflow.llm = ChatAnthropic(
        model="claude-opus-4-20250514",  # Use Opus for complex reasoning
        temperature=0.1  # Slight temperature for creativity
    )
    
    # Initialize MCP
    if not workflow.initialize_mcp_connection():
        print("Warning: Proceeding without MCP")
    
    # Run individual phases with custom logic
    print("Phase 1: Planning")
    plan = workflow.run_planning_phase()
    
    # Custom logic between phases
    print(f"Execution plan has {len(plan)} steps")
    
    print("Phase 2: Data Collection")
    data = workflow.run_data_collection_phase()
    
    print("Phase 3: Report Generation")
    report_path = workflow.run_report_generation_phase()
    
    return report_path


# ==============================================================================
# EXAMPLE 9: Testing Without Neo4j MCP
# ==============================================================================

def test_without_mcp():
    """
    Test the workflow without Neo4j MCP connection.
    Useful for development and testing agent logic.
    """
    from deep_agents_report_workflow import DeepAgentsReportWorkflow, ReportConfig
    
    config = ReportConfig(
        event_name="test",
        event_year=2025,
        config_path="config/config_ecomm.yaml",
        prompt_type="initial",
        output_dir="reports_test",
        neo4j_mcp_server="non-existent"  # Will fail gracefully
    )
    
    workflow = DeepAgentsReportWorkflow(config)
    
    # This will warn but continue
    workflow.initialize_mcp_connection()
    
    # Run planning phase only
    plan = workflow.run_planning_phase()
    print(f"Execution plan created: {len(plan)} steps")


# ==============================================================================
# EXAMPLE 10: Complete Workflow with Error Handling
# ==============================================================================

def robust_workflow_example():
    """
    Production-ready workflow with comprehensive error handling.
    """
    import sys
    from deep_agents_report_workflow import DeepAgentsReportWorkflow, ReportConfig
    
    try:
        # Configuration
        config = ReportConfig(
            event_name="ecomm",
            event_year=2025,
            config_path="config/config_ecomm.yaml",
            prompt_type="initial",
            output_dir="reports",
            neo4j_mcp_server="neo4j-test"
        )
        
        # Create workflow
        workflow = DeepAgentsReportWorkflow(config)
        
        # Run workflow
        print("Starting Deep Agents workflow...")
        report_path = workflow.run()
        
        # Verify output
        if os.path.exists(report_path):
            file_size = os.path.getsize(report_path)
            print(f"\n✓ Success!")
            print(f"  Report: {report_path}")
            print(f"  Size: {file_size:,} bytes")
            return report_path
        else:
            print(f"\n✗ Error: Report file not created")
            return None
            
    except KeyboardInterrupt:
        print("\n\n⚠ Workflow interrupted by user")
        sys.exit(1)
        
    except Exception as e:
        print(f"\n✗ Workflow failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def verify_prerequisites():
    """
    Verify all prerequisites before running workflow.
    """
    import os
    from pathlib import Path
    
    checks = []
    
    # Check Python version
    import sys
    python_version = sys.version_info
    checks.append(("Python 3.11+", python_version >= (3, 11)))
    
    # Check dependencies
    try:
        import langgraph
        checks.append(("LangGraph installed", True))
    except ImportError:
        checks.append(("LangGraph installed", False))
    
    try:
        import langchain_anthropic
        checks.append(("LangChain Anthropic installed", True))
    except ImportError:
        checks.append(("LangChain Anthropic installed", False))
    
    # Check environment variables
    checks.append(("ANTHROPIC_API_KEY set", bool(os.getenv("ANTHROPIC_API_KEY"))))
    
    # Check config files exist
    config_dir = Path("config")
    checks.append(("Config directory exists", config_dir.exists()))
    
    # Check prompts directory
    prompts_dir = Path("reports/prompts")
    checks.append(("Prompts directory exists", prompts_dir.exists()))
    
    # Print results
    print("\nPrerequisite Checks:")
    print("-" * 50)
    for check_name, passed in checks:
        status = "✓" if passed else "✗"
        print(f"{status} {check_name}")
    
    all_passed = all(passed for _, passed in checks)
    print("-" * 50)
    print(f"Status: {'READY' if all_passed else 'NOT READY'}\n")
    
    return all_passed


# ==============================================================================
# MAIN EXECUTION
# ==============================================================================

if __name__ == "__main__":
    import sys
    
    print("Deep Agents ML Report Workflow - Example Usage")
    print("=" * 60)
    
    # Verify prerequisites
    if not verify_prerequisites():
        print("\n⚠ Prerequisites not met. Please run:")
        print("  1. uv pip install -r requirements.txt")
        print("  2. Set ANTHROPIC_API_KEY in .env file")
        print("  3. Configure Neo4j MCP server")
        sys.exit(1)
    
    print("\nTo run the workflow, use one of these commands:\n")
    print("1. Initial Report:")
    print("   python deep_agents_report_workflow.py --event ecomm --year 2025 --config config/config_ecomm.yaml --type initial\n")
    print("2. Incremental Report:")
    print("   python deep_agents_report_workflow.py --event ecomm --year 2025 --config config/config_ecomm.yaml --type increment\n")
    print("3. Post-Show Analysis:")
    print("   python deep_agents_report_workflow.py --event ecomm --year 2025 --config config/config_ecomm.yaml --type post_show\n")
    print("\nOr run this script to see examples!")
