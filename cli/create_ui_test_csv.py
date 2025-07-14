#!/usr/bin/env python3
"""
Create a CSV file with exactly the same 3 companies that worked in the UI
"""

import csv

def create_ui_test_csv():
    """Create CSV with the exact 3 companies from the UI example."""
    
    companies = [
        {
            'CASEACCID': 'UI001',
            'Account Name': 'GMV',
            'Trading Name': '',
            'Domain': 'gmv.com',
            'Industry': '',
            'Product/Service Type': '',
            'Event': '100 Optical; ADAS and Autonomous Vehicle Technology Expo Europe; ADAS and Autonomous Vehicle Technology Expo USA; Cloud Security London'
        },
        {
            'CASEACCID': 'UI002', 
            'Account Name': 'IQVIA',
            'Trading Name': 'IQVIA',
            'Domain': 'iqvia.com',
            'Industry': '',
            'Product/Service Type': '',
            'Event': '100 Optical; Best Practice; Big Data Expo; Clinical Pharmacy Congress; Digital Health Intelligence Networks; Genomics and Precision Medicine Expo; Oncology Professional Care'
        },
        {
            'CASEACCID': 'UI003',
            'Account Name': 'Keepler', 
            'Trading Name': 'Keepler',
            'Domain': 'keepler.io',
            'Industry': '',
            'Product/Service Type': '',
            'Event': '100 Optical; Best Practice; Big Data Expo; Clinical Pharmacy Congress; Digital Health Intelligence Networks; Genomics and Precision Medicine Expo; Oncology Professional Care'
        }
    ]
    
    with open('ui_test.csv', 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['CASEACCID', 'Account Name', 'Trading Name', 'Domain', 'Industry', 'Product/Service Type', 'Event']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        writer.writerows(companies)
    
    print("✅ Created ui_test.csv with the exact 3 companies from your UI example")
    
    # Show what the CLI will generate
    print("\n📋 This should generate the following format:")
    for i, company in enumerate(companies, 1):
        print(f"\nCompany {i}:")
        print(f"Account Name = {company['Account Name']}")
        print(f"Trading Name = {company['Trading Name']}")
        print(f"Domain = {company['Domain']}")
        print(f"Product/Service Type = {company['Product/Service Type']}")
        print(f"Industry = {company['Industry']}")
        print(f"Event = {company['Event']}")

if __name__ == "__main__":
    create_ui_test_csv()