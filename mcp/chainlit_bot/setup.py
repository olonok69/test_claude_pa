#!/usr/bin/env python3
"""
Setup script to install the Neo4j MCP server and verify the environment
"""

import subprocess
import sys
import os
from dotenv import load_dotenv

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"Error: {e.stderr}")
        return False

def check_environment():
    """Check if required environment variables are set"""
    load_dotenv(".env")
    
    required_vars = [
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_API_KEY", 
        "AZURE_OPENAI_MODEL",
        "OPENAI_API_VERSION",
        "NEO4J_URI",
        "NEO4J_USERNAME",
        "NEO4J_PASSWORD",
        "NEO4J_DATABASE"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease copy .env.template to .env and fill in your values.")
        return False
    
    print("✅ All required environment variables are set")
    return True

def main():
    print("🚀 Setting up Neo4j MCP Chatbot...")
    
    # Check if .env file exists
    if not os.path.exists(".env"):
        print("❌ .env file not found. Please copy .env.template to .env and configure it.")
        sys.exit(1)
    
    # Check environment variables
    if not check_environment():
        sys.exit(1)
    
    # Install Python dependencies
    # if not run_command("pip install -r requirements.txt", "Installing Python dependencies"):
    #     sys.exit(1)
    
    # Install uvx if not already installed
    if not run_command("pip install uvx", "Installing uvx"):
        print("⚠️  uvx installation failed, but it might already be available")
    
    # Test Neo4j MCP server installation
    print("🔄 Testing Neo4j MCP server...")
    test_command = "uvx mcp-neo4j-cypher@0.2.1 --help"
    if run_command(test_command, "Testing Neo4j MCP server"):
        print("✅ Neo4j MCP server is available")
    else:
        print("⚠️  Neo4j MCP server test failed, but it might still work")
    
    print("\n🎉 Setup completed!")
    print("\nNext steps:")
    print("1. Make sure your Neo4j database is running")
    print("2. Run the chatbot with: chainlit run app.py")
    print("3. Test the connection in your browser")

if __name__ == "__main__":
    main()