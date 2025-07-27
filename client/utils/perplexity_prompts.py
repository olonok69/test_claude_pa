# client/utils/perplexity_prompts.py - Fixed version with year recency

"""
Optimized prompts specifically designed for Perplexity Advanced Search tool
These prompts are structured to maximize the effectiveness of Perplexity's search capabilities
"""

from typing import Dict, List
from utils.ai_research_config import get_config, get_countries_for_commodity


def create_simple_test_prompt() -> str:
    """Create a simple test prompt to verify Perplexity connection"""
    return """Please use the perplexity_advanced_search tool to test the connection.

Search for "wheat production statistics 2024" with recency filter "year".

This is a simple test to verify that the Perplexity Advanced Search tool is working correctly. Please execute this search and return a brief confirmation that the tool is functioning."""


def create_perplexity_search_prompt(commodity: str, data_type: str) -> str:
    """
    Create a highly optimized prompt for Perplexity Advanced Search

    Args:
        commodity: 'wheat' or 'corn'
        data_type: 'production', 'exports', etc.

    Returns:
        Optimized prompt string for Perplexity Advanced Search
    """
    config = get_config(commodity, data_type)

    commodity_name = config["commodity"]["display_name"]
    data_name = config["data_type"]["display_name"]
    unit = config["data_type"]["unit"]
    countries = config["commodity"]["allowed_countries"]

    # Create the search query optimized for Perplexity
    search_query = f"{commodity_name.lower()} {data_name.lower()} 2024/2025 2025/2026 USDA IGC forecast statistics"

    # Format countries for better parsing
    countries_list = ", ".join(countries)

    prompt = f"""I need you to use the perplexity_advanced_search tool to find the latest official data for {commodity_name} {data_name} {unit}.

Please search for "{search_query}" with recency filter "year".

I need data for the marketing years 2024/2025 and 2025/2026 (projections) for these specific countries/regions: {countries_list}

Focus on official sources like USDA, IGC (International Grains Council), FAO, and national agricultural ministries.

After you get the search results, please provide the data in this structured format:

**WORLD:** 
- 2024/2025: [value] {unit}
- 2025/2026: [value] {unit}

**China:**
- 2024/2025: [value] {unit} 
- 2025/2026: [value] {unit}

[Continue for all countries...]

Please include source attribution and mark data as "Estimate", "Forecast", or "Projection" as appropriate. If data for a country is not available, clearly state "Data not available" rather than estimating.

Use the perplexity_advanced_search tool now to find this information."""

    return prompt


def create_follow_up_search_prompt(
    commodity: str, data_type: str, missing_countries: List[str]
) -> str:
    """
    Create a follow-up search prompt for countries with missing data

    Args:
        commodity: 'wheat' or 'corn'
        data_type: 'production', 'exports', etc.
        missing_countries: List of countries that need additional research

    Returns:
        Follow-up prompt for missing countries
    """
    config = get_config(commodity, data_type)
    commodity_name = config["commodity"]["display_name"]
    data_name = config["data_type"]["display_name"]
    unit = config["data_type"]["unit"]

    missing_list = ", ".join(missing_countries)

    # Create alternative search terms for specific countries
    alt_search_terms = {
        "European Union": "EU-27 wheat production statistics",
        "United States": "USA US wheat USDA production",
        "Russia": "Russian Federation wheat production ministry",
        "Australia": "ABARES Australian wheat production forecast",
        "Canada": "Statistics Canada wheat production Agriculture Agri-food",
        "India": "India wheat production ministry agriculture",
        "China": "China wheat production national bureau statistics",
    }

    search_query = f"{commodity_name.lower()} {data_name.lower()} 2024/2025 2025/2026 {missing_list.lower()}"

    prompt = f"""Please use perplexity_advanced_search to find specific data for these countries that were missing from the previous search:

**Countries needing data:** {missing_list}

**Search Query:** "{search_query}"
**Recency Filter:** "year"

**ALTERNATIVE SEARCH STRATEGIES:**
Try these specific approaches for each country:

"""

    for country in missing_countries:
        if country in alt_search_terms:
            prompt += f"- **{country}:** Search for '{alt_search_terms[country]}'\n"

    prompt += f"""
**SOURCES TO PRIORITIZE:**
- National agricultural statistics agencies
- Regional agricultural organizations
- Recent trade reports and market analyses
- International organization reports (FAO, OECD)

**OUTPUT FORMAT:**
Provide data in the same structured format as before:

**[Country Name]:**
- 2024/2025: [value] {unit}
- 2025/2026: [value] {unit}
- Source: [specific source and date]

Focus specifically on finding data for: {missing_list}
"""

    return prompt


