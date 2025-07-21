#!/usr/bin/env python3
"""
Simple Perplexity Company Classification CLI Tool
Direct replacement of Google search with Perplexity search - keeping everything else identical.
"""

import argparse
import asyncio
import csv
import json
import os
import sys
import time
import pickle
import traceback
import shutil
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime
import re

# Add the client directory to the path so we can import existing modules
sys.path.insert(0, str(Path(__file__).parent / "client"))

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from client.services.ai_service import create_llm_model
from client.services.mcp_service import setup_mcp_client, get_tools_from_client, prepare_server_config
from langgraph.prebuilt import create_react_agent
from client.config import SERVER_CONFIG, DEFAULT_TEMPERATURE, DEFAULT_MAX_TOKENS

# Load environment variables
load_dotenv()

class ProgressTracker:
    """Same ProgressTracker as the working Google version."""
    
    def __init__(self, output_base: str):
        self.output_base = output_base
        self.progress_file = f"{output_base}_progress.pkl"
        self.temp_results_file = f"{output_base}_temp_results.json"
        self.error_log_file = f"{output_base}_errors.log"
        
        # Progress tracking
        self.processed_batches = set()
        self.failed_batches = set()
        self.all_data_rows = []
        self.header_row = None
        self.total_batches = 0
        self.start_time = time.time()
        self.last_save_time = None
        
        # Error tracking
        self.error_count = 0
        self.consecutive_errors = 0
        self.max_consecutive_errors = 3
        
        # Ensure output directory exists
        output_dir = Path(self.output_base).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"📁 ProgressTracker initialized for: {output_base}")
        print(f"   📄 Progress file: {self.progress_file}")
        print(f"   📄 Temp results: {self.temp_results_file}")
        print(f"   📄 Error log: {self.error_log_file}")
    
    def save_progress(self):
        """Save current progress to disk with atomic operations."""
        try:
            progress_data = {
                'processed_batches': list(self.processed_batches),
                'failed_batches': list(self.failed_batches),
                'all_data_rows': self.all_data_rows,
                'header_row': self.header_row,
                'total_batches': self.total_batches,
                'start_time': self.start_time,
                'error_count': self.error_count,
                'last_save_time': time.time()
            }
            
            # Atomic save for progress file
            temp_progress_file = f"{self.progress_file}.tmp"
            try:
                with open(temp_progress_file, 'wb') as f:
                    pickle.dump(progress_data, f)
                shutil.move(temp_progress_file, self.progress_file)
                print(f"   💾 Progress saved to: {self.progress_file}")
            except Exception as e:
                if os.path.exists(temp_progress_file):
                    os.remove(temp_progress_file)
                raise e
            
            self.last_save_time = time.time()
            return True
            
        except Exception as e:
            print(f"❌ Error saving progress: {e}")
            return False
    
    def load_progress(self) -> bool:
        """Load existing progress if available."""
        if not os.path.exists(self.progress_file):
            print(f"📂 No existing progress file found: {self.progress_file}")
            return False
            
        try:
            with open(self.progress_file, 'rb') as f:
                data = pickle.load(f)
                
            self.processed_batches = set(data.get('processed_batches', []))
            self.failed_batches = set(data.get('failed_batches', []))
            self.all_data_rows = data.get('all_data_rows', [])
            self.header_row = data.get('header_row', None)
            self.total_batches = data.get('total_batches', 0)
            self.start_time = data.get('start_time', time.time())
            self.error_count = data.get('error_count', 0)
            
            print(f"📥 Progress loaded successfully:")
            print(f"   ✅ Processed batches: {len(self.processed_batches)}")
            print(f"   ❌ Failed batches: {len(self.failed_batches)}")
            print(f"   📊 Data rows: {len(self.all_data_rows)}")
            return True
            
        except Exception as e:
            print(f"❌ Error loading progress file: {e}")
            return False
    
    def mark_batch_completed(self, batch_num: int, parsed_rows: List[List[str]]):
        """Mark a batch as completed and save results."""
        print(f"   ✅ Marking batch {batch_num} as completed...")
        
        self.processed_batches.add(batch_num)
        self.failed_batches.discard(batch_num)
        
        # Extract header and data rows
        batch_header, data_rows = self.extract_header_and_data(parsed_rows)
        
        # Set header if we don't have one yet
        if self.header_row is None and batch_header is not None:
            self.header_row = batch_header
            print(f"   📋 Header captured: {len(batch_header)} columns")
        
        # Add data rows
        if data_rows:
            self.all_data_rows.extend(data_rows)
            print(f"   📊 Added {len(data_rows)} data rows (total: {len(self.all_data_rows)})")
        
        self.consecutive_errors = 0
        
        # Save progress
        save_success = self.save_progress()
        if not save_success:
            print(f"   ⚠️  Warning: Failed to save progress for batch {batch_num}")
        else:
            print(f"   ✅ Progress saved successfully for batch {batch_num}")
    
    def mark_batch_failed(self, batch_num: int, error: str, traceback_str: str = ""):
        """Mark a batch as failed and log the error."""
        print(f"   ❌ Marking batch {batch_num} as failed...")
        
        self.failed_batches.add(batch_num)
        self.error_count += 1
        self.consecutive_errors += 1
        
        # Log error
        self.log_error(batch_num, error, traceback_str)
        
        # Save progress
        self.save_progress()
    
    def log_error(self, batch_num: int, error: str, traceback_str: str = ""):
        """Log an error to the error log file."""
        try:
            error_entry = f"\n{'='*50}\n"
            error_entry += f"Batch {batch_num} Error - {datetime.now().isoformat()}\n"
            error_entry += f"Error: {error}\n"
            if traceback_str:
                error_entry += f"Traceback:\n{traceback_str}\n"
            error_entry += f"{'='*50}\n"
            
            with open(self.error_log_file, 'a', encoding='utf-8') as f:
                f.write(error_entry)
                
        except Exception as e:
            print(f"⚠️  Error writing to error log: {e}")
    
    def extract_header_and_data(self, parsed_rows: List[List[str]]) -> Tuple[Optional[List[str]], List[List[str]]]:
        """Extract header and data rows from parsed table."""
        if not parsed_rows:
            return None, []
        
        header = None
        data_rows = []
        
        for row in parsed_rows:
            if not row or len(row) == 0:
                continue
            
            # Skip separator rows
            if self.is_separator_row(row):
                continue
            
            # Identify header row
            if self.is_header_row(row):
                if header is None:
                    header = row
                continue
            
            # This is a data row
            if row and any(cell.strip() for cell in row):
                data_rows.append(row)
        
        return header, data_rows
    
    def is_header_row(self, row: List[str]) -> bool:
        """Check if a row is a header row."""
        if not row or len(row) == 0:
            return False
        
        first_cell = row[0].lower().strip()
        header_indicators = [
            'company name', 'account name', 'trading name', 
            'tech industry', 'industry', 'product'
        ]
        
        return any(indicator in first_cell for indicator in header_indicators)
    
    def is_separator_row(self, row: List[str]) -> bool:
        """Check if a row is a markdown separator row."""
        if not row:
            return False
        
        return all(cell.strip() == '' or all(c in '-|: ' for c in cell.strip()) for cell in row)
    
    def should_stop_due_to_errors(self) -> bool:
        """Check if we should stop due to too many consecutive errors."""
        return self.consecutive_errors >= self.max_consecutive_errors
    
    def get_remaining_batches(self, total_batches: int) -> List[int]:
        """Get list of batches that still need to be processed."""
        return [i for i in range(1, total_batches + 1) 
                if i not in self.processed_batches]
    
    def get_final_results(self) -> List[List[str]]:
        """Get final results with header + data rows."""
        if self.header_row is None:
            return self.all_data_rows
        
        return [self.header_row] + self.all_data_rows
    
    def get_stats(self) -> Dict:
        """Get current processing statistics."""
        return {
            'total_batches': self.total_batches,
            'completed_batches': len(self.processed_batches),
            'failed_batches': len(self.failed_batches),
            'remaining_batches': self.total_batches - len(self.processed_batches),
            'error_count': self.error_count,
            'consecutive_errors': self.consecutive_errors,
            'success_rate': len(self.processed_batches) / max(1, self.total_batches) * 100,
            'total_data_rows': len(self.all_data_rows),
            'has_header': self.header_row is not None,
            'elapsed_time': time.time() - self.start_time if self.start_time else 0
        }
    
    def cleanup_temp_files(self):
        """Clean up temporary files after successful completion."""
        files_to_clean = [
            self.progress_file,
            self.temp_results_file,
            f"{self.progress_file}.tmp",
            f"{self.temp_results_file}.tmp",
        ]
        
        cleaned_count = 0
        for file_path in files_to_clean:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    cleaned_count += 1
            except Exception as e:
                print(f"⚠️  Error cleaning up {file_path}: {e}")
        
        print(f"🧹 Cleaned up {cleaned_count} temporary files")


