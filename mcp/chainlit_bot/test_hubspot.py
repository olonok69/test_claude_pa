#!/usr/bin/env python3
"""
Comprehensive verification script for Neo4j and HubSpot MCP servers
"""
import asyncio
import subprocess
import os
import sys
import json
from dotenv import load_dotenv
from mcp_client import MCPClient

load_dotenv()

async def test_prerequisites():
    """Test if required tools are available"""
    print("🔧 Testing Prerequisites...")
    
    # Test uvx
    try:
        result = subprocess.run(['uvx', '--version'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"✅ uvx is working: {result.stdout.strip()}")
            uvx_ok = True
        else:
            print(f"❌ uvx failed: {result.stderr}")
            uvx_ok = False
    except Exception as e:
        print(f"❌ uvx test failed: {e}")
        uvx_ok = False
    
    # Test npx (Node.js)
    try:
        result = subprocess.run(['npx', '--version'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"✅ npx is working: {result.stdout.strip()}")
            npx_ok = True
        else:
            print(f"❌ npx failed: {result.stderr}")
            npx_ok = False
    except Exception as e:
        print(f"❌ npx test failed: {e}")
        npx_ok = False
    
    return uvx_ok, npx_ok

async def test_environment_variables():
    """Check if all required environment variables are set"""
    print("\n🔧 Testing Environment Variables...")
    
    required_vars = {
        "Neo4j": ["NEO4J_URI", "NEO4J_USERNAME", "NEO4J_PASSWORD", "NEO4J_DATABASE"],
        "HubSpot": ["HUBSPOT_PRIVATE_APP_TOKEN"],
        "Azure OpenAI": ["AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_API_KEY", "AZURE_OPENAI_MODEL", "OPENAI_API_VERSION"]
    }
    
    all_good = True
    
    for system, vars_list in required_vars.items():
        print(f"\n📋 {system} Variables:")
        system_ok = True
        for var in vars_list:
            value = os.getenv(var)
            if value:
                # Mask sensitive values
                if "PASSWORD" in var or "TOKEN" in var or "KEY" in var:
                    display_value = f"{value[:8]}...{value[-4:]}" if len(value) > 12 else "***"
                else:
                    display_value = value
                print(f"   ✅ {var}: {display_value}")
            else:
                print(f"   ❌ {var}: Not set")
                system_ok = False
                all_good = False
        
        if system_ok:
            print(f"   ✅ All {system} variables set")
        else:
            print(f"   ❌ Missing {system} variables")
    
    return all_good

async def test_neo4j_direct():
    """Test direct Neo4j connection"""
    print("\n🔧 Testing Direct Neo4j Connection...")
    
    try:
        from neo4j import GraphDatabase
        
        uri = os.getenv('NEO4J_URI')
        username = os.getenv('NEO4J_USERNAME')
        password = os.getenv('NEO4J_PASSWORD')
        
        if not all([uri, username, password]):
            print("❌ Missing Neo4j credentials")
            return False
        
        print(f"   Connecting to: {uri}")
        print(f"   Username: {username}")
        
        driver = GraphDatabase.driver(uri, auth=(username, password))
        with driver.session() as session:
            result = session.run("RETURN 1 as test")
            record = result.single()
            if record and record["test"] == 1:
                print("✅ Direct Neo4j connection successful")
                
                # Test a simple data query
                result = session.run("MATCH (n) RETURN count(n) as nodeCount")
                count_record = result.single()
                if count_record:
                    print(f"   📊 Database has {count_record['nodeCount']} nodes")
                
                driver.close()
                return True
            else:
                print("❌ Neo4j query failed")
                driver.close()
                return False
                
    except ImportError:
        print("⚠️  neo4j driver not installed. Installing...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'neo4j'], check=True)
        return await test_neo4j_direct()
    except Exception as e:
        print(f"❌ Direct Neo4j connection failed: {e}")
        return False

async def test_mcp_servers_individual():
    """Test each MCP server individually"""
    print("\n🔧 Testing Individual MCP Servers...")
    
    # Test Neo4j MCP server
    print("\n📊 Testing Neo4j MCP Server:")
    try:
        result = subprocess.run(['uvx', 'mcp-neo4j-cypher@0.2.1', '--help'], 
                              capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print("✅ Neo4j MCP server is available")
            neo4j_mcp_ok = True
        else:
            print(f"❌ Neo4j MCP server failed: {result.stderr}")
            neo4j_mcp_ok = False
    except Exception as e:
        print(f"❌ Neo4j MCP server test failed: {e}")
        neo4j_mcp_ok = False
    
    # Test HubSpot MCP server
    print("\n🏢 Testing HubSpot MCP Server:")
    try:
        result = subprocess.run(['npx', '-y', '@hubspot/mcp-server', '--help'], 
                              capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            print("✅ HubSpot MCP server is available")
            hubspot_mcp_ok = True
        else:
            print(f"❌ HubSpot MCP server failed: {result.stderr}")
            hubspot_mcp_ok = False
    except Exception as e:
        print(f"❌ HubSpot MCP server test failed: {e}")
        hubspot_mcp_ok = False
    
    return neo4j_mcp_ok, hubspot_mcp_ok

async def test_mcp_client_connection():
    """Test the full MCP client connection"""
    print("\n🔧 Testing Full MCP Client Connection...")
    
    client = MCPClient()
    
    try:
        # Connect using the config file
        await client.connect_from_config("mcp_config.json")
        
        connected_servers = list(client.sessions.keys())
        
        if not connected_servers:
            print("❌ No MCP connections established")
            return False, []
        
        print(f"✅ Connected to servers: {', '.join(connected_servers)}")
        
        # Test each connected server
        for server_name in connected_servers:
            print(f"\n🔍 Testing {server_name} server:")
            
            # Get available tools
            if server_name in client.tools:
                tools = client.tools[server_name]
                print(f"   📋 Available tools: {[tool['name'] for tool in tools]}")
                
                # Try to call a simple tool if available
                if tools:
                    try:
                        # For Neo4j, try schema query
                        if server_name == "neo4j" and any("schema" in tool['name'].lower() for tool in tools):
                            schema_tool = next(tool for tool in tools if "schema" in tool['name'].lower())
                            result = await client.call_tool(server_name, schema_tool['name'], {})
                            print(f"   ✅ {schema_tool['name']} executed successfully")
                        
                        # For HubSpot, try a listing tool if available
                        elif server_name == "hubspot":
                            # Just confirm tools are available, actual test might need specific parameters
                            print(f"   ✅ HubSpot tools are available (skipping test call)")
                        
                    except Exception as e:
                        print(f"   ⚠️  Tool test failed: {e}")
            else:
                print(f"   ❌ No tools found for {server_name}")
        
        return True, connected_servers
        
    except Exception as e:
        print(f"❌ MCP client connection failed: {e}")
        import traceback
        traceback.print_exc()
        return False, []
        
    finally:
        await client.close_all()

async def suggest_fixes(results):
    """Suggest fixes based on test results"""
    print("\n" + "="*60)
    print("💡 RECOMMENDATIONS")
    print("="*60)
    
    uvx_ok, npx_ok, env_ok, neo4j_direct_ok, neo4j_mcp_ok, hubspot_mcp_ok, mcp_client_ok, connected_servers = results
    
    if not uvx_ok:
        print("\n🔧 Fix uvx:")
        print("   pip install uvx")
    
    if not npx_ok:
        print("\n🔧 Fix npx (Node.js):")
        print("   Install Node.js from https://nodejs.org/")
        print("   Or using package manager: brew install node (macOS) / apt install nodejs npm (Ubuntu)")
    
    if not env_ok:
        print("\n🔧 Fix Environment Variables:")
        print("   1. Copy .env.template to .env")
        print("   2. Fill in all required values")
        print("   3. Double-check sensitive tokens are correct")
    
    if not neo4j_direct_ok:
        print("\n🔧 Fix Neo4j Connection:")
        print("   1. Verify Neo4j Aura database is running")
        print("   2. Check URI format: neo4j+s://xxxxx.databases.neo4j.io")
        print("   3. Test credentials in Neo4j Browser first")
        print("   4. Ensure password is correct (not expired)")
    
    if not neo4j_mcp_ok:
        print("\n🔧 Fix Neo4j MCP Server:")
        print("   1. Try: uvx --force mcp-neo4j-cypher@0.2.1")
        print("   2. Or install globally: pip install mcp-neo4j-cypher")
    
    if not hubspot_mcp_ok:
        print("\n🔧 Fix HubSpot MCP Server:")
        print("   1. Install Node.js if not available")
        print("   2. Try: npm install -g @hubspot/mcp-server")
        print("   3. Verify HubSpot token permissions")
    
    if not mcp_client_ok:
        print("\n🔧 Fix MCP Client:")
        print("   1. Check mcp_config.json syntax")
        print("   2. Verify all environment variables are loaded")
        print("   3. Try running individual components first")
    
    # Final recommendations
    print(f"\n🎯 NEXT STEPS:")
    if uvx_ok and npx_ok and env_ok and neo4j_direct_ok and mcp_client_ok:
        print("✅ Everything looks good! You can run:")
        print("   chainlit run app.py --port 8080 --host 0.0.0.0")
    else:
        failed_components = []
        if not uvx_ok: failed_components.append("uvx")
        if not npx_ok: failed_components.append("npx/Node.js")
        if not env_ok: failed_components.append("environment variables")
        if not neo4j_direct_ok: failed_components.append("Neo4j connection")
        if not mcp_client_ok: failed_components.append("MCP client")
        
        print(f"❌ Fix these components first: {', '.join(failed_components)}")
        print("   Then re-run this verification script")

async def main():
    """Run comprehensive verification"""
    print("🚀 MCP Servers Verification Script")
    print("="*60)
    
    # Run all tests
    uvx_ok, npx_ok = await test_prerequisites()
    env_ok = await test_environment_variables()
    neo4j_direct_ok = await test_neo4j_direct()
    neo4j_mcp_ok, hubspot_mcp_ok = await test_mcp_servers_individual()
    mcp_client_ok, connected_servers = await test_mcp_client_connection()
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST RESULTS SUMMARY")
    print("="*60)
    
    results = [
        ("uvx", uvx_ok),
        ("npx/Node.js", npx_ok),
        ("Environment Variables", env_ok),
        ("Neo4j Direct", neo4j_direct_ok),
        ("Neo4j MCP Server", neo4j_mcp_ok),
        ("HubSpot MCP Server", hubspot_mcp_ok),
        ("MCP Client", mcp_client_ok),
    ]
    
    for name, status in results:
        status_icon = "✅" if status else "❌"
        print(f"{status_icon} {name}")
    
    if connected_servers:
        print(f"\n🔗 Connected Servers: {', '.join(connected_servers)}")
    
    # Provide recommendations
    await suggest_fixes((uvx_ok, npx_ok, env_ok, neo4j_direct_ok, neo4j_mcp_ok, hubspot_mcp_ok, mcp_client_ok, connected_servers))

if __name__ == "__main__":
    asyncio.run(main())