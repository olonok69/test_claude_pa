import os
import json
import logging
import aiohttp
import csv
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv
from pathlib import Path

from mcp.types import TextContent
from mcp.server.fastmcp import FastMCP
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.responses import JSONResponse
from perplexity_mcp import __version__

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("perplexity_mcp_sse_server")

# Create MCP server and transport
mcp = FastMCP("Perplexity MCP Server", host="0.0.0.0", port=8001)
transport = SseServerTransport("/messages/")

def validate_environment():
    """Validate required environment variables."""
    api_key = os.getenv("PERPLEXITY_API_KEY")
    if not api_key:
        logger.error("PERPLEXITY_API_KEY environment variable is required")
        raise ValueError("PERPLEXITY_API_KEY environment variable is required")
    
    model = os.getenv("PERPLEXITY_MODEL", "sonar")
    logger.info(f"Using Perplexity AI model: {model}")
    
    # List available models for reference
    available_models = {
        "sonar-deep-research": "128k context - Enhanced research capabilities",
        "sonar-reasoning-pro": "128k context - Advanced reasoning with professional focus", 
        "sonar-reasoning": "128k context - Enhanced reasoning capabilities",
        "sonar-pro": "200k context - Professional grade model",
        "sonar": "128k context - Default model",
        "r1-1776": "128k context - Alternative architecture"
    }
    
    logger.info("Available Perplexity models (set with PERPLEXITY_MODEL environment variable):")
    for model_name, description in available_models.items():
        marker = "→" if model_name == model else " "
        logger.info(f" {marker} {model_name}: {description}")
    
    return api_key, model

def load_csv_data() -> List[Dict[str, str]]:
    """Load and parse the CSV file."""
    csv_path = Path(__file__).parent / "src" / "perplexity_mcp" / "categories" / "classes.csv"
    
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

def get_show_categories() -> Dict[str, List[str]]:
    """Get categories organized by show."""
    csv_data = load_csv_data()
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
    
    return shows

def get_industry_categories() -> Dict[str, List[str]]:
    """Get categories organized by industry."""
    csv_data = load_csv_data()
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
    
    return industries

@mcp.resource("categories://all")
def get_all_categories() -> str:
    """Get all categories from the CSV file as raw data."""
    csv_data = load_csv_data()
    
    if not csv_data:
        return "No category data available."
    
    # Return as formatted JSON for easy consumption
    return json.dumps({
        "total_categories": len(csv_data),
        "categories": csv_data,
        "description": "Complete list of show categories with industries and products"
    }, indent=2)

@mcp.resource("categories://shows")
def get_shows_overview() -> str:
    """Get categories organized by show."""
    shows = get_show_categories()
    
    if not shows:
        return "No show data available."
    
    # Create summary
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

@mcp.resource("categories://shows/{show_name}")
def get_show_categories(show_name: str) -> str:
    """Get categories for a specific show."""
    shows = get_show_categories()
    
    # Normalize show name for matching
    show_name_normalized = show_name.upper().strip()
    
    for show, categories in shows.items():
        if show.upper().strip() == show_name_normalized:
            return json.dumps({
                "show": show,
                "total_categories": len(categories),
                "industries": list(set(cat['industry'] for cat in categories)),
                "categories": categories
            }, indent=2)
    
    available_shows = list(shows.keys())
    return json.dumps({
        "error": f"Show '{show_name}' not found",
        "available_shows": available_shows
    }, indent=2)

@mcp.resource("categories://industries")
def get_industries_overview() -> str:
    """Get categories organized by industry."""
    industries = get_industry_categories()
    
    if not industries:
        return "No industry data available."
    
    # Create summary
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

@mcp.resource("categories://industries/{industry_name}")
def get_industry_categories(industry_name: str) -> str:
    """Get categories for a specific industry."""
    industries = get_industry_categories()
    
    # Normalize industry name for matching
    industry_name_normalized = industry_name.lower().strip()
    
    for industry, products in industries.items():
        if industry.lower().strip() == industry_name_normalized:
            return json.dumps({
                "industry": industry,
                "total_products": len(products),
                "shows": list(set(prod['show'] for prod in products if prod['show'])),
                "products": products
            }, indent=2)
    
    available_industries = list(industries.keys())
    return json.dumps({
        "error": f"Industry '{industry_name}' not found",
        "available_industries": available_industries
    }, indent=2)

@mcp.resource("categories://search/{query}")
def search_categories(query: str) -> str:
    """Search categories by query string."""
    csv_data = load_csv_data()
    
    if not csv_data or not query:
        return json.dumps({"error": "No data or empty query"}, indent=2)
    
    query_lower = query.lower().strip()
    matches = []
    
    for row in csv_data:
        # Search in all fields
        show = row.get('Show', '').lower()
        industry = row.get('Industry', '').lower()
        product = row.get('Product', '').lower()
        
        if (query_lower in show or 
            query_lower in industry or 
            query_lower in product):
            matches.append(row)
    
    return json.dumps({
        "query": query,
        "total_matches": len(matches),
        "matches": matches
    }, indent=2)

