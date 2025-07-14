import streamlit as st
from typing import List, Dict, Any
from datetime import datetime

def filter_messages_by_settings(messages: List[Dict], user_settings: Dict = None) -> List[Dict]:
    """Filter messages based on user settings."""
    if not user_settings:
        user_settings = get_current_user_settings()
    
    filtered_messages = []
    
    for message in messages:
        # Check if tool messages should be shown
        if message.get('role') == 'tool':
            if not user_settings.get('show_tool_outputs', True):
                continue
            
            # Check specific tool type filters
            if not should_show_tool_message_by_type(message, user_settings):
                continue
        
        filtered_messages.append(message)
    
    return filtered_messages


def should_show_tool_message_by_type(message: Dict, user_settings: Dict) -> bool:
    """Determine if a tool message should be shown based on its type."""
    tool_name = message.get('tool_name', '').lower()
    
    # Check MSSQL tool filter
    if any(keyword in tool_name for keyword in ['sql', 'mssql', 'execute_sql', 'list_tables', 'describe_table']):
        return user_settings.get('show_mssql_outputs', True)
    
    # Check general tool filter
    return user_settings.get('show_general_outputs', True)


def get_current_user_settings() -> Dict:
    """Get current user's chat display settings."""
    return {
        'show_tool_outputs': st.session_state.get('show_tool_outputs', True),
        'message_order': st.session_state.get('message_order', 'Latest First'),
        'auto_scroll_enabled': st.session_state.get('auto_scroll_enabled', True),
        'show_timestamps': st.session_state.get('show_timestamps', True),
        'show_mssql_outputs': st.session_state.get('show_mssql_outputs', True),
        'show_general_outputs': st.session_state.get('show_general_outputs', True),
        'max_message_length': st.session_state.get('max_message_length', 500),
        'max_tool_output_length': st.session_state.get('max_tool_output_length', 300)
    }


def truncate_message_content(content: str, message_type: str = 'message') -> tuple:
    """Truncate message content based on settings and return (content, is_truncated)."""
    settings = get_current_user_settings()
    
    if message_type == 'tool':
        max_length = settings.get('max_tool_output_length', 300)
    else:
        max_length = settings.get('max_message_length', 500)
    
    if len(content) <= max_length:
        return content, False
    
    return content[:max_length] + "...", True


def format_message_timestamp(timestamp_str: str) -> str:
    """Format timestamp for display based on user settings."""
    settings = get_current_user_settings()
    
    if not settings.get('show_timestamps', True) or not timestamp_str:
        return ""
    
    try:
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        return dt.strftime('%H:%M:%S')
    except:
        return ""


def get_message_display_order(messages: List[Dict]) -> List[Dict]:
    """Get messages in the correct display order based on user settings."""
    settings = get_current_user_settings()
    
    if settings.get('message_order', 'Latest First') == 'Latest First':
        return list(reversed(messages))
    else:
        return messages


def create_message_stats(messages: List[Dict]) -> Dict[str, int]:
    """Create statistics for a list of messages."""
    stats = {
        'total': len(messages),
        'user': 0,
        'assistant': 0,
        'tool': 0,
        'mssql_tools': 0,
        'general_tools': 0
    }
    
    for message in messages:
        role = message.get('role', '')
        
        if role == 'user':
            stats['user'] += 1
        elif role == 'assistant':
            stats['assistant'] += 1
        elif role == 'tool':
            stats['tool'] += 1
            
            # Categorize tool type
            tool_name = message.get('tool_name', '').lower()
            if any(keyword in tool_name for keyword in ['sql', 'mssql', 'execute_sql', 'list_tables']):
                stats['mssql_tools'] += 1
            else:
                stats['general_tools'] += 1
    
    return stats


def export_messages_with_settings(messages: List[Dict], include_settings: bool = True) -> Dict:
    """Export messages with current user settings applied."""
    settings = get_current_user_settings()
    current_user = st.session_state.get('username')
    
    # Filter messages based on export settings
    if not settings.get('include_tool_outputs_in_export', True):
        messages = [msg for msg in messages if msg.get('role') != 'tool']
    
    # Remove timestamps if not included
    if not settings.get('include_timestamps_in_export', True):
        for msg in messages:
            if 'timestamp' in msg:
                del msg['timestamp']
    
    export_data = {
        "chat_export": {
            "user": current_user,
            "exported_at": datetime.now().isoformat(),
            "message_count": len(messages),
            "messages": messages
        }
    }
    
    if include_settings:
        export_data["export_settings"] = settings
        export_data["message_stats"] = create_message_stats(messages)
    
    return export_data


