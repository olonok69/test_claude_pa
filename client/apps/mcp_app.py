import os
import datetime
import streamlit as st
from langchain_core.messages import HumanMessage, ToolMessage, AIMessage
from services.ai_service import get_response_stream
from services.mcp_service import run_agent
from services.chat_service import get_current_chat, _append_message_to_session, get_clean_conversation_memory
from utils.async_helpers import run_async
from utils.ai_prompts import make_system_prompt, make_main_prompt
import ui_components.sidebar_components as sd_compents
from  ui_components.main_components import display_tool_executions
from config import DEFAULT_MAX_TOKENS, DEFAULT_TEMPERATURE
import traceback


def main():
    with st.sidebar:
        st.subheader("Chat History")
    sd_compents.create_history_chat_container()

# ------------------------------------------------------------------ Chat Part
    # Main chat interface
    st.header("Chat with AI Agent")
    
    # Show server connection status
    if st.session_state.get("agent"):
        server_count = len(st.session_state.servers)
        tool_count = len(st.session_state.tools)
        st.success(f"✅ Connected to {server_count} MCP servers with {tool_count} tools available")
        
        # Show which servers are connected
        connected_servers = list(st.session_state.servers.keys())
        st.info(f"📡 Active servers: {', '.join(connected_servers)}")
    else:
        st.warning("⚠️ Not connected to MCP servers. Click 'Connect to MCP Servers' in the sidebar to enable tools.")
    
    messages_container = st.container(border=True, height=600)
    
# ------------------------------------------------------------------ Chat history
     # Re-render previous messages
    if st.session_state.get('current_chat_id'):
        st.session_state["messages"] = get_current_chat(st.session_state['current_chat_id'])
        for m in st.session_state["messages"]:
            with messages_container.chat_message(m["role"]):
                if "tool" in m and m["tool"]:
                    st.code(m["tool"], language='yaml')
                if "content" in m and m["content"]:
                    st.markdown(m["content"])

# ------------------------------------------------------------------ Chat input
    user_text = st.chat_input("Ask about finance, databases, CRM, or explore available tools")

# ------------------------------------------------------------------ SideBar widgets
    # Main sidebar widgets
    sd_compents.create_sidebar_chat_buttons()
    sd_compents.create_provider_select_widget()
    sd_compents.create_advanced_configuration_widget()
    sd_compents.create_mcp_connection_widget()
    sd_compents.create_mcp_tools_widget()

# ------------------------------------------------------------------ Main Logic
    if user_text is None:  # nothing submitted yet
        st.stop()
    
    params = st.session_state.get('params')
    
    # Check if we have proper credentials loaded from environment
    selected_provider = params.get('model_id')
    credentials_valid = False
    
    if selected_provider == "OpenAI":
        credentials_valid = bool(os.getenv("OPENAI_API_KEY"))
    elif selected_provider == "Azure OpenAI":
        azure_keys = [
            os.getenv("AZURE_API_KEY"),
            os.getenv("AZURE_ENDPOINT"),
            os.getenv("AZURE_DEPLOYMENT"),
            os.getenv("AZURE_API_VERSION")
        ]
        credentials_valid = all(azure_keys)
    
    if not credentials_valid:
        err_mesg = f"❌ Missing credentials for {selected_provider}. Please check your .env file."
        _append_message_to_session({"role": "assistant", "content": err_mesg})
        with messages_container.chat_message("assistant"):
            st.markdown(err_mesg)
        st.rerun()