async def call_perplexity_api(query: str, recency: str = "month") -> Dict[str, Any]:
    """Call the Perplexity API with the given query and recency filter."""
    api_key, model = validate_environment()
    
    url = "https://api.perplexity.ai/chat/completions"
    
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "Be precise and concise."},
            {"role": "user", "content": query},
        ],
        "max_tokens": "512",
        "temperature": 0.2,
        "top_p": 0.9,
        "return_images": False,
        "return_related_questions": False,
        "search_recency_filter": recency,
        "top_k": 0,
        "stream": False,
        "presence_penalty": 0,
        "frequency_penalty": 1,
        "return_citations": True,
        "search_context_size": "low",
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, headers=headers) as response:
            response.raise_for_status()
            data = await response.json()
            return data

@mcp.tool()
async def perplexity_search_web(query: str, recency: str = "month") -> list[TextContent]:
    """Search the web using Perplexity AI with recency filtering.
    
    Args:
        query: The search query to find information about
        recency: Filter results by how recent they are. Options: 'day' (last 24h), 
                'week' (last 7 days), 'month' (last 30 days), 'year' (last 365 days)
    
    Returns:
        TextContent with the search results and citations
    """
    # Validate recency parameter
    valid_recency = ["day", "week", "month", "year"]
    if recency not in valid_recency:
        logger.warning(f"Invalid recency '{recency}', defaulting to 'month'")
        recency = "month"
    
    logger.info(f"Executing Perplexity search - Query: '{query}', Recency: '{recency}'")
    
    try:
        data = await call_perplexity_api(query, recency)
        content = data["choices"][0]["message"]["content"]
        
        # Format response with metadata and citations
        result = {
            "query": query,
            "recency_filter": recency,
            "model": os.getenv("PERPLEXITY_MODEL", "sonar"),
            "content": content,
            "usage": data.get("usage", {}),
            "citations": data.get("citations", [])
        }
        
        # Create formatted response
        formatted_response = f"**Query:** {query}\n"
        formatted_response += f"**Recency Filter:** {recency}\n"
        formatted_response += f"**Model:** {result['model']}\n\n"
        formatted_response += f"**Response:**\n{content}\n"
        
        if result["citations"]:
            formatted_response += "\n**Citations:**\n"
            for i, url in enumerate(result["citations"], 1):
                formatted_response += f"[{i}] {url}\n"
        
        if result["usage"]:
            formatted_response += f"\n**Token Usage:** {json.dumps(result['usage'])}"
        
        return [TextContent(type="text", text=formatted_response)]
        
    except aiohttp.ClientResponseError as e:
        error_msg = f"Perplexity API error: HTTP {e.status} - {e.message}"
        logger.error(error_msg)
        return [TextContent(type="text", text=f"Error: {error_msg}")]
    
    except Exception as e:
        error_msg = f"Error calling Perplexity API: {str(e)}"
        logger.error(error_msg)
        return [TextContent(type="text", text=f"Error: {error_msg}")]

@mcp.tool()
async def perplexity_advanced_search(
    query: str, 
    recency: str = "month",
    model: Optional[str] = None,
    max_tokens: int = 512,
    temperature: float = 0.2
) -> list[TextContent]:
    """Advanced Perplexity search with custom parameters.
    
    Args:
        query: The search query to find information about
        recency: Filter results by recency ('day', 'week', 'month', 'year')
        model: Override the default model (optional)
        max_tokens: Maximum tokens in response (default: 512)
        temperature: Response randomness (0.0-1.0, default: 0.2)
    
    Returns:
        TextContent with detailed search results and metadata
    """
    # Use provided model or fall back to environment/default
    if model is None:
        model = os.getenv("PERPLEXITY_MODEL", "sonar")
    
    # Validate parameters
    if recency not in ["day", "week", "month", "year"]:
        recency = "month"
    
    max_tokens = max(1, min(max_tokens, 2048))  # Clamp between 1 and 2048
    temperature = max(0.0, min(temperature, 1.0))  # Clamp between 0 and 1
    
    logger.info(f"Advanced Perplexity search - Query: '{query}', Model: '{model}', "
                f"Recency: '{recency}', Max tokens: {max_tokens}, Temperature: {temperature}")
    
    try:
        api_key = os.getenv("PERPLEXITY_API_KEY")
        if not api_key:
            raise ValueError("PERPLEXITY_API_KEY environment variable is required")
        
        url = "https://api.perplexity.ai/chat/completions"
        
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "Be precise and concise."},
                {"role": "user", "content": query},
            ],
            "max_tokens": str(max_tokens),
            "temperature": temperature,
            "top_p": 0.9,
            "return_images": False,
            "return_related_questions": False,
            "search_recency_filter": recency,
            "top_k": 0,
            "stream": False,
            "presence_penalty": 0,
            "frequency_penalty": 1,
            "return_citations": True,
            "search_context_size": "low",
        }

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as response:
                response.raise_for_status()
                data = await response.json()
        
        content = data["choices"][0]["message"]["content"]
        
        # Create comprehensive result
        result = {
            "query": query,
            "model": model,
            "recency_filter": recency,
            "parameters": {
                "max_tokens": max_tokens,
                "temperature": temperature
            },
            "content": content,
            "usage": data.get("usage", {}),
            "citations": data.get("citations", []),
            "finish_reason": data["choices"][0].get("finish_reason"),
            "response_metadata": {
                "timestamp": data.get("created"),
                "model_version": data.get("model")
            }
        }
        
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
    except Exception as e:
        error_msg = f"Error in advanced Perplexity search: {str(e)}"
        logger.error(error_msg)
        return [TextContent(type="text", text=f"Error: {error_msg}")]

