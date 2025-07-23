# client/utils/enhanced_ai_research.py - Complete reusable AI research system

import streamlit as st
import pandas as pd
import json
import asyncio
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import re
from services.mcp_service import run_agent
from services.chat_service import get_clean_conversation_memory
from langchain_core.messages import HumanMessage


class EnhancedAIResearchManager:
    """Enhanced AI Research Manager using the working prompt format"""

    # Configuration for all commodities and data types
    COMMODITY_CONFIG = {
        "wheat": {
            "display_name": "Wheat",
            "db_helper_class": "WheatProductionDB",
            "db_module": "wheat_helpers.database_helper",
            "countries": [
                "WORLD",
                "China",
                "European Union",
                "Russia",
                "United States",
                "Australia",
                "Canada",
                "India",
            ],
        },
        "corn": {
            "display_name": "Corn",
            "db_helper_class": "CornProductionDB",
            "db_module": "corn_helpers.database_helper",
            "countries": [
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

    DATA_TYPE_CONFIG = {
        "production": {
            "display_name": "Production",
            "unit": "(1000 MT)",
            "db_methods": {
                "get": "get_all_production_data",
                "update": "update_production_value",
            },
            "usda_crop_id": {"wheat": "0410000", "corn": "0440000"},
            "usda_rank": "Production",
            "igc_section": "wheat section",  # Will be updated for corn
        },
        "exports": {
            "display_name": "Exports",
            "unit": "(1000 MT)",
            "db_methods": {
                "get": "get_all_export_data",
                "update": "update_export_value",
            },
            "usda_crop_id": {"wheat": "0410000", "corn": "0440000"},
            "usda_rank": "Exports",
            "igc_section": "wheat section",
        },
        "imports": {
            "display_name": "Imports",
            "unit": "(1000 MT)",
            "db_methods": {
                "get": "get_all_import_data",
                "update": "update_import_value",
            },
            "usda_crop_id": {"wheat": "0410000", "corn": "0440000"},
            "usda_rank": "Imports",
            "igc_section": "wheat section",
        },
        "stocks": {
            "display_name": "Ending Stocks",
            "unit": "(1000 MT)",
            "db_methods": {
                "get": "get_all_stocks_data",
                "update": "update_stocks_value",
            },
            "usda_crop_id": {"wheat": "0410000", "corn": "0440000"},
            "usda_rank": "Ending_Stocks",
            "igc_section": "wheat section",
        },
        "su_ratio": {
            "display_name": "Stock-to-Use Ratio",
            "unit": "(%)",
            "db_methods": {
                "get": "get_all_su_ratio_data",
                "update": "update_su_ratio_value",
            },
            "usda_crop_id": {"wheat": "0410000", "corn": "0440000"},
            "usda_rank": "Stock_Use_Ratio",
            "igc_section": "wheat section",
        },
        "acreage": {
            "display_name": "Acreage",
            "unit": "(Million Hectares)",
            "db_methods": {
                "get": "get_all_acreage_data",
                "update": "update_acreage_value",
            },
            "usda_crop_id": {"wheat": "0410000", "corn": "0440000"},
            "usda_rank": "Area_Harvested",
            "igc_section": "wheat section",
        },
        "yield": {
            "display_name": "Yield",
            "unit": "(MT/Hectare)",
            "db_methods": {"get": "get_all_yield_data", "update": "update_yield_value"},
            "usda_crop_id": {"wheat": "0410000", "corn": "0440000"},
            "usda_rank": "Yield",
            "igc_section": "wheat section",
        },
        "world_demand": {
            "display_name": "World Demand",
            "unit": "(1000 MT)",
            "db_methods": {
                "get": "get_all_world_demand_data",
                "update": "update_world_demand_value",
            },
            "usda_crop_id": {"wheat": "0410000", "corn": "0440000"},
            "usda_rank": "Consumption",
            "igc_section": "wheat section",
        },
    }

    def __init__(self, commodity: str, data_type: str, db_helper):
        self.commodity = commodity
        self.data_type = data_type
        self.db_helper = db_helper

        # Get configurations
        self.commodity_config = self.COMMODITY_CONFIG[commodity]
        self.data_type_config = self.DATA_TYPE_CONFIG[data_type].copy()

        # Update config for corn
        if commodity == "corn":
            self.data_type_config["igc_section"] = "corn section"

        # Get countries from database or config
        self.countries = self._get_database_countries()

    def _get_database_countries(self) -> List[str]:
        """Get countries from database, fallback to config"""
        try:
            get_method = getattr(
                self.db_helper, self.data_type_config["db_methods"]["get"]
            )
            current_data = get_method()
            db_countries = list(current_data.keys())

            # Filter to only include countries that are in our config
            config_countries = self.commodity_config["countries"]
            filtered_countries = [c for c in db_countries if c in config_countries]

            return filtered_countries if filtered_countries else config_countries
        except Exception as e:
            st.warning(f"Could not get countries from database: {e}")
            return self.commodity_config["countries"]

    def generate_research_prompt(self) -> str:
        """Generate the working research prompt"""

        commodity_name = self.commodity_config["display_name"]
        data_name = self.data_type_config["display_name"]
        unit = self.data_type_config["unit"]
        crop_id = self.data_type_config["usda_crop_id"][self.commodity]
        rank_by = self.data_type_config["usda_rank"]
        igc_section = self.data_type_config["igc_section"]

        # Format countries list
        countries_formatted = "\n".join([f"- {country}" for country in self.countries])

        prompt = f"""Use perplexity advance search to get 2024/2025 and projections for 2025/2026 of {commodity_name} {data_name} {unit}
for the following areas 
                                        
{countries_formatted}

You can use any information available in these sites:
- https://www.igc.int/en/markets/marketinfo-forecasts.aspx# ({igc_section})
- https://ipad.fas.usda.gov/cropexplorer/cropview/commodityView.aspx?cropid={crop_id}&sel_year=2024&rankby={rank_by}
- https://www.fas.usda.gov/
- https://www.fas.usda.gov/data
- any other public available site

Please provide the data in a clear, structured format showing:
- Current estimates for 2024/2025
- Projections for 2025/2026
- Source information for each data point
- Any relevant notes or methodology information

Format the response clearly with country names and values that can be easily parsed."""

        return prompt

    def check_agent_availability(self) -> Tuple[bool, str]:
        """Check if MCP agent is available"""
        agent = st.session_state.get("agent")
        if not agent:
            return (
                False,
                "No MCP agent available. Please connect to MCP servers first via the AI Tools page.",
            )

        tools = st.session_state.get("tools", [])
        perplexity_tools = [tool for tool in tools if "perplexity" in tool.name.lower()]

        if not perplexity_tools:
            return (
                False,
                "No Perplexity tools available. Please ensure Perplexity MCP server is connected.",
            )

        return True, f"Agent ready with {len(perplexity_tools)} Perplexity tools"

    async def execute_research(
        self, progress_callback=None
    ) -> Tuple[bool, str, Optional[Dict]]:
        """Execute the research using the MCP agent"""

        if progress_callback:
            progress_callback(0.1, "Checking agent availability...")

        # Check agent availability
        agent_available, status_msg = self.check_agent_availability()
        if not agent_available:
            return False, status_msg, None

        agent = st.session_state.get("agent")

        if progress_callback:
            progress_callback(0.2, "Generating research prompt...")

        # Generate prompt
        prompt = self.generate_research_prompt()

        if progress_callback:
            progress_callback(0.3, "Sending request to AI agent...")

        try:
            # Create conversation memory
            conversation_memory = get_clean_conversation_memory()
            conversation_memory.append(HumanMessage(content=prompt))

            if progress_callback:
                progress_callback(0.4, "AI agent searching for data...")

            # Run the agent
            response = await run_agent(agent, conversation_memory)

            if progress_callback:
                progress_callback(0.8, "Processing AI response...")

            # Extract response text
            response_text = ""
            tool_executed = False

            if "messages" in response:
                # Skip the original conversation memory
                new_messages = response["messages"][len(conversation_memory) :]

                for msg in new_messages:
                    if hasattr(msg, "tool_calls") and msg.tool_calls:
                        # Check if perplexity tool was executed
                        for tool_call in msg.tool_calls:
                            if "perplexity" in tool_call.get("name", "").lower():
                                tool_executed = True
                                break
                    elif hasattr(msg, "content") and msg.content:
                        response_text += str(msg.content) + "\n"

            if not tool_executed:
                return False, "No Perplexity research tools were executed", None

            if not response_text.strip():
                return False, "No response text received from AI agent", None

            if progress_callback:
                progress_callback(0.9, "Parsing research results...")

            # Parse the response
            parsed_data = self._parse_response(response_text)

            if progress_callback:
                progress_callback(1.0, "Research completed!")

            return True, response_text, parsed_data

        except Exception as e:
            return False, f"Error during research execution: {str(e)}", None

    def _parse_response(self, response_text: str) -> Optional[Dict]:
        """Parse the AI response to extract structured data"""
        try:
            parsed_data = {}

            # Initialize structure for all countries
            for country in self.countries:
                parsed_data[country] = {
                    "2024/2025": None,
                    "2025/2026": None,
                    "source": None,
                    "notes": None,
                }

            lines = response_text.split("\n")
            current_country = None

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # Look for country names
                for country in self.countries:
                    # More flexible country matching
                    country_variants = [country, country.upper(), country.lower()]
                    if country == "European Union":
                        country_variants.extend(["EU", "EU-27", "European Union 27"])
                    elif country == "United States":
                        country_variants.extend(
                            ["USA", "US", "U.S.", "United States of America"]
                        )

                    for variant in country_variants:
                        if variant in line:
                            # Check if this line actually refers to the country data
                            if any(
                                keyword in line.lower()
                                for keyword in [
                                    self.data_type.lower(),
                                    "production",
                                    "export",
                                    "import",
                                    "stock",
                                    "yield",
                                    "acre",
                                    "demand",
                                    "mt",
                                    "million",
                                    "thousand",
                                    ":",
                                ]
                            ):
                                current_country = country
                                break

                    if current_country:
                        break

                # Extract numerical data for current country
                if current_country:
                    # Look for year-specific data
                    numbers = re.findall(r"(\d{1,3}(?:,\d{3})*(?:\.\d+)?)", line)

                    if numbers:
                        try:
                            # Convert the first number found
                            value_str = numbers[0].replace(",", "")
                            value = float(value_str)

                            # Determine which year this refers to
                            if any(
                                pattern in line
                                for pattern in ["2024/25", "2024-25", "2024/2025"]
                            ):
                                if parsed_data[current_country]["2024/2025"] is None:
                                    parsed_data[current_country]["2024/2025"] = value
                            elif any(
                                pattern in line
                                for pattern in ["2025/26", "2025-26", "2025/2026"]
                            ):
                                if parsed_data[current_country]["2025/2026"] is None:
                                    parsed_data[current_country]["2025/2026"] = value

                            # Context-based assignment if no explicit year
                            elif any(
                                word in line.lower()
                                for word in [
                                    "forecast",
                                    "projection",
                                    "estimate",
                                    "expected",
                                ]
                            ):
                                if parsed_data[current_country]["2025/2026"] is None:
                                    parsed_data[current_country]["2025/2026"] = value
                            elif any(
                                word in line.lower()
                                for word in ["current", "actual", "2024"]
                            ):
                                if parsed_data[current_country]["2024/2025"] is None:
                                    parsed_data[current_country]["2024/2025"] = value

                        except (ValueError, IndexError):
                            continue

                # Extract source information
                if any(
                    source_word in line.lower()
                    for source_word in ["source:", "usda", "igc", "according to"]
                ):
                    if (
                        current_country
                        and parsed_data[current_country]["source"] is None
                    ):
                        parsed_data[current_country]["source"] = line[:100]

            # Clean up and return only countries with data
            cleaned_data = {}
            for country, data in parsed_data.items():
                if data["2024/2025"] is not None or data["2025/2026"] is not None:
                    cleaned_data[country] = {
                        "2024/2025": data["2024/2025"],
                        "2025/2026": data["2025/2026"],
                    }

            return cleaned_data if cleaned_data else None

        except Exception as e:
            st.error(f"Error parsing response: {e}")
            return None

    def create_comparison_table(
        self, current_data: Dict, research_data: Dict
    ) -> pd.DataFrame:
        """Create comparison table between current and research data"""
        comparison_data = []

        for country in self.countries:
            if country not in current_data:
                continue

            row = {
                "Country/Region": country,
                "Current 2024/2025": current_data[country].get("2024/2025", 0),
                "Research 2024/2025": research_data.get(country, {}).get(
                    "2024/2025", "N/A"
                ),
                "Current 2025/2026": current_data[country].get("2025/2026", 0),
                "Research 2025/2026": research_data.get(country, {}).get(
                    "2025/2026", "N/A"
                ),
            }

            # Calculate difference for 2025/2026
            research_val = research_data.get(country, {}).get("2025/2026")
            if research_val and isinstance(research_val, (int, float)):
                current_val = current_data[country].get("2025/2026", 0)
                difference = research_val - current_val
                row["Difference"] = f"{difference:+.1f}" if difference != 0 else "0.0"
            else:
                row["Difference"] = "N/A"

            comparison_data.append(row)

        return pd.DataFrame(comparison_data)

    def update_projections(self, updates: Dict[str, float]) -> Tuple[bool, str]:
        """Update 2025/2026 projections in database"""
        try:
            update_method_name = self.data_type_config["db_methods"]["update"]
            update_method = getattr(self.db_helper, update_method_name)

            # Get current data for change calculation
            get_method_name = self.data_type_config["db_methods"]["get"]
            get_method = getattr(self.db_helper, get_method_name)
            current_data = get_method()

            updated_count = 0

            for country, new_value in updates.items():
                if country in current_data:
                    # Calculate change from 2024/2025
                    current_2024_25 = current_data[country].get("2024/2025", 0)
                    change = new_value - current_2024_25

                    # Update in database
                    success = update_method(country, "2025/2026", new_value, change)
                    if success:
                        updated_count += 1

            if updated_count > 0:
                return (
                    True,
                    f"Successfully updated {updated_count} countries' projections.",
                )
            else:
                return False, "No updates were made."

        except Exception as e:
            return False, f"Error updating projections: {str(e)}"


def create_ai_research_tab(
    commodity: str, data_type: str, db_helper, current_data: Dict
):
    """Create AI Research tab using the enhanced system"""

    # Initialize research manager
    research_manager = EnhancedAIResearchManager(commodity, data_type, db_helper)

    st.header(
        f"🤖 AI Research - {research_manager.commodity_config['display_name']} {research_manager.data_type_config['display_name']}"
    )

    # Display current data table
    st.subheader("📊 Current Database Data")

    display_years = ["2022/2023", "2023/2024", "2024/2025", "2025/2026"]
    table_data = []

    for country in research_manager.countries:
        if country in current_data:
            row = {"Country/Region": country}
            for year in display_years:
                if year in current_data[country]:
                    row[year] = f"{current_data[country][year]:.1f}"
                else:
                    row[year] = "N/A"
            table_data.append(row)

    current_df = pd.DataFrame(table_data)
    st.dataframe(current_df, use_container_width=True, hide_index=True)

    st.markdown("---")

    # AI Research Section
    st.subheader("🔮 AI-Powered Data Research")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.info(
            f"""
        **Research Target:** {research_manager.commodity_config['display_name']} {research_manager.data_type_config['display_name']} data {research_manager.data_type_config['unit']}
        
        **Years:** 2024/2025 (estimates) and 2025/2026 (projections)
        
        **Countries:** {len(research_manager.countries)} countries from database
        
        **Sources:** IGC, USDA FAS, and other official agricultural statistics
        
        **Agent:** Uses main MCP agent with Perplexity, Google Search, and Firecrawl tools
        """
        )

    with col2:
        # Check agent status
        agent_available, status_msg = research_manager.check_agent_availability()

        if agent_available:
            st.success("🟢 MCP Agent Ready")
            st.info(status_msg)
        else:
            st.error("🔴 Agent Not Available")
            st.warning(status_msg)

            if st.button("🔗 Go to AI Tools Page", use_container_width=True):
                st.switch_page("pages/9_mcp_app.py")

    # Research execution
    research_key = f"{commodity}_{data_type}_enhanced_research"

    # Only show research button if agent is available
    if agent_available:
        if st.button(
            f"🚀 Start AI Research for {research_manager.commodity_config['display_name']} {research_manager.data_type_config['display_name']}",
            type="primary",
            use_container_width=True,
            key=f"research_btn_{research_key}",
            help="Execute AI research using the proven prompt format",
        ):
            # Initialize research results storage
            if "enhanced_research_results" not in st.session_state:
                st.session_state.enhanced_research_results = {}

            # Create progress tracking
            progress_bar = st.progress(0)
            status_text = st.empty()

            def update_progress(value, message):
                progress_bar.progress(value)
                status_text.text(message)

            # Execute research
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                success, response_text, parsed_data = loop.run_until_complete(
                    research_manager.execute_research(update_progress)
                )

                # Store results
                st.session_state.enhanced_research_results[research_key] = {
                    "success": success,
                    "response_text": response_text,
                    "parsed_data": parsed_data,
                    "timestamp": datetime.now().isoformat(),
                    "commodity": commodity,
                    "data_type": data_type,
                }

                progress_bar.empty()
                status_text.empty()

                if success:
                    st.success("✅ Research completed successfully!")
                    st.rerun()
                else:
                    st.error(f"❌ Research failed: {response_text}")

            except Exception as e:
                progress_bar.empty()
                status_text.empty()
                st.error(f"❌ Research execution failed: {str(e)}")

    # Display results if available
    if research_key in st.session_state.get("enhanced_research_results", {}):
        results = st.session_state.enhanced_research_results[research_key]

        if results["success"]:
            st.markdown("---")
            st.subheader("📋 Research Results")

            # Show timestamp
            timestamp = datetime.fromisoformat(results["timestamp"])
            st.caption(f"Research completed: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")

            # Show AI response in expandable section
            with st.expander("🤖 View Full AI Response", expanded=False):
                st.text_area(
                    "AI Research Response",
                    value=results["response_text"],
                    height=400,
                    disabled=True,
                    key=f"response_text_{research_key}",
                )

            # Show parsed data if available
            if results["parsed_data"]:
                st.subheader("📊 Data Comparison")

                comparison_df = research_manager.create_comparison_table(
                    current_data, results["parsed_data"]
                )

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

                # Update projections section
                st.subheader("💾 Update Projections")

                st.warning(
                    "⚠️ **Important:** Only 2025/2026 projections will be updated. Historical data remains unchanged."
                )

                # Create update form
                with st.form(f"update_form_{research_key}"):
                    st.markdown("**Select countries to update with research data:**")

                    updates_to_make = {}

                    for country in research_manager.countries:
                        if country not in current_data:
                            continue

                        research_value = (
                            results["parsed_data"].get(country, {}).get("2025/2026")
                        )

                        if research_value and isinstance(research_value, (int, float)):
                            current_value = current_data[country].get("2025/2026", 0)

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
                        clear_results = st.form_submit_button(
                            "🗑️ Clear Research Results",
                            use_container_width=True,
                        )

                    if submit_updates and updates_to_make:
                        success, message = research_manager.update_projections(
                            updates_to_make
                        )

                        if success:
                            st.success(f"✅ {message}")
                            # Clear cache and refresh
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error(f"❌ {message}")

                    elif submit_updates and not updates_to_make:
                        st.warning("⚠️ No countries selected for update.")

                    if clear_results:
                        del st.session_state.enhanced_research_results[research_key]
                        st.rerun()

            else:
                st.warning(
                    "⚠️ Could not parse structured data from AI response. Please review the raw response above."
                )

        else:
            st.error(
                f"❌ Research failed: {results.get('response_text', 'Unknown error')}"
            )


def add_enhanced_ai_research_tab(
    commodity: str, data_type: str, db_helper, current_data: Dict, tab_list: List[str]
) -> List[str]:
    """Add enhanced AI research tab to existing page structure"""
    tab_list.append("🤖 AI Research")
    return tab_list
