# client/utils/ai_research_components.py

import streamlit as st
import pandas as pd
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import asyncio
from services.mcp_service import run_agent
from services.chat_service import get_clean_conversation_memory
from langchain_core.messages import HumanMessage, ToolMessage, AIMessage

# Import configuration and optimized prompts
from utils.ai_research_config import (
    get_config,
    generate_prompt_template,
    get_countries_for_commodity,
)
from utils.perplexity_prompts import create_perplexity_search_prompt


class AIResearchManager:
    """Manages AI research operations for agricultural data"""

    def __init__(self, commodity: str, data_type: str, db_helper):
        """
        Initialize AI Research Manager

        Args:
            commodity: 'wheat' or 'corn'
            data_type: 'production', 'exports', 'imports', 'stocks', etc.
            db_helper: Database helper instance
        """
        self.commodity = commodity
        self.data_type = data_type
        self.db_helper = db_helper

        # Get configuration from config file
        self.config = get_config(commodity, data_type)

    def get_current_countries(self) -> List[str]:
        """Get list of countries from current database"""
        try:
            data_method = getattr(
                self.db_helper, self.config["data_type"]["db_methods"]["get_data"]
            )
            current_data = data_method()
            return list(current_data.keys())
        except:
            # Fallback to configured countries
            return get_countries_for_commodity(self.commodity)

    def generate_research_prompt(self) -> str:
        """Generate research prompt based on commodity and data type"""
        return generate_prompt_template(self.commodity, self.data_type)

    async def test_perplexity_search(self) -> Tuple[bool, str]:
        """Test Perplexity search with a simple query - following 9_mcp_app.py pattern"""
        try:
            from utils.perplexity_prompts import create_simple_test_prompt

            if not st.session_state.get("agent"):
                return False, "AI agent not available"

            # Create simple test prompt
            test_prompt = create_simple_test_prompt()

            # Create conversation memory following the working pattern
            conversation_memory = get_clean_conversation_memory()
            conversation_memory.append(HumanMessage(content=test_prompt))

            # Run the agent with test prompt
            response = await run_agent(st.session_state.agent, conversation_memory)

            # Process response following the same pattern as 9_mcp_app.py
            if "messages" in response:
                if len(response["messages"]) == 1 and isinstance(
                    response["messages"][0], dict
                ):
                    # Error response
                    error_content = response["messages"][0].get("content", "")
                    return False, f"Error response: {error_content}"
                else:
                    # Success - we got a proper response
                    new_messages = response["messages"][len(conversation_memory) :]

                    # Look for tool executions
                    tool_executed = False
                    for msg in new_messages:
                        if hasattr(msg, "tool_calls") and msg.tool_calls:
                            for tool_call in msg.tool_calls:
                                if "perplexity" in tool_call.get("name", "").lower():
                                    tool_executed = True
                                    break

                    if tool_executed:
                        return (
                            True,
                            "Perplexity search test successful - tool was executed",
                        )
                    else:
                        return False, "No Perplexity tool was executed in the test"
            else:
                return False, f"Unexpected response format: {str(response)[:200]}..."

        except Exception as e:
            return False, f"Test failed: {str(e)}"

    def test_perplexity_connection(self) -> Tuple[bool, str]:
        """Test if Perplexity connection is working"""
        try:
            # Check if agent exists
            if not st.session_state.get("agent"):
                return False, "No AI agent available"

            # Check if tools are available
            available_tools = st.session_state.get("tools", [])
            if not available_tools:
                return False, "No tools available"

            # Check for Perplexity tools
            perplexity_tools = [
                tool for tool in available_tools if "perplexity" in tool.name.lower()
            ]

            if not perplexity_tools:
                return False, "No Perplexity tools found"

            # Check if perplexity_advanced_search is available
            advanced_search_tool = None
            for tool in perplexity_tools:
                if "advanced_search" in tool.name.lower():
                    advanced_search_tool = tool
                    break

            if not advanced_search_tool:
                return (
                    False,
                    f"perplexity_advanced_search tool not found. Available: {[t.name for t in perplexity_tools]}",
                )

            return (
                True,
                f"Connection OK. Found {len(perplexity_tools)} Perplexity tools including perplexity_advanced_search",
            )

        except Exception as e:
            return False, f"Error testing connection: {str(e)}"
        """Generate optimized prompt specifically for Perplexity Advanced Search"""
        return create_perplexity_search_prompt(self.commodity, self.data_type)

    async def research_data(
        self, progress_callback=None
    ) -> Tuple[bool, str, Optional[Dict]]:
        """
        Research data using AI agent

        Returns:
            success: bool
            message: str
            parsed_data: Optional[Dict] - parsed research results
        """
        if not st.session_state.get("agent"):
            return (
                False,
                "AI agent not available. Please connect to MCP servers first.",
                None,
            )

        try:
            if progress_callback:
                progress_callback(0.1, "Generating research prompt...")

            prompt = self.generate_research_prompt()

            if progress_callback:
                progress_callback(0.2, "Sending research request to AI agent...")

            # Get conversation memory
            conversation_memory = get_clean_conversation_memory()
            conversation_memory.append(HumanMessage(content=prompt))

            if progress_callback:
                progress_callback(0.3, "AI agent researching data...")

            # Run the agent
            response = await run_agent(st.session_state.agent, conversation_memory)

            if progress_callback:
                progress_callback(0.8, "Processing AI response...")

            # Extract response text
            response_text = ""
            if "messages" in response:
                for msg in response["messages"]:
                    if hasattr(msg, "content") and msg.content:
                        response_text += str(msg.content) + "\n"

            if progress_callback:
                progress_callback(0.9, "Parsing research results...")

            # Try to parse the response into structured data
            parsed_data = self._parse_research_response(response_text)

            # Store results properly in session state (following 9_mcp_app.py pattern)
            if "research_results" not in st.session_state:
                st.session_state.research_results = {}

            research_key = f"{self.commodity}_{self.data_type}_research"

            # Store the research request in session state (like chat messages)
            user_message = {"role": "user", "content": prompt}

            # Store the assistant response
            if assistant_response:
                assistant_message = {"role": "assistant", "content": assistant_response}

                # Store in session state for persistence
                st.session_state.research_results[research_key] = {
                    "success": True,
                    "response_text": response_text,
                    "parsed_data": parsed_data,
                    "timestamp": datetime.now().isoformat(),
                    "user_message": user_message,
                    "assistant_message": assistant_message,
                }

            if progress_callback:
                progress_callback(1.0, "Research completed!")

            return True, response_text, parsed_data

        except Exception as e:
            return False, f"Error during research: {str(e)}", None

    def _parse_research_response(self, response_text: str) -> Optional[Dict]:
        """
        Parse Perplexity response to extract structured data

        Enhanced parser for Perplexity Advanced Search results
        """
        try:
            parsed_data = {}
            countries = self.get_current_countries()

            # Initialize structure
            for country in countries:
                parsed_data[country] = {
                    "2024/2025": None,
                    "2025/2026": None,
                    "source": None,
                    "notes": None,
                }

            # Enhanced parsing logic for Perplexity results
            lines = response_text.split("\n")
            current_country = None
            current_section = None

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # Look for country names (case insensitive)
                for country in countries:
                    if country.lower() in line.lower():
                        # Additional checks to ensure it's actually referring to the country
                        if any(
                            keyword in line.lower()
                            for keyword in [
                                "production",
                                "export",
                                "import",
                                "stock",
                                "yield",
                                "acre",
                                "demand",
                            ]
                        ):
                            current_country = country
                            break

                # Look for year-specific data
                if current_country:
                    # Extract numerical values and associate with years
                    import re

                    # Pattern for numbers with potential units (million, thousand, Mt, etc.)
                    number_patterns = [
                        r"(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(?:million|mn|m\.?\s*metric\s*tons?|mmt|mt|thousand|k)",
                        r"(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(?:mt|mmt)",
                        r"(\d{1,3}(?:,\d{3})*(?:\.\d+)?)",
                    ]

                    for pattern in number_patterns:
                        matches = re.findall(pattern, line.lower())
                        if matches:
                            try:
                                # Take the first number found
                                value_str = matches[0].replace(",", "")
                                value = float(value_str)

                                # Determine which year this refers to
                                if (
                                    "2024/25" in line
                                    or "2024-25" in line
                                    or "2024/2025" in line
                                ):
                                    if (
                                        parsed_data[current_country]["2024/2025"]
                                        is None
                                    ):
                                        parsed_data[current_country][
                                            "2024/2025"
                                        ] = value
                                elif (
                                    "2025/26" in line
                                    or "2025-26" in line
                                    or "2025/2026" in line
                                ):
                                    if (
                                        parsed_data[current_country]["2025/2026"]
                                        is None
                                    ):
                                        parsed_data[current_country][
                                            "2025/2026"
                                        ] = value

                                # If no specific year mentioned but we have context
                                elif any(
                                    word in line.lower()
                                    for word in ["forecast", "projection", "estimate"]
                                ):
                                    if (
                                        parsed_data[current_country]["2025/2026"]
                                        is None
                                    ):
                                        parsed_data[current_country][
                                            "2025/2026"
                                        ] = value
                                elif any(
                                    word in line.lower()
                                    for word in ["current", "this year", "2024"]
                                ):
                                    if (
                                        parsed_data[current_country]["2024/2025"]
                                        is None
                                    ):
                                        parsed_data[current_country][
                                            "2024/2025"
                                        ] = value

                                break  # Found a number, move to next line
                            except ValueError:
                                continue

                # Extract source information
                if any(
                    source in line.lower()
                    for source in ["usda", "igc", "source:", "according to"]
                ):
                    if (
                        current_country
                        and parsed_data[current_country]["source"] is None
                    ):
                        parsed_data[current_country]["source"] = line[
                            :100
                        ]  # First 100 chars

            # Clean up data - remove countries with no data
            cleaned_data = {}
            for country, data in parsed_data.items():
                if data["2024/2025"] is not None or data["2025/2026"] is not None:
                    cleaned_data[country] = {
                        "2024/2025": data["2024/2025"],
                        "2025/2026": data["2025/2026"],
                    }

            return cleaned_data if cleaned_data else None

        except Exception as e:
            st.error(f"Error parsing Perplexity research response: {e}")
            return None

    def create_comparison_table(
        self, current_data: Dict, research_data: Dict
    ) -> pd.DataFrame:
        """Create comparison table between current and research data"""
        comparison_data = []

        for country in current_data.keys():
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

            # Calculate differences for 2025/2026
            if research_data.get(country, {}).get("2025/2026") and isinstance(
                research_data[country]["2025/2026"], (int, float)
            ):

                current_val = current_data[country].get("2025/2026", 0)
                research_val = research_data[country]["2025/2026"]
                difference = research_val - current_val
                row["Difference"] = f"{difference:+.1f}" if difference != 0 else "0.0"
            else:
                row["Difference"] = "N/A"

            comparison_data.append(row)

        return pd.DataFrame(comparison_data)

    def update_projections(self, updates: Dict[str, float]) -> Tuple[bool, str]:
        """
        Update 2025/2026 projections in database

        Args:
            updates: Dict mapping country names to new values

        Returns:
            success: bool
            message: str
        """
        try:
            update_method = getattr(
                self.db_helper, self.data_configs[self.data_type]["update_method"]
            )

            # Get current data to calculate changes
            data_method = getattr(
                self.db_helper, self.data_configs[self.data_type]["db_method"]
            )
            current_data = data_method()

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
    """
    Create AI Research tab for any commodity and data type

    Args:
        commodity: 'wheat' or 'corn'
        data_type: 'production', 'exports', 'imports', etc.
        db_helper: Database helper instance
        current_data: Current data from database
    """
    config = get_config(commodity, data_type)

    st.header(
        f"🤖 AI Research - {config['commodity']['display_name']} {config['data_type']['display_name']}"
    )

    # Initialize research manager
    research_manager = AIResearchManager(commodity, data_type, db_helper)

    # Display current data
    st.subheader("📊 Current Database Data")

    # Show current data table
    display_years = ["2022/2023", "2023/2024", "2024/2025", "2025/2026"]
    table_data = []

    for country, data in current_data.items():
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
        **Research Target:** {config['commodity']['display_name']} {config['data_type']['display_name']} data {config['data_type']['unit']} for 2024/2025 and 2025/2026 projections
        
        **Data Sources:** IGC, USDA FAS, and other official agricultural statistics sources
        
        **AI Tool:** Perplexity Advanced Search with recency filtering for latest data
        
        **Search Strategy:** Optimized queries targeting official agricultural reports and forecasts
        """
        )

    with col2:
        # Check if Perplexity tools are available
        agent_available = bool(st.session_state.get("agent"))
        perplexity_tools = [
            tool
            for tool in st.session_state.get("tools", [])
            if "perplexity" in tool.name.lower()
        ]

        if agent_available and perplexity_tools:
            st.success("🟢 Perplexity Ready")
            st.info(f"🔮 {len(perplexity_tools)} Perplexity tools available")

            # Show available tool names
            tool_names = [tool.name for tool in perplexity_tools]
            st.caption(f"Tools: {', '.join(tool_names)}")

        elif agent_available:
            st.warning("🟡 Agent Ready, Missing Perplexity")
            st.warning("Please connect to Perplexity MCP server")
        else:
            st.error("🔴 AI Agent Not Available")
            st.warning("Please connect to MCP servers in the MCP Tools page first.")

        # Add test connection button
        if st.button("🔧 Test Connection", use_container_width=True):
            research_manager = AIResearchManager(commodity, data_type, db_helper)

            # Test 1: Connection test
            test_success, test_message = research_manager.test_perplexity_connection()

            if test_success:
                st.success(f"✅ Connection: {test_message}")

                # Test 2: Actual search test
                st.info("🔄 Testing Perplexity search...")
                import asyncio

                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

                    search_success, search_message = loop.run_until_complete(
                        research_manager.test_perplexity_search()
                    )

                    if search_success:
                        st.success(f"✅ Search: {search_message}")
                    else:
                        st.error(f"❌ Search: {search_message}")

                except Exception as e:
                    st.error(f"❌ Search test failed: {str(e)}")
            else:
                st.error(f"❌ Connection: {test_message}")

    # Debug information
    with st.expander("🐛 Debug Information", expanded=False):
        st.write("**Session State Debug:**")
        st.write(f"- Agent available: {bool(st.session_state.get('agent'))}")
        st.write(f"- Total tools: {len(st.session_state.get('tools', []))}")
        st.write(f"- Perplexity tools: {len(perplexity_tools)}")

        if perplexity_tools:
            st.write("**Available Perplexity Tools:**")
            for tool in perplexity_tools:
                st.write(
                    f"- {tool.name}: {getattr(tool, 'description', 'No description')}"
                )

        st.write("**MCP Servers:**")
        servers = st.session_state.get("servers", {})
        for name, config in servers.items():
            st.write(f"- {name}: {config.get('url', 'No URL')}")

    # Research button and progress
    research_enabled = agent_available and len(perplexity_tools) > 0

    if st.button(
        f"🔮 Start Perplexity Research for {config['commodity']['display_name']} {config['data_type']['display_name']}",
        type="primary",
        disabled=not research_enabled,
        use_container_width=True,
        help="Uses Perplexity Advanced Search to find latest agricultural data",
    ):
        # Initialize session state for research results
        if "research_results" not in st.session_state:
            st.session_state.research_results = {}

        research_key = f"{commodity}_{data_type}_research"

        # Create progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()

        def update_progress(value, message):
            progress_bar.progress(value)
            status_text.text(message)

        # Run research
        try:
            import asyncio

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            success, response_text, parsed_data = loop.run_until_complete(
                research_manager.research_data(update_progress)
            )

            # Store results in session state
            st.session_state.research_results[research_key] = {
                "success": success,
                "response_text": response_text,
                "parsed_data": parsed_data,
                "timestamp": datetime.now().isoformat(),
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
            st.error(f"❌ Research failed: {str(e)}")

    # Display research results if available
    research_key = f"{commodity}_{data_type}_research"
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

            # Show parsed data if available
            if results["parsed_data"]:
                st.subheader("📊 Comparison Table")

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
                st.subheader("💾 Update Projections")

                st.warning(
                    """
                **⚠️ Important:** Only 2025/2026 projections will be updated. 
                Historical and current year data will remain unchanged.
                """
                )

                # Create update form
                with st.form(f"update_projections_{research_key}"):
                    st.markdown("**Select countries to update with research data:**")

                    updates_to_make = {}

                    for country in current_data.keys():
                        research_value = (
                            results["parsed_data"].get(country, {}).get("2025/2026")
                        )

                        if research_value and isinstance(research_value, (int, float)):
                            current_value = current_data[country].get("2025/2026", 0)

                            if research_value != current_value:
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


# Utility function to add AI research tab to existing pages
def add_ai_research_to_page(
    commodity: str, data_type: str, db_helper, current_data: Dict, tab_list: List
):
    """
    Helper function to add AI research tab to existing page structure

    Args:
        commodity: 'wheat' or 'corn'
        data_type: 'production', 'exports', etc.
        db_helper: Database helper instance
        current_data: Current database data
        tab_list: List of existing tabs

    Returns:
        Updated tab list with AI Research tab
    """
    tab_list.append("🤖 AI Research")
    return tab_list
