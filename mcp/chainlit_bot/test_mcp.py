#!/usr/bin/env python3
"""
Test script to verify MCP Neo4j connection works
"""
import asyncio
import sys
from mcp_client import MCPClient
from dotenv import load_dotenv
import os

load_dotenv(".env")

async def test_neo4j_connection():
    """Test the Neo4j MCP connection"""
    print("🧪 Testing Neo4j MCP Connection...")
    
    # Check environment variables
    required_vars = ["NEO4J_URI", "NEO4J_USERNAME", "NEO4J_PASSWORD", "NEO4J_DATABASE"]
    missing = [var for var in required_vars if not os.getenv(var)]
    
    if missing:
        print(f"❌ Missing environment variables: {', '.join(missing)}")
        return False
    
    print(f"✅ Environment variables set")
    print(f"   NEO4J_URI: {os.getenv('NEO4J_URI')}")
    print(f"   NEO4J_USERNAME: {os.getenv('NEO4J_USERNAME')}")
    print(f"   NEO4J_DATABASE: {os.getenv('NEO4J_DATABASE')}")
    
    client = MCPClient()
    
    try:
        # Test connection
        print("\n🔌 Connecting to Neo4j MCP server...")
        await client.connect_from_config()
        
        if not client.sessions:
            print("❌ No MCP sessions established")
            return False
        
        # List tools
        tools = client.get_all_tools()
        print(f"\n✅ Connected! Found {len(tools)} tools:")
        for tool in tools:
            print(f"   - {tool['name']}: {tool['description']}")
        
        # Test a simple query if tools are available
        if tools and "neo4j-aura" in client.sessions:
            print("\n🔍 Testing a simple query...")
            try:
                # Look for a tool that might execute queries
                query_tools = [t for t in tools if 'query' in t['name'].lower() or 'cypher' in t['name'].lower()]
                if query_tools:
                    tool_name = query_tools[0]['name']
                    print(f"   Using tool: {tool_name}")
                    
                    # Try a simple count query
                    result = await client.call_tool("neo4j-aura", tool_name, {
                        "query": "RETURN 1 as test"
                    })
                    print(f"   ✅ Query successful: {result}")
                else:
                    print("   ⚠️  No query tools found, but connection is working")
                    
            except Exception as e:
                print(f"   ⚠️  Query test failed: {e}")
        
        print("\n🎉 MCP connection test completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Connection test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        await client.close_all()

async def test_mcp_server_availability():
    """Test if the MCP server binary is available"""
    print("🔧 Testing MCP server availability...")
    
    import subprocess
    try:
        # Test if uvx is available
        result = subprocess.run(['uvx', '--version'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ uvx is available")
        else:
            print("❌ uvx is not available or not working")
            return False
            
        # Test if the Neo4j MCP server can be found
        result = subprocess.run(['uvx', 'mcp-neo4j-cypher@0.2.1', '--help'], 
                              capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print("✅ Neo4j MCP server is available")
            return True
        else:
            print("❌ Neo4j MCP server not found or not working")
            print(f"   Error: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ MCP server test timed out")
        return False
    except FileNotFoundError:
        print("❌ uvx command not found")
        return False
    except Exception as e:
        print(f"❌ Error testing MCP server: {e}")
        return False

async def main():
    """Run all tests"""
    print("🚀 Running MCP Neo4j Tests\n")
    
    # Test 1: MCP server availability
    server_ok = await test_mcp_server_availability()
    print()
    
    # Test 2: Connection test
    if server_ok:
        connection_ok = await test_neo4j_connection()
    else:
        print("⏭️  Skipping connection test due to server availability issues")
        connection_ok = False
    
    print("\n" + "="*50)
    if server_ok and connection_ok:
        print("🎉 All tests passed! Your setup is ready.")
        print("   You can now run: chainlit run app.py --port 8080 --host 0.0.0.0")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        if not server_ok:
            print("   💡 Try: pip install uvx")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())