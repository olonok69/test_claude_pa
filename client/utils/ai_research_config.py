# client/utils/ai_research_config.py

"""
Configuration file for AI Research functionality across different commodities and data types.
This makes it easy to adapt the AI research feature for all wheat and corn pages.
"""

# Commodity configurations
COMMODITY_CONFIGS = {
    "wheat": {
        "display_name": "Wheat",
        "db_file": "wheat_production.db",
        "db_helper_class": "WheatProductionDB",
        "db_helper_module": "wheat_helpers.database_helper",
        "allowed_countries": [
            "WORLD",
            "China",
            "European Union",
            "India",
            "Russia",
            "United States",
            "Australia",
            "Canada",
        ],
    },
    "corn": {
        "display_name": "Corn",
        "db_file": "corn_production.db",
        "db_helper_class": "CornProductionDB",
        "db_helper_module": "corn_helpers.database_helper",
        "allowed_countries": [
            "WORLD",
            "United States",
            "China",
            "Brazil",
            "European Union",
            "Argentina",
            "Ukraine",
            "India",
        ],
    },
}

# Data type configurations
DATA_TYPE_CONFIGS = {
    "production": {
        "display_name": "Production",
        "unit": "(1000 MT)",
        "db_methods": {
            "get_data": "get_all_production_data",
            "update_data": "update_production_value",
        },
        "igc_section": "wheat section" if "wheat" else "corn section",
        "usda_crop_id": "0410000",  # wheat crop ID
        "usda_rank_by": "Production",
        "sites": [
            "https://www.igc.int/en/markets/marketinfo-forecasts.aspx#",
            "https://ipad.fas.usda.gov/cropexplorer/cropview/commodityView.aspx?cropid={crop_id}&sel_year=2024&rankby={rank_by}",
            "https://www.fas.usda.gov/",
            "https://www.fas.usda.gov/data",
        ],
    },
    "exports": {
        "display_name": "Exports",
        "unit": "(1000 MT)",
        "db_methods": {
            "get_data": "get_all_export_data",
            "update_data": "update_export_value",
        },
        "igc_section": "wheat section",
        "usda_crop_id": "0410000",
        "usda_rank_by": "Exports",
        "sites": [
            "https://www.igc.int/en/markets/marketinfo-forecasts.aspx#",
            "https://ipad.fas.usda.gov/cropexplorer/cropview/commodityView.aspx?cropid={crop_id}&sel_year=2024&rankby={rank_by}",
            "https://www.fas.usda.gov/",
            "https://www.fas.usda.gov/data",
        ],
    },
    "imports": {
        "display_name": "Imports",
        "unit": "(1000 MT)",
        "db_methods": {
            "get_data": "get_all_import_data",
            "update_data": "update_import_value",
        },
        "igc_section": "wheat section",
        "usda_crop_id": "0410000",
        "usda_rank_by": "Imports",
        "sites": [
            "https://www.igc.int/en/markets/marketinfo-forecasts.aspx#",
            "https://ipad.fas.usda.gov/cropexplorer/cropview/commodityView.aspx?cropid={crop_id}&sel_year=2024&rankby={rank_by}",
            "https://www.fas.usda.gov/",
            "https://www.fas.usda.gov/data",
        ],
    },
    "stocks": {
        "display_name": "Ending Stocks",
        "unit": "(1000 MT)",
        "db_methods": {
            "get_data": "get_all_stocks_data",
            "update_data": "update_stocks_value",
        },
        "igc_section": "wheat section",
        "usda_crop_id": "0410000",
        "usda_rank_by": "Ending_Stocks",
        "sites": [
            "https://www.igc.int/en/markets/marketinfo-forecasts.aspx#",
            "https://www.fas.usda.gov/",
            "https://www.fas.usda.gov/data",
        ],
    },
    "su_ratio": {
        "display_name": "Stock-to-Use Ratio",
        "unit": "(%)",
        "db_methods": {
            "get_data": "get_all_su_ratio_data",
            "update_data": "update_su_ratio_value",
        },
        "igc_section": "wheat section",
        "usda_crop_id": "0410000",
        "usda_rank_by": "Stock_Use_Ratio",
        "sites": [
            "https://www.igc.int/en/markets/marketinfo-forecasts.aspx#",
            "https://www.fas.usda.gov/",
            "https://www.fas.usda.gov/data",
        ],
    },
    "acreage": {
        "display_name": "Acreage",
        "unit": "(Million Hectares)",
        "db_methods": {
            "get_data": "get_all_acreage_data",
            "update_data": "update_acreage_value",
        },
        "igc_section": "wheat section",
        "usda_crop_id": "0410000",
        "usda_rank_by": "Area_Harvested",
        "sites": [
            "https://ipad.fas.usda.gov/cropexplorer/cropview/commodityView.aspx?cropid={crop_id}&sel_year=2024&rankby={rank_by}",
            "https://www.fas.usda.gov/",
            "https://www.fas.usda.gov/data",
        ],
    },
    "yield": {
        "display_name": "Yield",
        "unit": "(MT/Hectare)",
        "db_methods": {
            "get_data": "get_all_yield_data",
            "update_data": "update_yield_value",
        },
        "igc_section": "wheat section",
        "usda_crop_id": "0410000",
        "usda_rank_by": "Yield",
        "sites": [
            "https://ipad.fas.usda.gov/cropexplorer/cropview/commodityView.aspx?cropid={crop_id}&sel_year=2024&rankby={rank_by}",
            "https://www.fas.usda.gov/",
            "https://www.fas.usda.gov/data",
        ],
    },
    "world_demand": {
        "display_name": "World Demand",
        "unit": "(1000 MT)",
        "db_methods": {
            "get_data": "get_all_world_demand_data",
            "update_data": "update_world_demand_value",
        },
        "igc_section": "wheat section",
        "usda_crop_id": "0410000",
        "usda_rank_by": "Consumption",
        "sites": [
            "https://www.igc.int/en/markets/marketinfo-forecasts.aspx#",
            "https://www.fas.usda.gov/",
            "https://www.fas.usda.gov/data",
        ],
    },
}

