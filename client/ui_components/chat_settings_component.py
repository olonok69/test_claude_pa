import streamlit as st
from datetime import datetime
from typing import Dict, List

def create_chat_settings_sidebar():
    """Create chat settings in the sidebar with tool output controls."""
    current_user = st.session_state.get('username')
    if not current_user or not st.session_state.get("authentication_status"):
        return
    
    st.markdown("### ⚙️ Chat Settings")
    
    with st.container(border=True):
        # Tool output visibility toggle
        show_tool_outputs = st.session_state.get('show_tool_outputs', True)
        new_show_tool_outputs = st.checkbox(
            "🔧 Show Tool Outputs", 
            value=show_tool_outputs,
            help="Toggle visibility of tool execution messages in chat",
            key="sidebar_tool_outputs_toggle"
        )
        
        if new_show_tool_outputs != show_tool_outputs:
            st.session_state['show_tool_outputs'] = new_show_tool_outputs
            st.rerun()
        
        # Chat display settings
        st.markdown("**Display Options:**")
        
        # Message order preference (future enhancement)
        message_order = st.radio(
            "Message Order",
            ["Latest First", "Oldest First"],
            index=0,  # Default to latest first
            help="Choose how messages are displayed in chat",
            key="message_order_setting"
        )
        
        if message_order != st.session_state.get('message_order', 'Latest First'):
            st.session_state['message_order'] = message_order
            st.info("Message order updated!")
        
        # Auto-scroll setting
        auto_scroll = st.checkbox(
            "📜 Auto-scroll to new messages",
            value=st.session_state.get('auto_scroll_enabled', True),
            help="Automatically scroll to new messages",
            key="auto_scroll_setting"
        )
        st.session_state['auto_scroll_enabled'] = auto_scroll
        
        # Show timestamps
        show_timestamps = st.checkbox(
            "🕒 Show Message Timestamps",
            value=st.session_state.get('show_timestamps', True),
            help="Display timestamps on messages",
            key="timestamps_setting"
        )
        st.session_state['show_timestamps'] = show_timestamps
    
    # Chat statistics
    with st.container(border=True):
        st.markdown("**Chat Statistics:**")
        
        from services.chat_service import get_user_chat_stats, get_messages_by_type
        
        stats = get_user_chat_stats(current_user)
        messages_by_type = get_messages_by_type(current_user)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Total Messages", stats["total_messages"])
            st.metric("User Messages", len(messages_by_type["user"]))
        
        with col2:
            st.metric("Tool Executions", stats["tool_executions"])
            st.metric("AI Responses", len(messages_by_type["assistant"]))
        
        # Current chat stats
        current_chat_messages = st.session_state.get(f"user_{current_user}_messages", [])
        current_chat_tools = len([msg for msg in current_chat_messages if msg.get('role') == 'tool'])
        
        st.markdown("**Current Chat:**")
        st.write(f"Messages: {len(current_chat_messages)}")
        st.write(f"Tool calls: {current_chat_tools}")


def create_advanced_chat_settings():
    """Create advanced chat settings for power users."""
    current_user = st.session_state.get('username')
    if not current_user:
        return
    
    # Advanced settings in expander
    with st.expander("🔧 Advanced Chat Settings", expanded=False):
        
        # Tool output filtering
        st.markdown("**Tool Output Filtering:**")
        
        # Get available tool types
        tools = st.session_state.get("tools", [])
        tool_types = set()
        for tool in tools:
            if hasattr(tool, 'name'):
                if 'sql' in tool.name.lower() or 'mssql' in tool.name.lower():
                    tool_types.add('MSSQL')
                else:
                    tool_types.add('General')
        
        # Tool type filters
        if tool_types:
            st.markdown("**Show outputs from:**")
            
            show_mssql_outputs = st.checkbox(
                "🗃️ MSSQL Tools",
                value=st.session_state.get('show_mssql_outputs', True),
                key="mssql_outputs_filter"
            )
            st.session_state['show_mssql_outputs'] = show_mssql_outputs
            
            show_general_outputs = st.checkbox(
                "🔧 General Tools",
                value=st.session_state.get('show_general_outputs', True),
                key="general_outputs_filter"
            )
            st.session_state['show_general_outputs'] = show_general_outputs
        
        # Message display limits
        st.markdown("**Display Limits:**")
        
        max_message_length = st.slider(
            "Max message display length",
            min_value=100,
            max_value=2000,
            value=st.session_state.get('max_message_length', 500),
            step=100,
            help="Truncate long messages for better readability",
            key="max_message_length_setting"
        )
        st.session_state['max_message_length'] = max_message_length
        
        max_tool_output_length = st.slider(
            "Max tool output display length",
            min_value=50,
            max_value=1000,
            value=st.session_state.get('max_tool_output_length', 300),
            step=50,
            help="Truncate long tool outputs for better readability",
            key="max_tool_output_length_setting"
        )
        st.session_state['max_tool_output_length'] = max_tool_output_length
        
        # Chat export settings
        st.markdown("**Export Settings:**")
        
        include_tool_outputs_in_export = st.checkbox(
            "Include tool outputs in exports",
            value=st.session_state.get('include_tool_outputs_in_export', True),
            help="Whether to include tool execution messages in chat exports",
            key="export_tool_outputs_setting"
        )
        st.session_state['include_tool_outputs_in_export'] = include_tool_outputs_in_export
        
        include_timestamps_in_export = st.checkbox(
            "Include timestamps in exports",
            value=st.session_state.get('include_timestamps_in_export', True),
            help="Whether to include message timestamps in chat exports",
            key="export_timestamps_setting"
        )
        st.session_state['include_timestamps_in_export'] = include_timestamps_in_export


