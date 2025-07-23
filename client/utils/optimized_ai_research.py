# client/utils/optimized_ai_research.py - Updated with working prompt format

import streamlit as st
import pandas as pd
import json
import asyncio
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import re
from services.mcp_service import run_agent
from langchain_core.messages import HumanMessage


class OptimizedAIResearchManager:
    """AI Research Manager using the proven working prompt format"""

    def __init__(self, commodity: str, data_type: str, db_helper):
        self.commodity = commodity
        self.data_type = data_type
        self.db_helper = db_helper

        # Import the optimized prompts
        from utils.perplexity_prompts import get_research_prompt

        self.get_research_prompt = get_research_prompt

        # Get countries from database
        self.countries = self._get_database_countries()

    def _get_database_countries(self) -> List[str]:
        """Get countries from database"""
        try:
            # Get the appropriate data method based on data type
            method_mapping = {
                "production": "get_all_production_data",
                "exports": "get_all_export_data",
                "imports": "get_all_import_data",
                "stocks": "get_all_stocks_data",
                "su_ratio": "get_all_su_ratio_data",
                "acreage": "get_all_acreage_data",
                "yield": "get_all_yield_data",
                "world_demand": "get_all_world_demand_data",
            }

            method_name = method_mapping.get(self.data_type, "get_all_production_data")
            get_method = getattr(self.db_helper, method_name)
            current_data = get_method()

            return list(current_data.keys())
        except Exception as e:
            st.warning(f"Could not get countries from database: {e}")
            # Default countries
            default_countries = {
                "wheat": [
                    "WORLD",
                    "China",
                    "European Union",
                    "Russia",
                    "United States",
                    "Australia",
                    "Canada",
                    "India",
                ],
                "corn": [
                    "WORLD",
                    "United States",
                    "China",
                    "Brazil",
                    "European Union",
                    "Argentina",
                    "Ukraine",
                    "India",
                ],
            }
            return default_countries.get(self.commodity, [])

    def generate_research_prompt(self) -> str:
        """Generate the working research prompt using the proven format"""
        return self.get_research_prompt(self.commodity, self.data_type, self.countries)

    def check_agent_availability(self) -> Tuple[bool, str]:
        """Check if MCP agent with Perplexity is available"""
        agent = st.session_state.get("agent")
        if not agent:
            return False, "No MCP agent available. Please connect to MCP servers first."

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
        """Execute the research using the proven prompt format"""

        if progress_callback:
            progress_callback(0.1, "Checking agent availability...")

        # Check agent availability
        agent_available, status_msg = self.check_agent_availability()
        if not agent_available:
            return False, status_msg, None

        agent = st.session_state.get("agent")

        if progress_callback:
            progress_callback(0.2, "Generating research prompt...")

        # Generate the working prompt
        prompt = self.generate_research_prompt()

        if progress_callback:
            progress_callback(0.3, "Sending request to AI agent...")

        try:
            # Create conversation memory with just the prompt
            conversation_memory = [HumanMessage(content=prompt)]

            if progress_callback:
                progress_callback(0.4, "AI agent researching data with Perplexity...")

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

            # Parse the response using enhanced parser
            parsed_data = self._parse_response_enhanced(response_text)

            if progress_callback:
                progress_callback(1.0, "Research completed successfully!")

            return True, response_text, parsed_data

        except Exception as e:
            return False, f"Error during research execution: {str(e)}", None

    def _parse_response_enhanced(self, response_text: str) -> Optional[Dict]:
        """Enhanced parser optimized for Perplexity responses"""
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

            # Enhanced country detection
            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # Look for country names with enhanced matching
                for country in self.countries:
                    country_variants = self._get_country_variants(country)

                    for variant in country_variants:
                        if variant.lower() in line.lower():
                            # Additional checks to ensure it's actually referring to the country data
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
                                    "-",
                                    "2024",
                                    "2025",
                                ]
                            ):
                                current_country = country
                                break

                    if current_country:
                        break

                # Extract numerical data for current country
                if current_country:
                    # Enhanced number extraction with multiple patterns
                    numbers = self._extract_numbers_from_line(line)

                    for number in numbers:
                        # Determine which year this refers to with enhanced logic
                        year_assigned = self._assign_number_to_year(
                            line, number, current_country, parsed_data
                        )
                        if year_assigned:
                            break

                # Extract source information
                if any(
                    source_word in line.lower()
                    for source_word in [
                        "source:",
                        "usda",
                        "igc",
                        "according to",
                        "based on",
                        "fao",
                        "oecd",
                    ]
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

    def _get_country_variants(self, country: str) -> List[str]:
        """Get all possible variants of a country name"""
        variants = [country, country.upper(), country.lower()]

        # Add specific variants
        if country == "European Union":
            variants.extend(["EU", "EU-27", "European Union 27", "Europe"])
        elif country == "United States":
            variants.extend(
                ["USA", "US", "U.S.", "United States of America", "America"]
            )
        elif country == "Russia":
            variants.extend(["Russian Federation"])
        elif country == "China":
            variants.extend(["People's Republic of China", "PRC"])

        return variants

    def _extract_numbers_from_line(self, line: str) -> List[float]:
        """Extract numbers from a line with multiple patterns"""
        numbers = []

        # Pattern for numbers with units
        patterns = [
            r"(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(?:million|mn|m\.?\s*metric\s*tons?|mmt|mt)",
            r"(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(?:thousand|k)",
            r"(\d{1,3}(?:,\d{3})*(?:\.\d+)?)",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, line.lower())
            for match in matches:
                try:
                    value_str = match.replace(",", "")
                    value = float(value_str)
                    numbers.append(value)
                except ValueError:
                    continue

        return numbers

    def _assign_number_to_year(
        self, line: str, number: float, country: str, parsed_data: Dict
    ) -> bool:
        """Assign a number to the appropriate year with enhanced logic"""
        # Check for explicit year mentions
        if any(pattern in line for pattern in ["2024/25", "2024-25", "2024/2025"]):
            if parsed_data[country]["2024/2025"] is None:
                parsed_data[country]["2024/2025"] = number
                return True
        elif any(pattern in line for pattern in ["2025/26", "2025-26", "2025/2026"]):
            if parsed_data[country]["2025/2026"] is None:
                parsed_data[country]["2025/2026"] = number
                return True

        # Context-based assignment
        elif any(
            word in line.lower()
            for word in ["forecast", "projection", "estimate", "expected", "projected"]
        ):
            if parsed_data[country]["2025/2026"] is None:
                parsed_data[country]["2025/2026"] = number
                return True
        elif any(
            word in line.lower() for word in ["current", "actual", "2024", "this year"]
        ):
            if parsed_data[country]["2024/2025"] is None:
                parsed_data[country]["2024/2025"] = number
                return True

        return False

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
            # Get the appropriate update method based on data type
            method_mapping = {
                "production": "update_production_value",
                "exports": "update_export_value",
                "imports": "update_import_value",
                "stocks": "update_stocks_value",
                "su_ratio": "update_su_ratio_value",
                "acreage": "update_acreage_value",
                "yield": "update_yield_value",
                "world_demand": "update_world_demand_value",
            }

            update_method_name = method_mapping.get(
                self.data_type, "update_production_value"
            )
            update_method = getattr(self.db_helper, update_method_name)

            # Get current data for change calculation
            get_method_mapping = {
                "production": "get_all_production_data",
                "exports": "get_all_export_data",
                "imports": "get_all_import_data",
                "stocks": "get_all_stocks_data",
                "su_ratio": "get_all_su_ratio_data",
                "acreage": "get_all_acreage_data",
                "yield": "get_all_yield_data",
                "world_demand": "get_all_world_demand_data",
            }

            get_method_name = get_method_mapping.get(
                self.data_type, "get_all_production_data"
            )
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


def create_optimized_ai_research_tab(
    commodity: str, data_type: str, db_helper, current_data: Dict
):
    """Create optimized AI Research tab using the proven working prompt format"""

    # Initialize research manager
    research_manager = OptimizedAIResearchManager(commodity, data_type, db_helper)

    st.header(f"🤖 AI Research - {commodity.title()} {data_type.title()}")

    # Show current data
    st.subheader("📊 Current Database Data")
    display_current_data_table(current_data, research_manager.countries)

    st.markdown("---")

    # AI Research Section
    st.subheader("🔮 Perplexity AI Research (Optimized)")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.info(
            f"""
        **Research Target:** {commodity.title()} {data_type.title()} data for 2024/2025 and 2025/2026
        
        **Countries:** {len(research_manager.countries)} countries from database
        
        **Method:** Uses the proven working prompt format that you tested successfully
        
        **Sources:** IGC, USDA FAS, and other official agricultural statistics
        
        **Tool:** Perplexity Advanced Search with recency filtering
        """
        )

    with col2:
        # Check agent status
        agent_available, status_msg = research_manager.check_agent_availability()

        if agent_available:
            st.success("🟢 Ready")
            st.info(status_msg)
        else:
            st.error("🔴 Not Ready")
            st.warning(status_msg)

    # Research execution
    research_key = f"{commodity}_{data_type}_optimized_research"

    if agent_available:
        if st.button(
            f"🚀 Start Optimized Research",
            type="primary",
            use_container_width=True,
            help="Uses the exact working prompt format you tested",
        ):
            execute_optimized_research(research_manager, research_key, current_data)

    # Display results
    display_research_results(research_key, research_manager, current_data)


def display_current_data_table(current_data: Dict, countries: List[str]):
    """Display current data table"""
    display_years = ["2022/2023", "2023/2024", "2024/2025", "2025/2026"]
    table_data = []

    for country in countries:
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


def execute_optimized_research(research_manager, research_key: str, current_data: Dict):
    """Execute the optimized research"""
    # Initialize research results storage
    if "optimized_research_results" not in st.session_state:
        st.session_state.optimized_research_results = {}

    # Create progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()

    def update_progress(value, message):
        progress_bar.progress(value)
        status_text.text(message)

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        success, response_text, parsed_data = loop.run_until_complete(
            research_manager.execute_research(update_progress)
        )

        # Store results
        st.session_state.optimized_research_results[research_key] = {
            "success": success,
            "response_text": response_text,
            "parsed_data": parsed_data,
            "timestamp": datetime.now().isoformat(),
            "commodity": research_manager.commodity,
            "data_type": research_manager.data_type,
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


def display_research_results(research_key: str, research_manager, current_data: Dict):
    """Display research results"""
    if research_key in st.session_state.get("optimized_research_results", {}):
        results = st.session_state.optimized_research_results[research_key]

        if results["success"]:
            st.markdown("---")
            st.subheader("📋 Research Results")

            # Show timestamp
            timestamp = datetime.fromisoformat(results["timestamp"])
            st.caption(f"Research completed: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")

            # Show AI response
            with st.expander("🤖 View Full AI Response", expanded=False):
                st.text_area(
                    "AI Research Response",
                    value=results["response_text"],
                    height=400,
                    disabled=True,
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

                # Update section
                display_update_section(
                    research_manager, research_key, results, current_data
                )

            else:
                st.warning("⚠️ Could not parse structured data from AI response.")

        else:
            st.error(
                f"❌ Research failed: {results.get('response_text', 'Unknown error')}"
            )


def display_update_section(
    research_manager, research_key: str, results: Dict, current_data: Dict
):
    """Display the update projections section"""
    st.subheader("💾 Update Projections")

    st.warning("⚠️ **Important:** Only 2025/2026 projections will be updated.")

    with st.form(f"update_form_{research_key}"):
        st.markdown("**Select countries to update with research data:**")

        updates_to_make = {}

        for country in research_manager.countries:
            if country not in current_data:
                continue

            research_value = results["parsed_data"].get(country, {}).get("2025/2026")

            if research_value and isinstance(research_value, (int, float)):
                current_value = current_data[country].get("2025/2026", 0)

                if (
                    abs(research_value - current_value) > 0.1
                ):  # Only show significant differences
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
            success, message = research_manager.update_projections(updates_to_make)

            if success:
                st.success(f"✅ {message}")
                st.cache_data.clear()
                st.rerun()
            else:
                st.error(f"❌ {message}")

        elif submit_updates and not updates_to_make:
            st.warning("⚠️ No countries selected for update.")

        if clear_results:
            del st.session_state.optimized_research_results[research_key]
            st.rerun()
