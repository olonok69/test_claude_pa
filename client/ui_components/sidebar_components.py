import streamlit as st
from config import MODEL_OPTIONS
import traceback
import os
from services.mcp_service import connect_to_mcp_servers
from services.chat_service import create_chat, delete_chat, switch_chat
from utils.tool_schema_parser import extract_tool_parameters
from utils.async_helpers import reset_connection_state


def create_history_chat_container():
    history_container = st.sidebar.container(height=200, border=None)
    with history_container:
        chat_history_menu = [
                f"{chat['chat_name']}_::_{chat['chat_id']}"
                for chat in st.session_state["history_chats"]
            ]
        chat_history_menu = chat_history_menu[:50][::-1]
        
        if chat_history_menu:
            # Get current selection index
            current_selection = None
            for i, chat_option in enumerate(chat_history_menu):
                chat_id = chat_option.split("_::_")[1]
                if chat_id == st.session_state.get("current_chat_id"):
                    current_selection = i
                    break
            
            if current_selection is None:
                current_selection = 0
            
            selected_chat = st.radio(
                label="History Chats",
                format_func=lambda x: x.split("_::_")[0] + '...' if "_::_" in x else x,
                options=chat_history_menu,
                label_visibility="collapsed",
                index=current_selection,
                key="chat_selector"
            )
            
            if selected_chat:
                selected_chat_id = selected_chat.split("_::_")[1]
                # Only switch if it's a different chat
                if selected_chat_id != st.session_state.get("current_chat_id"):
                    switch_chat(selected_chat_id)
                    st.rerun()


def create_sidebar_chat_buttons():
    with st.sidebar:
        c1, c2 = st.columns(2)
        create_chat_button = c1.button(
            "New Chat", use_container_width=True, key="create_chat_button"
        )
        if create_chat_button:
            create_chat()
            st.rerun()

        delete_chat_button = c2.button(
            "Delete Chat", use_container_width=True, key="delete_chat_button"
        )
        if delete_chat_button and st.session_state.get('current_chat_id'):
            delete_chat(st.session_state['current_chat_id'])
            st.rerun()

def create_provider_select_widget():
    params = st.session_state.setdefault('params', {})
    
    # Load previously selected provider or default to the first
    default_provider = params.get("model_id", list(MODEL_OPTIONS.keys())[0])
    default_index = list(MODEL_OPTIONS.keys()).index(default_provider)
    
    # Provider selector with synced state
    selected_provider = st.sidebar.selectbox(
        '🔎 Choose Provider',
        options=list(MODEL_OPTIONS.keys()),
        index=default_index,
        key="provider_selection",
        on_change=reset_connection_state
    )
    
    # Save new provider and its index
    if selected_provider:
        params['model_id'] = selected_provider
        params['provider_index'] = list(MODEL_OPTIONS.keys()).index(selected_provider)
        st.sidebar.success(f"Model: {MODEL_OPTIONS[selected_provider]}")

    # Check credentials status
    with st.sidebar.container():
        st.subheader("🔐 Credentials Status")
        
        if selected_provider == "OpenAI":
            openai_key = os.getenv("OPENAI_API_KEY")
            if openai_key:
                st.success("✅ OpenAI API Key loaded")
            else:
                st.error("❌ OpenAI API Key not found in .env")
                
        elif selected_provider == "Azure OpenAI":
            azure_key = os.getenv("AZURE_API_KEY")
            azure_endpoint = os.getenv("AZURE_ENDPOINT")
            azure_deployment = os.getenv("AZURE_DEPLOYMENT")
            azure_version = os.getenv("AZURE_API_VERSION")
            
            if all([azure_key, azure_endpoint, azure_deployment, azure_version]):
                st.success("✅ Azure OpenAI configuration loaded")
                with st.expander("Azure Config Details"):
                    st.text(f"Endpoint: {azure_endpoint}")
                    st.text(f"Deployment: {azure_deployment}")
                    st.text(f"API Version: {azure_version}")
            else:
                st.error("❌ Azure OpenAI configuration incomplete")
                missing = []
                if not azure_key:
                    missing.append("AZURE_API_KEY")
                if not azure_endpoint:
                    missing.append("AZURE_ENDPOINT")
                if not azure_deployment:
                    missing.append("AZURE_DEPLOYMENT")
                if not azure_version:
                    missing.append("AZURE_API_VERSION")
                st.error(f"Missing: {', '.join(missing)}")

def create_advanced_configuration_widget():
    params = st.session_state["params"]
    with st.sidebar.expander("⚙️  Basic config", expanded=False):
        params['max_tokens'] = st.number_input("Max tokens",
                                    min_value=1024,
                                    max_value=10240,
                                    value=4096,
                                    step=512,)
        params['temperature'] = st.slider("Temperature", 0.0, 1.0, step=0.05, value=1.0)
                
def create_mcp_connection_widget():
    with st.sidebar:
        st.subheader("Server Management")
        with st.expander(f"MCP Servers ({len(st.session_state.servers)})"):
            for name, config in st.session_state.servers.items():
                with st.container(border=True):
                    st.markdown(f"**Server:** {name}")
                    st.markdown(f"**URL:** {config['url']}")
                    if st.button(f"Remove {name}", key=f"remove_{name}"):
                        del st.session_state.servers[name]
                        st.rerun()

        if st.session_state.get("agent"):
            st.success(f"📶 Connected to {len(st.session_state.servers)} MCP servers!"
                       f" Found {len(st.session_state.tools)} tools.")
            if st.button("Disconnect from MCP Servers"):
                with st.spinner("Disconnecting from MCP servers..."):
                    try:
                        reset_connection_state()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error disconnecting from MCP servers: {str(e)}")
                        st.code(traceback.format_exc(), language="python")
        else:
            st.warning("⚠️ Not connected to MCP server")
            if st.button("Connect to MCP Servers"):
                with st.spinner("Connecting to MCP servers..."):
                    try:
                        connect_to_mcp_servers()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error connecting to MCP servers: {str(e)}")
                        st.code(traceback.format_exc(), language="python")

def create_mcp_tools_widget():
    with st.sidebar:
        if st.session_state.tools:
            st.subheader("🧰 Available Tools")

            selected_tool_name = st.selectbox(
                "Select a Tool",
                options=[tool.name for tool in st.session_state.tools],
                index=0
            )

            if selected_tool_name:
                selected_tool = next(
                    (tool for tool in st.session_state.tools if tool.name == selected_tool_name),
                    None
                )

                if selected_tool:
                    with st.container():
                        st.write("**Description:**")
                        st.write(selected_tool.description)

                        parameters = extract_tool_parameters(selected_tool)

                        if parameters:
                            st.write("**Parameters:**")
                            for param in parameters:
                                st.code(param)