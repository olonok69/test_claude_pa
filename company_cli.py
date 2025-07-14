#!/usr/bin/env python3
"""
Company Classification CLI Tool
Command-line interface for classifying companies using the existing MCP server infrastructure.
"""

import argparse
import asyncio
import csv
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional
import traceback
import importlib.util

# Add the client directory to the path so we can import existing modules
sys.path.insert(0, str(Path(__file__).parent / "client"))

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from services.ai_service import create_llm_model
from services.mcp_service import setup_mcp_client, get_tools_from_client, prepare_server_config
from services.chat_service import get_clean_conversation_memory
from langgraph.prebuilt import create_react_agent
from config import SERVER_CONFIG, DEFAULT_TEMPERATURE, DEFAULT_MAX_TOKENS

# Load environment variables
load_dotenv()

class CompanyClassificationCLI:
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the CLI tool with configuration."""
        self.config_path = config_path or os.path.join( "cli_servers_config.json")
        self.client = None
        self.agent = None
        self.tools = []
        self.llm = None
        
    async def setup_connections(self):
        """Set up MCP client connections and initialize the agent."""
        print("🔧 Setting up MCP connections...")
        
        # Validate environment variables
        if not self._validate_environment():
            raise ValueError("Missing required environment variables")
        
        # Create LLM instance
        llm_provider = "OpenAI" if os.getenv("OPENAI_API_KEY") else "Azure OpenAI"
        try:
            self.llm = create_llm_model(
                llm_provider,
                temperature=DEFAULT_TEMPERATURE,
                max_tokens=DEFAULT_MAX_TOKENS
            )
            print(f"✅ LLM initialized: {llm_provider}")
        except Exception as e:
            raise ValueError(f"Failed to initialize LLM: {e}")
        
        # Prepare server configuration
        try:
            # Load server configuration
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    server_config = json.load(f)
                servers = server_config.get('mcpServers', {})
            else:
                servers = SERVER_CONFIG['mcpServers']
            
            prepared_servers = prepare_server_config(servers)
            print(f"🔌 Prepared {len(prepared_servers)} server configurations")
            
            # Setup MCP client
            self.client = await setup_mcp_client(prepared_servers)
            self.tools = await get_tools_from_client(self.client)
            
            # Create agent
            self.agent = create_react_agent(self.llm, self.tools)
            
            print(f"✅ Connected to MCP servers with {len(self.tools)} tools")
            self._print_available_tools()
            
        except Exception as e:
            raise ValueError(f"Failed to setup MCP connections: {e}")
    
    def _validate_environment(self) -> bool:
        """Validate that required environment variables are set."""
        required_vars = []
        
        # Check AI provider credentials
        if not os.getenv("OPENAI_API_KEY"):
            azure_vars = ["AZURE_API_KEY", "AZURE_ENDPOINT", "AZURE_DEPLOYMENT", "AZURE_API_VERSION"]
            if not all(os.getenv(var) for var in azure_vars):
                required_vars.extend(["OPENAI_API_KEY or Azure OpenAI credentials"])
        
        # Check Google Search credentials
        if not os.getenv("GOOGLE_API_KEY"):
            required_vars.append("GOOGLE_API_KEY")
        if not os.getenv("GOOGLE_SEARCH_ENGINE_ID"):
            required_vars.append("GOOGLE_SEARCH_ENGINE_ID")
        
        # Check Perplexity credentials
        if not os.getenv("PERPLEXITY_API_KEY"):
            required_vars.append("PERPLEXITY_API_KEY")
        
        if required_vars:
            print(f"❌ Missing required environment variables: {', '.join(required_vars)}")
            return False
        
        return True
    
    async def _check_server_accessibility(self, servers: Dict[str, Dict]):
        """Check if servers are accessible before attempting connection."""
        for name, config in servers.items():
            transport = config.get('transport', 'unknown')
            
            if transport == 'sse':
                url = config.get('url', '')
                if url:
                    try:
                        import aiohttp
                        async with aiohttp.ClientSession() as session:
                            # Check if server is responding
                            health_url = url.replace('/sse', '/health')
                            async with session.get(health_url, timeout=5) as response:
                                if response.status == 200:
                                    print(f"   ✅ {name}: Server is responding at {health_url}")
                                else:
                                    print(f"   ❌ {name}: Server returned status {response.status}")
                    except Exception as e:
                        print(f"   ❌ {name}: Cannot reach server at {url} - {e}")
                else:
                    print(f"   ❌ {name}: No URL configured")
            
            elif transport == 'stdio':
                command = config.get('command', '')
                args = config.get('args', [])
                try:
                    # Check if the stdio server module can be imported
                    if args and args[0] == '-m':
                        module_name = args[1]
                        print(f"   🔍 {name}: Checking stdio module: {module_name}")
                        
                        # Try to import the module
                        import importlib
                        try:
                            spec = importlib.util.find_spec(module_name)
                            if spec is None:
                                print(f"   ❌ {name}: Module {module_name} not found")
                            else:
                                print(f"   ✅ {name}: Module {module_name} found at {spec.origin}")
                        except Exception as e:
                            print(f"   ❌ {name}: Error checking module {module_name}: {e}")
                    else:
                        print(f"   🔍 {name}: stdio command: {command} {args}")
                except Exception as e:
                    print(f"   ❌ {name}: Error checking stdio server: {e}")
            else:
                print(f"   ❌ {name}: Unknown transport type: {transport}")
    
    def _print_available_tools(self):
        """Print available tools for debugging."""
        google_tools = []
        perplexity_tools = []
        company_tagging_tools = []
        
        for tool in self.tools:
            tool_name = tool.name.lower()
            if any(keyword in tool_name for keyword in ['google-search', 'read-webpage', 'google']):
                google_tools.append(tool.name)
            elif any(keyword in tool_name for keyword in ['perplexity', 'perplexity_search']):
                perplexity_tools.append(tool.name)
            elif any(keyword in tool_name for keyword in ['search_show_categories', 'company', 'taxonomy']):
                company_tagging_tools.append(tool.name)
        
        if google_tools:
            print(f"  🔍 Google Search: {', '.join(google_tools)}")
        if perplexity_tools:
            print(f"  🔮 Perplexity: {', '.join(perplexity_tools)}")
        if company_tagging_tools:
            print(f"  📊 Company Tagging: {', '.join(company_tagging_tools)}")
    
    def read_csv_file(self, csv_path: str) -> List[Dict]:
        """Read and parse the CSV file."""
        print(f"📖 Reading CSV file: {csv_path}")
        
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"CSV file not found: {csv_path}")
        
        companies = []
        try:
            with open(csv_path, 'r', encoding='utf-8', newline='') as csvfile:
                # Try to detect the delimiter
                sample = csvfile.read(1024)
                csvfile.seek(0)
                sniffer = csv.Sniffer()
                delimiter = sniffer.sniff(sample).delimiter
                
                reader = csv.DictReader(csvfile, delimiter=delimiter)
                
                for row_num, row in enumerate(reader, 1):
                    # Clean and validate row data
                    cleaned_row = {k.strip(): v.strip() if v else "" for k, v in row.items()}
                    
                    # Check for required columns
                    required_columns = ['Account Name', 'Trading Name', 'Domain', 'Event']
                    missing_columns = [col for col in required_columns if col not in cleaned_row]
                    
                    if missing_columns:
                        print(f"⚠️  Row {row_num}: Missing columns {missing_columns}, skipping...")
                        continue
                    
                    # Only add rows that have at least an Account Name
                    if cleaned_row.get('Account Name'):
                        companies.append(cleaned_row)
                    else:
                        print(f"⚠️  Row {row_num}: No Account Name, skipping...")
            
            print(f"✅ Successfully read {len(companies)} companies from CSV")
            return companies
            
        except Exception as e:
            raise ValueError(f"Error reading CSV file: {e}")
    
    def format_companies_for_analysis(self, companies: List[Dict]) -> str:
        """Format companies data for the analysis prompt."""
        formatted_lines = []
        
        for company in companies:
            # Create the formatted line similar to the UI example
            parts = []
            
            if company.get('Account Name'):
                parts.append(f"Account Name = {company['Account Name']}")
            
            if company.get('Trading Name'):
                parts.append(f"Trading Name = {company['Trading Name']}")
            else:
                parts.append("Trading Name = ")
            
            if company.get('Domain'):
                parts.append(f"Domain = {company['Domain']}")
            else:
                parts.append("Domain = ")
            
            if company.get('Product/Service Type'):
                parts.append(f"Product/Service Type = {company['Product/Service Type']}")
            else:
                parts.append("Product/Service Type = ")
            
            if company.get('Industry'):
                parts.append(f"Industry = {company['Industry']}")
            else:
                parts.append("Industry = ")
            
            if company.get('Event'):
                parts.append(f"Event = {company['Event']}")
            else:
                parts.append("Event = ")
            
            formatted_lines.append(" ".join(parts))
        
        return "\n".join(formatted_lines)
    
    async def classify_companies(self, companies: List[Dict]) -> str:
        """Classify companies using the MCP server infrastructure."""
        print(f"🔍 Classifying {len(companies)} companies...")
        
        # Format companies for analysis
        company_data = self.format_companies_for_analysis(companies)
        
        # Create the company tagging prompt (similar to the UI implementation)
        company_tagging_prompt = f"""You are a professional data analyst tasked with tagging exhibitor companies with accurate industry and product categories from our established taxonomy.

