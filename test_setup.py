"""
Test script for Deep Agents ML Report Workflow

This script validates:
1. Python dependencies are installed
2. Neo4j MCP connection works
3. Basic workflow components function correctly
4. File I/O operations work

Author: Senior Python Developer
Date: 2025
"""

import sys
import os
from typing import List, Tuple


def test_imports() -> Tuple[bool, List[str]]:
    """
    Test that all required Python packages can be imported.
    
    Returns:
        Tuple of (success: bool, error_messages: List[str])
    """
    required_imports = [
        ('langgraph', 'LangGraph'),
        ('langchain_anthropic', 'LangChain Anthropic'),
        ('langchain_core', 'LangChain Core'),
        ('langchain_mcp', 'LangChain MCP'),
        ('yaml', 'PyYAML'),
        ('pydantic', 'Pydantic'),
        ('dotenv', 'python-dotenv'),
    ]
    
    errors = []
    print("\n" + "="*60)
    print("TEST 1: Python Dependencies")
    print("="*60)
    
    for module_name, display_name in required_imports:
        try:
            __import__(module_name)
            print(f"✓ {display_name:20s} - OK")
        except ImportError as e:
            error_msg = f"✗ {display_name:20s} - FAILED: {str(e)}"
            print(error_msg)
            errors.append(error_msg)
    
    success = len(errors) == 0
    print(f"\nResult: {'PASSED' if success else 'FAILED'}")
    return success, errors


def test_environment_variables() -> Tuple[bool, List[str]]:
    """
    Test that required environment variables are set.
    
    Returns:
        Tuple of (success: bool, error_messages: List[str])
    """
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = [
        'ANTHROPIC_API_KEY',
    ]
    
    optional_vars = [
        'NEO4J_URI',
        'NEO4J_USERNAME',
        'NEO4J_PASSWORD',
        'LANGSMITH_API_KEY',
    ]
    
    errors = []
    warnings = []
    
    print("\n" + "="*60)
    print("TEST 2: Environment Variables")
    print("="*60)
    
    # Check required variables
    print("\nRequired:")
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Mask the value for security
            masked = value[:8] + "..." if len(value) > 8 else "***"
            print(f"✓ {var:25s} - Set ({masked})")
        else:
            error_msg = f"✗ {var:25s} - NOT SET"
            print(error_msg)
            errors.append(error_msg)
    
    # Check optional variables
    print("\nOptional:")
    for var in optional_vars:
        value = os.getenv(var)
        if value:
            masked = value[:8] + "..." if len(value) > 8 else "***"
            print(f"✓ {var:25s} - Set ({masked})")
        else:
            warning_msg = f"⚠ {var:25s} - Not set"
            print(warning_msg)
            warnings.append(warning_msg)
    
    success = len(errors) == 0
    print(f"\nResult: {'PASSED' if success else 'FAILED'}")
    if warnings:
        print(f"Warnings: {len(warnings)}")
    return success, errors


def test_mcp_connection() -> Tuple[bool, List[str]]:
    """
    Test Neo4j MCP connection.
    
    Returns:
        Tuple of (success: bool, error_messages: List[str])
    """
    print("\n" + "="*60)
    print("TEST 3: Neo4j MCP Connection")
    print("="*60)
    
    errors = []
    
    try:
        from langchain_mcp import MCPToolkit
        
        print("\nAttempting to connect to Neo4j MCP server...")
        
        # Try to initialize MCP toolkit
        toolkit = MCPToolkit(
            server_name="neo4j-test",
            connection_type="stdio"
        )
        
        print("✓ MCP Toolkit initialized")
        
        # Get available tools
        tools = toolkit.get_tools()
        print(f"✓ Found {len(tools)} MCP tools:")
        
        for tool in tools:
            print(f"  - {tool.name}")
        
        print("\nResult: PASSED")
        return True, []
        
    except Exception as e:
        error_msg = f"✗ MCP Connection failed: {str(e)}"
        print(error_msg)
        errors.append(error_msg)
        print("\nResult: FAILED")
        print("\nNote: Neo4j MCP connection is optional for testing.")
        print("The workflow will warn if MCP is unavailable but can still run.")
        return False, errors


