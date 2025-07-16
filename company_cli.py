#!/usr/bin/env python3
"""
Company Classification CLI Tool - Batch Processing Version
Command-line interface for classifying companies using batched processing.
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
import re

# Add the client directory to the path so we can import existing modules
sys.path.insert(0, str(Path(__file__).parent / "client"))

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage
from client.services.ai_service import create_llm_model
from client.services.mcp_service import setup_mcp_client, get_tools_from_client, prepare_server_config
from langgraph.prebuilt import create_react_agent
from client.config import SERVER_CONFIG, DEFAULT_TEMPERATURE, DEFAULT_MAX_TOKENS


# Load environment variables
load_dotenv()

class CompanyClassificationCLI:
    def __init__(self, config_path: Optional[str] = None, batch_size: int = 10):
        """Initialize the CLI tool with configuration."""
        # Default to CLI-specific config file with localhost URLs
        self.config_path = config_path or "cli_servers_config.json"
        self.batch_size = batch_size
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
            print(f"🔌 Connected to {len(prepared_servers)} MCP servers")
            
            # Setup MCP client
            self.client = await setup_mcp_client(prepared_servers)
            self.tools = await get_tools_from_client(self.client)
            
            # Create agent
            self.agent = create_react_agent(self.llm, self.tools)
            
            print(f"✅ Initialized with {len(self.tools)} available tools")
            
        except Exception as e:
            print(f"❌ MCP Connection Error: {str(e)}")
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
            # Create the formatted block exactly like the UI
            company_block = []
            
            # Each field on its own line, exactly like UI
            company_block.append(f"Account Name = {company.get('Account Name', '')}")
            company_block.append(f"Trading Name = {company.get('Trading Name', '')}")
            company_block.append(f"Domain = {company.get('Domain', '')}")
            company_block.append(f"Event = {company.get('Event', '')}")
            
            formatted_lines.append('\n'.join(company_block))
        
        # Join companies with blank line separation
        return '\n\n'.join(formatted_lines)
    
    def create_batch_prompt(self, companies_batch: List[Dict]) -> str:
        """Create the prompt for a batch of companies."""
        company_data = self.format_companies_for_analysis(companies_batch)
        
        return f"""You are a professional data analyst tasked with tagging exhibitor companies with accurate industry and product categories from our established taxonomy.

COMPANY DATA TO ANALYZE:
{company_data}

MANDATORY RESEARCH PROCESS:

1. **Retrieve Complete Taxonomy** (ONCE ONLY):
   - Use search_show_categories tool without any filters to get all available categories

2. **For EACH Company - Research Phase:**
   - Choose research name: Domain > Trading Name > Company Name
   - Use perplexity_search_web tool: "[company name] products services technology offerings"
   - Use google-search tool: "site:[domain] products services" 
   - Identify what the company actually sells/offers

3. **Analysis Phase:**
   - Map company offerings to relevant shows (CAI, DOL, CCSE, BDAIW, DCW)
   - Match findings to EXACT taxonomy pairs from step 1
   - Select up to 4 (Industry | Product) pairs per company
   - Use pairs EXACTLY as they appear - no modifications to spelling, spacing, or characters

