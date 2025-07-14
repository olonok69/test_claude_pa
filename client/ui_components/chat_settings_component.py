# Enhanced ui_components/chat_settings_component.py with processing time settings

import streamlit as st
from datetime import datetime
from typing import Dict, List

def create_chat_settings_sidebar():
    """Create chat settings in the sidebar with tool output controls and processing time settings."""
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
        
        # Processing time visibility toggle
        show_processing_times = st.session_state.get('show_processing_times', True)
        new_show_processing_times = st.checkbox(
            "⏱️ Show Processing Times", 
            value=show_processing_times,
            help="Display how long each response took to generate",
            key="sidebar_processing_times_toggle"
        )
        
        if new_show_processing_times != show_processing_times:
            st.session_state['show_processing_times'] = new_show_processing_times
            st.rerun()
        
        # Chat display settings
        st.markdown("**Display Options:**")
        
        # Message order preference
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
    
    # Processing Time Settings Section
    with st.container(border=True):
        st.markdown("**⏱️ Processing Time Settings:**")
        
        # Color coding for processing times
        color_processing_times = st.checkbox(
            "🎨 Color-code processing times",
            value=st.session_state.get('color_processing_times', True),
            help="Green for fast, Orange for medium, Red for slow responses",
            key="color_processing_times_setting"
        )
        st.session_state['color_processing_times'] = color_processing_times
        
        # Completion notifications
        show_completion_notifications = st.checkbox(
            "🔔 Show completion notifications",
            value=st.session_state.get('show_completion_notifications', True),
            help="Show success/info/warning messages after each response",
            key="completion_notifications_setting"
        )
        st.session_state['show_completion_notifications'] = show_completion_notifications
        
        # Performance thresholds
        st.markdown("**Performance Thresholds:**")
        
        fast_threshold = st.slider(
            "Fast (Green) < X seconds",
            min_value=0.5,
            max_value=5.0,
            value=st.session_state.get('fast_threshold', 2.0),
            step=0.1,
            help="Responses faster than this are colored green",
            key="fast_threshold_setting"
        )
        st.session_state['fast_threshold'] = fast_threshold
        
        slow_threshold = st.slider(
            "Slow (Red) > X seconds",
            min_value=2.0,
            max_value=15.0,
            value=st.session_state.get('slow_threshold', 5.0),
            step=0.5,
            help="Responses slower than this are colored red",
            key="slow_threshold_setting"
        )
        st.session_state['slow_threshold'] = slow_threshold
    
    # Chat statistics with processing time analytics
    with st.container(border=True):
        st.markdown("**📊 Chat Statistics:**")
        
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
        
        # Processing time analytics
        current_chat_messages = st.session_state.get(f"user_{current_user}_messages", [])
        processing_times = [msg.get('processing_time') for msg in current_chat_messages if msg.get('processing_time')]
        
        if processing_times:
            st.markdown("**⏱️ Performance Analytics:**")
            
            avg_time = sum(processing_times) / len(processing_times)
            min_time = min(processing_times)
            max_time = max(processing_times)
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Avg Response", f"{avg_time:.2f}s")
                st.metric("Fastest", f"{min_time:.2f}s")
            with col2:
                st.metric("Slowest", f"{max_time:.2f}s")
                st.metric("Total Time", f"{sum(processing_times):.1f}s")
            
            # Performance distribution
            fast_count = sum(1 for t in processing_times if t < fast_threshold)
            slow_count = sum(1 for t in processing_times if t > slow_threshold)
            medium_count = len(processing_times) - fast_count - slow_count
            
            st.markdown("**Response Speed Distribution:**")
            st.write(f"🟢 Fast: {fast_count} ({fast_count/len(processing_times)*100:.1f}%)")
            st.write(f"🟠 Medium: {medium_count} ({medium_count/len(processing_times)*100:.1f}%)")
            st.write(f"🔴 Slow: {slow_count} ({slow_count/len(processing_times)*100:.1f}%)")