def test_file_operations() -> Tuple[bool, List[str]]:
    """
    Test file I/O operations.
    
    Returns:
        Tuple of (success: bool, error_messages: List[str])
    """
    print("\n" + "="*60)
    print("TEST 4: File Operations")
    print("="*60)
    
    errors = []
    test_dir = "/tmp/deep_agents_test"
    test_file = os.path.join(test_dir, "test.txt")
    
    try:
        # Test directory creation
        os.makedirs(test_dir, exist_ok=True)
        print(f"✓ Created test directory: {test_dir}")
        
        # Test file write
        test_content = "Test content for Deep Agents workflow"
        with open(test_file, 'w') as f:
            f.write(test_content)
        print(f"✓ Wrote test file: {test_file}")
        
        # Test file read
        with open(test_file, 'r') as f:
            read_content = f.read()
        
        if read_content == test_content:
            print(f"✓ Read test file successfully")
        else:
            error_msg = "✗ File content mismatch"
            print(error_msg)
            errors.append(error_msg)
        
        # Cleanup
        os.remove(test_file)
        os.rmdir(test_dir)
        print(f"✓ Cleaned up test files")
        
        print("\nResult: PASSED")
        return True, []
        
    except Exception as e:
        error_msg = f"✗ File operations failed: {str(e)}"
        print(error_msg)
        errors.append(error_msg)
        print("\nResult: FAILED")
        return False, errors


def test_yaml_config() -> Tuple[bool, List[str]]:
    """
    Test YAML configuration loading.
    
    Returns:
        Tuple of (success: bool, error_messages: List[str])
    """
    print("\n" + "="*60)
    print("TEST 5: YAML Configuration")
    print("="*60)
    
    errors = []
    
    try:
        import yaml
        
        # Test YAML parsing
        test_config = """
event:
  name: "test"
  year: 2025
recommendation:
  min_similarity_score: 0.5
  max_recommendations: 20
"""
        
        config = yaml.safe_load(test_config)
        print(f"✓ Parsed YAML configuration")
        print(f"  - Event: {config['event']['name']}")
        print(f"  - Year: {config['event']['year']}")
        print(f"  - Min similarity: {config['recommendation']['min_similarity_score']}")
        
        print("\nResult: PASSED")
        return True, []
        
    except Exception as e:
        error_msg = f"✗ YAML configuration test failed: {str(e)}"
        print(error_msg)
        errors.append(error_msg)
        print("\nResult: FAILED")
        return False, errors


def test_langchain_anthropic() -> Tuple[bool, List[str]]:
    """
    Test LangChain Anthropic integration.
    
    Returns:
        Tuple of (success: bool, error_messages: List[str])
    """
    print("\n" + "="*60)
    print("TEST 6: LangChain Anthropic Integration")
    print("="*60)
    
    errors = []
    
    try:
        from langchain_anthropic import ChatAnthropic
        from dotenv import load_dotenv
        
        load_dotenv()
        
        # Initialize LLM (don't call it, just initialize)
        llm = ChatAnthropic(
            model="claude-sonnet-4-20250514",
            temperature=0
        )
        
        print(f"✓ Initialized ChatAnthropic")
        print(f"  - Model: claude-sonnet-4-20250514")
        print(f"  - Temperature: 0")
        
        print("\nResult: PASSED")
        print("\nNote: This test only validates initialization.")
        print("Actual API calls require a valid ANTHROPIC_API_KEY.")
        
        return True, []
        
    except Exception as e:
        error_msg = f"✗ LangChain Anthropic test failed: {str(e)}"
        print(error_msg)
        errors.append(error_msg)
        print("\nResult: FAILED")
        return False, errors


def run_all_tests() -> bool:
    """
    Run all tests and provide summary.
    
    Returns:
        True if all tests passed, False otherwise
    """
    print("\n" + "="*60)
    print("DEEP AGENTS WORKFLOW - TEST SUITE")
    print("="*60)
    
    tests = [
        ("Python Dependencies", test_imports),
        ("Environment Variables", test_environment_variables),
        ("Neo4j MCP Connection", test_mcp_connection),
        ("File Operations", test_file_operations),
        ("YAML Configuration", test_yaml_config),
        ("LangChain Anthropic", test_langchain_anthropic),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            success, errors = test_func()
            results.append((test_name, success, errors))
        except Exception as e:
            print(f"\n✗ Test '{test_name}' crashed: {str(e)}")
            results.append((test_name, False, [str(e)]))
    
    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, success, _ in results if success)
    total = len(results)
    
    for test_name, success, errors in results:
        status = "✓ PASSED" if success else "✗ FAILED"
        print(f"{test_name:30s} - {status}")
        if errors and not success:
            for error in errors[:3]:  # Show first 3 errors
                print(f"  {error}")
    
    print("\n" + "="*60)
    print(f"Results: {passed}/{total} tests passed")
    print("="*60)
    
    if passed == total:
        print("\n✓ All tests passed! You're ready to run the workflow.")
        return True
    else:
        print(f"\n⚠ {total - passed} test(s) failed. Please review the errors above.")
        print("\nCommon fixes:")
        print("1. Install missing dependencies: uv pip install -r requirements.txt")
        print("2. Set environment variables in .env file")
        print("3. Configure Neo4j MCP server (optional but recommended)")
        return False


def main():
    """Main entry point"""
    success = run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
