# client/utils/enhanced_ai_research_tab.py

import streamlit as st
import pandas as pd
import asyncio
import os
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from utils.generic_agricultural_ai_agent import run_agricultural_ai_research


def create_ai_research_tab(
    commodity: str,
    data_type: str,
    current_data: Dict,
    db_helper,
    update_method_name: str,
):
    """
    Create a generic AI Research tab for any agricultural data type

    Args:
        commodity: 'wheat' or 'corn'
        data_type: 'production', 'exports', 'imports', 'stocks', 'su_ratio', 'acreage', 'yield', 'world_demand'
        current_data: Current database data
        db_helper: Database helper instance
        update_method_name: Name of the update method in db_helper
    """

    # Configuration mapping
    config_map = {
        "wheat": {
            "display_name": "Wheat",
            "icon": "🌾",
            "countries": {
                "production": [
                    "WORLD",
                    "China",
                    "European Union",
                    "India",
                    "Russia",
                    "United States",
                    "Australia",
                    "Canada",
                ],
                "exports": [
                    "WORLD",
                    "China",
                    "European Union",
                    "Russia",
                    "United States",
                    "Australia",
                    "Canada",
                    "India",
                ],
                "imports": [
                    "WORLD",
                    "Egypt",
                    "Indonesia",
                    "European Union",
                    "Turkey",
                    "Philippines",
                    "China",
                    "Algeria",
                    "Morocco",
                ],
                "stocks": [
                    "WORLD",
                    "China",
                    "European Union",
                    "India",
                    "Russia",
                    "United States",
                    "Australia",
                    "Canada",
                ],
                "su_ratio": [
                    "WORLD",
                    "China",
                    "European Union",
                    "India",
                    "Russia",
                    "United States",
                    "Australia",
                    "Canada",
                ],
                "acreage": [
                    "WORLD",
                    "China",
                    "European Union",
                    "India",
                    "Russia",
                    "United States",
                    "Australia",
                    "Canada",
                ],
                "yield": [
                    "WORLD",
                    "China",
                    "European Union",
                    "India",
                    "Russia",
                    "United States",
                    "Australia",
                    "Canada",
                ],
                "world_demand": [
                    "Food",
                    "Feed",
                    "Industrial",
                    "Seed",
                    "Other",
                    "Total Consumption",
                ],
            },
        },
        "corn": {
            "display_name": "Corn",
            "icon": "🌽",
            "countries": {
                "production": [
                    "WORLD",
                    "China",
                    "European Union",
                    "India",
                    "Russia",
                    "United States",
                    "Australia",
                    "Canada",
                ],
                "exports": [
                    "WORLD",
                    "China",
                    "European Union",
                    "India",
                    "Russia",
                    "United States",
                    "Australia",
                    "Canada",
                ],
                "imports": [
                    "World",
                    "Mexico",
                    "Japan",
                    "China",
                    "South Korea",
                    "European Union",
                    "Vietnam",
                    "Egypt",
                    "Colombia",
                ],
                "stocks": [
                    "WORLD",
                    "United States",
                    "China",
                    "Brazil",
                    "European Union",
                    "Argentina",
                    "Ukraine",
                    "India",
                ],
                "su_ratio": [
                    "WORLD",
                    "United States",
                    "China",
                    "Brazil",
                    "European Union",
                    "Argentina",
                    "Ukraine",
                    "India",
                ],
                "acreage": [
                    "WORLD",
                    "United States",
                    "China",
                    "Brazil",
                    "European Union",
                    "Argentina",
                    "Ukraine",
                    "India",
                ],
                "yield": [
                    "WORLD",
                    "United States",
                    "China",
                    "Brazil",
                    "European Union",
                    "Argentina",
                    "Ukraine",
                    "India",
                ],
                "world_demand": [
                    "Feed",
                    "Food",
                    "Industrial",
                    "Other",
                    "Total Consumption",
                ],
            },
        },
    }

    # Unit mapping - corrected to match actual database display units
    unit_map = {
        "production": "Million Metric Tons",
        "exports": "Million Metric Tons",
        "imports": "Million Metric Tons",
        "stocks": "Million Metric Tons",
        "su_ratio": "%",
        "acreage": "Million Hectares",
        "yield": "tonnes per hectare",
        "world_demand": "Million Metric Tons",
    }

    # Data type display names
    data_type_names = {
        "production": "Production",
        "exports": "Exports",
        "imports": "Imports",
        "stocks": "Ending Stocks",
        "su_ratio": "Stock-to-Use Ratio",
        "acreage": "Acreage",
        "yield": "Yield",
        "world_demand": "World Demand",
    }

    # Get configuration
    commodity_config = config_map.get(commodity, config_map["wheat"])
    target_countries = commodity_config["countries"].get(
        data_type, commodity_config["countries"]["production"]
    )
    unit = unit_map.get(data_type, "1000 MT")
    data_display_name = data_type_names.get(data_type, data_type.title())

    st.header(
        f"🤖 AI Research - {commodity_config['display_name']} {data_display_name}"
    )

    # Display current data
    st.subheader("📊 Current Database Data")

    # Show current data table
    display_years = ["2022/2023", "2023/2024", "2024/2025", "2025/2026"]
    table_data = []

    for country, data in current_data.items():
        if country in target_countries:
            row = {"Country/Region": country}
            for year in display_years:
                if year in data:
                    row[year] = f"{data[year]:.1f}"
                else:
                    row[year] = "N/A"
            table_data.append(row)

    current_df = pd.DataFrame(table_data)
    st.dataframe(current_df, use_container_width=True, hide_index=True)

    st.markdown("---")

    # AI Research Section
    st.subheader("🔮 Perplexity AI-Powered Data Research")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.info(
            f"""
        **Research Target:** {commodity_config['display_name']} {data_display_name} data ({unit}) for 2024/2025 and 2025/2026 projections
        
        **Data Sources:** IGC, USDA FAS, and other official agricultural statistics sources
        
        **AI Tool:** Perplexity Advanced Search with recency filtering for latest data
        
        **Search Strategy:** Optimized queries targeting official agricultural reports and forecasts
        
        **Connection:** Uses main MCP agent if available, otherwise creates dedicated Perplexity client
        """
        )

    with col2:
        # Check connection status
        main_agent = st.session_state.get("agent")
        main_tools = st.session_state.get("tools", [])
        perplexity_tools = [
            tool for tool in main_tools if "perplexity" in tool.name.lower()
        ]

        if main_agent and perplexity_tools:
            st.success("🟢 Main MCP Agent Ready")
            st.info(f"🔮 {len(perplexity_tools)} Perplexity tools available")
        elif main_agent:
            st.warning("🟡 Main Agent Ready, Missing Perplexity")
            st.info("Will create dedicated Perplexity client")
        else:
            st.warning("🟡 No Main Agent")
            st.info("Will create dedicated Perplexity client")

    # Debug information
    with st.expander("🐛 Debug Information", expanded=False):
        st.write("**Configuration Debug:**")
        st.write(f"- Commodity: {commodity}")
        st.write(f"- Data Type: {data_type}")
        st.write(f"- Unit: {unit}")
        st.write(f"- Target Countries: {len(target_countries)}")
        st.write(f"- Countries: {target_countries}")

        st.write("**Session State Debug:**")
        st.write(f"- Main agent available: {bool(main_agent)}")
        st.write(f"- Total tools: {len(main_tools)}")
        st.write(f"- Perplexity tools: {len(perplexity_tools)}")

        st.write("**Environment Variables:**")
        st.write(
            f"- ANTHROPIC_API_KEY: {'Set' if os.getenv('ANTHROPIC_API_KEY') else 'Not set'}"
        )
        st.write(
            f"- PERPLEXITY_SERVER_URL: {os.getenv('PERPLEXITY_SERVER_URL', 'Default')}"
        )

    # Research button
    research_key = f"{commodity}_{data_type}_research"

    if st.button(
        f"🔮 Start Perplexity Research for {commodity_config['display_name']} {data_display_name}",
        type="primary",
        use_container_width=True,
        help="Uses Perplexity Advanced Search to find latest agricultural data",
        key=f"research_{commodity}_{data_type}",
    ):
        # Initialize session state for research results
        if "research_results" not in st.session_state:
            st.session_state.research_results = {}

        # Create progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()

        def update_progress(value, message):
            progress_bar.progress(value)
            status_text.text(message)

        # Run research
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            success, response_text, research_data, comparison_table = (
                loop.run_until_complete(
                    run_agricultural_ai_research(
                        commodity,
                        data_type,
                        target_countries,
                        unit,
                        current_data,
                        update_progress,
                    )
                )
            )

            progress_bar.empty()
            status_text.empty()

            if success:
                # Store results
                st.session_state.research_results[research_key] = {
                    "success": True,
                    "response_text": response_text,
                    "research_data": research_data,
                    "comparison_table": comparison_table,
                    "timestamp": datetime.now().isoformat(),
                }
                st.success("✅ Research completed successfully!")
                st.rerun()
            else:
                st.error(f"❌ Research failed: {response_text}")

        except Exception as e:
            progress_bar.empty()
            status_text.empty()
            st.error(f"❌ Research failed: {str(e)}")

    # Display research results if available
    if research_key in st.session_state.get("research_results", {}):
        results = st.session_state.research_results[research_key]

        if results["success"]:
            st.markdown("---")
            st.subheader("📋 Research Results")

            # Show timestamp
            timestamp = datetime.fromisoformat(results["timestamp"])
            st.caption(
                f"Research completed at: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
            )

            # Show raw AI response in expandable section
            with st.expander("🤖 View Full AI Response"):
                st.text_area(
                    "AI Research Response",
                    value=results["response_text"],
                    height=300,
                    disabled=True,
                )

            # Show comparison table if available
            if results.get("comparison_table") is not None:
                st.subheader("📊 Comparison Table")

                comparison_df = results["comparison_table"]

                # Style the comparison table
                def highlight_differences(val):
                    if val == "N/A" or val == "0.0":
                        return ""
                    try:
                        if "+" in str(val):
                            return "background-color: #d4edda; color: #155724"
                        elif "-" in str(val):
                            return "background-color: #f8d7da; color: #721c24"
                    except:
                        pass
                    return ""

                styled_df = comparison_df.style.map(
                    highlight_differences, subset=["Difference"]
                )
                st.dataframe(styled_df, use_container_width=True, hide_index=True)

                # Update section
                if results.get("research_data"):
                    st.subheader("💾 Update Projections")

                    st.warning(
                        """
                    **⚠️ Important:** Only 2025/2026 projections will be updated. 
                    Historical and current year data will remain unchanged.
                    """
                    )

                    # Create update form
                    with st.form(f"update_projections_{research_key}"):
                        st.markdown(
                            "**Select countries to update with research data:**"
                        )

                        updates_to_make = {}
                        research_data = results["research_data"]

                        for country in target_countries:
                            if country in current_data:
                                research_value = research_data.get(country, {}).get(
                                    "2025/2026"
                                )

                                if research_value and isinstance(
                                    research_value, (int, float)
                                ):
                                    current_value = current_data[country].get(
                                        "2025/2026", 0
                                    )

                                    if (
                                        abs(research_value - current_value) > 0.1
                                    ):  # Only show if significant difference
                                        col1, col2, col3 = st.columns([2, 1, 1])

                                        with col1:
                                            update_checkbox = st.checkbox(
                                                f"Update {country}",
                                                key=f"update_{country}_{research_key}",
                                            )

                                        with col2:
                                            st.write(f"Current: {current_value:.1f}")

                                        with col3:
                                            st.write(f"Research: {research_value:.1f}")

                                        if update_checkbox:
                                            updates_to_make[country] = research_value

                        col1, col2 = st.columns(2)

                        with col1:
                            submit_updates = st.form_submit_button(
                                "📥 Update Selected Projections",
                                type="primary",
                                use_container_width=True,
                            )

                        with col2:
                            clear_research = st.form_submit_button(
                                "🗑️ Clear Research Results", use_container_width=True
                            )

                        if submit_updates and updates_to_make:
                            update_method = getattr(db_helper, update_method_name)
                            updated_count = 0

                            for country, new_value in updates_to_make.items():
                                # Calculate change from 2024/2025
                                current_2024_25 = current_data[country].get(
                                    "2024/2025", 0
                                )
                                change = new_value - current_2024_25

                                # Update in database
                                success = update_method(
                                    country, "2025/2026", new_value, change
                                )
                                if success:
                                    updated_count += 1

                            if updated_count > 0:
                                st.success(
                                    f"✅ Updated {updated_count} countries' projections"
                                )
                                st.cache_data.clear()
                                st.rerun()
                            else:
                                st.error("❌ No updates were applied")

                        elif submit_updates and not updates_to_make:
                            st.warning("⚠️ No countries selected for update.")

                        if clear_research:
                            del st.session_state.research_results[research_key]
                            st.rerun()

            else:
                st.warning(
                    "⚠️ Could not parse structured data from AI response. Please review the raw response above."
                )

        else:
            st.error(
                f"❌ Research failed: {results.get('response_text', 'Unknown error')}"
            )


# Convenience functions for different commodities and data types
def create_wheat_ai_research_tab(
    data_type: str, current_data: Dict, db_helper, update_method_name: str
):
    """Create AI research tab for wheat data"""
    create_ai_research_tab(
        "wheat", data_type, current_data, db_helper, update_method_name
    )


def create_corn_ai_research_tab(
    data_type: str, current_data: Dict, db_helper, update_method_name: str
):
    """Create AI research tab for corn data"""
    create_ai_research_tab(
        "corn", data_type, current_data, db_helper, update_method_name
    )
