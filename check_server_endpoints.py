#!/usr/bin/env python3
"""
Quick script to check what endpoints are available on each server
"""

import requests

def check_endpoint(url, description):
    try:
        response = requests.get(url, timeout=5)
        print(f"{description}: {response.status_code} - {response.text[:100]}...")
    except Exception as e:
        print(f"{description}: ERROR - {e}")

def main():
    print("🔍 Checking server endpoints...\n")
    
    # Server 3 (Yahoo Finance)
    print("📊 Yahoo Finance Server (Port 8002):")
    check_endpoint("http://localhost:8002/", "Root endpoint")
    check_endpoint("http://localhost:8002/health", "Health endpoint")
    check_endpoint("http://localhost:8002/sse", "SSE endpoint")
    print()
    
    # Server 4 (Neo4j)
    print("🗄️ Neo4j Server (Port 8003):")
    check_endpoint("http://localhost:8003/", "Root endpoint") 
    check_endpoint("http://localhost:8003/health", "Health endpoint")
    check_endpoint("http://localhost:8003/sse", "SSE endpoint")
    print()
    
    # Server 5 (HubSpot)
    print("🏢 HubSpot Server (Port 8004):")
    check_endpoint("http://localhost:8004/", "Root endpoint")
    check_endpoint("http://localhost:8004/health", "Health endpoint")
    check_endpoint("http://localhost:8004/sse", "SSE endpoint")

if __name__ == "__main__":
    main()