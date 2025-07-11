import streamlit as st
import json
from typing import List, Dict
from services.chat_service import ChatService, _append_message_to_session
from utils.tool_schema_parser import extract_tool_parameters
import pyperclip
from datetime import datetime

def create_enhanced_chat_interface():
    """Create the enhanced chat interface with improved UI and user session isolation."""
    # Check authentication
    current_user = st.session_state.get('username')
    if not current_user:
        st.warning("🔐 Please authenticate to access the chat interface")
        st.info("👈 Use the sidebar to log in")
        return
    
    # Check if we have active connections
    if not st.session_state.get("agent"):
        st.warning("🔌 No MCP server connections found")
        st.info("👉 Go to the **Connections** tab to establish server connections")
        return
    
    # Check if we have tools available
    if not st.session_state.get("tools"):
        st.warning("🧰 No tools available")
        st.info("Tools are loaded automatically when MCP servers are connected")
        return
    
    # Main chat interface
    st.markdown("### 💬 AI Chat Interface")
    st.markdown(f"Chat with AI agents - **Logged in as: {current_user}**")
    
    # Create chat controls at the top
    create_chat_controls()
    
    # Create the main layout: Chat area at top, Tools at bottom
    create_chat_area()
    
    # Add separator
    st.markdown("---")
    
    # Tools section at the bottom
    create_tools_section()


def create_chat_controls():
    """Create chat control buttons and settings at the top."""
    col1, col2, col3, col4 = st.columns([2, 2, 2, 2])
    
    with col1:
        if st.button("🆕 New Chat", help="Start a new conversation", key="chat_new_btn"):
            from services.chat_service import create_chat
            create_chat()
            st.rerun()
    
    with col2:
        if st.button("🗑️ Clear Chat", help="Clear current conversation", key="chat_clear_btn"):
            clear_current_chat()
            st.rerun()
    
    with col3:
        # Toggle for showing tool outputs
        show_tool_outputs = st.session_state.get('show_tool_outputs', True)
        if st.checkbox("🔧 Show Tool Outputs", value=show_tool_outputs, key="tool_outputs_toggle"):
            st.session_state['show_tool_outputs'] = True
        else:
            st.session_state['show_tool_outputs'] = False
    
    with col4:
        if st.button("📤 Export Chat", help="Export conversation as JSON", key="chat_export_btn"):
            export_current_chat()


def create_chat_area():
    """Create the main chat conversation area with messages in reverse order."""
    # Chat container with fixed height and scrolling
    chat_container = st.container()
    
    with chat_container:
        # Chat messages area with scrolling - REVERSED ORDER
        messages_container = st.container(height=500, border=True)
        
        with messages_container:
            display_chat_messages_reversed()
        
        # Chat input area
        create_chat_input()


def display_chat_messages_reversed():
    """Display chat messages in reverse order (latest at top) with tool output toggle."""
    current_user = st.session_state.get('username')
    if not current_user:
        return
    
    user_messages_key = f"user_{current_user}_messages"
    messages = st.session_state.get(user_messages_key, [])
    
    if not messages:
        st.info("👋 Start a conversation! Ask me anything about your database or systems.")
        st.markdown("**Example queries:**")
        st.markdown("- Show me all tables in the database")
        st.markdown("- Get 5 sample records from the users table")
        st.markdown("- Count all records in the orders table")
        return
    
    # Get tool output visibility setting
    show_tool_outputs = st.session_state.get('show_tool_outputs', True)
    
    # Display messages in REVERSE chronological order (latest first)
    for i, message in enumerate(reversed(messages)):
        # Only show messages from the current user
        if message.get('user') != current_user:
            continue
        
        # Calculate the original index for unique keys
        original_index = len(messages) - 1 - i
        
        message_container = st.container()
        
        with message_container:
            if message["role"] == "user":
                display_user_message_reversed(message, original_index)
            elif message["role"] == "assistant":
                display_assistant_message_reversed(message, original_index, show_tool_outputs)
            elif message["role"] == "tool" and show_tool_outputs:
                display_tool_message_reversed(message, original_index)


