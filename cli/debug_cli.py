#!/usr/bin/env python3
"""
Debug Script for Company Classification CLI
Provides detailed debugging information about the classification process.
"""

import asyncio
import csv
import json
import os
import sys
from pathlib import Path

# Add the client directory to the path
sys.path.insert(0, str(Path(__file__).parent / "client"))

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from services.ai_service import create_llm_model
from services.mcp_service import setup_mcp_client, get_tools_from_client, prepare_server_config
from langgraph.prebuilt import create_react_agent
from config import DEFAULT_TEMPERATURE, DEFAULT_MAX_TOKENS

load_dotenv()

async def debug_classification(csv_path: str):
    """Debug the classification process step by step."""
    print("🔍 Debug Classification Process")
    print("=" * 50)
    
    # Load server configuration
    config_path = "cli_servers_config.json"
    with open(config_path, 'r') as f:
        server_config = json.load(f)
    servers = server_config.get('mcpServers', {})
    
    prepared_servers = prepare_server_config(servers)
    print(f"🔌 Prepared {len(prepared_servers)} server configurations")
    
    # Setup MCP client
    client = await setup_mcp_client(prepared_servers)
    tools = await get_tools_from_client(client)
    
    print(f"✅ Connected with {len(tools)} tools:")
    for tool in tools:
        print(f"   - {tool.name}: {tool.description[:100]}...")
    
    # Create LLM and agent
    llm_provider = "OpenAI" if os.getenv("OPENAI_API_KEY") else "Azure OpenAI"
    llm = create_llm_model(llm_provider, temperature=DEFAULT_TEMPERATURE, max_tokens=DEFAULT_MAX_TOKENS)
    agent = create_react_agent(llm, tools)
    
    print(f"🤖 Created agent with {llm_provider}")
    
    # Read CSV file
    print(f"\n📖 Reading CSV file: {csv_path}")
    companies = []
    
    with open(csv_path, 'r', encoding='utf-8', newline='') as csvfile:
        sniffer = csv.Sniffer()
        sample = csvfile.read(1024)
        csvfile.seek(0)
        delimiter = sniffer.sniff(sample).delimiter
        reader = csv.DictReader(csvfile, delimiter=delimiter)
        
        for row in reader:
            cleaned_row = {k.strip(): v.strip() if v else "" for k, v in row.items()}
            if cleaned_row.get('Account Name'):
                companies.append(cleaned_row)
    
    print(f"✅ Read {len(companies)} companies")
    
    # Show first few companies
    print("\n📊 First 3 companies:")
    for i, company in enumerate(companies[:3]):
        print(f"   {i+1}. {company.get('Account Name', 'N/A')} - {company.get('Domain', 'N/A')}")
    
    # Test with just 1 company first
    test_company = companies[0]
    print(f"\n🧪 Testing with single company: {test_company.get('Account Name')}")
    
    # Format single company
    formatted_company = f"Account Name = {test_company.get('Account Name', '')} Trading Name = {test_company.get('Trading Name', '')} Domain = {test_company.get('Domain', '')} Product/Service Type = {test_company.get('Product/Service Type', '')} Industry = {test_company.get('Industry', '')} Event = {test_company.get('Event', '')}"
    
    print(f"📝 Formatted: {formatted_company}")
    
    # Create a simpler, more direct prompt
    simple_prompt = f"""You are tasked with categorizing companies using available tools. 

COMPANY TO ANALYZE:
{formatted_company}

PROCESS:
1. First, use the search_show_categories tool to get the taxonomy
2. Then, use google-search to research the company
3. Use perplexity_search_web to get additional information
4. Finally, create a markdown table with the results

Start with step 1 - get the taxonomy using search_show_categories tool."""
    
    print(f"\n📤 Sending simplified prompt to agent...")
    
    try:
        # Run the agent with detailed logging
        conversation_memory = [HumanMessage(content=simple_prompt)]
        response = await agent.ainvoke({"messages": conversation_memory})
        
        print(f"\n📥 Agent Response Structure:")
        print(f"   Type: {type(response)}")
        print(f"   Keys: {list(response.keys()) if isinstance(response, dict) else 'Not a dict'}")
        
        if "messages" in response:
            print(f"   Messages count: {len(response['messages'])}")
            
            for i, msg in enumerate(response["messages"]):
                print(f"\n   Message {i+1}:")
                print(f"     Type: {type(msg).__name__}")
                
                if hasattr(msg, "content") and msg.content:
                    content = str(msg.content)
                    print(f"     Content length: {len(content)}")
                    print(f"     Content preview: {content[:200]}...")
                    
                    # Check if it contains a table
                    if "|" in content and "Company Name" in content:
                        print(f"     ✅ Contains markdown table")
                        
                        # Extract table
                        lines = content.split('\n')
                        table_lines = []
                        in_table = False
                        
                        for line in lines:
                            if "|" in line and ("Company Name" in line or "Tech Industry" in line):
                                in_table = True
                            if in_table and "|" in line:
                                table_lines.append(line.strip())
                                print(f"       Table line: {line.strip()}")
                            elif in_table and not line.strip():
                                continue
                            elif in_table and "|" not in line.strip() and line.strip():
                                break
                        
                        print(f"     📊 Extracted {len(table_lines)} table lines")
                    else:
                        print(f"     ❌ No markdown table found")
                
                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    print(f"     Tool calls: {len(msg.tool_calls)}")
                    for j, tool_call in enumerate(msg.tool_calls):
                        print(f"       {j+1}. {tool_call.get('name', 'Unknown')} - {tool_call.get('args', {})}")
        
        # Check if we got a proper response
        final_response = None
        if "messages" in response:
            for msg in response["messages"]:
                if hasattr(msg, "content") and msg.content:
                    content = str(msg.content)
                    if "|" in content and "Company Name" in content:
                        final_response = content
                        break
        
        if final_response:
            print(f"\n✅ Successfully extracted response:")
            print(final_response)
        else:
            print(f"\n❌ No proper table response found")
            print(f"💡 This might be due to:")
            print(f"   - Agent not completing the full process")
            print(f"   - Tool execution errors")
            print(f"   - LLM not following instructions properly")
            print(f"   - API rate limits or timeouts")
        
    except Exception as e:
        print(f"❌ Error during agent execution: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        await client.__aexit__(None, None, None)
        print("\n🧹 Cleaned up connections")

async def main():
    """Main debug function."""
    if len(sys.argv) < 2:
        print("Usage: python debug_cli.py <csv_file>")
        sys.exit(1)
    
    csv_path = sys.argv[1]
    if not os.path.exists(csv_path):
        print(f"❌ CSV file not found: {csv_path}")
        sys.exit(1)
    
    await debug_classification(csv_path)

if __name__ == "__main__":
    asyncio.run(main())