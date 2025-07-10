import streamlit as st
from config import SERVER_CONFIG
import uuid
from langchain_core.messages import HumanMessage, AIMessage
from typing import Optional, List, Dict, Any
import asyncio
from utils.async_helpers import run_async
import json
from datetime import datetime

# Session state initialization with user isolation
def init_session():
    """Initialize session with user-specific isolation."""
    current_user = st.session_state.get('username')
    
    if not current_user:
        return
    
    # Create user-specific keys
    user_key_prefix = f"user_{current_user}_"
    
    defaults = {
        f"{user_key_prefix}params": {},
        f"{user_key_prefix}current_chat_id": None,
        f"{user_key_prefix}current_chat_index": 0,
        f"{user_key_prefix}history_chats": get_user_history(current_user),
        f"{user_key_prefix}messages": [],
        f"{user_key_prefix}conversation_memory": [],
        "client": None,  # Shared across users
        "agent": None,   # Shared across users
        "tools": [],     # Shared across users
        "tool_executions": [],
        "servers": SERVER_CONFIG['mcpServers'],
    }
    
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val
    
    # Also set global keys pointing to user-specific data for backward compatibility
    st.session_state["params"] = st.session_state[f"{user_key_prefix}params"]
    st.session_state["current_chat_id"] = st.session_state[f"{user_key_prefix}current_chat_id"]
    st.session_state["current_chat_index"] = st.session_state[f"{user_key_prefix}current_chat_index"]
    st.session_state["history_chats"] = st.session_state[f"{user_key_prefix}history_chats"]
    st.session_state["messages"] = st.session_state[f"{user_key_prefix}messages"]
    st.session_state["conversation_memory"] = st.session_state[f"{user_key_prefix}conversation_memory"]


def get_user_history(username: str) -> List[Dict]:
    """Get chat history for a specific user."""
    user_key = f"user_{username}_history_chats"
    
    if user_key in st.session_state and st.session_state[user_key]:
        return st.session_state[user_key]
    else:
        chat_id = str(uuid.uuid4())
        new_chat = {
            'chat_id': chat_id,
            'chat_name': 'New chat',
            'messages': [],
            'created_by': username,
            'created_at': datetime.now().isoformat()
        }
        
        # Update user-specific session state
        st.session_state[f"user_{username}_current_chat_index"] = 0
        st.session_state[f"user_{username}_current_chat_id"] = chat_id
        st.session_state[user_key] = [new_chat]
        
        return [new_chat]


def switch_user_context(username: str):
    """Switch to a specific user's context and clear previous user data."""
    if not username:
        return
    
    # Clear any existing global references to prevent data leakage
    keys_to_clear = ["params", "current_chat_id", "current_chat_index", 
                     "history_chats", "messages", "conversation_memory"]
    
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    
    # Initialize session for the new user
    init_session()


def get_current_chat(chat_id: str, username: str = None) -> List[Dict]:
    """Get messages for the current chat for a specific user."""
    if not username:
        username = st.session_state.get('username')
    
    if not username:
        return []
    
    user_history_key = f"user_{username}_history_chats"
    user_chats = st.session_state.get(user_history_key, [])
    
    for chat in user_chats:
        if chat['chat_id'] == chat_id and chat.get('created_by') == username:
            return chat['messages']
    return []


def _append_message_to_session(msg: dict) -> None:
    """Append message to the current user's chat session."""
    current_user = st.session_state.get('username')
    if not current_user:
        return
    
    chat_id = st.session_state.get("current_chat_id")
    if not chat_id:
        return
    
    # Get user-specific keys
    user_messages_key = f"user_{current_user}_messages"
    user_history_key = f"user_{current_user}_history_chats"
    
    # Avoid duplicating messages
    user_messages = st.session_state.get(user_messages_key, [])
    if user_messages and len(user_messages) > 0:
        last_message = user_messages[-1]
        # Check if this is a duplicate message
        if (last_message.get("role") == msg.get("role") and 
            last_message.get("content") == msg.get("content") and
            last_message.get("tool") == msg.get("tool")):
            return  # Don't add duplicate
    
    # Add timestamp and user info to message
    msg['timestamp'] = datetime.now().isoformat()
    msg['user'] = current_user
    
    # Update user-specific messages
    user_messages.append(msg)
    st.session_state[user_messages_key] = user_messages
    st.session_state["messages"] = user_messages  # Update global reference
    
    # Update the chat in user's history
    user_chats = st.session_state.get(user_history_key, [])
    for chat in user_chats:
        if chat["chat_id"] == chat_id and chat.get('created_by') == current_user:
            chat["messages"] = user_messages
            # Only rename chat based on user messages, not tool messages
            if (chat["chat_name"] == "New chat" and 
                msg["role"] == "user" and 
                "content" in msg):                 
                chat["chat_name"] = " ".join(msg["content"].split()[:5]) or "Empty"
            chat["last_updated"] = datetime.now().isoformat()
            break
    
    st.session_state[user_history_key] = user_chats
    st.session_state["history_chats"] = user_chats  # Update global reference