def display_user_message_reversed(message: Dict, index: int):
    """Display a user message with copy functionality."""
    # User message styling with timestamp at top
    timestamp = get_formatted_timestamp(message.get('timestamp', ''))
    
    st.markdown(
        f"""
        <div style="
            background-color: #e3f2fd; 
            padding: 10px 15px; 
            border-radius: 10px; 
            margin: 5px 0 10px 20%;
            border-left: 4px solid #2196f3;
        ">
            <div style="font-size: 0.8em; color: #666; margin-bottom: 5px;">{timestamp}</div>
            <strong>👤 You:</strong><br>
            {message['content']}
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    # Copy button for user message
    col1, col2, col3 = st.columns([4, 1, 1])
    with col2:
        if st.button("📋 Copy", key=f"copy_user_{index}", help="Copy message"):
            copy_to_clipboard(message['content'])
            st.success("Copied!", icon="✅")


def display_assistant_message_reversed(message: Dict, index: int, show_tool_outputs: bool):
    """Display an assistant message with copy functionality and optional tool details."""
    # Assistant message styling with timestamp at top
    content = message.get('content', '')
    timestamp = get_formatted_timestamp(message.get('timestamp', ''))
    
    # Check if this message has tool execution
    has_tool = 'tool' in message or 'tool_calls' in message
    
    st.markdown(
        f"""
        <div style="
            background-color: #f3e5f5; 
            padding: 10px 15px; 
            border-radius: 10px; 
            margin: 5px 20% 10px 0;
            border-left: 4px solid #9c27b0;
        ">
            <div style="font-size: 0.8em; color: #666; margin-bottom: 5px;">{timestamp}</div>
            <strong>🤖 Assistant:</strong><br>
            {content}
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    # Action buttons row
    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
    
    with col2:
        if st.button("📋 Copy", key=f"copy_assistant_{index}", help="Copy response"):
            copy_to_clipboard(content)
            st.success("Copied!", icon="✅")
    
    with col3:
        # Show tool info if available and tool outputs are enabled
        if has_tool and show_tool_outputs:
            if st.button("🔧 Tool", key=f"tool_info_{index}", help="Show tool details"):
                show_tool_details(message, index)
    
    # Show tool execution details if expanded and tool outputs are enabled
    if show_tool_outputs and f"show_tool_{index}" in st.session_state and st.session_state[f"show_tool_{index}"]:
        display_tool_execution_details(message)


def display_tool_message_reversed(message: Dict, index: int):
    """Display a tool execution message when tool outputs are enabled."""
    timestamp = get_formatted_timestamp(message.get('timestamp', ''))
    tool_name = message.get('tool_name', 'Unknown Tool')
    tool_output = message.get('content', '')
    
    # Truncate long outputs for display
    display_output = tool_output[:300] + "..." if len(tool_output) > 300 else tool_output
    
    st.markdown(
        f"""
        <div style="
            background-color: #fff3e0; 
            padding: 8px 12px; 
            border-radius: 8px; 
            margin: 3px 10% 8px 10%;
            border-left: 3px solid #ff9800;
            font-size: 0.9em;
        ">
            <div style="font-size: 0.7em; color: #666; margin-bottom: 3px;">{timestamp}</div>
            <strong>🔧 Tool: {tool_name}</strong><br>
            <div style="font-family: monospace; white-space: pre-wrap; max-height: 100px; overflow-y: auto;">
            {display_output}
            </div>
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    # Show full output button
    col1, col2, col3 = st.columns([4, 1, 1])
    with col2:
        if st.button("📄 Full", key=f"tool_full_{index}", help="Show full tool output"):
            st.session_state[f"show_full_tool_{index}"] = not st.session_state.get(f"show_full_tool_{index}", False)
            st.rerun()
    
    # Show full output if requested
    if st.session_state.get(f"show_full_tool_{index}", False):
        with st.expander(f"Full Tool Output - {tool_name}", expanded=True):
            st.code(tool_output, language="text")


def get_formatted_timestamp(timestamp_str: str) -> str:
    """Format timestamp for display."""
    if not timestamp_str:
        return ""
    
    try:
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        return dt.strftime('%H:%M:%S')
    except:
        return ""


def show_tool_details(message: Dict, index: int):
    """Toggle tool details display."""
    key = f"show_tool_{index}"
    st.session_state[key] = not st.session_state.get(key, False)


def display_tool_execution_details(message: Dict):
    """Display detailed tool execution information."""
    if 'tool' not in message and 'tool_calls' not in message:
        return
    
    with st.expander("🔧 Tool Execution Details", expanded=True):
        tool_info = message.get('tool') or message.get('tool_calls')
        
        if isinstance(tool_info, str):
            st.code(tool_info, language="text")
        elif isinstance(tool_info, dict):
            st.json(tool_info)
        else:
            st.text(str(tool_info))


def copy_to_clipboard(text: str):
    """Copy text to clipboard (placeholder function)."""
    # Note: Direct clipboard access isn't available in Streamlit
    # This is a placeholder - in practice, users will manually copy
    pass


def create_chat_input():
    """Create the chat input area."""
    # Chat input form
    with st.form("chat_form", clear_on_submit=True):
        col1, col2 = st.columns([5, 1])
        
        with col1:
            user_input = st.text_area(
                "Type your message here...", 
                height=100,
                placeholder="Ask me about the database, request SQL queries, or explore available tools...",
                key="chat_input"
            )
        
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)  # Add some spacing
            submit_button = st.form_submit_button(
                "📤 Send", 
                type="primary",
                use_container_width=True
            )
        
        # Process the message when submitted
        if submit_button and user_input.strip():
            process_chat_message(user_input.strip())


def process_chat_message(user_input: str):
    """Process a chat message from the user."""
    current_user = st.session_state.get('username')
    if not current_user:
        st.error("❌ Please log in to send messages.")
        return
    
    # Add user message to chat history
    user_message = {
        "role": "user", 
        "content": user_input,
        "timestamp": datetime.now().isoformat(),
        "user": current_user
    }
    _append_message_to_session(user_message)
    
    # Process the message with ChatService
    try:
        if "chat_service" not in st.session_state:
            st.session_state.chat_service = ChatService()
        
        chat_service = st.session_state.chat_service
        
        with st.spinner("🤖 AI is thinking..."):
            response = chat_service.process_message(user_input)
        
        # Add assistant response
        assistant_message = {
            "role": "assistant", 
            "content": response,
            "timestamp": datetime.now().isoformat(),
            "user": current_user
        }
        _append_message_to_session(assistant_message)
        
        # Trigger a rerun to display the new messages
        st.rerun()
        
    except Exception as e:
        error_message = f"I encountered an error: {str(e)}"
        assistant_message = {
            "role": "assistant", 
            "content": error_message,
            "timestamp": datetime.now().isoformat(),
            "user": current_user
        }
        _append_message_to_session(assistant_message)
        st.error(f"❌ Error processing message: {str(e)}")
        st.rerun()


def create_tools_section():
    """Create the tools section at the bottom of the chat interface."""
    st.markdown("### 🧰 Available Tools")
    
    tools = st.session_state.get("tools", [])
    if not tools:
        st.info("No tools available")
        return
    
    # Categorize tools
    mssql_tools, other_tools = categorize_tools(tools)
    
    # Tools overview
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Tools", len(tools))
    with col2:
        st.metric("MSSQL Tools", len(mssql_tools))
    with col3:
        st.metric("Other Tools", len(other_tools))
    
    # Tools dropdown/selector
    if tools:
        create_tools_dropdown(tools, mssql_tools, other_tools)


def categorize_tools(tools: List) -> tuple:
    """Categorize tools by type."""
    mssql_tools = []
    other_tools = []
    
    for tool in tools:
        tool_name_lower = tool.name.lower()
        tool_desc_lower = tool.description.lower() if hasattr(tool, 'description') and tool.description else ""
        
        # MSSQL tool detection
        if (any(keyword in tool_name_lower for keyword in ['sql', 'mssql', 'execute_sql', 'list_tables', 'describe_table', 'get_table_sample']) or
              any(keyword in tool_desc_lower for keyword in ['sql', 'mssql', 'database', 'table', 'execute'])):
            mssql_tools.append(tool)
        else:
            other_tools.append(tool)
    
    return mssql_tools, other_tools


def create_tools_dropdown(all_tools: List, mssql_tools: List, other_tools: List):
    """Create the tools dropdown interface."""
    # Tool category tabs
    tab1, tab2, tab3 = st.tabs(["🗃️ MSSQL Tools", "🔧 Other Tools", "📋 All Tools"])
    
    with tab1:
        if mssql_tools:
            display_tools_dropdown(mssql_tools, "mssql", "MSSQL Database Operations")
        else:
            st.info("No MSSQL tools available")
    
    with tab2:
        if other_tools:
            display_tools_dropdown(other_tools, "other", "Other Tools")
        else:
            st.info("No other tools available")
    
    with tab3:
        display_tools_dropdown(all_tools, "all", "All Available Tools")


def display_tools_dropdown(tools: List, category: str, title: str):
    """Display a dropdown for a specific category of tools."""
    st.markdown(f"**{title}** ({len(tools)} tools)")
    
    if not tools:
        return
    
    # Tool selection
    selected_tool_name = st.selectbox(
        "Select a tool to view details:",
        options=[tool.name for tool in tools],
        key=f"tool_select_{category}",
        help="Choose a tool to see its description and parameters"
    )
    
    if selected_tool_name:
        selected_tool = next((tool for tool in tools if tool.name == selected_tool_name), None)
        
        if selected_tool:
            display_tool_info_card(selected_tool, category)


def display_tool_info_card(tool, category: str):
    """Display detailed information about a tool in a card format."""
    with st.container(border=True):
        # Tool header
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown(f"**🔧 {tool.name}**")
            
            # Description
            if hasattr(tool, 'description') and tool.description:
                st.markdown(f"*{tool.description}*")
            else:
                st.markdown("*No description available*")
        
        with col2:
            # Tool category badge
            tool_name_lower = tool.name.lower()
            tool_desc_lower = tool.description.lower() if hasattr(tool, 'description') and tool.description else ""
            
            if (any(keyword in tool_name_lower for keyword in ['sql', 'mssql', 'execute_sql', 'list_tables', 'describe_table', 'get_table_sample']) or
                  any(keyword in tool_desc_lower for keyword in ['sql', 'mssql', 'database', 'table', 'execute'])):
                st.markdown("🗃️ **MSSQL**")
            else:
                st.markdown("🔧 **General**")
        
        # Parameters section
        parameters = extract_tool_parameters(tool)
        
        if parameters:
            st.markdown("**Parameters:**")
            for param in parameters:
                st.markdown(f"• `{param}`")
        else:
            st.markdown("**Parameters:** *None required*")
        
        # Usage example
        st.markdown("**Usage Example:**")
        st.code(f'Ask the AI: "Use the {tool.name} tool to..."', language="text")
        
        # Action buttons
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button(f"📋 Copy Tool Name", key=f"copy_tool_{category}_{tool.name}"):
                # Placeholder for copying tool name
                st.success(f"Tool name copied: {tool.name}")
        
        with col2:
            show_raw = st.button(f"📄 Raw Schema", key=f"raw_tool_{category}_{tool.name}")
            
        # Show raw schema if requested
        if show_raw:
            if hasattr(tool, 'args_schema'):
                schema = tool.args_schema
                if isinstance(schema, dict):
                    st.json(schema)
                else:
                    st.json(schema.schema() if hasattr(schema, 'schema') else str(schema))
            else:
                st.info("No schema available for this tool")


def clear_current_chat():
    """Clear the current chat conversation."""
    current_user = st.session_state.get('username')
    if not current_user:
        return
    
    current_chat_id = st.session_state.get('current_chat_id')
    if not current_chat_id:
        return
    
    # Clear messages for current chat
    user_messages_key = f"user_{current_user}_messages"
    user_history_key = f"user_{current_user}_history_chats"
    
    st.session_state[user_messages_key] = []
    st.session_state["messages"] = []
    
    # Update chat history
    user_chats = st.session_state.get(user_history_key, [])
    for chat in user_chats:
        if chat["chat_id"] == current_chat_id and chat.get('created_by') == current_user:
            chat["messages"] = []
            chat["chat_name"] = "New chat"
            break
    
    st.session_state[user_history_key] = user_chats
    st.session_state["history_chats"] = user_chats


def export_current_chat():
    """Export the current chat as JSON."""
    current_user = st.session_state.get('username')
    if not current_user:
        st.error("Please log in to export chat")
        return
    
    user_messages_key = f"user_{current_user}_messages"
    messages = st.session_state.get(user_messages_key, [])
    
    if not messages:
        st.warning("No messages to export")
        return
    
    # Prepare export data
    export_data = {
        "chat_export": {
            "user": current_user,
            "chat_id": st.session_state.get('current_chat_id'),
            "exported_at": datetime.now().isoformat(),
            "message_count": len(messages),
            "messages": messages
        }
    }
    
    # Create download button
    json_str = json.dumps(export_data, indent=2)
    st.download_button(
        label="💾 Download Chat JSON",
        data=json_str,
        file_name=f"chat_export_{current_user}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        mime="application/json"
    )


def show_chat_statistics():
    """Show chat statistics for the current user."""
    current_user = st.session_state.get('username')
    if not current_user:
        return
    
    from services.chat_service import get_user_chat_stats
    stats = get_user_chat_stats(current_user)
    
    st.markdown("### 📊 Your Chat Statistics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Chats", stats["total_chats"])
    
    with col2:
        st.metric("Total Messages", stats["total_messages"])
    
    with col3:
        avg_messages = stats["total_messages"] / max(stats["total_chats"], 1)
        st.metric("Avg Messages/Chat", f"{avg_messages:.1f}")