def get_tool_usage_summary(messages: List[Dict]) -> Dict[str, Any]:
    """Get a summary of tool usage in the messages."""
    tool_usage = {}
    tool_categories = {'MSSQL': 0, 'General': 0}
    
    for message in messages:
        if message.get('role') == 'tool':
            tool_name = message.get('tool_name', 'Unknown')
            tool_usage[tool_name] = tool_usage.get(tool_name, 0) + 1
            
            # Categorize
            if any(keyword in tool_name.lower() for keyword in ['sql', 'mssql', 'execute_sql', 'list_tables']):
                tool_categories['MSSQL'] += 1
            else:
                tool_categories['General'] += 1
    
    return {
        'tool_usage': tool_usage,
        'categories': tool_categories,
        'most_used': max(tool_usage.items(), key=lambda x: x[1]) if tool_usage else None,
        'total_executions': sum(tool_usage.values())
    }


def search_messages(messages: List[Dict], search_term: str, search_type: str = 'all') -> List[Dict]:
    """Search through messages based on content and type."""
    if not search_term:
        return messages
    
    search_term = search_term.lower()
    filtered_messages = []
    
    for message in messages:
        content = message.get('content', '').lower()
        role = message.get('role', '')
        
        # Apply search type filter
        if search_type == 'user' and role != 'user':
            continue
        elif search_type == 'assistant' and role != 'assistant':
            continue
        elif search_type == 'tool' and role != 'tool':
            continue
        
        # Search in content
        if search_term in content:
            filtered_messages.append(message)
            continue
        
        # Search in tool names for tool messages
        if role == 'tool':
            tool_name = message.get('tool_name', '').lower()
            if search_term in tool_name:
                filtered_messages.append(message)
    
    return filtered_messages


def validate_message_structure(message: Dict) -> bool:
    """Validate that a message has the required structure."""
    required_fields = ['role', 'content', 'timestamp', 'user']
    
    for field in required_fields:
        if field not in message:
            return False
    
    # Validate role
    valid_roles = ['user', 'assistant', 'tool']
    if message['role'] not in valid_roles:
        return False
    
    # Additional validation for tool messages
    if message['role'] == 'tool':
        if 'tool_name' not in message:
            return False
    
    return True


def clean_message_for_display(message: Dict) -> Dict:
    """Clean and prepare a message for display."""
    cleaned_message = message.copy()
    
    # Truncate content based on settings
    content = cleaned_message.get('content', '')
    message_type = 'tool' if cleaned_message.get('role') == 'tool' else 'message'
    
    truncated_content, is_truncated = truncate_message_content(content, message_type)
    cleaned_message['content'] = truncated_content
    cleaned_message['is_truncated'] = is_truncated
    
    # Format timestamp
    timestamp = cleaned_message.get('timestamp', '')
    cleaned_message['formatted_timestamp'] = format_message_timestamp(timestamp)
    
    return cleaned_message


def get_conversation_context(messages: List[Dict], max_context_messages: int = 10) -> str:
    """Get conversation context for AI processing (excluding tool messages)."""
    context_messages = []
    
    # Only include user and assistant messages for context
    for message in messages:
        if message.get('role') in ['user', 'assistant']:
            context_messages.append(message)
    
    # Get recent messages
    recent_messages = context_messages[-max_context_messages:]
    
    context_parts = []
    for message in recent_messages:
        role = message.get('role', '')
        content = message.get('content', '')
        
        if role == 'user':
            context_parts.append(f"User: {content}")
        elif role == 'assistant':
            context_parts.append(f"Assistant: {content}")
    
    return "\n".join(context_parts)


def create_message_filters_ui():
    """Create UI controls for message filtering."""
    st.markdown("**Message Filters:**")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        search_term = st.text_input(
            "Search messages", 
            placeholder="Enter search term...",
            key="message_search"
        )
    
    with col2:
        search_type = st.selectbox(
            "Message type",
            options=['all', 'user', 'assistant', 'tool'],
            key="message_type_filter"
        )
    
    with col3:
        if st.button("🔍 Apply Filter", key="apply_message_filter"):
            st.session_state['message_search_applied'] = True
            st.rerun()
    
    return search_term, search_type


def apply_message_filters(messages: List[Dict]) -> List[Dict]:
    """Apply all active message filters."""
    # Get user settings
    settings = get_current_user_settings()
    
    # Apply settings-based filters
    filtered_messages = filter_messages_by_settings(messages, settings)
    
    # Apply search filters if active
    if st.session_state.get('message_search_applied', False):
        search_term = st.session_state.get('message_search', '')
        search_type = st.session_state.get('message_type_filter', 'all')
        
        if search_term:
            filtered_messages = search_messages(filtered_messages, search_term, search_type)
    
    # Apply display order
    filtered_messages = get_message_display_order(filtered_messages)
    
    return filtered_messages


def reset_message_filters():
    """Reset all message filters to defaults."""
    filter_keys = [
        'message_search',
        'message_type_filter', 
        'message_search_applied'
    ]
    
    for key in filter_keys:
        if key in st.session_state:
            del st.session_state[key]