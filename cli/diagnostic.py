#!/usr/bin/env python3
"""
Diagnostic Script for MCP Connection Issues
Helps identify and troubleshoot connection problems with MCP servers.
"""

import os
import sys
import json
import asyncio
import subprocess
from pathlib import Path
import importlib.util

# Add client directory to path
sys.path.insert(0, str(Path(__file__).parent / "client"))

async def check_environment():
    """Check environment variables and configuration."""
    print("🔍 Checking Environment Configuration")
    print("=" * 50)
    
    # Check AI provider credentials
    print("\n🤖 AI Provider Configuration:")
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        print(f"   ✅ OpenAI API Key: {'*' * (len(openai_key) - 4) + openai_key[-4:]}")
    else:
        print("   ❌ OpenAI API Key: Not set")
        
        # Check Azure OpenAI
        azure_keys = {
            "AZURE_API_KEY": os.getenv("AZURE_API_KEY"),
            "AZURE_ENDPOINT": os.getenv("AZURE_ENDPOINT"), 
            "AZURE_DEPLOYMENT": os.getenv("AZURE_DEPLOYMENT"),
            "AZURE_API_VERSION": os.getenv("AZURE_API_VERSION")
        }
        
        azure_complete = all(azure_keys.values())
        if azure_complete:
            print("   ✅ Azure OpenAI: Configured")
            for key, value in azure_keys.items():
                if value:
                    display_value = value if key != "AZURE_API_KEY" else f"{'*' * (len(value) - 4) + value[-4:]}"
                    print(f"      {key}: {display_value}")
        else:
            print("   ❌ Azure OpenAI: Incomplete configuration")
    
    # Check Google Search credentials
    print("\n🔍 Google Search Configuration:")
    google_key = os.getenv("GOOGLE_API_KEY")
    google_engine = os.getenv("GOOGLE_SEARCH_ENGINE_ID")
    
    if google_key:
        print(f"   ✅ Google API Key: {'*' * (len(google_key) - 4) + google_key[-4:]}")
    else:
        print("   ❌ Google API Key: Not set")
        
    if google_engine:
        print(f"   ✅ Search Engine ID: {google_engine}")
    else:
        print("   ❌ Search Engine ID: Not set")
    
    # Check Perplexity credentials
    print("\n🔮 Perplexity Configuration:")
    perplexity_key = os.getenv("PERPLEXITY_API_KEY")
    perplexity_model = os.getenv("PERPLEXITY_MODEL", "sonar")
    
    if perplexity_key:
        print(f"   ✅ Perplexity API Key: {'*' * (len(perplexity_key) - 4) + perplexity_key[-4:]}")
    else:
        print("   ❌ Perplexity API Key: Not set")
        
    print(f"   ✅ Perplexity Model: {perplexity_model}")

async def check_project_structure():
    """Check project structure and required files."""
    print("\n📁 Project Structure Check")
    print("=" * 50)
    
    required_files = [
        "client/services/ai_service.py",
        "client/services/mcp_service.py", 
        "client/services/chat_service.py",
        "client/utils/async_helpers.py",
        "client/config.py",
        "client/servers_config.json",
        "client/mcp_servers/company_tagging/server.py",
        "client/mcp_servers/company_tagging/categories/classes.csv"
    ]
    
    all_present = True
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"   ✅ {file_path}")
        else:
            print(f"   ❌ {file_path}")
            all_present = False
    
    if all_present:
        print("\n✅ All required files are present")
    else:
        print("\n❌ Some required files are missing")
    
    return all_present

async def check_dependencies():
    """Check Python dependencies."""
    print("\n📦 Python Dependencies Check")
    print("=" * 50)
    
    required_packages = [
        "streamlit",
        "langchain_openai",
        "langchain_mcp_adapters", 
        "langgraph",
        "python-dotenv",
        "mcp",
        "aiohttp"
    ]
    
    all_installed = True
    for package in required_packages:
        try:
            __import__(package)
            print(f"   ✅ {package}")
        except ImportError:
            print(f"   ❌ {package}")
            all_installed = False
    
    if not all_installed:
        print("\n💡 To install missing packages:")
        print("   pip install streamlit langchain-openai langchain-mcp-adapters langgraph python-dotenv mcp aiohttp")
    
    return all_installed