def create_advanced_chat_settings():
    """Create advanced chat settings for power users with enhanced processing time controls."""
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
        
        # Performance monitoring settings
        st.markdown("**⏱️ Performance Monitoring:**")
        
        enable_performance_warnings = st.checkbox(
            "Enable performance warnings",
            value=st.session_state.get('enable_performance_warnings', True),
            help="Show warnings for slow responses",
            key="performance_warnings_setting"
        )
        st.session_state['enable_performance_warnings'] = enable_performance_warnings
        
        log_processing_times = st.checkbox(
            "Log processing times to console",
            value=st.session_state.get('log_processing_times', False),
            help="Log processing times for debugging",
            key="log_processing_times_setting"
        )
        st.session_state['log_processing_times'] = log_processing_times
        
        # Advanced thresholds
        st.markdown("**Advanced Thresholds:**")
        
        warning_threshold = st.slider(
            "Warning threshold (seconds)",
            min_value=5.0,
            max_value=30.0,
            value=st.session_state.get('warning_threshold', 10.0),
            step=1.0,
            help="Show warning notifications for responses slower than this",
            key="warning_threshold_setting"
        )
        st.session_state['warning_threshold'] = warning_threshold
        
        timeout_threshold = st.slider(
            "Expected timeout (seconds)",
            min_value=15.0,
            max_value=120.0,
            value=st.session_state.get('timeout_threshold', 60.0),
            step=5.0,
            help="Expected maximum response time before timeout",
            key="timeout_threshold_setting"
        )
        st.session_state['timeout_threshold'] = timeout_threshold
        
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
        
        include_processing_times_in_export = st.checkbox(
            "Include processing times in exports",
            value=st.session_state.get('include_processing_times_in_export', True),
            help="Whether to include processing time data in chat exports",
            key="export_processing_times_setting"
        )
        st.session_state['include_processing_times_in_export'] = include_processing_times_in_export


def create_chat_actions_panel():
    """Create a panel with quick chat actions including processing time analytics."""
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
        if st.button("📊 Performance Report", help="Generate a performance analysis of the current chat", key="performance_report_btn"):
            show_performance_report()