COMPANY DATA TO ANALYZE:
{company_data}

MANDATORY RESEARCH PROCESS:

1. **Retrieve Complete Taxonomy** (ONCE ONLY):
   - Use search_show_categories tool without any filters to get all available categories

2. **For EACH Company - Research Phase:**
   - Choose research name: Domain > Trading Name > Company Name
   - Use google-search tool: "site:[domain] products services" 
   - Use perplexity_search_web tool: "[company name] products services technology offerings"
   - Identify what the company actually sells/offers

3. **Analysis Phase:**
   - Map company offerings to relevant shows (CAI, DOL, CCSE, BDAIW, DCW)
   - Match findings to EXACT taxonomy pairs from step 1
   - Select up to 4 (Industry | Product) pairs per company
   - Use pairs EXACTLY as they appear - no modifications to spelling, spacing, or characters

4. **Output Requirements:**
   - Generate ONLY a markdown table with these columns:
   | Company Name | Trading Name | Tech Industry 1 | Tech Product 1 | Tech Industry 2 | Tech Product 2 | Tech Industry 3 | Tech Product 3 | Tech Industry 4 | Tech Product 4 |
   - Do NOT provide any additional text, explanations, or context
   - Do NOT show research details or tool executions
   - ONLY the markdown table

CRITICAL RULES:
- MUST use both google-search AND perplexity_search_web for each company
- MUST use search_show_categories to get taxonomy before starting
- Use taxonomy pairs EXACTLY as written
- Output ONLY the markdown table, nothing else

