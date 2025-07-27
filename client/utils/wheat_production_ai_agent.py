# client/utils/wheat_production_ai_agent.py

import streamlit as st
import pandas as pd
import asyncio
import os
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from langchain_core.messages import HumanMessage, ToolMessage, AIMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from services.ai_service import create_llm_model


class WheatProductionAIAgent:
    """Independent AI agent for wheat production research using Perplexity MCP server only"""

    def __init__(self):
        """Initialize the independent wheat production AI agent"""
        self.client = None
        self.agent = None
        self.tools = []

        # Define the countries we need data for
        self.target_countries = [
            "WORLD",
            "China",
            "European Union",
            "Russia",
            "United States",
            "Australia",
            "Canada",
            "India",
        ]

    async def initialize_agent(self) -> Tuple[bool, str]:
        """
        Initialize the independent Perplexity MCP agent

        Returns:
            success: bool
            message: str - Status message
        """
        try:
            # Clean up any existing client
            if self.client:
                await self.cleanup()

            # Perplexity server configuration (only this server)
            perplexity_config = {
                "Perplexity Search": {
                    "transport": "sse",
                    "url": os.getenv(
                        "PERPLEXITY_SERVER_URL", "http://mcpserver3:8003/sse"
                    ),
                    "timeout": 600,
                    "headers": None,
                    "sse_read_timeout": 900,
                }
            }

            # Create LLM with default Anthropic settings
            llm = create_llm_model(
                "Anthropic",
                temperature=1.0,  # Default temperature
                max_tokens=4096,  # Default max tokens
            )

            # Setup MCP client for Perplexity only
            self.client = MultiServerMCPClient(perplexity_config)
            await self.client.__aenter__()

            # Get tools
            self.tools = self.client.get_tools()

            # Verify we have perplexity tools
            perplexity_tools = [
                tool for tool in self.tools if "perplexity" in tool.name.lower()
            ]

            if not perplexity_tools:
                await self.cleanup()
                return False, "No Perplexity tools found in server response"

            # Create agent
            self.agent = create_react_agent(llm, self.tools)

            return (
                True,
                f"Initialized independent agent with {len(perplexity_tools)} Perplexity tools",
            )

        except Exception as e:
            await self.cleanup()
            return False, f"Failed to initialize agent: {str(e)}"

    async def clear_perplexity_cache(self) -> Tuple[bool, str]:
        """
        Clear the Perplexity server cache

        Returns:
            success: bool
            message: str - Status message
        """
        try:
            if not self.agent:
                return False, "Agent not initialized"

            clear_cache_prompt = """Please use the clear_api_cache tool to clear the Perplexity server cache.

This will ensure we get fresh data for our wheat production research."""

            conversation_memory = [HumanMessage(content=clear_cache_prompt)]
            response = await self._run_agent(conversation_memory)

            # Check if cache clear tool was executed
            cache_cleared = False
            for msg in response.get("messages", []):
                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    for tool_call in msg.tool_calls:
                        if "clear_api_cache" in tool_call.get("name", "").lower():
                            cache_cleared = True
                            break

            if cache_cleared:
                return True, "Perplexity cache cleared successfully"
            else:
                return False, "Failed to clear cache - tool not executed"

        except Exception as e:
            return False, f"Error clearing cache: {str(e)}"

    async def research_wheat_production(
        self, progress_callback=None
    ) -> Tuple[bool, str, Optional[Dict]]:
        """
        Research wheat production data using Perplexity Advanced Search

        Args:
            progress_callback: Optional callback for progress updates

        Returns:
            success: bool
            message: str
            parsed_data: Optional[Dict] - Structured data
        """
        try:
            if progress_callback:
                progress_callback(0.1, "Initializing agent...")

            # Initialize agent if not already done
            if not self.agent:
                success, msg = await self.initialize_agent()
                if not success:
                    return False, msg, None

            if progress_callback:
                progress_callback(0.2, "Clearing Perplexity cache...")

            # Clear cache first
            cache_success, cache_msg = await self.clear_perplexity_cache()
            if not cache_success:
                st.warning(f"Cache clear warning: {cache_msg}")

            if progress_callback:
                progress_callback(0.3, "Generating research prompt...")

            # Create the specific prompt for wheat production
            research_prompt = self._create_wheat_production_prompt()

            if progress_callback:
                progress_callback(0.4, "Executing Perplexity Advanced Search...")

            # Execute research
            conversation_memory = [HumanMessage(content=research_prompt)]
            response = await self._run_agent(conversation_memory)

            if progress_callback:
                progress_callback(0.7, "Processing search results...")

            # Extract response
            response_text = ""
            tool_executed = False

            if "messages" in response:
                new_messages = response["messages"][len(conversation_memory) :]

                for msg in new_messages:
                    if hasattr(msg, "tool_calls") and msg.tool_calls:
                        for tool_call in msg.tool_calls:
                            if "perplexity" in tool_call.get("name", "").lower():
                                tool_executed = True
                    elif (
                        isinstance(msg, AIMessage)
                        and hasattr(msg, "content")
                        and msg.content
                    ):
                        response_text += str(msg.content) + "\n"

            if not tool_executed:
                return False, "Perplexity search tool was not executed", None

            if not response_text.strip():
                return False, "No response received from Perplexity search", None

            if progress_callback:
                progress_callback(0.9, "Parsing wheat production data...")

            # Parse the response into structured data
            parsed_data = self._parse_wheat_production_response(response_text)

            if progress_callback:
                progress_callback(1.0, "Research completed!")

            return True, response_text.strip(), parsed_data

        except Exception as e:
            return False, f"Research error: {str(e)}", None

    def _create_wheat_production_prompt(self) -> str:
        """Create optimized prompt for wheat production research"""
        countries_list = "\n".join(
            [f"- {country}" for country in self.target_countries]
        )

        prompt = f"""Use perplexity_advanced_search to get 2024/2025 and projections for 2025/2026 of Wheat Production in MILLION METRIC TONS for the following areas:

{countries_list}

SEARCH PARAMETERS:
- Query: "wheat production 2024/2025 2025/2026 forecast projection USDA IGC statistics million metric tons"
- Recency: "year" (1 year filter)
- Max tokens: 1024
- Temperature: 0.2

You can use any information available in these sites:
- https://www.igc.int/en/markets/marketinfo-forecasts.aspx# (wheat section)
- https://ipad.fas.usda.gov/cropexplorer/cropview/commodityView.aspx?cropid=0410000&sel_year=2024&rankby=Production
- https://www.fas.usda.gov/
- https://www.fas.usda.gov/data
- any other public available site

CRITICAL REQUIREMENTS:
1. The response must be ONLY a properly formatted table that can be easily parsed
2. Values MUST be in MILLION METRIC TONS (not thousands)
3. Use this EXACT format:

| Country/Region | 2024/2025 | 2025/2026 | Source | Date |
|---|---|---|---|---|
| WORLD | 800.1 | 808.6 | USDA/IGC | July 2025 |
| China | 140.1 | 142.0 | USDA FAS | 2025 |
| European Union | 124.0 | 137.0 | EU Commission | July 2025 |
| India | 114.0 | 113.0 | USDA/FAO | July 2025 |
| Russia | 87.5 | 81.2 | USDA | July 2025 |
| United States | 53.7 | 37.6 | USDA WASDE | July 2025 |
| Australia | 29.0 | 32.0 | USDA | July 2025 |
| Canada | 33.4 | 35.0 | AAFC | March 2025 |

IMPORTANT: 
- Do NOT include any explanatory text, just the table
- Values should be in MILLION METRIC TONS (MMT) - NOT thousands
- Convert values if sources show thousands of metric tons (divide by 1000)
- Use the most recent official data available"""

        return prompt

    def _parse_wheat_production_response(self, response_text: str) -> Optional[Dict]:
        """
        Parse the Perplexity response to extract wheat production data

        Args:
            response_text: Raw response from Perplexity

        Returns:
            Parsed data dictionary or None
        """
        try:
            parsed_data = {}

            # Look for table format in the response
            lines = response_text.split("\n")

            # Find table rows (look for | separators)
            table_rows = []
            for line in lines:
                line = line.strip()
                if "|" in line and not line.startswith("|---"):
                    # Split by | and clean up
                    parts = [part.strip() for part in line.split("|")]
                    if len(parts) >= 4:  # Country, 2024/25, 2025/26, source minimum
                        table_rows.append(parts)

            # Skip header row if present
            if table_rows and any(
                header in table_rows[0][0].lower() for header in ["country", "region"]
            ):
                table_rows = table_rows[1:]

            # Parse each data row
            for row in table_rows:
                if len(row) >= 4:
                    country = row[1].strip() if len(row) > 1 else row[0].strip()

                    # Skip empty countries
                    if not country or country == "":
                        continue

                    # Clean country name
                    country = country.replace("**", "").strip()

                    # Check if this is one of our target countries
                    matched_country = None
                    for target in self.target_countries:
                        if (
                            target.lower() in country.lower()
                            or country.lower() in target.lower()
                        ):
                            matched_country = target
                            break

                    if matched_country:
                        try:
                            # Extract values
                            val_2024_25 = None
                            val_2025_26 = None

                            if len(row) >= 3:
                                # Try to parse 2024/2025 value
                                val_str = row[2].strip().replace(",", "")
                                if (
                                    val_str
                                    and val_str.replace(".", "")
                                    .replace("-", "")
                                    .isdigit()
                                ):
                                    val_2024_25 = float(val_str)
                                    # Convert from thousands to millions if value is too large
                                    if (
                                        val_2024_25 > 1000
                                    ):  # Likely in thousands, convert to millions
                                        val_2024_25 = val_2024_25 / 1000

                            if len(row) >= 4:
                                # Try to parse 2025/2026 value
                                val_str = row[3].strip().replace(",", "")
                                if (
                                    val_str
                                    and val_str.replace(".", "")
                                    .replace("-", "")
                                    .isdigit()
                                ):
                                    val_2025_26 = float(val_str)
                                    # Convert from thousands to millions if value is too large
                                    if (
                                        val_2025_26 > 1000
                                    ):  # Likely in thousands, convert to millions
                                        val_2025_26 = val_2025_26 / 1000

                            # Store data
                            parsed_data[matched_country] = {
                                "2024/2025": val_2024_25,
                                "2025/2026": val_2025_26,
                            }

                        except (ValueError, IndexError):
                            continue

            # If parsing failed, try alternative method
            if not parsed_data:
                parsed_data = self._fallback_parse_method(response_text)

            return parsed_data if parsed_data else None

        except Exception as e:
            st.error(f"Error parsing response: {e}")
            return None

    def _fallback_parse_method(self, response_text: str) -> Optional[Dict]:
        """Fallback parsing method if table parsing fails"""
        try:
            import re

            parsed_data = {}

            # Look for patterns like "Country: 123.4" or "Country - 123.4"
            for country in self.target_countries:
                # Pattern to find country and numbers
                pattern = rf"{re.escape(country)}.*?(\d{{1,3}}(?:,\d{{3}})*(?:\.\d+)?)"
                matches = re.findall(pattern, response_text, re.IGNORECASE)

                if matches:
                    try:
                        # Take the first number found
                        value = float(matches[0].replace(",", ""))
                        # Convert from thousands to millions if value is too large
                        if value > 1000:  # Likely in thousands, convert to millions
                            value = value / 1000

                        parsed_data[country] = {
                            "2024/2025": value,
                            "2025/2026": None,  # May be filled by another pattern
                        }
                    except:
                        continue

            return parsed_data if parsed_data else None

        except Exception:
            return None

    async def _run_agent(self, conversation_memory):
        """Run the agent with conversation memory"""
        from services.mcp_service import run_agent

        return await run_agent(self.agent, conversation_memory)

    async def cleanup(self):
        """Cleanup the agent and client"""
        try:
            if self.client:
                # Properly close the client connection
                await self.client.__aexit__(None, None, None)
                st.info("✅ MCP client connection closed successfully")
        except Exception as e:
            # Don't show error to user unless it's critical
            st.warning(f"Warning during cleanup: {e}")
        finally:
            # Always reset the state
            self.client = None
            self.agent = None
            self.tools = []

    def create_comparison_table(
        self, current_data: Dict, research_data: Dict
    ) -> pd.DataFrame:
        """
        Create a properly formatted comparison table

        Args:
            current_data: Current database data
            research_data: Research results data

        Returns:
            Formatted pandas DataFrame
        """
        comparison_data = []

        for country in self.target_countries:
            # Get current data (already in millions)
            current_2024_25 = current_data.get(country, {}).get("2024/2025", 0.0)
            current_2025_26 = current_data.get(country, {}).get("2025/2026", 0.0)

            # Get research data (should now be in millions after parsing)
            research_2024_25 = research_data.get(country, {}).get("2024/2025")
            research_2025_26 = research_data.get(country, {}).get("2025/2026")

            # Calculate difference for 2025/2026
            difference = "N/A"
            if research_2025_26 and isinstance(research_2025_26, (int, float)):
                diff_val = research_2025_26 - current_2025_26
                difference = f"{diff_val:+.1f}" if diff_val != 0 else "0.0"

            row = {
                "Country/Region": country,
                "Current 2024/2025": (
                    f"{current_2024_25:.1f}" if current_2024_25 else "0.0"
                ),
                "Research 2024/2025": (
                    f"{research_2024_25:.1f}" if research_2024_25 else "N/A"
                ),
                "Current 2025/2026": (
                    f"{current_2025_26:.1f}" if current_2025_26 else "0.0"
                ),
                "Research 2025/2026": (
                    f"{research_2025_26:.1f}" if research_2025_26 else "N/A"
                ),
                "Difference": difference,
            }

            comparison_data.append(row)

        return pd.DataFrame(comparison_data)


# Integration function for wheat production page
async def run_wheat_production_ai_research(
    current_data: Dict, progress_callback=None
) -> Tuple[bool, str, Optional[Dict], Optional[pd.DataFrame]]:
    """
    Run independent wheat production AI research

    Args:
        current_data: Current wheat production data from database
        progress_callback: Optional progress callback function

    Returns:
        success: bool
        message: str
        research_data: Optional[Dict]
        comparison_table: Optional[pd.DataFrame]
    """
    agent = WheatProductionAIAgent()

    try:
        # Run research
        success, message, research_data = await agent.research_wheat_production(
            progress_callback
        )

        if success and research_data:
            # Create comparison table
            comparison_table = agent.create_comparison_table(
                current_data, research_data
            )
            return True, message, research_data, comparison_table
        else:
            return False, message, None, None

    except Exception as e:
        return False, f"Research failed: {str(e)}", None, None
    finally:
        # Always cleanup - this should fix the resource issue
        try:
            await agent.cleanup()
        except Exception as cleanup_error:
            # Log cleanup error but don't fail the function
            st.warning(f"Cleanup warning: {cleanup_error}")
            pass
