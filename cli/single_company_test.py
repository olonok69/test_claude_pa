#!/usr/bin/env python3
"""
Create a single company test CSV for debugging
"""

import csv

def create_single_company_test():
    """Create a CSV file with just one company for testing."""
    
    company_data = {
        'CASEACCID': 'TEST001',
        'Account Name': 'Microsoft',
        'Trading Name': 'Microsoft',
        'Domain': 'microsoft.com',
        'Industry': '',
        'Product/Service Type': '',
        'Event': 'Cloud and AI Infrastructure'
    }
    
    with open('single_test.csv', 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['CASEACCID', 'Account Name', 'Trading Name', 'Domain', 'Industry', 'Product/Service Type', 'Event']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        writer.writerow(company_data)
    
    print("✅ Created single_test.csv with Microsoft for testing")
    
    # Also show the content
    print("\n📋 CSV Content:")
    with open('single_test.csv', 'r') as f:
        print(f.read())

if __name__ == "__main__":
    create_single_company_test()