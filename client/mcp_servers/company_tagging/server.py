#!/usr/bin/env python3
"""
Company Tagging MCP Server with stdio transport.
Provides category taxonomy resources for company research and categorization.
"""

import os
import json
import logging
import asyncio
import csv
from typing import Optional, Dict, Any, List
from pathlib import Path

from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    LoggingLevel,
)
import mcp.types as types

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("company_tagging_mcp")

# Initialize server
server = Server("company-tagging-mcp")

def load_csv_data() -> List[Dict[str, str]]:
    """Load and parse the CSV file."""
    csv_path = Path(__file__).parent / "categories" / "classes.csv"
    
    if not csv_path.exists():
        logger.warning(f"CSV file not found at {csv_path}")
        return []
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            data = list(csv_reader)
            logger.info(f"Loaded {len(data)} rows from CSV file")
            return data
    except Exception as e:
        logger.error(f"Error loading CSV file: {str(e)}")
        return []

def format_categories_for_analysis() -> str:
    """Format categories data for company analysis and tagging."""
    csv_data = load_csv_data()
    
    if not csv_data:
        return "No category data available."
    
    # Group by show for better organization
    shows_data = {}
    for row in csv_data:
        show = row.get('Show', '').strip()
        industry = row.get('Industry', '').strip()
        product = row.get('Product', '').strip()
        
        if show and industry and product:
            if show not in shows_data:
                shows_data[show] = []
            shows_data[show].append(f"{industry} | {product}")
    
    # Format for analysis
    formatted_output = "TAXONOMY CATEGORIES - Industry and Product Pairs by Show:\n\n"
    
    show_names = {
        'CAI': 'Cloud and AI Infrastructure',
        'DOL': 'DevOps Live', 
        'CCSE': 'Cloud and Cyber Security Expo',
        'BDAIW': 'Big Data and AI World',
        'DCW': 'Data Centre World'
    }
    
    for show_code, full_name in show_names.items():
        if show_code in shows_data:
            formatted_output += f"**{show_code} ({full_name}):**\n"
            for category in shows_data[show_code]:
                formatted_output += f"- {category}\n"
            formatted_output += "\n"
    
    formatted_output += f"Total categories available: {len(csv_data)}\n"
    formatted_output += "\nIMPORTANT: Use industry and product pairs EXACTLY as shown above. Do not modify spelling, spacing, or characters (for example, do not replace & with 'and')."
    
    return formatted_output

@server.list_resources()
async def handle_list_resources() -> list[Resource]:
    """List available resources."""
    resources = [
        Resource(
            uri="categories://all",
            name="All Categories",
            description="Complete list of show categories with industries and products",
            mimeType="application/json",
        ),
        Resource(
            uri="categories://shows",
            name="Categories by Show",
            description="Categories organized by show with statistics",
            mimeType="application/json",
        ),
        Resource(
            uri="categories://industries",
            name="Categories by Industry",
            description="Categories organized by industry",
            mimeType="application/json",
        ),
        Resource(
            uri="categories://for-analysis",
            name="Categories for Analysis",
            description="Categories formatted for company analysis and tagging",
            mimeType="text/plain",
        ),
        Resource(
            uri="categories://system-prompt",
            name="System Prompt for Company Tagging",
            description="Detailed system prompt with instructions for company categorization",
            mimeType="text/plain",
        ),
    ]
    
    # Add dynamic show-specific resources
    csv_data = load_csv_data()
    shows = set(row.get('Show', '') for row in csv_data if row.get('Show'))
    
    for show in shows:
        resources.append(
            Resource(
                uri=f"categories://shows/{show}",
                name=f"{show} Categories",
                description=f"Categories for {show} show",
                mimeType="application/json",
            )
        )
    
    return resources

