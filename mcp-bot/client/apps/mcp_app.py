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


def check_authentication():
    """Check if user is authenticated and redirect if not."""
    if not st.session_state.get("authentication_status"):
        st.error(
            "🔐 Authentication required. Please log in to access this application."
        )
        st.stop()


def main():
    """Main application function with authentication check."""
    # Check authentication before proceeding
    check_authentication()

    # Initialize the title
    st.title("🔍 Google Search MCP Client - Chat Interface")

    # Add user welcome message
    if st.session_state.get("name"):
        st.success(f"Welcome back, **{st.session_state['name']}**! 👋")

    # Create the main tabs
    tab1, tab2, tab3, tab4 = st.tabs(
        ["💬 Chat", "⚙️ Configuration", "🔌 Connections", "🧰 Tools"]
    )

    # Sidebar with remaining components (CSM logo already added in app.py)
    with st.sidebar:
        # Add other sidebar components (logo is already at top from app.py)
        sd_components.create_user_info_sidebar()
        sd_components.create_history_chat_container()
        sd_components.create_sidebar_chat_buttons()

    # Chat Tab - Main conversation interface
    with tab1:
        # Check authentication again for this tab
        if not st.session_state.get("authentication_status"):
            st.warning("🔐 Please authenticate to access the chat interface.")
            return

        # Main chat interface
        st.header("💬 Chat with Google Search Agent")

        # Show available search engine status
        google_tools = [
            tool
            for tool in st.session_state.get("tools", [])
            if any(
                keyword in tool.name.lower()
                for keyword in ["google-search", "read-webpage"]
            )
            or ("google" in tool.name.lower())
        ]
        if google_tools:
            st.success(f"🔍 Google Search: {len(google_tools)} tools available")
        else:
            st.warning("🔍 Google Search: Not connected")

        st.markdown(
            "Ask questions to search the web using Google Search tools for comprehensive research and analysis."
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
        user_text = st.chat_input("Ask a question or search the web")

        # Handle chat logic
        if user_text is not None:  # something submitted
            params = st.session_state.get("params")

            # Check if we have proper credentials loaded from environment
            selected_provider = params.get("model_id")
            credentials_valid = False

            if selected_provider == "OpenAI":
                credentials_valid = bool(os.getenv("OPENAI_API_KEY"))
            elif selected_provider == "Azure OpenAI":
                azure_keys = [
                    os.getenv("AZURE_API_KEY"),
                    os.getenv("AZURE_ENDPOINT"),
                    os.getenv("AZURE_DEPLOYMENT"),
                    os.getenv("AZURE_API_VERSION"),
                ]
                credentials_valid = all(azure_keys)

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
                                    run_agent(
                                        st.session_state.agent, conversation_memory
                                    )
                                )

                                tool_output = None
                                # Extract tool executions if available
                                if "messages" in response:
                                    for msg in response["messages"]:
                                        # Look for AIMessage with tool calls
                                        if (
                                            hasattr(msg, "tool_calls")
                                            and msg.tool_calls
                                        ):
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
                                                            "tool_name": tool_call[
                                                                "name"
                                                            ],
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
                                        assistant_response = response["messages"][
                                            0
                                        ].get("content", "")
                                        with messages_container.chat_message(
                                            "assistant"
                                        ):
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
                                                    st.code(
                                                        tool_message, language="yaml"
                                                    )
                                                    # Store tool message separately - don't include in main conversation flow
                                                    _append_message_to_session(
                                                        {
                                                            "role": "assistant",
                                                            "tool": tool_message,
                                                        }
                                                    )
                                            elif isinstance(msg, AIMessage):
                                                if (
                                                    hasattr(msg, "content")
                                                    and msg.content
                                                ):
                                                    assistant_response = str(
                                                        msg.content
                                                    )
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
        check_authentication()  # Additional check for sensitive configurations
        create_configuration_tab()

    # Connections Tab
    with tab3:
        check_authentication()  # Additional check for connections
        create_connection_tab()

    # Tools Tab
    with tab4:
        check_authentication()  # Additional check for tools
        create_tools_tab()
