#!/usr/bin/env python3
"""
Health check script for all MCP servers in the application.
Run this script to verify all services are running correctly.
"""

import requests
import json
from typing import Dict, Any

def check_server_health(name: str, url: str) -> Dict[str, Any]:
    """Check the health of a single server."""
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            try:
                data = response.json()
                return {
                    "status": "healthy",
                    "response_time": response.elapsed.total_seconds(),
                    "data": data
                }
            except json.JSONDecodeError:
                return {
                    "status": "healthy", 
                    "response_time": response.elapsed.total_seconds(),
                    "data": response.text
                }
        else:
            return {
                "status": "unhealthy",
                "error": f"HTTP {response.status_code}",
                "response_time": response.elapsed.total_seconds()
            }
    except requests.exceptions.ConnectionError:
        return {"status": "unreachable", "error": "Connection refused"}
    except requests.exceptions.Timeout:
        return {"status": "timeout", "error": "Request timed out"}
    except Exception as e:
        return {"status": "error", "error": str(e)}

def main():
    """Check health of all servers."""
    servers = {
        "Yahoo Finance MCP Server": "http://localhost:8002/health",
        "Neo4j MCP Server": "http://localhost:8003/health", 
        "HubSpot MCP Server": "http://localhost:8004/health",
        "Streamlit Client": "http://localhost:8501"
    }
    
    # Alternative endpoints to try if main health check fails
    fallback_servers = {
        "Yahoo Finance MCP Server": "http://localhost:8002/",
        "Neo4j MCP Server": "http://localhost:8003/",
    }
    
    print("🔍 Checking health of all services...\n")
    
    all_healthy = True
    
    for name, url in servers.items():
        print(f"Checking {name}...")
        result = check_server_health(name, url)
        
        # If main health check fails, try fallback for specific servers
        if result["status"] != "healthy" and name in fallback_servers:
            print(f"  ⚠️  Main health endpoint failed, trying fallback...")
            fallback_url = fallback_servers[name]
            result = check_server_health(name, fallback_url)
        
        if result["status"] == "healthy":
            print(f"  ✅ {name} is healthy")
            if "response_time" in result:
                print(f"     Response time: {result['response_time']:.3f}s")
        else:
            print(f"  ❌ {name} is {result['status']}")
            if "error" in result:
                print(f"     Error: {result['error']}")
            all_healthy = False
        print()
    
    if all_healthy:
        print("🎉 All services are healthy!")
        print("\n📡 MCP Server Endpoints:")
        print("  - Yahoo Finance: http://localhost:8002/sse")
        print("  - Neo4j: http://localhost:8003/sse")
        print("  - HubSpot: http://localhost:8004/sse")
        print("\n🌐 Application URL:")
        print("  - Streamlit Client: http://localhost:8501")
    else:
        print("⚠️  Some services are not healthy. Please check the logs.")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())