def create_chat() -> Dict:
    """Create a new chat session for the current user."""
    current_user = st.session_state.get('username')
    if not current_user:
        return {}
    
    chat_id = str(uuid.uuid4())
    new_chat = {
        'chat_id': chat_id,
        'chat_name': 'New chat',
        'messages': [],
        'created_by': current_user,
        'created_at': datetime.now().isoformat()
    }
    
    # Get user-specific keys
    user_history_key = f"user_{current_user}_history_chats"
    user_messages_key = f"user_{current_user}_messages"
    user_memory_key = f"user_{current_user}_conversation_memory"
    
    # Update user-specific session state
    user_chats = st.session_state.get(user_history_key, [])
    user_chats.append(new_chat)
    
    st.session_state[user_history_key] = user_chats
    st.session_state[f"user_{current_user}_current_chat_index"] = 0
    st.session_state[f"user_{current_user}_current_chat_id"] = chat_id
    st.session_state[user_messages_key] = []
    st.session_state[user_memory_key] = []
    
    # Update global references
    st.session_state["history_chats"] = user_chats
    st.session_state["current_chat_id"] = chat_id
    st.session_state["current_chat_index"] = 0
    st.session_state["messages"] = []
    st.session_state["conversation_memory"] = []
    
    return new_chat


def switch_chat(chat_id: str):
    """Switch to a different chat for the current user."""
    current_user = st.session_state.get('username')
    if not current_user:
        return
    
    current_chat_id = st.session_state.get("current_chat_id")
    if chat_id == current_chat_id:
        return  # Already on this chat
    
    # Get user-specific keys
    user_history_key = f"user_{current_user}_history_chats"
    user_messages_key = f"user_{current_user}_messages"
    user_memory_key = f"user_{current_user}_conversation_memory"
    
    # Get chat messages for this user only
    chat_messages = get_current_chat(chat_id, current_user)
    
    # Verify the chat belongs to the current user
    user_chats = st.session_state.get(user_history_key, [])
    target_chat = None
    for i, chat in enumerate(user_chats):
        if chat["chat_id"] == chat_id and chat.get('created_by') == current_user:
            target_chat = chat
            st.session_state[f"user_{current_user}_current_chat_index"] = i
            break
    
    if not target_chat:
        return  # Chat not found or doesn't belong to user
    
    # Update user-specific session state
    st.session_state[f"user_{current_user}_current_chat_id"] = chat_id
    st.session_state[user_messages_key] = chat_messages
    st.session_state[user_memory_key] = []  # Reset conversation memory for new chat
    
    # Update global references
    st.session_state["current_chat_id"] = chat_id
    st.session_state["messages"] = chat_messages
    st.session_state["conversation_memory"] = []


def delete_chat(chat_id: str):
    """Delete a chat from the current user's history."""
    current_user = st.session_state.get('username')
    if not current_user or not chat_id:
        return

    # Get user-specific keys
    user_history_key = f"user_{current_user}_history_chats"
    user_chats = st.session_state.get(user_history_key, [])
    
    # Remove chat only if it belongs to the current user
    updated_chats = [
        chat for chat in user_chats
        if not (chat["chat_id"] == chat_id and chat.get('created_by') == current_user)
    ]
    
    if len(updated_chats) == len(user_chats):
        return  # Chat not found or doesn't belong to user
    
    st.session_state[user_history_key] = updated_chats
    st.session_state["history_chats"] = updated_chats  # Update global reference

    # Handle current chat deletion
    current_chat_id = st.session_state.get("current_chat_id")
    if current_chat_id == chat_id:
        if updated_chats:
            # Switch to the first available chat
            first_chat = updated_chats[0]
            st.session_state[f"user_{current_user}_current_chat_id"] = first_chat["chat_id"]
            st.session_state[f"user_{current_user}_current_chat_index"] = 0
            st.session_state[f"user_{current_user}_messages"] = first_chat["messages"]
            
            # Update global references
            st.session_state["current_chat_id"] = first_chat["chat_id"]
            st.session_state["current_chat_index"] = 0
            st.session_state["messages"] = first_chat["messages"]
        else:
            # No chats left, create a new one
            create_chat()
        
        # Clear conversation memory when switching/deleting chats
        st.session_state[f"user_{current_user}_conversation_memory"] = []
        st.session_state["conversation_memory"] = []


def get_conversation_summary(max_messages: int = 10) -> str:
    """Get a summary of recent conversation for current user."""
    current_user = st.session_state.get('username')
    if not current_user:
        return "Please log in to view conversation."
    
    user_messages = st.session_state.get(f"user_{current_user}_messages", [])
    if not user_messages:
        return "This is the start of a new conversation."
    
    recent_messages = user_messages[-max_messages:]
    summary_parts = []
    
    for msg in recent_messages:
        if msg["role"] == "user":
            summary_parts.append(f"User: {msg['content'][:100]}...")
        elif msg["role"] == "assistant" and "content" in msg and msg["content"]:
            summary_parts.append(f"Assistant: {msg['content'][:100]}...")
    
    return "\n".join(summary_parts)


