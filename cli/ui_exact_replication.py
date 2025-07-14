#!/usr/bin/env python3
"""
Test script that replicates EXACTLY what the UI does when user types:
"tag the following companies:" followed by company data
"""

import asyncio
import os
import sys
from pathlib import Path

# Add client directory to path
sys.path.insert(0, str(Path(__file__).parent / "client"))

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from services.ai_service import create_llm_model
from services.mcp_service import setup_mcp_client, get_tools_from_client, prepare_server_config
from langgraph.prebuilt import create_react_agent
from config import DEFAULT_TEMPERATURE, DEFAULT_MAX_TOKENS
import json

load_dotenv()

async def test_ui_exact_replication():
    """Test the exact UI replication."""
    print("🎯 Testing EXACT UI Replication")
    print("=" * 50)
    
    # Setup (same as CLI)
    config_path = "cli_servers_config.json"
    with open(config_path, 'r') as f:
        server_config = json.load(f)
    servers = server_config.get('mcpServers', {})
    
    prepared_servers = prepare_server_config(servers)
    client = await setup_mcp_client(prepared_servers)
    tools = await get_tools_from_client(client)
    
    llm_provider = "OpenAI" if os.getenv("OPENAI_API_KEY") else "Azure OpenAI"
    llm = create_llm_model(llm_provider, temperature=DEFAULT_TEMPERATURE, max_tokens=DEFAULT_MAX_TOKENS)
    agent = create_react_agent(llm, tools)
    
    print(f"✅ Setup complete with {len(tools)} tools")
    
    # This is EXACTLY what the UI does - it creates this prompt when user types "tag the following companies:"
    user_text = """tag the following companies:
Account Name = Microsoft Trading Name = Microsoft Domain = microsoft.com Product/Service Type =  Industry =  Event = Cloud and AI Infrastructure"""
    
    print(f"📝 User text (simulating UI input):")
    print(f"   {user_text}")
    
    # The UI extracts company data from the user text
    def extract_company_data_from_text(user_text):
        """Extract company data from user text for the prompt."""
        # Find the part of the text that contains company data
        lines = user_text.split('\n')
        company_data_lines = []
        
        for line in lines:
            # Look for lines that contain company information
            if any(keyword in line for keyword in ['CASEACCID', 'Account Name', 'Trading Name', 'Domain', 'Event']):
                company_data_lines.append(line.strip())
            elif line.strip() and '=' in line and any(company_data_lines):
                # Continue collecting if we're in a company data block
                company_data_lines.append(line.strip())
        
        return '\n'.join(company_data_lines) if company_data_lines else user_text
    
    company_data = extract_company_data_from_text(user_text)
    print(f"📊 Extracted company data:")
    print(f"   {company_data}")
    
    # This is the EXACT prompt the UI creates in the company tagging workflow
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
    
    print(f"🚀 Running UI-exact prompt...")
    
    # Create conversation memory for the agent (same as UI)
    conversation_memory = []
    conversation_memory.append(HumanMessage(content=company_tagging_prompt))
    
    # Run the agent with the specialized prompt (same as UI)
    response = await agent.ainvoke({"messages": conversation_memory})
    
    print(f"📥 Response received, processing...")
    
    # Extract and display the response (EXACT same logic as UI)
    assistant_response = None
    if "messages" in response:
        for msg in response["messages"]:
            if hasattr(msg, "content") and msg.content:
                assistant_response = str(msg.content)
                # Look for markdown table in the response (same as UI)
                if "|" in assistant_response and "Company Name" in assistant_response:
                    # Extract just the table part (same as UI)
                    lines = assistant_response.split('\n')
                    table_lines = []
                    in_table = False
                    for line in lines:
                        if "|" in line and ("Company Name" in line or "Tech Industry" in line):
                            in_table = True
                        if in_table and "|" in line:
                            table_lines.append(line.strip())
                        elif in_table and not line.strip():
                            # Empty line might end the table
                            continue
                        elif in_table and "|" not in line.strip() and line.strip():
                            # Non-empty line without | ends the table
                            break
                    
                    if table_lines:
                        assistant_response = '\n'.join(table_lines)
                        print(f"✅ Extracted table with {len(table_lines)} lines")
                        break
    
    if assistant_response:
        print(f"\n🎉 SUCCESS! UI replication worked:")
        print("=" * 50)
        print(assistant_response)
        print("=" * 50)
    else:
        print(f"\n❌ FAILED! No response extracted")
        print(f"📝 Raw response messages:")
        if "messages" in response:
            for i, msg in enumerate(response["messages"]):
                if hasattr(msg, "content") and msg.content:
                    content = str(msg.content)
                    print(f"   Message {i+1}: {content[:300]}...")
    
    # Cleanup
    await client.__aexit__(None, None, None)

if __name__ == "__main__":
    asyncio.run(test_ui_exact_replication())