4. **Output Requirements:**
   - Generate a markdown table with these columns:
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
    
    def parse_markdown_table(self, response: str) -> List[List[str]]:
        """Parse markdown table response into structured data."""
        lines = response.strip().split('\n')
        table_rows = []
        
        for line in lines:
            if "|" in line and line.strip():
                # Parse markdown table row
                columns = [col.strip() for col in line.split('|')]
                # Remove empty first/last columns from markdown formatting
                if columns and not columns[0]:
                    columns = columns[1:]
                if columns and not columns[-1]:
                    columns = columns[:-1]
                
                # Skip separator lines
                if columns and not all(col == '' or '-' in col for col in columns):
                    table_rows.append(columns)
        
        return table_rows
    
    async def process_batch(self, batch_companies: List[Dict], batch_num: int, total_batches: int) -> List[List[str]]:
        """Process a single batch of companies."""
        print(f"🔄 Processing batch {batch_num}/{total_batches} ({len(batch_companies)} companies)")
        
        try:
            # Create batch prompt
            batch_prompt = self.create_batch_prompt(batch_companies)
            
            # Create conversation memory
            conversation_memory = []
            conversation_memory.append(HumanMessage(content=batch_prompt))
            
            # Run the agent
            response = await self.agent.ainvoke({"messages": conversation_memory})
            
            # Extract the response
            assistant_response = None
            if "messages" in response:
                for msg in response["messages"]:
                    if isinstance(msg, AIMessage) and hasattr(msg, "content") and msg.content:
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
            
            if assistant_response and "|" in assistant_response:
                # Parse the markdown table
                parsed_rows = self.parse_markdown_table(assistant_response)
                print(f"   ✅ Batch {batch_num} completed: {len(parsed_rows)-1} companies processed")  # -1 for header
                return parsed_rows
            else:
                print(f"   ❌ Batch {batch_num} failed: No valid table response")
                return []
                
        except Exception as e:
            print(f"   ❌ Batch {batch_num} error: {str(e)}")
            return []
    
    async def classify_companies_batched(self, companies: List[Dict]) -> tuple[str, List[List[str]]]:
        """Classify companies using batched processing."""
        print(f"🔍 Processing {len(companies)} companies in batches of {self.batch_size}")
        
        # Split companies into batches
        batches = [companies[i:i + self.batch_size] for i in range(0, len(companies), self.batch_size)]
        total_batches = len(batches)
        
        print(f"📊 Created {total_batches} batches")
        
        all_results = []
        markdown_lines = []
        header_added = False
        
        for batch_num, batch_companies in enumerate(batches, 1):
            # Process batch
            batch_results = await self.process_batch(batch_companies, batch_num, total_batches)
            
            if batch_results:
                if not header_added:
                    # Add header from first successful batch
                    all_results.append(batch_results[0])  # Header row
                    markdown_lines.append('|'.join([''] + batch_results[0] + ['']))
                    if len(batch_results) > 1:
                        # Add separator line
                        separator = ['---'] * len(batch_results[0])
                        markdown_lines.append('|'.join([''] + separator + ['']))
                    header_added = True
                
                # Add data rows (skip header if present)
                data_rows = batch_results[1:] if len(batch_results) > 1 and not header_added else batch_results[1:]
                for row in data_rows:
                    all_results.append(row)
                    markdown_lines.append('|'.join([''] + row + ['']))
        
        # Create markdown content
        markdown_content = '\n'.join(markdown_lines)
        
        print(f"✅ Batch processing completed: {len(all_results)-1} companies processed")  # -1 for header
        
        return markdown_content, all_results
    
    def save_csv_results(self, results: List[List[str]], csv_path: str):
        """Save results to CSV file."""
        try:
            with open(csv_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerows(results)
            print(f"💾 CSV results saved to: {csv_path}")
        except Exception as e:
            raise ValueError(f"Error saving CSV results: {e}")
    
    async def save_results(self, markdown_content: str, csv_results: List[List[str]], base_output_path: str):
        """Save the classification results to both MD and CSV files."""
        # Determine file paths
        base_path = Path(base_output_path)
        md_path = base_path.with_suffix('.md')
        csv_path = base_path.with_suffix('.csv')
        
        try:
            # Save markdown file
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            print(f"💾 Markdown results saved to: {md_path}")
            
            # Save CSV file
            if csv_results:
                self.save_csv_results(csv_results, str(csv_path))
            
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
        description="Company Classification CLI Tool - Batch Processing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python company_cli.py --input companies.csv --output results
  python company_cli.py --input companies.csv --output results --batch-size 5
  python company_cli.py --input companies.csv --output results --config custom_config.json
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
        help="Base path for output files (will create .md and .csv files)"
    )
    
    parser.add_argument(
        "--batch-size", "-b",
        type=int,
        default=10,
        help="Number of companies to process in each batch (default: 10)"
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
    cli = CompanyClassificationCLI(config_path=args.config, batch_size=args.batch_size)
    
    try:
        print("🚀 Starting Company Classification CLI Tool - Batch Processing")
        print("=" * 60)
        
        # Setup connections
        await cli.setup_connections()
        
        # Read CSV file
        companies = cli.read_csv_file(args.input)
        
        if not companies:
            print("❌ No valid companies found in the CSV file")
            return 1
        
        # Classify companies in batches
        markdown_content, csv_results = await cli.classify_companies_batched(companies)
        
        # Save results
        await cli.save_results(markdown_content, csv_results, args.output)
        
        # Print summary
        processed_count = len(csv_results) - 1 if csv_results else 0  # -1 for header
        print(f"\n📊 Processing Summary:")
        print(f"   Total companies in file: {len(companies)}")
        print(f"   Successfully processed: {processed_count}")
        print(f"   Batch size used: {args.batch_size}")
        print(f"   Output files: {args.output}.md, {args.output}.csv")
        
        # Print results if verbose
        if args.verbose and markdown_content:
            print("\n" + "=" * 60)
            print("CLASSIFICATION RESULTS:")
            print("=" * 60)
            print(markdown_content)
        
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