def show_performance_report():
    """Display a detailed performance report for the current chat."""
    current_user = st.session_state.get('username')
    if not current_user:
        return
    
    user_messages_key = f"user_{current_user}_messages"
    messages = st.session_state.get(user_messages_key, [])
    
    # Extract processing times and categorize messages
    processing_times = []
    user_messages = []
    assistant_messages = []
    tool_messages = []
    
    for msg in messages:
        if msg.get('role') == 'user':
            user_messages.append(msg)
        elif msg.get('role') == 'assistant':
            assistant_messages.append(msg)
            if msg.get('processing_time'):
                processing_times.append(msg['processing_time'])
        elif msg.get('role') == 'tool':
            tool_messages.append(msg)
    
    with st.expander("📊 Chat Performance Report", expanded=True):
        if not processing_times:
            st.info("No processing time data available for this chat.")
            return
        
        # Overall statistics
        st.markdown("**Overall Performance:**")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Responses", len(processing_times))
        
        with col2:
            avg_time = sum(processing_times) / len(processing_times)
            st.metric("Average Time", f"{avg_time:.2f}s")
        
        with col3:
            st.metric("Fastest", f"{min(processing_times):.2f}s")
        
        with col4:
            st.metric("Slowest", f"{max(processing_times):.2f}s")
        
        # Performance distribution
        fast_threshold = st.session_state.get('fast_threshold', 2.0)
        slow_threshold = st.session_state.get('slow_threshold', 5.0)
        
        fast_responses = [t for t in processing_times if t < fast_threshold]
        medium_responses = [t for t in processing_times if fast_threshold <= t <= slow_threshold]
        slow_responses = [t for t in processing_times if t > slow_threshold]
        
        st.markdown("**Performance Distribution:**")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            fast_pct = len(fast_responses) / len(processing_times) * 100
            st.metric("🟢 Fast Responses", f"{len(fast_responses)} ({fast_pct:.1f}%)")
        
        with col2:
            medium_pct = len(medium_responses) / len(processing_times) * 100
            st.metric("🟠 Medium Responses", f"{len(medium_responses)} ({medium_pct:.1f}%)")
        
        with col3:
            slow_pct = len(slow_responses) / len(processing_times) * 100
            st.metric("🔴 Slow Responses", f"{len(slow_responses)} ({slow_pct:.1f}%)")
        
        # Performance trends (if enough data)
        if len(processing_times) >= 5:
            st.markdown("**Performance Trend:**")
            
            # Calculate trend over time
            first_half = processing_times[:len(processing_times)//2]
            second_half = processing_times[len(processing_times)//2:]
            
            first_avg = sum(first_half) / len(first_half)
            second_avg = sum(second_half) / len(second_half)
            
            if second_avg < first_avg:
                trend = "📈 Improving"
                trend_value = f"{((first_avg - second_avg) / first_avg) * 100:.1f}% faster"
            elif second_avg > first_avg:
                trend = "📉 Declining"
                trend_value = f"{((second_avg - first_avg) / first_avg) * 100:.1f}% slower"
            else:
                trend = "➡️ Stable"
                trend_value = "No significant change"
            
            st.info(f"{trend}: {trend_value}")
        
        # Detailed breakdown
        if st.checkbox("Show detailed breakdown"):
            st.markdown("**Detailed Response Times:**")
            
            for i, (msg, time) in enumerate(zip(assistant_messages, processing_times)):
                if time < fast_threshold:
                    color = "🟢"
                elif time <= slow_threshold:
                    color = "🟠"
                else:
                    color = "🔴"
                
                timestamp = get_formatted_timestamp(msg.get('timestamp', ''))
                content_preview = msg.get('content', '')[:50] + "..."
                
                st.write(f"{color} Response #{i+1}: {time:.2f}s at {timestamp}")
                st.write(f"   └─ {content_preview}")


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


def get_formatted_timestamp(timestamp_str: str) -> str:
    """Format timestamp for display."""
    if not timestamp_str:
        return ""
    
    try:
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        return dt.strftime('%H:%M:%S')
    except:
        return ""


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
    """Export chat with current settings applied including processing time data."""
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
    include_processing_times = st.session_state.get('include_processing_times_in_export', True)
    
    # Filter messages based on settings
    filtered_messages = []
    processing_time_stats = []
    
    for msg in messages:
        # Skip tool messages if not included
        if msg.get('role') == 'tool' and not include_tools:
            continue
        
        # Create export message
        export_msg = msg.copy()
        
        # Remove timestamps if not included
        if not include_timestamps and 'timestamp' in export_msg:
            del export_msg['timestamp']
        
        # Handle processing times
        if export_msg.get('processing_time'):
            if include_processing_times:
                processing_time_stats.append(export_msg['processing_time'])
            else:
                del export_msg['processing_time']
        
        filtered_messages.append(export_msg)
    
    # Calculate processing time statistics
    stats = {}
    if processing_time_stats:
        stats = {
            "total_processing_time": sum(processing_time_stats),
            "average_processing_time": sum(processing_time_stats) / len(processing_time_stats),
            "min_processing_time": min(processing_time_stats),
            "max_processing_time": max(processing_time_stats),
            "messages_with_timing": len(processing_time_stats)
        }
    
    # Prepare export data
    export_data = {
        "chat_export": {
            "user": current_user,
            "chat_id": st.session_state.get('current_chat_id'),
            "exported_at": datetime.now().isoformat(),
            "settings": {
                "include_tool_outputs": include_tools,
                "include_timestamps": include_timestamps,
                "include_processing_times": include_processing_times,
                "show_tool_outputs": st.session_state.get('show_tool_outputs', True)
            },
            "message_count": len(filtered_messages),
            "processing_stats": stats,
            "messages": filtered_messages
        }
    }
    
    # Create download button
    import json
    json_str = json.dumps(export_data, indent=2)
    st.download_button(
        label="💾 Download Filtered Chat with Stats",
        data=json_str,
        file_name=f"chat_export_with_stats_{current_user}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        mime="application/json"
    )