# Corn-specific crop IDs and configurations
CORN_CONFIGS = {
    "production": {"usda_crop_id": "0440000"},
    "exports": {"usda_crop_id": "0440000"},
    "imports": {"usda_crop_id": "0440000"},
    "stocks": {"usda_crop_id": "0440000"},
    "su_ratio": {"usda_crop_id": "0440000"},
    "acreage": {"usda_crop_id": "0440000"},
    "yield": {"usda_crop_id": "0440000"},
    "world_demand": {"usda_crop_id": "0440000"},
}


def get_config(commodity: str, data_type: str) -> dict:
    """
    Get configuration for a specific commodity and data type combination

    Args:
        commodity: 'wheat' or 'corn'
        data_type: 'production', 'exports', etc.

    Returns:
        Combined configuration dictionary
    """
    if commodity not in COMMODITY_CONFIGS:
        raise ValueError(f"Unknown commodity: {commodity}")

    if data_type not in DATA_TYPE_CONFIGS:
        raise ValueError(f"Unknown data type: {data_type}")

    # Get base configurations
    commodity_config = COMMODITY_CONFIGS[commodity].copy()
    data_type_config = DATA_TYPE_CONFIGS[data_type].copy()

    # Apply corn-specific overrides
    if commodity == "corn" and data_type in CORN_CONFIGS:
        data_type_config.update(CORN_CONFIGS[data_type])
        # Update IGC section for corn
        data_type_config["igc_section"] = "corn section"

    # Format sites with specific crop ID and rank by
    formatted_sites = []
    for site in data_type_config["sites"]:
        formatted_site = site.format(
            crop_id=data_type_config.get("usda_crop_id", "0410000"),
            rank_by=data_type_config.get("usda_rank_by", "Production"),
        )
        formatted_sites.append(formatted_site)

    data_type_config["sites"] = formatted_sites

    # Combine configurations
    combined_config = {"commodity": commodity_config, "data_type": data_type_config}

    return combined_config


def generate_prompt_template(commodity: str, data_type: str) -> str:
    """
    Generate a prompt template optimized for Perplexity Advanced Search

    Args:
        commodity: 'wheat' or 'corn'
        data_type: 'production', 'exports', etc.

    Returns:
        Formatted prompt template string optimized for Perplexity
    """
    config = get_config(commodity, data_type)

    commodity_name = config["commodity"]["display_name"]
    data_name = config["data_type"]["display_name"]
    unit = config["data_type"]["unit"]
    igc_section = config["data_type"]["igc_section"]

    # Get countries list
    countries = config["commodity"]["allowed_countries"]
    countries_formatted = "\n".join([f"- {country}" for country in countries])

    # Get sites list
    sites = config["data_type"]["sites"]
    sites_formatted = "\n".join([f"- {site}" for site in sites])

    prompt_template = f"""Use the perplexity_advanced_search tool to find the latest data for {commodity_name} {data_name} {unit}.

**SEARCH PARAMETERS:**
- Query: "{commodity_name.lower()} {data_name.lower()} 2024/2025 2025/2026 forecast projection USDA IGC statistics"
- Recency Filter: "year" 
- Focus Sources: Official agricultural statistics and government reports

**TARGET COUNTRIES/REGIONS:**
{countries_formatted}

**PRIMARY DATA SOURCES TO SEARCH:**
{sites_formatted}
- Other official agricultural agencies and reports

**REQUIRED DATA YEARS:**
- 2024/2025 (current marketing year estimates)
- 2025/2026 (projections/forecasts)

**OUTPUT REQUIREMENTS:**
Provide structured data in this format for each country:

**[Country Name]:**
- 2024/2025: [value] {unit} (Source: [source name], Date: [date])
- 2025/2026: [value] {unit} (Source: [source name], Date: [date])
- Notes: [any important methodology or data quality notes]

**SEARCH INSTRUCTIONS:**
1. Look specifically in the {igc_section} when using IGC data
2. Cross-reference USDA and IGC sources when possible
3. Prioritize official government agricultural statistics
4. Note data quality (actual, estimate, forecast, projection)
5. Include source attribution and publication dates
6. If marketing year data unavailable, note the closest period available
7. Highlight any significant changes or trends between years

Execute this search comprehensively and provide detailed results for all requested countries."""

    return prompt_template