async def check_mcp_servers():
    """Check MCP server accessibility."""
    print("\n🔌 MCP Server Accessibility Check")
    print("=" * 50)
    
    # Check if docker-compose is running
    print("\n🐳 Docker Services Check:")
    try:
        result = subprocess.run(["docker-compose", "ps"], capture_output=True, text=True)
        if result.returncode == 0:
            print("   ✅ Docker Compose is available")
            print("   Services status:")
            lines = result.stdout.strip().split('\n')
            for line in lines[1:]:  # Skip header
                if line.strip():
                    print(f"      {line}")
        else:
            print("   ❌ Docker Compose not available or not running")
    except FileNotFoundError:
        print("   ❌ Docker Compose not found")
    
    # Check SSE servers
    print("\n🌐 SSE Server Check:")
    try:
        import aiohttp
        
        servers = [
            ("Google Search", "http://localhost:8002/health"),
            ("Perplexity", "http://localhost:8001/health")
        ]
        
        for name, url in servers:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=5) as response:
                        if response.status == 200:
                            print(f"   ✅ {name}: Server responding at {url}")
                        else:
                            print(f"   ❌ {name}: Server returned status {response.status}")
            except Exception as e:
                print(f"   ❌ {name}: Cannot reach {url} - {e}")
                
    except ImportError:
        print("   ❌ aiohttp not available for server checks")
    
    # Check stdio server
    print("\n📡 Stdio Server Check:")
    try:
        module_name = "mcp_servers.company_tagging.server"
        spec = importlib.util.find_spec(module_name)
        if spec:
            print(f"   ✅ Company Tagging Module: {spec.origin}")
        else:
            print(f"   ❌ Company Tagging Module: {module_name} not found")
    except Exception as e:
        print(f"   ❌ Error checking stdio server: {e}")

async def check_server_configuration():
    """Check server configuration file."""
    print("\n⚙️ Server Configuration Check") 
    print("=" * 50)
    
    config_path = "client/servers_config.json"
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            print(f"   ✅ Configuration file found: {config_path}")
            
            servers = config.get('mcpServers', {})
            print(f"   📊 Configured servers: {len(servers)}")
            
            for name, server_config in servers.items():
                transport = server_config.get('transport', 'unknown')
                print(f"      {name}: {transport}")
                
                if transport == 'sse':
                    url = server_config.get('url', 'no url')
                    print(f"         URL: {url}")
                elif transport == 'stdio':
                    command = server_config.get('command', 'no command')
                    args = server_config.get('args', [])
                    print(f"         Command: {command} {' '.join(args)}")
                    
        except Exception as e:
            print(f"   ❌ Error reading configuration: {e}")
    else:
        print(f"   ❌ Configuration file not found: {config_path}")

async def run_simple_test():
    """Run a simple connection test."""
    print("\n🧪 Simple Connection Test")
    print("=" * 50)
    
    try:
        # Try to import and test basic functionality
        from dotenv import load_dotenv
        load_dotenv()
        
        print("   ✅ Environment variables loaded")
        
        # Test AI service
        from services.ai_service import create_llm_model
        try:
            llm_provider = "OpenAI" if os.getenv("OPENAI_API_KEY") else "Azure OpenAI"
            llm = create_llm_model(llm_provider)
            print(f"   ✅ LLM created: {llm_provider}")
        except Exception as e:
            print(f"   ❌ LLM creation failed: {e}")
        
        # Test MCP service import
        from services.mcp_service import setup_mcp_client, prepare_server_config
        from config import SERVER_CONFIG
        
        print("   ✅ MCP service imported")
        
        # Test server configuration preparation
        servers = SERVER_CONFIG['mcpServers']
        prepared_servers = prepare_server_config(servers)
        print(f"   ✅ Server configuration prepared: {len(prepared_servers)} servers")
        
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Main diagnostic function."""
    print("🔧 MCP Connection Diagnostic Tool")
    print("=" * 50)
    
    # Run all checks
    await check_environment()
    
    structure_ok = await check_project_structure()
    if not structure_ok:
        print("\n❌ Project structure issues detected. Please ensure all files are present.")
        return
    
    deps_ok = await check_dependencies()
    if not deps_ok:
        print("\n❌ Missing dependencies detected. Please install required packages.")
        return
    
    await check_server_configuration()
    await check_mcp_servers()
    await run_simple_test()
    
    print("\n" + "=" * 50)
    print("🎯 Diagnostic Complete")
    print("=" * 50)
    
    print("\n💡 Next Steps:")
    print("1. If Docker services are not running: docker-compose up mcpserver1 mcpserver2 -d")
    print("2. If environment variables are missing: Edit your .env file")
    print("3. If dependencies are missing: pip install -r client/requirements.txt")
    print("4. If servers are not responding: Check server logs with docker-compose logs")

if __name__ == "__main__":
    asyncio.run(main())