# ------------------------------------------------------------------ handle question (if any text)
    if user_text:
        user_text_dct = {"role": "user", "content": user_text}
        _append_message_to_session(user_text_dct)
        with messages_container.chat_message("user"):
            st.markdown(user_text)

        with st.spinner("Thinking…", show_time=True):
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
                        response = run_async(run_agent(st.session_state.agent, conversation_memory))
                        
                        tool_output = None
                        # Extract tool executions if available
                        if "messages" in response:
                            for msg in response["messages"]:
                                # Look for AIMessage with tool calls
                                if hasattr(msg, 'tool_calls') and msg.tool_calls:
                                    for tool_call in msg.tool_calls:
                                        # Find corresponding ToolMessage
                                        tool_output = next(
                                            (m.content for m in response["messages"] 
                                                if isinstance(m, ToolMessage) and 
                                                hasattr(m, 'tool_call_id') and
                                                m.tool_call_id == tool_call['id']),
                                            None
                                        )
                                        if tool_output:
                                            st.session_state.tool_executions.append({
                                                "tool_name": tool_call['name'],
                                                "input": tool_call['args'],
                                                "output": tool_output,
                                                "timestamp": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                            })
                        
                        # Extract and display the response
                        output = ""
                        tool_count = 0
                        assistant_response = None
                        
                        if "messages" in response:
                            # Handle case where response contains error message
                            if len(response["messages"]) == 1 and isinstance(response["messages"][0], dict):
                                # This is likely our custom error response
                                assistant_response = response["messages"][0].get("content", "")
                                with messages_container.chat_message("assistant"):
                                    st.markdown(assistant_response)
                            else:
                                # Skip messages that were part of the input conversation
                                new_messages = response["messages"][len(conversation_memory):]
                                
                                for msg in new_messages:
                                    if isinstance(msg, HumanMessage):
                                        continue  # Skip human messages
                                    elif isinstance(msg, ToolMessage):
                                        tool_count += 1
                                        with messages_container.chat_message("assistant"):
                                            tool_message = f"**ToolMessage - {tool_count} ({getattr(msg, 'name', 'Unknown')}):** \n" + str(msg.content)
                                            st.code(tool_message, language='yaml')
                                            # Store tool message separately - don't include in main conversation flow
                                            _append_message_to_session({'role': 'assistant', 'tool': tool_message})
                                    elif isinstance(msg, AIMessage):
                                        if hasattr(msg, "content") and msg.content:
                                            assistant_response = str(msg.content)
                                            output = assistant_response
                                            with messages_container.chat_message("assistant"):
                                                st.markdown(output)
                        
                        # Only add the final AI response to conversation memory
                        if assistant_response:
                            response_dct = {"role": "assistant", "content": assistant_response}
                            _append_message_to_session(response_dct)
                            
                    except Exception as agent_error:
                        # Handle agent-specific errors
                        error_message = f"⚠️ Agent execution error: {str(agent_error)}"
                        if "recursion limit" in str(agent_error).lower():
                            error_message = """⚠️ The agent encountered a complex task that couldn't be completed in the available steps. 

**Possible solutions:**
1. **Break down your request** into smaller, more specific questions
2. **Be more specific** about what you want to achieve
3. **Check MCP server connections** - try disconnecting and reconnecting
4. **Simplify the query** - avoid very complex multi-step requests

**What happened:** The agent tried too many steps without reaching a conclusion, which usually means it got stuck in a loop or encountered tool execution issues."""
                        
                        with messages_container.chat_message("assistant"):
                            st.markdown(error_message)
                        _append_message_to_session({"role": "assistant", "content": error_message})
                        
                # Fall back to regular stream response if agent not available
                else:
                    st.warning("You are not connected to MCP servers!")
                    response_stream = get_response_stream(
                        main_prompt,
                        llm_provider=st.session_state['params']['model_id'],
                        system=system_prompt,
                        temperature=st.session_state['params'].get('temperature', DEFAULT_TEMPERATURE),
                        max_tokens=st.session_state['params'].get('max_tokens', DEFAULT_MAX_TOKENS), 
                    )         
                    with messages_container.chat_message("assistant"):
                        response = st.write_stream(response_stream)
                        response_dct = {"role": "assistant", "content": response}
                        _append_message_to_session(response_dct)
                        
            except Exception as e:
                response = f"⚠️ Something went wrong: {str(e)}"
                st.error(response)
                st.code(traceback.format_exc(), language="python")
                _append_message_to_session({"role": "assistant", "content": response})
                st.stop()
            
    display_tool_executions()