def get_page_config(commodity: str, data_type: str) -> dict:
    """
    Get page-specific configuration for adding AI research functionality

    Args:
        commodity: 'wheat' or 'corn'
        data_type: 'production', 'exports', etc.

    Returns:
        Page configuration dictionary
    """
    config = get_config(commodity, data_type)

    return {
        "page_title": f"{config['commodity']['display_name']} {config['data_type']['display_name']} Dashboard",
        "page_icon": "🌾" if commodity == "wheat" else "🌽",
        "db_file": config["commodity"]["db_file"],
        "db_helper_info": {
            "class_name": config["commodity"]["db_helper_class"],
            "module": config["commodity"]["db_helper_module"],
        },
        "allowed_countries": config["commodity"]["allowed_countries"],
        "get_data_method": config["data_type"]["db_methods"]["get_data"],
        "update_data_method": config["data_type"]["db_methods"]["update_data"],
        "unit": config["data_type"]["unit"],
        "display_name": config["data_type"]["display_name"],
    }


# Helper function to dynamically import database helper
def get_db_helper_class(commodity: str):
    """
    Dynamically import and return the appropriate database helper class

    Args:
        commodity: 'wheat' or 'corn'

    Returns:
        Database helper class
    """
    config = COMMODITY_CONFIGS[commodity]

    module_name = config["db_helper_module"]
    class_name = config["db_helper_class"]

    # Dynamic import
    import importlib

    module = importlib.import_module(module_name)
    db_helper_class = getattr(module, class_name)

    return db_helper_class


# Example usage functions for easy integration
def add_ai_research_to_wheat_page(data_type: str, current_data: dict, tab_list: list):
    """Add AI research tab to wheat page"""
    from utils.ai_research_components import (
        add_ai_research_to_page,
        get_db_helper_class,
    )

    db_helper_class = get_db_helper_class("wheat")
    db_helper = db_helper_class()

    return add_ai_research_to_page(
        "wheat", data_type, db_helper, current_data, tab_list
    )


def add_ai_research_to_corn_page(data_type: str, current_data: dict, tab_list: list):
    """Add AI research tab to corn page"""
    from utils.ai_research_components import (
        add_ai_research_to_page,
        get_db_helper_class,
    )

    db_helper_class = get_db_helper_class("corn")
    db_helper = db_helper_class()

    return add_ai_research_to_page("corn", data_type, db_helper, current_data, tab_list)


def create_ai_research_tab_for_page(commodity: str, data_type: str, current_data: dict):
    """Create AI research tab for any page"""
    from utils.ai_research_components import create_ai_research_tab

    db_helper_class = get_db_helper_class(commodity)
    db_helper = db_helper_class()

    create_ai_research_tab(commodity, data_type, db_helper, current_data)


# Validation functions
def validate_commodity(commodity: str) -> bool:
    """Validate commodity name"""
    return commodity in COMMODITY_CONFIGS


def validate_data_type(data_type: str) -> bool:
    """Validate data type name"""
    return data_type in DATA_TYPE_CONFIGS


def get_available_commodities() -> list:
    """Get list of available commodities"""
    return list(COMMODITY_CONFIGS.keys())


def get_available_data_types() -> list:
    """Get list of available data types"""
    return list(DATA_TYPE_CONFIGS.keys())


def get_countries_for_commodity(commodity: str) -> list:
    """Get allowed countries for a commodity"""
    if commodity in COMMODITY_CONFIGS:
        return COMMODITY_CONFIGS[commodity]["allowed_countries"]
    return []