@mcp.tool()
async def search_show_categories(
    show_name: Optional[str] = None,
    industry_filter: Optional[str] = None,
    product_filter: Optional[str] = None
) -> list[TextContent]:
    """Search and filter show categories from the CSV data.
    
    Args:
        show_name: Filter by specific show (CAI, DOL, CCSE, BDAIW, DCW)
        industry_filter: Filter by industry name (partial match)
        product_filter: Filter by product name (partial match)
    
    Returns:
        TextContent with filtered category results
    """
    csv_data = load_csv_data()
    
    if not csv_data:
        return [TextContent(type="text", text="No category data available.")]
    
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
    
    return [TextContent(type="text", text=json.dumps(result, indent=2))]

async def health_check(request):
    """Health check endpoint that validates Perplexity API connection and CSV data."""
    try:
        api_key = os.getenv("PERPLEXITY_API_KEY")
        model = os.getenv("PERPLEXITY_MODEL", "sonar")
        
        # Check CSV data
        csv_data = load_csv_data()
        csv_status = {
            "available": len(csv_data) > 0,
            "total_records": len(csv_data),
            "shows": list(set(row.get('Show', '') for row in csv_data if row.get('Show')))
        }
        
        if not api_key:
            return JSONResponse({
                "status": "unhealthy",
                "error": "PERPLEXITY_API_KEY not configured",
                "csv_data": csv_status
            })
        
        # Test API connection with a simple query
        test_data = await call_perplexity_api("test connection", "day")
        
        return JSONResponse({
            "status": "healthy",
            "version": __version__,
            "model": model,
            "api_key_configured": bool(api_key),
            "test_query_successful": True,
            "csv_data": csv_status,
            "available_models": [
                "sonar-deep-research",
                "sonar-reasoning-pro", 
                "sonar-reasoning",
                "sonar-pro",
                "sonar",
                "r1-1776"
            ],
            "available_resources": [
                "categories://all",
                "categories://shows",
                "categories://shows/{show_name}",
                "categories://industries",
                "categories://industries/{industry_name}",
                "categories://search/{query}"
            ]
        })
        
    except Exception as e:
        csv_data = load_csv_data()
        csv_status = {
            "available": len(csv_data) > 0,
            "total_records": len(csv_data),
            "shows": list(set(row.get('Show', '') for row in csv_data if row.get('Show')))
        }
        
        return JSONResponse({
            "status": "unhealthy",
            "error": str(e),
            "version": __version__,
            "model": os.getenv("PERPLEXITY_MODEL", "sonar"),
            "api_key_configured": bool(os.getenv("PERPLEXITY_API_KEY")),
            "csv_data": csv_status
        })

async def handle_sse(request):
    """Handle SSE connections for MCP."""
    async with transport.connect_sse(request.scope, request.receive, request._send) as (
        in_stream, out_stream,
    ):
        await mcp._mcp_server.run(
            in_stream, out_stream, mcp._mcp_server.create_initialization_options()
        )

# Build the complete Starlette app with all routes
app = Starlette(
    routes=[
        Route("/health", health_check, methods=["GET"]),
        Route("/sse", handle_sse, methods=["GET"]),
        Mount("/messages/", app=transport.handle_post_message),
    ]
)

if __name__ == "__main__":
    import uvicorn
    
    try:
        # Validate environment on startup
        validate_environment()
        
        # Load and validate CSV data
        csv_data = load_csv_data()
        if csv_data:
            logger.info(f"CSV data loaded successfully: {len(csv_data)} records")
            shows = set(row.get('Show', '') for row in csv_data if row.get('Show'))
            logger.info(f"Available shows: {', '.join(sorted(shows))}")
        else:
            logger.warning("No CSV data loaded - resources will return empty results")
        
        logger.info(f"Starting Perplexity MCP Server v{__version__} with SSE transport...")
        logger.info("Perplexity MCP Server running on http://0.0.0.0:8001")
        logger.info("SSE endpoint: http://0.0.0.0:8001/sse")
        logger.info("Health check: http://0.0.0.0:8001/health")
        logger.info("Available MCP resources:")
        logger.info("  - categories://all")
        logger.info("  - categories://shows")
        logger.info("  - categories://shows/{show_name}")
        logger.info("  - categories://industries")
        logger.info("  - categories://industries/{industry_name}")
        logger.info("  - categories://search/{query}")
        
        uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
        
    except ValueError as e:
        logger.error(f"Configuration error: {str(e)}")
        exit(1)
    except Exception as e:
        logger.error(f"Startup error: {str(e)}")
        exit(1)