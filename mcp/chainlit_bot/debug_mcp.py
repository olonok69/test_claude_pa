#!/usr/bin/env python3
"""
Debug script to diagnose MCP Neo4j connection issues
"""
import asyncio
import subprocess
import os
import sys
from dotenv import load_dotenv

load_dotenv()

async def test_uvx():
    """Test if uvx is working"""
    print("🔧 Testing uvx...")
    try:
        result = subprocess.run(['uvx', '--version'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"✅ uvx is working: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ uvx failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ uvx test failed: {e}")
        return False

async def test_mcp_server():
    """Test if the MCP server can be installed/run"""
    print("\n🔧 Testing Neo4j MCP server...")
    try:
        # Test help command
        result = subprocess.run(['uvx', 'mcp-neo4j-cypher@0.2.1', '--help'], 
                              capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            print("✅ Neo4j MCP server is available")
            return True
        else:
            print(f"❌ MCP server failed: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("❌ MCP server test timed out")
        return False
    except Exception as e:
        print(f"❌ MCP server test failed: {e}")
        return False

async def test_neo4j_direct():
    """Test direct Neo4j connection"""
    print("\n🔧 Testing direct Neo4j connection...")
    try:
        from neo4j import GraphDatabase
        
        uri = os.getenv('NEO4J_URI')
        username = os.getenv('NEO4J_USERNAME')
        password = os.getenv('NEO4J_PASSWORD')
        
        if not all([uri, username, password]):
            print("❌ Missing Neo4j credentials in .env")
            return False
        
        print(f"   URI: {uri}")
        print(f"   Username: {username}")
        
        driver = GraphDatabase.driver(uri, auth=(username, password))
        with driver.session() as session:
            result = session.run("RETURN 1 as test")
            record = result.single()
            if record and record["test"] == 1:
                print("✅ Direct Neo4j connection successful")
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

async def test_mcp_with_manual_env():
    """Test MCP server with manual environment"""
    print("\n🔧 Testing MCP server with Neo4j environment...")
    
    env = os.environ.copy()
    env.update({
        'NEO4J_URI': os.getenv('NEO4J_URI', ''),
        'NEO4J_USERNAME': os.getenv('NEO4J_USERNAME', ''),
        'NEO4J_PASSWORD': os.getenv('NEO4J_PASSWORD', ''),
        'NEO4J_DATABASE': os.getenv('NEO4J_DATABASE', 'neo4j')
    })
    
    try:
        # Try to run the MCP server briefly
        process = subprocess.Popen(
            ['uvx', 'mcp-neo4j-cypher@0.2.1'],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait a bit and then terminate
        await asyncio.sleep(5)
        
        if process.poll() is None:  # Still running
            process.terminate()
            await asyncio.sleep(1)
            if process.poll() is None:
                process.kill()
            
            print("✅ MCP server started successfully (terminated after test)")
            return True
        else:
            stdout, stderr = process.communicate()
            print(f"❌ MCP server exited early:")
            print(f"   stdout: {stdout}")
            print(f"   stderr: {stderr}")
            return False
            
    except Exception as e:
        print(f"❌ MCP server manual test failed: {e}")
        return False

async def suggest_fixes():
    """Suggest fixes based on test results"""
    print("\n" + "="*50)
    print("🔧 TROUBLESHOOTING SUGGESTIONS")
    print("="*50)
    
    # Test all components
    uvx_ok = await test_uvx()
    neo4j_ok = await test_neo4j_direct()
    mcp_server_ok = await test_mcp_server()
    mcp_env_ok = await test_mcp_with_manual_env()
    
    print("\n📋 RESULTS SUMMARY:")
    print(f"   uvx: {'✅' if uvx_ok else '❌'}")
    print(f"   Neo4j direct: {'✅' if neo4j_ok else '❌'}")
    print(f"   MCP server: {'✅' if mcp_server_ok else '❌'}")
    print(f"   MCP with env: {'✅' if mcp_env_ok else '❌'}")
    
    print("\n💡 RECOMMENDED ACTIONS:")
    
    if not uvx_ok:
        print("1. Install uvx: pip install uvx")
        
    if not neo4j_ok:
        print("2. Fix Neo4j connection:")
        print("   - Check your .env file has correct credentials")
        print("   - Verify Neo4j Aura URI format: neo4j+s://xxxxx.databases.neo4j.io")
        print("   - Test in Neo4j Browser first")
        
    if not mcp_server_ok:
        print("3. Fix MCP server:")
        print("   - Try: uvx --force mcp-neo4j-cypher@0.2.1")
        print("   - Or install globally: pip install mcp-neo4j-cypher")
        
    if neo4j_ok and not mcp_env_ok:
        print("4. Environment variable issue:")
        print("   - Check .env file is in the correct directory")
        print("   - Verify environment variables are loaded correctly")
    
    if all([uvx_ok, neo4j_ok, mcp_server_ok]):
        print("🎉 All components seem to work individually!")
        print("   The issue might be with the async connection handling.")
        print("   Try restarting the chatbot.")

if __name__ == "__main__":
    asyncio.run(suggest_fixes())