class SimplePerplexityCompanyClassificationCLI:
    """Simple CLI that replaces Google search with Perplexity search."""
    
    def __init__(self, config_path: Optional[str] = None, batch_size: int = 10, 
                 enabled_servers: Set[str] = None, output_base: str = "results"):
        self.config_path = config_path or "cli_servers_config.json"
        self.batch_size = batch_size
        self.enabled_servers = enabled_servers or {"perplexity", "company_tagging"}
        self.output_base = output_base
        
        # Initialize progress tracker
        self.progress = ProgressTracker(output_base)
        
        # MCP components
        self.client = None
        self.agent = None
        self.tools = []
        self.llm = None
        
        # Processing state
        self.companies = []
        self.retry_delay = 5
        self.max_retries = 3
    
    def sanitize_json_string(self, text: str) -> str:
        """Sanitize a string to prevent JSON parsing errors."""
        if not isinstance(text, str):
            return str(text)
        
        # Remove problematic characters
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F]', '', text)
        return text
    
    def clean_response_content(self, response_content: str) -> str:
        """Clean response content to prevent parsing errors."""
        if not response_content:
            return ""
        
        # Sanitize the content
        cleaned = self.sanitize_json_string(response_content)
        
        # Try to find and extract only the markdown table
        lines = cleaned.split('\n')
        table_lines = []
        in_table = False
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check if this is a table line
            if '|' in line and ('Company Name' in line or 'Tech Industry' in line):
                in_table = True
                table_lines.append(line)
            elif in_table and '|' in line:
                table_lines.append(line)
            elif in_table and not line and len(table_lines) > 0:
                continue
            elif in_table and line and '|' not in line:
                break
        
        if table_lines:
            return '\n'.join(table_lines)
        
        return cleaned
    
    def validate_server_requirements(self) -> bool:
        """Validate that required environment variables are set."""
        missing_vars = []
        
        # Check AI provider credentials
        if self._has_azure_credentials():
            pass
        elif os.getenv("OPENAI_API_KEY"):
            pass
        else:
            missing_vars.append("AZURE_API_KEY + AZURE_ENDPOINT + AZURE_DEPLOYMENT + AZURE_API_VERSION or OPENAI_API_KEY")
        
        # Check Perplexity credentials if enabled
        if "perplexity" in self.enabled_servers:
            if not os.getenv("PERPLEXITY_API_KEY"):
                missing_vars.append("PERPLEXITY_API_KEY")
        
        if missing_vars:
            print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
            return False
        
        return True
    
    def _has_azure_credentials(self) -> bool:
        """Check if Azure OpenAI credentials are complete."""
        azure_vars = ["AZURE_API_KEY", "AZURE_ENDPOINT", "AZURE_DEPLOYMENT", "AZURE_API_VERSION"]
        return all(os.getenv(var) for var in azure_vars)
    
    def get_server_config(self) -> Dict[str, Dict]:
        """Get server configuration based on enabled servers."""
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r') as f:
                server_config = json.load(f)
            all_servers = server_config.get('mcpServers', {})
        else:
            all_servers = SERVER_CONFIG['mcpServers']
        
        filtered_servers = {}
        
        # Company Tagging is always included
        if "Company Tagging" in all_servers:
            filtered_servers["Company Tagging"] = all_servers["Company Tagging"]
        
        # Add Perplexity Search if enabled (INSTEAD of Google Search)
        if "perplexity" in self.enabled_servers and "Perplexity Search" in all_servers:
            filtered_servers["Perplexity Search"] = all_servers["Perplexity Search"]
        
        return filtered_servers
    
    async def setup_connections(self):
        """Set up MCP client connections and initialize the agent."""
        print("🔧 Setting up MCP connections...")
        
        if not self.validate_server_requirements():
            raise ValueError("Missing required environment variables")
        
        # Create LLM instance
        if self._has_azure_credentials():
            llm_provider = "Azure OpenAI"
        else:
            llm_provider = "OpenAI"
        
        try:
            self.llm = create_llm_model(
                llm_provider,
                temperature=DEFAULT_TEMPERATURE,
                max_tokens=DEFAULT_MAX_TOKENS
            )
            print(f"✅ LLM initialized: {llm_provider}")
        except Exception as e:
            raise ValueError(f"Failed to initialize LLM: {e}")
        
        # Get server configuration
        try:
            servers = self.get_server_config()
            prepared_servers = prepare_server_config(servers)
            
            print(f"🔌 Connecting to {len(prepared_servers)} MCP servers...")
            
            self.client = await setup_mcp_client(prepared_servers)
            self.tools = await get_tools_from_client(self.client)
            
            # Create agent
            self.agent = create_react_agent(self.llm, self.tools)
            
            print(f"✅ Initialized with {len(self.tools)} available tools")
            
            # Log tool information
            tool_names = [tool.name for tool in self.tools]
            print(f"🔧 Available tools: {', '.join(tool_names)}")
            
        except Exception as e:
            print(f"❌ MCP Connection Error: {str(e)}")
            raise ValueError(f"Failed to setup MCP connections: {e}")
    
    def read_csv_file(self, csv_path: str) -> List[Dict]:
        """Read and parse the CSV file."""
        print(f"📖 Reading CSV file: {csv_path}")
        
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"CSV file not found: {csv_path}")
        
        companies = []
        try:
            with open(csv_path, 'r', encoding='utf-8', newline='') as csvfile:
                sample = csvfile.read(1024)
                csvfile.seek(0)
                sniffer = csv.Sniffer()
                delimiter = sniffer.sniff(sample).delimiter
                
                reader = csv.DictReader(csvfile, delimiter=delimiter)
                
                for row_num, row in enumerate(reader, 1):
                    # Clean and validate row data
                    cleaned_row = {}
                    for k, v in row.items():
                        if k is not None and v is not None:
                            cleaned_row[k.strip()] = self.sanitize_json_string(str(v).strip())
                    
                    # Check for required columns
                    required_columns = ['Account Name', 'Trading Name', 'Domain', 'Event']
                    if all(col in cleaned_row for col in required_columns):
                        if cleaned_row.get('Account Name'):
                            companies.append(cleaned_row)
            
            print(f"✅ Successfully read {len(companies)} companies from CSV")
            return companies
            
        except Exception as e:
            raise ValueError(f"Error reading CSV file: {e}")
    
    def format_companies_for_analysis(self, companies: List[Dict]) -> str:
        """Format companies data for the analysis prompt."""
        formatted_lines = []
        
        for company in companies:
            company_block = []
            company_block.append(f"Account Name = {company.get('Account Name', '')}")
            company_block.append(f"Trading Name = {company.get('Trading Name', '')}")
            company_block.append(f"Domain = {company.get('Domain', '')}")
            company_block.append(f"Industry = {company.get('Industry', '')}")
            company_block.append(f"Product/Service Type = {company.get('Product/Service Type', '')}")
            company_block.append(f"Event = {company.get('Event', '')}")
            
            formatted_lines.append('\n'.join(company_block))
        
        return '\n\n'.join(formatted_lines)
    
    def create_research_prompt(self, companies_batch: List[Dict]) -> str:
        """Create research prompt for the batch - SAME AS GOOGLE VERSION but with Perplexity."""
        company_data = self.format_companies_for_analysis(companies_batch)
        
        # SAME EXACT PROMPT as Google version, just replacing "google-search" with "perplexity_search_web"
        return f"""You are a professional data analyst tasked with tagging exhibitor companies with accurate industry and product categories from our established taxonomy.

COMPANY DATA TO ANALYZE:
{company_data}

MANDATORY RESEARCH PROCESS:

1. **Retrieve Complete Taxonomy** (ONCE ONLY):
   - Use search_show_categories tool without any filters to get all available categories

2. **For EACH Company - Research Phase:**
   - Choose research name priority: Domain > Trading Name > Account Name
   - Use perplexity_search_web tool: "[company name] products services technology offerings"
   - Identify what the company actually sells/offers

3. **Analysis Phase:**
   - Map company offerings to relevant shows (CAI, DOL, CCSE, BDAIW, DCW)
   - Match findings to EXACT taxonomy pairs from step 1
   - Select up to 4 (Industry | Product) pairs per company
   - Use pairs EXACTLY as they appear

4. **Output Requirements:**
   - Generate a markdown table with ONLY DATA ROWS (NO HEADER)
   - Use this exact format for each company:
   | Company Name | Trading Name | Tech Industry 1 | Tech Product 1 | Tech Industry 2 | Tech Product 2 | Tech Industry 3 | Tech Product 3 | Tech Industry 4 | Tech Product 4 |
   - Do NOT include the header row in your response
   - Do NOT provide additional text, explanations, or context
   - ONLY the data rows without header

CRITICAL RULES:
- MUST use search_show_categories to get taxonomy before starting
- Use taxonomy pairs EXACTLY as written
- Output ONLY data rows (no header row)
- Each row should have company data only

Begin the systematic analysis now."""
    
    def parse_markdown_table(self, response: str) -> List[List[str]]:
        """Parse markdown table response into structured data."""
        if not response:
            return []
        
        # Clean the response first
        response = self.clean_response_content(response)
        
        lines = response.strip().split('\n')
        table_rows = []
        
        for line in lines:
            line = line.strip()
            if "|" in line and line:
                # Parse markdown table row
                columns = [col.strip() for col in line.split('|')]
                # Remove empty first/last columns from markdown formatting
                if columns and not columns[0]:
                    columns = columns[1:]
                if columns and not columns[-1]:
                    columns = columns[:-1]
                
                # Skip separator lines
                if columns and not all(col == '' or '-' in col for col in columns):
                    # Sanitize each column
                    sanitized_columns = [self.sanitize_json_string(col) for col in columns]
                    table_rows.append(sanitized_columns)
        
        return table_rows
    
    async def process_batch_with_retry(self, batch_companies: List[Dict], 
                                     batch_num: int, total_batches: int) -> List[List[str]]:
        """Process a batch with retry logic - SAME AS GOOGLE VERSION."""
        for attempt in range(self.max_retries):
            try:
                print(f"🔄 Processing batch {batch_num}/{total_batches} (attempt {attempt + 1}/{self.max_retries})")
                
                batch_prompt = self.create_research_prompt(batch_companies)
                conversation_memory = [HumanMessage(content=batch_prompt)]
                
                # Run the agent with timeout
                response = await asyncio.wait_for(
                    self.agent.ainvoke({"messages": conversation_memory}),
                    timeout=300  # 5 minute timeout per batch
                )
                
                # Extract and clean the response
                assistant_response = None
                if "messages" in response:
                    for msg in response["messages"]:
                        if isinstance(msg, AIMessage) and hasattr(msg, "content") and msg.content:
                            assistant_response = self.clean_response_content(str(msg.content))
                            break
                
                if assistant_response and "|" in assistant_response:
                    parsed_rows = self.parse_markdown_table(assistant_response)
                    if parsed_rows:
                        print(f"   ✅ Batch {batch_num} completed: {len(parsed_rows)} rows processed")
                        return parsed_rows
                
                # If we get here, no valid response was found
                if attempt < self.max_retries - 1:
                    print(f"   ⚠️  Batch {batch_num} attempt {attempt + 1} failed (no valid response), retrying...")
                    await asyncio.sleep(self.retry_delay)
                    continue
                else:
                    print(f"   ❌ Batch {batch_num} failed after {self.max_retries} attempts")
                    return []
                    
            except asyncio.TimeoutError:
                error_msg = f"Batch {batch_num} timeout after 5 minutes"
                print(f"   ⏰ {error_msg}")
                if attempt < self.max_retries - 1:
                    print(f"   🔄 Retrying in {self.retry_delay} seconds...")
                    await asyncio.sleep(self.retry_delay)
                    continue
                else:
                    self.progress.mark_batch_failed(batch_num, error_msg)
                    return []
                    
            except Exception as e:
                error_msg = f"Batch {batch_num} error: {str(e)}"
                traceback_str = traceback.format_exc()
                print(f"   ❌ {error_msg}")
                
                if attempt < self.max_retries - 1:
                    print(f"   🔄 Retrying in {self.retry_delay} seconds...")
                    await asyncio.sleep(self.retry_delay)
                    continue
                else:
                    self.progress.mark_batch_failed(batch_num, error_msg, traceback_str)
                    return []
        
        return []
    
    async def classify_companies_batched(self, companies: List[Dict]) -> Tuple[str, List[List[str]]]:
        """Classify companies using batched processing - SAME AS GOOGLE VERSION."""
        
        # Split companies into batches
        batches = [companies[i:i + self.batch_size] for i in range(0, len(companies), self.batch_size)]
        total_batches = len(batches)
        
        # Initialize progress tracker
        self.progress.total_batches = total_batches
        self.progress.start_time = time.time()
        
        # Load existing progress if available
        if self.progress.load_progress():
            print(f"📂 Resuming from previous run...")
        
        # Set default header if we don't have one
        if self.progress.header_row is None:
            self.progress.header_row = [
                "Company Name", "Trading Name", 
                "Tech Industry 1", "Tech Product 1",
                "Tech Industry 2", "Tech Product 2", 
                "Tech Industry 3", "Tech Product 3",
                "Tech Industry 4", "Tech Product 4"
            ]
            print("📋 Using default header structure")
        
        # Get remaining batches to process
        remaining_batches = self.progress.get_remaining_batches(total_batches)
        
        if not remaining_batches:
            print("✅ All batches already completed!")
        else:
            print(f"📊 Processing {len(remaining_batches)} remaining batches out of {total_batches} total")
        
        # Process remaining batches
        for batch_idx in remaining_batches:
            batch_num = batch_idx
            batch_companies = batches[batch_idx - 1]  # Convert to 0-based for list access
            
            # Process batch with retry logic
            batch_results = await self.process_batch_with_retry(batch_companies, batch_num, total_batches)
            
            if batch_results:
                self.progress.mark_batch_completed(batch_num, batch_results)
            else:
                print(f"   ❌ Batch {batch_num} failed completely")
                
                # Check if we should stop due to too many consecutive errors
                if self.progress.should_stop_due_to_errors():
                    print(f"❌ Stopping due to {self.progress.consecutive_errors} consecutive errors")
                    break
            
            # Print progress update
            stats = self.progress.get_stats()
            print(f"📊 Progress: {stats['completed_batches']}/{stats['total_batches']} batches "
                  f"({stats['success_rate']:.1f}% success rate, {stats['total_data_rows']} companies)")
        
        # Final save
        self.progress.save_progress()
        
        # Generate final results
        final_results = self.progress.get_final_results()
        
        # Generate markdown content
        if final_results and len(final_results) > 0:
            header = final_results[0]
            data_rows = final_results[1:] if len(final_results) > 1 else []
            
            # Format as markdown table
            markdown_lines = []
            markdown_lines.append('|' + '|'.join([''] + header + ['']) + '|')
            
            # Add separator line
            separator = ['---'] * len(header)
            markdown_lines.append('|' + '|'.join([''] + separator + ['']) + '|')
            
            # Add data rows
            for row in data_rows:
                if len(row) >= len(header):
                    markdown_lines.append('|' + '|'.join([''] + row[:len(header)] + ['']) + '|')
            
            markdown_content = '\n'.join(markdown_lines)
        else:
            markdown_content = "No results to display"
        
        return markdown_content, final_results
    
    def save_csv_results(self, results: List[List[str]], csv_path: str):
        """Save results to CSV file."""
        if not results:
            print("⚠️  No results to save")
            return
            
        try:
            with open(csv_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerows(results)
            print(f"💾 CSV results saved to: {csv_path}")
        except Exception as e:
            raise ValueError(f"Error saving CSV results: {e}")
    
    async def save_results(self, markdown_content: str, csv_results: List[List[str]], base_output_path: str):
        """Save the classification results to both MD and CSV files."""
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
            
            # Save final statistics
            stats = self.progress.get_stats()
            stats_path = base_path.with_suffix('.stats.json')
            with open(stats_path, 'w', encoding='utf-8') as f:
                json.dump(stats, f, indent=2)
            print(f"📊 Statistics saved to: {stats_path}")
            
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
    """Main CLI function - SAME AS GOOGLE VERSION."""
    parser = argparse.ArgumentParser(
        description="Simple Perplexity Company Classification CLI Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument("--input", "-i", required=True, help="Path to input CSV file")
    parser.add_argument("--output", "-o", required=True, help="Base path for output files")
    parser.add_argument("--servers", "-s", type=str, default="perplexity", 
                       help="MCP servers to use: 'perplexity' (default: perplexity)")
    parser.add_argument("--batch-size", "-b", type=int, default=3, 
                       help="Batch size (default: 3)")
    parser.add_argument("--config", "-c", help="Path to server configuration file")
    parser.add_argument("--clean-start", action="store_true", 
                       help="Start fresh, ignoring previous progress")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    
    args = parser.parse_args()
    
    try:
        # Parse server selection - SIMPLE: just use perplexity
        enabled_servers = {"perplexity", "company_tagging"}
        
        # Initialize CLI tool
        cli = SimplePerplexityCompanyClassificationCLI(
            config_path=args.config,
            batch_size=args.batch_size,
            enabled_servers=enabled_servers,
            output_base=args.output
        )
        
        # Clean start if requested
        if args.clean_start:
            print("🧹 Starting fresh (ignoring previous progress)")
            cli.progress.cleanup_temp_files()
        
        print("🚀 Simple Perplexity Company Classification CLI Tool")
        print("=" * 80)
        
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
        
        # Print final summary
        stats = cli.progress.get_stats()
        print(f"\n📊 Final Processing Summary:")
        print(f"   Total companies in file: {len(companies)}")
        print(f"   Total batches: {stats['total_batches']}")
        print(f"   Completed batches: {stats['completed_batches']}")
        print(f"   Failed batches: {stats['failed_batches']}")
        print(f"   Success rate: {stats['success_rate']:.1f}%")
        print(f"   Total data rows: {stats['total_data_rows']}")
        
        # Clean up temp files on successful completion
        if stats['completed_batches'] == stats['total_batches']:
            cli.progress.cleanup_temp_files()
            print("✅ Processing completed successfully!")
        else:
            print(f"⚠️  Processing incomplete. Run again to continue.")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        if args.verbose:
            print("\nFull traceback:")
            traceback.print_exc()
        return 1
    
    finally:
        if 'cli' in locals():
            await cli.cleanup()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))