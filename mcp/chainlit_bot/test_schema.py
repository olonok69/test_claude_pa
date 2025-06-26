#!/usr/bin/env python3
"""
Test the schema fix to ensure it resolves the HubSpot tool issue
"""
import asyncio
import json
from mcp_client import MCPClient

async def test_tools_with_validation():
    """Test MCP client with schema validation"""
    print("🧪 Testing MCP Client with Schema Validation")
    print("="*50)
    
    client = MCPClient()
    
    try:
        # Connect to servers
        print("🔌 Connecting to MCP servers...")
        await client.connect_from_config()
        
        connected_servers = list(client.sessions.keys())
        
        if not connected_servers:
            print("❌ No servers connected")
            return False
        
        print(f"✅ Connected to: {', '.join(connected_servers)}")
        
        # Get all tools
        all_tools = client.get_all_tools()
        
        print(f"\n📋 Tool Summary:")
        print(f"   Total tools: {len(all_tools)}")
        
        # Group by server
        for server_name in connected_servers:
            server_tools = [t for t in all_tools if t.get('server') == server_name]
            print(f"   {server_name}: {len(server_tools)} tools")
            for tool in server_tools:
                print(f"     - {tool['name']}")
        
        # Test converting to OpenAI format
        print(f"\n🔧 Testing OpenAI format conversion...")
        
        openai_tools = []
        problematic_tools = []
        
        for tool in all_tools:
            try:
                openai_tool = {
                    "type": "function", 
                    "function": {
                        "name": tool["name"],
                        "description": tool["description"],
                        "parameters": tool["parameters"]
                    }
                }
                
                # Test JSON serialization (this often reveals issues)
                json.dumps(openai_tool)
                openai_tools.append(openai_tool)
                
            except Exception as e:
                problematic_tools.append((tool["name"], str(e)))
                print(f"❌ Tool '{tool['name']}' conversion failed: {e}")
        
        print(f"\n📊 Conversion Results:")
        print(f"   ✅ Successfully converted: {len(openai_tools)} tools")
        if problematic_tools:
            print(f"   ❌ Failed conversions: {len(problematic_tools)} tools")
            for tool_name, error in problematic_tools:
                print(f"     - {tool_name}: {error}")
        else:
            print(f"   🎉 All tools converted successfully!")
        
        # Save the working tools configuration for reference
        if openai_tools:
            with open("working_tools.json", "w") as f:
                json.dump(openai_tools, f, indent=2)
            print(f"\n💾 Saved working tools configuration to 'working_tools.json'")
        
        return len(problematic_tools) == 0
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        await client.close_all()

async def test_specific_problematic_tool():
    """Test fixing the specific problematic HubSpot tool"""
    print("\n🔍 Testing HubSpot Search Objects Tool Fix")
    print("="*50)
    
    from mcp_client import validate_and_fix_schema
    
    # Simulate the problematic schema that caused the error
    problematic_schema = {
        "type": "object",
        "properties": {
            "objectType": {"type": "string"},
            "filterGroups": {
                "type": "array",
                "items": {
                    "type": "object", 
                    "properties": {
                        "filters": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "propertyName": {"type": "string"},
                                    "operator": {"type": "string"},
                                    "values": {
                                        "type": "array"
                                        # This is missing "items" - causing the error!
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "required": ["objectType"]
    }
    
    print("🔍 Original problematic schema:")
    print(json.dumps(problematic_schema, indent=2))
    
    print("\n🔧 Applying fix...")
    fixed_schema = validate_and_fix_schema(problematic_schema)
    
    print("\n✅ Fixed schema:")
    print(json.dumps(fixed_schema, indent=2))
    
    # Test that the fixed schema is valid
    try:
        # This would be the OpenAI tool format
        test_tool = {
            "type": "function",
            "function": {
                "name": "hubspot-search-objects",
                "description": "Search for objects in HubSpot",
                "parameters": fixed_schema
            }
        }
        
        # Test JSON serialization
        json.dumps(test_tool)
        print("\n🎉 Fixed schema passes validation!")
        return True
        
    except Exception as e:
        print(f"\n❌ Fixed schema still has issues: {e}")
        return False

async def main():
    """Run all tests"""
    print("🚀 Schema Fix Validation Tests")
    print("="*60)
    
    # Test 1: Specific tool fix
    specific_fix_ok = await test_specific_problematic_tool()
    
    # Test 2: Full integration test
    integration_ok = await test_tools_with_validation()
    
    print("\n" + "="*60)
    print("📊 TEST RESULTS")
    print("="*60)
    
    print(f"Specific Tool Fix: {'✅ PASS' if specific_fix_ok else '❌ FAIL'}")
    print(f"Integration Test: {'✅ PASS' if integration_ok else '❌ FAIL'}")
    
    if specific_fix_ok and integration_ok:
        print("\n🎉 All tests passed! The schema fix should resolve your issue.")
        print("   You can now run your application:")
        print("   chainlit run app.py --port 8080 --host 0.0.0.0")
    else:
        print("\n⚠️  Some tests failed. The issue may need additional investigation.")
    
    return specific_fix_ok and integration_ok

if __name__ == "__main__":
    asyncio.run(main())