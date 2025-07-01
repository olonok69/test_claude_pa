#!/usr/bin/env python3
"""
Test script to verify LinkedIn API connection works
"""

import os
import sys
from dotenv import load_dotenv
from open_linkedin_api import Linkedin

def test_linkedin_connection():
    """Test basic LinkedIn connection and functionality"""
    
    # Load environment variables
    load_dotenv()
    
    username = os.getenv("LINKEDIN_USERNAME")
    password = os.getenv("LINKEDIN_PASSWORD")
    
    if not username or not password:
        print("❌ ERROR: LinkedIn credentials not found in .env file")
        print("Please make sure your .env file contains:")
        print("LINKEDIN_USERNAME=your_email@example.com")
        print("LINKEDIN_PASSWORD=your_password")
        return False
    
    print(f"🔄 Testing LinkedIn connection for: {username}")
    
    try:
        # Initialize LinkedIn client
        api = Linkedin(username, password)
        print("✅ LinkedIn client initialized successfully")
        
        # Test 1: Get current user profile
        print("🔄 Testing: Get current user profile...")
        profile = api.get_user_profile()
        if profile and 'firstName' in profile:
            print(f"✅ Current user profile: {profile.get('firstName', '')} {profile.get('lastName', '')}")
        else:
            print("⚠️  Current user profile retrieved but may be incomplete")
        
        # Test 2: Simple people search
        print("🔄 Testing: Search people...")
        search_results = api.search_people(keywords="engineer", limit=5)
        if search_results:
            print(f"✅ People search successful: Found {len(search_results)} results")
            for i, person in enumerate(search_results[:3], 1):
                name = person.get('name', 'Unknown')
                title = person.get('jobtitle', 'No title')
                print(f"   {i}. {name} - {title}")
        else:
            print("⚠️  People search returned no results")
        
        # Test 3: Company search
        print("🔄 Testing: Search companies...")
        company_results = api.search_companies(keywords="technology", limit=3)
        if company_results:
            print(f"✅ Company search successful: Found {len(company_results)} results")
            for i, company in enumerate(company_results[:2], 1):
                name = company.get('name', 'Unknown')
                headline = company.get('headline', 'No headline')
                print(f"   {i}. {name} - {headline}")
        else:
            print("⚠️  Company search returned no results")
        
        print("\n🎉 All tests completed successfully!")
        print("Your LinkedIn connection is working properly.")
        return True
        
    except Exception as e:
        print(f"❌ ERROR: LinkedIn connection failed: {e}")
        print("\nTroubleshooting tips:")
        print("1. Verify your LinkedIn email and password are correct")
        print("2. Check if LinkedIn has temporarily blocked your account")
        print("3. Try logging into LinkedIn manually in your browser")
        print("4. Make sure you don't have 2FA enabled, or use app-specific password")
        return False

if __name__ == "__main__":
    success = test_linkedin_connection()
    sys.exit(0 if success else 1)