def create_verification_search_prompt(
    commodity: str, data_type: str, country_data: Dict
) -> str:
    """
    Create a verification prompt to cross-check found data

    Args:
        commodity: 'wheat' or 'corn'
        data_type: 'production', 'exports', etc.
        country_data: Dictionary of found data to verify

    Returns:
        Verification prompt
    """
    config = get_config(commodity, data_type)
    commodity_name = config["commodity"]["display_name"]
    data_name = config["data_type"]["display_name"]

    countries_with_data = list(country_data.keys())
    countries_list = ", ".join(countries_with_data)

    prompt = f"""Please use perplexity_advanced_search to verify and cross-check the following {commodity_name} {data_name} data:

**Search Query:** "{commodity_name.lower()} {data_name.lower()} verification USDA IGC cross-check 2024/2025 2025/2026"
**Recency Filter:** "year"

**DATA TO VERIFY:**
"""

    for country, data in country_data.items():
        prompt += f"\n**{country}:**"
        if data.get("2024/2025"):
            prompt += f"\n- 2024/2025: {data['2024/2025']}"
        if data.get("2025/2026"):
            prompt += f"\n- 2025/2026: {data['2025/2026']}"

    prompt += f"""

**VERIFICATION INSTRUCTIONS:**
1. Search for the most recent official reports from USDA and IGC
2. Look for any contradictory information or significant differences
3. Check for updated forecasts or revisions published recently
4. Verify that the data represents the correct marketing year period

**OUTPUT FORMAT:**
For each country, indicate:
- **CONFIRMED:** Data matches multiple official sources
- **REVISED:** Data has been updated (provide new values)
- **CONFLICTED:** Sources show different values (list alternatives)
- **UNCERTAIN:** Cannot verify with current sources

Only report discrepancies or confirmations - don't repeat identical data."""

    return prompt


# Example usage for different commodities and data types
EXAMPLE_PROMPTS = {
    "wheat_production": create_perplexity_search_prompt("wheat", "production"),
    "wheat_exports": create_perplexity_search_prompt("wheat", "exports"),
    "corn_production": create_perplexity_search_prompt("corn", "production"),
    "corn_imports": create_perplexity_search_prompt("corn", "imports"),
}


def get_optimized_prompt(
    commodity: str, data_type: str, prompt_type: str = "main"
) -> str:
    """
    Get an optimized prompt for Perplexity Advanced Search

    Args:
        commodity: 'wheat' or 'corn'
        data_type: 'production', 'exports', etc.
        prompt_type: 'main', 'follow_up', or 'verification'

    Returns:
        Optimized prompt string
    """
    if prompt_type == "main":
        return create_perplexity_search_prompt(commodity, data_type)
    elif prompt_type == "follow_up":
        # This would need missing countries list - placeholder for now
        return create_follow_up_search_prompt(commodity, data_type, [])
    elif prompt_type == "verification":
        # This would need country data - placeholder for now
        return create_verification_search_prompt(commodity, data_type, {})
    else:
        raise ValueError(f"Unknown prompt type: {prompt_type}")


# Perplexity search tips and best practices
PERPLEXITY_BEST_PRACTICES = {
    "search_query_tips": [
        "Include specific years (2024/2025, 2025/2026)",
        "Use official agency names (USDA, IGC, FAO)",
        "Include commodity-specific terms",
        "Add geographic modifiers when needed",
    ],
    "recency_filters": {
        "year": "Most recent data within the past year (recommended for agricultural forecasts)",
        "month": "Very recent updates (use for breaking news)",
        "week": "Latest updates (use for urgent information)",
    },
    "parsing_tips": [
        "Look for structured tables in sources",
        "Cross-reference multiple official sources",
        "Note data revision dates and methodology",
        "Distinguish between estimates and projections",
    ],
}