def get_clean_conversation_memory() -> List:
    """Get conversation memory with only user/assistant content messages for LLM compatibility."""
    current_user = st.session_state.get('username')
    if not current_user:
        return []
    
    conversation_messages = []
    
    current_chat_id = st.session_state.get('current_chat_id')
    if current_chat_id:
        messages = get_current_chat(current_chat_id, current_user)
        
        for msg in messages:
            # Only include messages from the current user's session
            if msg.get('user') == current_user:
                if msg["role"] == "user" and "content" in msg:
                    conversation_messages.append(HumanMessage(content=msg["content"]))
                elif (msg["role"] == "assistant" and 
                      "content" in msg and 
                      msg["content"] and 
                      "tool" not in msg):  # Only regular assistant messages, not tool messages
                    conversation_messages.append(AIMessage(content=msg["content"]))
    
    return conversation_messages


def clear_user_session_data(username: str):
    """Clear all session data for a specific user (useful for logout)."""
    if not username:
        return
    
    user_keys_to_clear = [
        f"user_{username}_params",
        f"user_{username}_current_chat_id",
        f"user_{username}_current_chat_index",
        f"user_{username}_history_chats",
        f"user_{username}_messages",
        f"user_{username}_conversation_memory"
    ]
    
    for key in user_keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]


class ChatService:
    """Service class to handle chat interactions with the MCP agent."""
    
    def __init__(self):
        """Initialize the chat service."""
        self.agent = None
        self.tools = []
        
    def process_message(self, user_input: str) -> str:
        """
        Process a user message and return the AI response.
        
        Args:
            user_input: The user's input message
            
        Returns:
            The AI agent's response
        """
        try:
            # Check authentication
            current_user = st.session_state.get('username')
            if not current_user:
                return "❌ Please log in to use the chat service."
            
            # Get the agent from session state
            if not st.session_state.get("agent"):
                return "❌ No MCP agent available. Please connect to MCP servers first."
            
            # Get conversation history for current user
            conversation_messages = get_clean_conversation_memory()
            
            # Add the current user message
            conversation_messages.append(HumanMessage(content=user_input))
            
            # Run the agent with conversation context
            response = run_async(self._run_agent_async(conversation_messages))
            
            # Extract the response content
            if hasattr(response, 'content'):
                return response.content
            elif isinstance(response, dict) and 'messages' in response:
                # Extract the last message content
                messages = response['messages']
                if messages and hasattr(messages[-1], 'content'):
                    return messages[-1].content
                elif messages and isinstance(messages[-1], dict):
                    return messages[-1].get('content', str(messages[-1]))
            
            return str(response)
            
        except Exception as e:
            error_message = f"Error processing message: {str(e)}"
            st.error(error_message)
            return error_message
    
    async def _run_agent_async(self, messages: List) -> Any:
        """
        Run the agent asynchronously with the given messages.
        
        Args:
            messages: List of conversation messages
            
        Returns:
            Agent response
        """
        agent = st.session_state["agent"]
        
        # Invoke the agent with the messages
        result = await agent.ainvoke({"messages": messages})
        
        return result
    
    def get_available_tools(self) -> List[str]:
        """Get list of available tool names."""
        tools = st.session_state.get("tools", [])
        return [tool.name for tool in tools]
    
    def is_connected(self) -> bool:
        """Check if the chat service is connected to MCP servers."""
        return st.session_state.get("agent") is not None
    
    def get_connection_status(self) -> Dict[str, Any]:
        """Get detailed connection status."""
        return {
            "connected": self.is_connected(),
            "agent_available": st.session_state.get("agent") is not None,
            "tools_count": len(st.session_state.get("tools", [])),
            "servers_count": len(st.session_state.get("servers", {})),
            "available_tools": self.get_available_tools(),
            "current_user": st.session_state.get('username')
        }


def get_user_chat_stats(username: str = None) -> Dict[str, int]:
    """Get chat statistics for a user."""
    if not username:
        username = st.session_state.get('username')
    
    if not username:
        return {"total_chats": 0, "total_messages": 0}
    
    user_history_key = f"user_{username}_history_chats"
    user_chats = st.session_state.get(user_history_key, [])
    
    total_chats = len(user_chats)
    total_messages = sum(len(chat.get('messages', [])) for chat in user_chats)
    
    return {
        "total_chats": total_chats,
        "total_messages": total_messages,
        "user": username
    }


# Authentication event handlers
def on_user_login(username: str):
    """Handle user login - initialize user-specific session."""
    switch_user_context(username)


def on_user_logout(username: str):
    """Handle user logout - clear user-specific session data."""
    clear_user_session_data(username)
    
    # Clear global session state
    keys_to_clear = ["params", "current_chat_id", "current_chat_index", 
                     "history_chats", "messages", "conversation_memory"]
    
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]