Begin the systematic analysis now."""
        
        try:
            # Create conversation memory
            conversation_memory = []
            conversation_memory.append(HumanMessage(content=company_tagging_prompt))
            
            # Run the agent
            print("🤖 Running AI agent for company classification...")
            response = await self.agent.ainvoke({"messages": conversation_memory})
            
            # Extract response
            assistant_response = None
            if "messages" in response:
                for msg in response["messages"]:
                    if hasattr(msg, "content") and msg.content:
                        assistant_response = str(msg.content)
                        # Look for markdown table in the response
                        if "|" in assistant_response and "Company Name" in assistant_response:
                            # Extract just the table part
                            lines = assistant_response.split('\n')
                            table_lines = []
                            in_table = False
                            for line in lines:
                                if "|" in line and ("Company Name" in line or "Tech Industry" in line):
                                    in_table = True
                                if in_table and "|" in line:
                                    table_lines.append(line.strip())
                                elif in_table and not line.strip():
                                    continue
                                elif in_table and "|" not in line.strip() and line.strip():
                                    break
                            
                            if table_lines:
                                assistant_response = '\n'.join(table_lines)
                        break
            
            if assistant_response:
                print("✅ Company classification completed!")
                return assistant_response
            else:
                raise ValueError("No response generated from the agent")
                
        except Exception as e:
            raise ValueError(f"Error during company classification: {e}")
    
    async def save_results(self, results: str, output_path: str):
        """Save the classification results to a file."""
        print(f"💾 Saving results to: {output_path}")
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(results)
            print("✅ Results saved successfully!")
        except Exception as e:
            raise ValueError(f"Error saving results: {e}")
    
    async def cleanup(self):
        """Clean up resources."""
        if self.client:
            try:
                await self.client.__aexit__(None, None, None)
                print("🧹 Cleaned up MCP connections")
            except Exception as e:
                print(f"⚠️  Error during cleanup: {e}")

async def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="Company Classification CLI Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python company_cli.py --input companies.csv --output results.md
  python company_cli.py --input companies.csv --output results.md --config custom_config.json
  python company_cli.py --input companies.csv --output results.md --verbose
        """
    )
    
    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Path to the input CSV file with company data"
    )
    
    parser.add_argument(
        "--output", "-o",
        required=True,
        help="Path to the output file for classification results"
    )
    
    parser.add_argument(
        "--config", "-c",
        help="Path to custom server configuration JSON file"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    
    args = parser.parse_args()
    
    # Initialize CLI tool
    cli = CompanyClassificationCLI(config_path=args.config)
    
    try:
        print("🚀 Starting Company Classification CLI Tool")
        print("=" * 50)
        
        # Setup connections
        await cli.setup_connections()
        
        # Read CSV file
        companies = cli.read_csv_file(args.input)
        
        if not companies:
            print("❌ No valid companies found in the CSV file")
            return 1
        
        # Classify companies
        results = await cli.classify_companies(companies)
        
        # Save results
        await cli.save_results(results, args.output)
        
        # Print results if verbose
        if args.verbose:
            print("\n" + "=" * 50)
            print("CLASSIFICATION RESULTS:")
            print("=" * 50)
            print(results)
        
        print("\n✅ Company classification completed successfully!")
        return 0
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        if args.verbose:
            print("\nFull traceback:")
            traceback.print_exc()
        return 1
    
    finally:
        await cli.cleanup()

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))