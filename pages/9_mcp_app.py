import os
import datetime
import streamlit as st
from langchain_core.messages import HumanMessage, ToolMessage, AIMessage
from services.ai_service import get_response_stream
from services.mcp_service import run_agent, use_prompt
from services.chat_service import (
    get_current_chat,
    _append_message_to_session,
    get_clean_conversation_memory,
    init_session,
)
from utils.async_helpers import run_async
from utils.ai_prompts import make_system_prompt, make_main_prompt
import ui_components.sidebar_components as sd_components
from ui_components.main_components import display_tool_executions
from ui_components.tab_components import (
    create_configuration_tab,
    create_connection_tab,
    create_tools_tab,
)
from config import DEFAULT_MAX_TOKENS, DEFAULT_TEMPERATURE
import traceback

# Initialize session for MCP
init_session()

# Page configuration
st.set_page_config(
    page_title="AI & MCP Tools Interface",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Hide the navigation on this page
st.markdown(
    """
<style>
    /* Hide Streamlit's default page navigation */
    [data-testid="stSidebarNav"] {
        display: none !important;
    }
    
    /* Hide navigation container */
    section[data-testid="stSidebarNav"] {
        display: none !important;
    }
    
    /* Adjust sidebar spacing */
    .css-1d391kg {
        padding-top: 1rem;
    }
</style>
""",
    unsafe_allow_html=True,
)

# Check authentication
if not st.session_state.get("authentication_status"):
    st.error("🔐 Authentication required. Please log in to access this page.")
    if st.button("Return to Login"):
        st.switch_page("app.py")
    st.stop()

# Add unified sidebar navigation
with st.sidebar:
    # Logo section
    logo_path = os.path.join(".", "icons", "Logo.png")
    if os.path.exists(logo_path):
        col1, col2 = st.columns([1, 3])
        with col1:
            st.image(logo_path, width=60)
        with col2:
            st.markdown(
                """
            <div style="padding-top: 10px;">
                <h3 style="margin: 0; color: #2F2E78;">PPF Europe</h3>
                <p style="margin: 0; font-size: 12px; color: #666;">MCP Tools</p>
            </div>
            """,
                unsafe_allow_html=True,
            )

    st.markdown("---")

    # User info and authentication status
    st.success(f"✅ Welcome, **{st.session_state['name']}**!")
    st.info(f"👤 Username: {st.session_state['username']}")

    if st.button(
        "🏠 Return to Main Dashboard", use_container_width=True, type="primary"
    ):
        st.switch_page("app.py")

    st.markdown("---")

    # Quick Navigation to Wheat pages
    st.markdown("### 🌾 Wheat Analysis")

    with st.expander("📊 Wheat Supply & Demand", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🌾 Production", use_container_width=True, key="wheat_prod"):
                st.switch_page("pages/1_wheat_production.py")
            if st.button("📥 Imports", use_container_width=True, key="wheat_imp"):
                st.switch_page("pages/3_wheat_imports.py")
            if st.button("📊 S/U Ratio", use_container_width=True, key="wheat_su"):
                st.switch_page("pages/5_stock_to_use_ratio.py")
            if st.button("🌱 Yield", use_container_width=True, key="wheat_yield"):
                st.switch_page("pages/7_wheat_yield.py")
        with col2:
            if st.button("📦 Exports", use_container_width=True, key="wheat_exp"):
                st.switch_page("pages/2_wheat_exports.py")
            if st.button("🏢 Stocks", use_container_width=True, key="wheat_stock"):
                st.switch_page("pages/4_wheat_stocks.py")
            if st.button("🌾 Acreage", use_container_width=True, key="wheat_acre"):
                st.switch_page("pages/6_wheat_acreage.py")
            if st.button("🌍 World Demand", use_container_width=True, key="wheat_dem"):
                st.switch_page("pages/8_wheat_world_demand.py")

    st.markdown("---")

    # Corn pages
    st.markdown("### 🌽 Corn Analysis")

    with st.expander("📊 Corn Supply & Demand", expanded=False):
        if st.button("🌽 Production", use_container_width=True, key="corn_prod"):
            st.switch_page("pages/10_corn_production.py")
        if st.button("📦 Exports", use_container_width=True, key="corn_exp"):
            st.switch_page("pages/11_corn_exports.py")
        if st.button("📥 Imports", use_container_width=True, key="corn_imp"):
            st.switch_page("pages/12_corn_imports.py")
        st.info("🏢 Stocks - Coming Soon")
        st.info("📊 S/U Ratio - Coming Soon")
        st.info("🌽 Acreage - Coming Soon")
        st.info("🌱 Yield - Coming Soon")
        st.info("🌍 World Demand - Coming Soon")

    st.markdown("---")

    # MCP-specific sidebar components
    st.markdown("### 💬 Chat Management")
    sd_components.create_history_chat_container()
    sd_components.create_sidebar_chat_buttons()

    # Connection status and tool counts
    st.markdown("---")
    st.markdown("### 🔌 Connection Status")

    # Connection status
    if st.session_state.get("agent"):
        st.success("🟢 Connected to MCP")
    else:
        st.error("🔴 Not Connected")

    # Provider status
    provider = st.session_state.get("params", {}).get("model_id", "Not Set")
    st.info(f"🤖 Provider: {provider}")

    # Tools, prompts, and resources count
    tools_count = len(st.session_state.get("tools", []))
    prompts_count = len(st.session_state.get("prompts", []))
    resources_count = len(st.session_state.get("resources", []))

    col1, col2 = st.columns(2)
    with col1:
        st.metric("🧰 Tools", tools_count)
    with col2:
        st.metric("📝 Prompts", prompts_count)

    if resources_count > 0:
        st.metric("📁 Resources", resources_count)

    # Show detailed tool breakdown if tools are available
    if tools_count > 0:
        firecrawl_tools = [
            tool
            for tool in st.session_state.get("tools", [])
            if any(
                keyword in tool.name.lower()
                for keyword in ["firecrawl", "scrape", "crawl", "map", "extract"]
            )
        ]
        google_tools = [
            tool
            for tool in st.session_state.get("tools", [])
            if any(
                keyword in tool.name.lower()
                for keyword in [
                    "google-search",
                    "read-webpage",
                    "clear-cache",
                    "cache-stats",
                ]
            )
        ]
        perplexity_tools = [
            tool
            for tool in st.session_state.get("tools", [])
            if any(
                keyword in tool.name.lower()
                for keyword in ["perplexity", "clear_api_cache", "get_cache_stats"]
            )
        ]

        with st.container():
            st.markdown("**Tool Categories:**")
            if firecrawl_tools:
                st.text(f"🔥 Firecrawl: {len(firecrawl_tools)}")
            if google_tools:
                st.text(f"🔍 Google: {len(google_tools)}")
            if perplexity_tools:
                st.text(f"🔮 Perplexity: {len(perplexity_tools)}")


# Title
st.title("🔥 Firecrawl, Google Search & Perplexity MCP Client")
st.markdown("### AI-Powered Chat Interface with Web Tools")

# Add user welcome message
st.success(f"Welcome back, **{st.session_state['name']}**! 👋")

# Create the main tabs
tab1, tab2, tab3, tab4 = st.tabs(
    ["💬 Chat", "⚙️ Configuration", "🔌 Connections", "🧰 Tools"]
)

# Chat Tab - Main conversation interface
with tab1:
    # Main chat interface
    st.header("💬 Chat with Firecrawl, Google Search & Perplexity Agent")

    # Show available search engine status
    firecrawl_tools = [
        tool
        for tool in st.session_state.get("tools", [])
        if any(
            keyword in tool.name.lower()
            for keyword in ["firecrawl", "scrape", "crawl", "map", "extract"]
        )
    ]
    google_tools = [
        tool
        for tool in st.session_state.get("tools", [])
        if any(
            keyword in tool.name.lower()
            for keyword in [
                "google-search",
                "read-webpage",
                "clear-cache",
                "cache-stats",
            ]
        )
    ]
    perplexity_tools = [
        tool
        for tool in st.session_state.get("tools", [])
        if any(
            keyword in tool.name.lower()
            for keyword in ["perplexity", "clear_api_cache", "get_cache_stats"]
        )
    ]

    status_parts = []
    if firecrawl_tools:
        status_parts.append(f"🔥 Firecrawl: {len(firecrawl_tools)} tools")
    if google_tools:
        status_parts.append(f"🔍 Google Search: {len(google_tools)} tools")
    if perplexity_tools:
        status_parts.append(f"🔮 Perplexity: {len(perplexity_tools)} tools")

    if status_parts:
        st.success(" | ".join(status_parts) + " available")
    else:
        st.warning(
            "🔥 Firecrawl: Not connected | 🔍 Google Search: Not connected | 🔮 Perplexity: Not connected"
        )

    st.markdown(
        "Ask questions to search the web, scrape content, and analyze data using Firecrawl, Google Search, and Perplexity AI tools."
    )

    messages_container = st.container(border=True, height=600)

    # Re-render previous messages
    if st.session_state.get("current_chat_id"):
        st.session_state["messages"] = get_current_chat(
            st.session_state["current_chat_id"]
        )
        for m in st.session_state["messages"]:
            with messages_container.chat_message(m["role"]):
                if "tool" in m and m["tool"]:
                    st.code(m["tool"], language="yaml")
                if "content" in m and m["content"]:
                    st.markdown(m["content"])

    # Chat input
    user_text = st.chat_input("Ask a question or request web scraping/search")

    # Handle chat logic
    if user_text is not None:  # something submitted
        params = st.session_state.get("params")

        # Check if we have proper credentials loaded from environment
        selected_provider = params.get("model_id")
        credentials_valid = False

        if selected_provider == "OpenAI":
            credentials_valid = bool(os.getenv("OPENAI_API_KEY"))
        elif selected_provider == "Anthropic":
            credentials_valid = bool(os.getenv("ANTHROPIC_API_KEY"))

        if not credentials_valid:
            err_mesg = f"❌ Missing credentials for {selected_provider}. Please check your .env file and configure in the Configuration tab."
            _append_message_to_session({"role": "assistant", "content": err_mesg})
            with messages_container.chat_message("assistant"):
                st.markdown(err_mesg)
            st.rerun()

        # Handle question (if any text)
        if user_text:
            user_text_dct = {"role": "user", "content": user_text}
            _append_message_to_session(user_text_dct)
            with messages_container.chat_message("user"):
                st.markdown(user_text)

            with st.spinner("Thinking…", show_time=True):
                # Handle normal conversation
                system_prompt = make_system_prompt()
                main_prompt = make_main_prompt(user_text)
                try:
                    # If agent is available, use it
                    if st.session_state.agent:
                        # Create conversation memory for the agent (clean version without tool messages)
                        conversation_memory = get_clean_conversation_memory()

                        # Add the current user message to the conversation
                        conversation_memory.append(HumanMessage(content=user_text))

                        try:
                            # Run the agent with full conversation context
                            response = run_async(
                                run_agent(st.session_state.agent, conversation_memory)
                            )

                            tool_output = None
                            # Extract tool executions if available
                            if "messages" in response:
                                for msg in response["messages"]:
                                    # Look for AIMessage with tool calls
                                    if hasattr(msg, "tool_calls") and msg.tool_calls:
                                        for tool_call in msg.tool_calls:
                                            # Find corresponding ToolMessage
                                            tool_output = next(
                                                (
                                                    m.content
                                                    for m in response["messages"]
                                                    if isinstance(m, ToolMessage)
                                                    and hasattr(m, "tool_call_id")
                                                    and m.tool_call_id
                                                    == tool_call["id"]
                                                ),
                                                None,
                                            )
                                            if tool_output:
                                                st.session_state.tool_executions.append(
                                                    {
                                                        "tool_name": tool_call["name"],
                                                        "input": tool_call["args"],
                                                        "output": tool_output,
                                                        "timestamp": datetime.datetime.now().strftime(
                                                            "%Y-%m-%d %H:%M:%S"
                                                        ),
                                                        "user": st.session_state.get(
                                                            "username", "Unknown"
                                                        ),
                                                    }
                                                )

                            # Extract and display the response
                            output = ""
                            tool_count = 0
                            assistant_response = None

                            if "messages" in response:
                                # Handle case where response contains error message
                                if len(response["messages"]) == 1 and isinstance(
                                    response["messages"][0], dict
                                ):
                                    # This is likely our custom error response
                                    assistant_response = response["messages"][0].get(
                                        "content", ""
                                    )
                                    with messages_container.chat_message("assistant"):
                                        st.markdown(assistant_response)
                                else:
                                    # Skip messages that were part of the input conversation
                                    new_messages = response["messages"][
                                        len(conversation_memory) :
                                    ]

                                    for msg in new_messages:
                                        if isinstance(msg, HumanMessage):
                                            continue  # Skip human messages
                                        elif isinstance(msg, ToolMessage):
                                            tool_count += 1
                                            with messages_container.chat_message(
                                                "assistant"
                                            ):
                                                tool_message = (
                                                    f"**ToolMessage - {tool_count} ({getattr(msg, 'name', 'Unknown')}):** \n"
                                                    + str(msg.content)
                                                )
                                                st.code(tool_message, language="yaml")
                                                # Store tool message separately - don't include in main conversation flow
                                                _append_message_to_session(
                                                    {
                                                        "role": "assistant",
                                                        "tool": tool_message,
                                                    }
                                                )
                                        elif isinstance(msg, AIMessage):
                                            if hasattr(msg, "content") and msg.content:
                                                assistant_response = str(msg.content)
                                                output = assistant_response
                                                with messages_container.chat_message(
                                                    "assistant"
                                                ):
                                                    st.markdown(output)

                            # Only add the final AI response to conversation memory
                            if assistant_response:
                                response_dct = {
                                    "role": "assistant",
                                    "content": assistant_response,
                                }
                                _append_message_to_session(response_dct)

                        except Exception as agent_error:
                            # Handle agent-specific errors
                            error_message = (
                                f"⚠️ Agent execution error: {str(agent_error)}"
                            )
                            if "recursion limit" in str(agent_error).lower():
                                error_message = """⚠️ The agent encountered a complex task that couldn't be completed in the available steps. 

**Possible solutions:**
1. **Break down your request** into smaller, more specific questions
2. **Be more specific** about what you want to achieve
3. **Check MCP server connections** - try disconnecting and reconnecting in the Connections tab
4. **Simplify the query** - avoid very complex multi-step requests

**What happened:** The agent tried too many steps without reaching a conclusion, which usually means it got stuck in a loop or encountered tool execution issues."""

                            with messages_container.chat_message("assistant"):
                                st.markdown(error_message)
                            _append_message_to_session(
                                {"role": "assistant", "content": error_message}
                            )

                    # Fall back to regular stream response if agent not available
                    else:
                        available_servers = list(
                            st.session_state.get("servers", {}).keys()
                        )
                        if available_servers:
                            server_list = ", ".join(available_servers)
                            st.warning(
                                f"⚠️ You are not connected to the MCP servers ({server_list})! Please connect in the Connections tab."
                            )
                        else:
                            st.warning(
                                "⚠️ No MCP servers configured! Please check your configuration."
                            )

                        response_stream = get_response_stream(
                            main_prompt,
                            llm_provider=st.session_state["params"]["model_id"],
                            system=system_prompt,
                            temperature=st.session_state["params"].get(
                                "temperature", DEFAULT_TEMPERATURE
                            ),
                            max_tokens=st.session_state["params"].get(
                                "max_tokens", DEFAULT_MAX_TOKENS
                            ),
                        )
                        with messages_container.chat_message("assistant"):
                            response = st.write_stream(response_stream)
                            response_dct = {
                                "role": "assistant",
                                "content": response,
                            }
                            _append_message_to_session(response_dct)

                except Exception as e:
                    response = f"⚠️ Something went wrong: {str(e)}"
                    st.error(response)
                    st.code(traceback.format_exc(), language="python")
                    _append_message_to_session(
                        {"role": "assistant", "content": response}
                    )
                    st.stop()

    # Display tool executions in the chat tab
    display_tool_executions()

# Configuration Tab
with tab2:
    create_configuration_tab()

# Connections Tab
with tab3:
    create_connection_tab()

# Tools Tab
with tab4:
    create_tools_tab()

# Footer
st.markdown("---")
user_info = f"👤 {st.session_state.get('name', 'User')}"
st.markdown(
    f"""
    <div style='text-align: center; color: #666; font-size: 0.8em;'>
    🤖 AI & MCP Tools Interface | {user_info} | PPF Europe Analysis Platform
    </div>
    """,
    unsafe_allow_html=True,
)