@server.read_resource()
async def handle_read_resource(uri: str) -> str:
    """Read a specific resource."""
    csv_data = load_csv_data()
    
    if uri == "categories://all":
        return json.dumps({
            "total_categories": len(csv_data),
            "categories": csv_data,
            "description": "Complete list of show categories with industries and products"
        }, indent=2)
    
    elif uri == "categories://shows":
        shows = {}
        for row in csv_data:
            show = row.get('Show', '').strip()
            industry = row.get('Industry', '').strip()
            product = row.get('Product', '').strip()
            
            if show and industry and product:
                if show not in shows:
                    shows[show] = []
                shows[show].append({
                    'industry': industry,
                    'product': product
                })
        
        summary = {
            "total_shows": len(shows),
            "shows": {}
        }
        
        for show, categories in shows.items():
            summary["shows"][show] = {
                "total_categories": len(categories),
                "industries": list(set(cat['industry'] for cat in categories)),
                "categories": categories
            }
        
        return json.dumps(summary, indent=2)
    
    elif uri == "categories://industries":
        industries = {}
        for row in csv_data:
            industry = row.get('Industry', '').strip()
            product = row.get('Product', '').strip()
            show = row.get('Show', '').strip()
            
            if industry and product:
                if industry not in industries:
                    industries[industry] = []
                industries[industry].append({
                    'product': product,
                    'show': show
                })
        
        summary = {
            "total_industries": len(industries),
            "industries": {}
        }
        
        for industry, products in industries.items():
            summary["industries"][industry] = {
                "total_products": len(products),
                "shows": list(set(prod['show'] for prod in products if prod['show'])),
                "products": list(set(prod['product'] for prod in products))
            }
        
        return json.dumps(summary, indent=2)
    
    elif uri == "categories://for-analysis":
        return format_categories_for_analysis()
    
    elif uri == "categories://system-prompt":
        return """You are:
 a data analyst
Tasked with:
Tagging exhibitor companies with the most accurate tags from an industry and product taxonomy structure we have in our categories
Based on:
 products and services that each company is most likely to sell in each trade show.
What is important:
 Accuracy and consistency.
 
Instructions:
The taxonomy is our categories and is a set of pairs industry and product connected with a code of shows that companies might be interested to exhibit at.
The context is that companies might be interested in exhibiting at one or more technology shows: Big Data and AI World (BDAIW), DevOps Live (DOL), Data CenterWorld (DCW), Cloud and Cyber Security Expo (CSSE), and CAI (Cloud and AI Infrastructure).
The task is to find out what products and services each of those companies offers and allocate pairs of industry and product from the categories file.
A few important instructions to follow:
•The context of which show is important as companies could play in many industries and offer many products, but only the ones more relevant to the topics of the shows included in File 1 must be selected.
•Use any web sources available, including LinkedIn, as well as websites for each company.
•Use first the "Domain" if it exists. Second use the Trading Name If the first is blank (and only if this is blank) then if the rest blank use the main "Company Name".
•Donot add any new or different industries nor products from the taxonomy provided in our categories
•A company can have multiple industries and multiple products within each industry, hence select up to 4 pairs of industry and product
Process to follow:
-Choose what name to use (domain name, Trading Name if available, otherwise Account Name) and find relevant information in internet sources (use our google or perplexity tools) to identify what products and/or services they sell within the context of those shows.
-Understand the taxonomy categories (pairs of Industry and product for each show). retrieve all categories available
-Check what relevant shows(from all categories) they might be interested in exhibiting at (attribute "Event" provided in the input). Now, in the context of these shows only:
-Allocate up to 4 pairs of Industry and Product from File 2 matching those products and services you just identified. Use only pairs are they appear exactly, no changes at all. Check that there are no spaces and that the spelling and characters used are identical (for example, do not replace & with "and").
Output:
Generate tables with the Company Name, the alternative "Trading Name", and add 8 columns for Tech Industry 1, Tech Product 1, Tech Industry 2, Tech Product 2, Tech Industry 3, Tech Product 3, Tech Industry 4 and Tech Product 4."""
    
    elif uri.startswith("categories://shows/"):
        show_name = uri.split("/")[-1].upper().strip()
        
        show_categories = []
        for row in csv_data:
            if row.get('Show', '').upper().strip() == show_name:
                show_categories.append({
                    'industry': row.get('Industry', '').strip(),
                    'product': row.get('Product', '').strip()
                })
        
        if show_categories:
            return json.dumps({
                "show": show_name,
                "total_categories": len(show_categories),
                "industries": list(set(cat['industry'] for cat in show_categories)),
                "categories": show_categories
            }, indent=2)
        else:
            available_shows = list(set(row.get('Show', '') for row in csv_data if row.get('Show')))
            return json.dumps({
                "error": f"Show '{show_name}' not found",
                "available_shows": available_shows
            }, indent=2)
    
    else:
        raise ValueError(f"Unknown resource URI: {uri}")

@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="search_show_categories",
            description="Search and filter show categories from the CSV data",
            inputSchema={
                "type": "object",
                "properties": {
                    "show_name": {
                        "type": "string",
                        "description": "Filter by specific show (CAI, DOL, CCSE, BDAIW, DCW)",
                    },
                    "industry_filter": {
                        "type": "string",
                        "description": "Filter by industry name (partial match)",
                    },
                    "product_filter": {
                        "type": "string",
                        "description": "Filter by product name (partial match)",
                    },
                },
            },
        ),
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict[str, Any] | None) -> list[types.TextContent]:
    """Handle tool calls."""
    if not arguments:
        arguments = {}
    
    if name == "search_show_categories":
        return await search_show_categories(arguments)
    else:
        raise ValueError(f"Unknown tool: {name}")

async def search_show_categories(arguments: dict[str, Any]) -> list[types.TextContent]:
    """Search and filter show categories from the CSV data."""
    csv_data = load_csv_data()
    
    if not csv_data:
        return [types.TextContent(type="text", text="No category data available.")]
    
    show_name = arguments.get("show_name")
    industry_filter = arguments.get("industry_filter")
    product_filter = arguments.get("product_filter")
    
    filtered_data = csv_data.copy()
    filters_applied = []
    
    # Apply show filter
    if show_name:
        show_name_upper = show_name.upper().strip()
        filtered_data = [row for row in filtered_data 
                        if row.get('Show', '').upper().strip() == show_name_upper]
        filters_applied.append(f"Show: {show_name}")
    
    # Apply industry filter
    if industry_filter:
        industry_lower = industry_filter.lower().strip()
        filtered_data = [row for row in filtered_data 
                        if industry_lower in row.get('Industry', '').lower()]
        filters_applied.append(f"Industry contains: {industry_filter}")
    
    # Apply product filter
    if product_filter:
        product_lower = product_filter.lower().strip()
        filtered_data = [row for row in filtered_data 
                        if product_lower in row.get('Product', '').lower()]
        filters_applied.append(f"Product contains: {product_filter}")
    
    # Organize results
    result = {
        "filters_applied": filters_applied,
        "total_matches": len(filtered_data),
        "original_total": len(csv_data),
        "matches": filtered_data
    }
    
    if not filtered_data:
        result["message"] = "No categories match the specified filters."
        result["available_shows"] = list(set(row.get('Show', '') for row in csv_data if row.get('Show')))
    
    return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

async def main():
    """Main entry point for the server."""
    # Run the server using stdio transport
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="company-tagging-mcp",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())