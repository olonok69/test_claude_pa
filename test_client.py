#!/usr/bin/env python3
"""
Test client for PDF Document Processor MCP Server

This script demonstrates how to use the MCP server from a client application.
"""

import asyncio
import json
import base64
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test_server():
    """Test the PDF processor MCP server"""
    
    # Server parameters
    server_params = StdioServerParameters(
        command="python",
        args=["pdf_processor_server.py"]
    )
    
    print("🚀 Starting PDF Document Processor MCP Server test...")
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the session
            await session.initialize()
            print("✅ Server connection established")
            
            # Test 1: List available prompts
            print("\n📋 Testing: List available prompts")
            try:
                tools = await session.list_tools()
                print(f"Available tools: {[tool.name for tool in tools.tools]}")
                
                # Call list_prompts tool
                result = await session.call_tool("list_prompts", {})
                print("Available prompts:")
                print(result.content[0].text)
                
            except Exception as e:
                print(f"❌ Error listing prompts: {e}")
            
            # Test 2: Get a specific prompt
            print("\n🔍 Testing: Get specific prompt")
            try:
                result = await session.call_tool("get_prompt_by_id", {
                    "prompt_id": "add14cb9-561e-4426-9507-b6ec5d4dbcb0"
                })
                print("Prompt details:")
                print(result.content[0].text[:500] + "..." if len(result.content[0].text) > 500 else result.content[0].text)
                
            except Exception as e:
                print(f"❌ Error getting prompt: {e}")
            
            # Test 3: Test PDF extraction (if sample PDF exists)
            sample_pdf_path = Path("sample.pdf")
            if sample_pdf_path.exists():
                print("\n📄 Testing: PDF extraction")
                try:
                    # Read and encode PDF
                    with open(sample_pdf_path, "rb") as f:
                        pdf_data = f.read()
                    pdf_base64 = base64.b64encode(pdf_data).decode('utf-8')
                    
                    # Extract content
                    result = await session.call_tool("extract_pdf_to_markdown", {
                        "pdf_base64": pdf_base64,
                        "filename": "sample.pdf"
                    })
                    print("PDF extraction result:")
                    print(result.content[0].text[:1000] + "..." if len(result.content[0].text) > 1000 else result.content[0].text)
                    
                except Exception as e:
                    print(f"❌ Error extracting PDF: {e}")
            else:
                print("\n📄 Skipping PDF extraction test (no sample.pdf found)")
            
            # Test 4: Test prompt application
            print("\n🎯 Testing: Apply prompt to content")
            try:
                sample_content = """
# Medical Report Sample

## Patient Information
- Name: John Doe
- Age: 45
- Date: 2024-01-15

## Symptoms
- Chronic back pain
- Limited mobility
- Difficulty performing daily activities

## Diagnosis
- Lumbar disc herniation L4-L5
- Muscle spasms in lower back
                """
                
                result = await session.call_tool("apply_prompt_to_content", {
                    "content": sample_content,
                    "prompt_id": "add14cb9-561e-4426-9507-b6ec5d4dbcb0"
                })
                print("Prompt application result:")
                print(result.content[0].text[:1000] + "..." if len(result.content[0].text) > 1000 else result.content[0].text)
                
            except Exception as e:
                print(f"❌ Error applying prompt: {e}")
            
            print("\n✅ All tests completed!")

def create_sample_data():
    """Create some sample data for testing"""
    
    # Create a minimal sample PDF content (just for testing)
    sample_text = """
Test Document

This is a sample document for testing the PDF processor.

Medical Information:
- Patient has reported back pain
- Duration: 6 months
- Severity: Moderate to severe
- Impact on work: Significant limitations
    """
    
    print("📝 Sample text created for testing")
    print("To test with a real PDF, place a file named 'sample.pdf' in the current directory")

async def main():
    """Main test function"""
    create_sample_data()
    
    try:
        await test_server()
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())