def create_chat_actions_panel():
    """Create a panel with quick chat actions."""
    current_user = st.session_state.get('username')
    if not current_user:
        return
    
    st.markdown("**Quick Actions:**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🧹 Clear Tool Outputs", help="Remove all tool output messages from current chat", key="clear_tools_btn"):
            clear_tool_outputs_from_chat()
            st.success("Tool outputs cleared!")
            st.rerun()
    
    with col2:
        if st.button("📊 Chat Summary", help="Generate a summary of the current chat", key="chat_summary_btn"):
            show_chat_summary()


def clear_tool_outputs_from_chat():
    """Remove all tool output messages from the current chat."""
    current_user = st.session_state.get('username')
    if not current_user:
        return
    
    user_messages_key = f"user_{current_user}_messages"
    user_history_key = f"user_{current_user}_history_chats"
    current_chat_id = st.session_state.get('current_chat_id')
    
    if not current_chat_id:
        return
    
    # Filter out tool messages
    current_messages = st.session_state.get(user_messages_key, [])
    filtered_messages = [msg for msg in current_messages if msg.get('role') != 'tool']
    
    # Update session state
    st.session_state[user_messages_key] = filtered_messages
    st.session_state["messages"] = filtered_messages
    
    # Update chat history
    user_chats = st.session_state.get(user_history_key, [])
    for chat in user_chats:
        if chat["chat_id"] == current_chat_id and chat.get('created_by') == current_user:
            chat["messages"] = filtered_messages
            break
    
    st.session_state[user_history_key] = user_chats
    st.session_state["history_chats"] = user_chats


def show_chat_summary():
    """Display a summary of the current chat."""
    from services.chat_service import get_conversation_summary, get_messages_by_type
    
    current_user = st.session_state.get('username')
    if not current_user:
        return
    
    # Get summary and statistics
    summary = get_conversation_summary(max_messages=20)
    messages_by_type = get_messages_by_type(current_user)
    
    with st.expander("📊 Chat Summary", expanded=True):
        # Summary statistics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("User Messages", len(messages_by_type["user"]))
        
        with col2:
            st.metric("AI Responses", len(messages_by_type["assistant"]))
        
        with col3:
            st.metric("Tool Executions", len(messages_by_type["tool"]))
        
        # Conversation summary
        st.markdown("**Recent Conversation Summary:**")
        st.text_area(
            "Summary",
            value=summary,
            height=200,
            disabled=True,
            label_visibility="collapsed"
        )
        
        # Most used tools
        if messages_by_type["tool"]:
            tool_usage = {}
            for tool_msg in messages_by_type["tool"]:
                tool_name = tool_msg.get('tool_name', 'Unknown')
                tool_usage[tool_name] = tool_usage.get(tool_name, 0) + 1
            
            st.markdown("**Most Used Tools:**")
            for tool_name, count in sorted(tool_usage.items(), key=lambda x: x[1], reverse=True)[:5]:
                st.write(f"• {tool_name}: {count} times")


def should_show_tool_message(message: Dict) -> bool:
    """Determine if a tool message should be displayed based on current settings."""
    # Check global tool output setting
    if not st.session_state.get('show_tool_outputs', True):
        return False
    
    tool_name = message.get('tool_name', '').lower()
    
    # Check specific tool type filters
    if 'sql' in tool_name or 'mssql' in tool_name:
        return st.session_state.get('show_mssql_outputs', True)
    else:
        return st.session_state.get('show_general_outputs', True)


def get_truncated_content(content: str, message_type: str = 'message') -> str:
    """Get truncated content based on settings."""
    if message_type == 'tool':
        max_length = st.session_state.get('max_tool_output_length', 300)
    else:
        max_length = st.session_state.get('max_message_length', 500)
    
    if len(content) <= max_length:
        return content
    
    return content[:max_length] + "..."


def export_chat_with_settings():
    """Export chat with current settings applied."""
    current_user = st.session_state.get('username')
    if not current_user:
        return
    
    user_messages_key = f"user_{current_user}_messages"
    messages = st.session_state.get(user_messages_key, [])
    
    if not messages:
        st.warning("No messages to export")
        return
    
    # Apply export settings
    include_tools = st.session_state.get('include_tool_outputs_in_export', True)
    include_timestamps = st.session_state.get('include_timestamps_in_export', True)
    
    # Filter messages based on settings
    filtered_messages = []
    for msg in messages:
        # Skip tool messages if not included
        if msg.get('role') == 'tool' and not include_tools:
            continue
        
        # Create export message
        export_msg = msg.copy()
        
        # Remove timestamps if not included
        if not include_timestamps and 'timestamp' in export_msg:
            del export_msg['timestamp']
        
        filtered_messages.append(export_msg)
    
    # Prepare export data
    export_data = {
        "chat_export": {
            "user": current_user,
            "chat_id": st.session_state.get('current_chat_id'),
            "exported_at": datetime.now().isoformat(),
            "settings": {
                "include_tool_outputs": include_tools,
                "include_timestamps": include_timestamps,
                "show_tool_outputs": st.session_state.get('show_tool_outputs', True)
            },
            "message_count": len(filtered_messages),
            "messages": filtered_messages
        }
    }
    
    # Create download button
    import json
    json_str = json.dumps(export_data, indent=2)
    st.download_button(
        label="💾 Download Filtered Chat",
        data=json_str,
        file_name=f"chat_export_filtered_{current_user}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        mime="application/json"
    )