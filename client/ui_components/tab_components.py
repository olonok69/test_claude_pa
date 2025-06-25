import streamlit as st
from config import MODEL_OPTIONS
import traceback
import os
from services.mcp_service import connect_to_mcp_servers
from utils.tool_schema_parser import extract_tool_parameters
from utils.async_helpers import reset_connection_state


def create_configuration_tab():
    """Create the Configuration tab content."""
    st.header("⚙️ Configuration")
    st.markdown("Configure your AI provider and model parameters.")
    
    # Provider Configuration Section
    with st.container(border=True):
        st.subheader("🔎 AI Provider Selection")
        
        params = st.session_state.setdefault('params', {})
        
        # Load previously selected provider or default to the first
        default_provider = params.get("model_id", list(MODEL_OPTIONS.keys())[0])
        default_index = list(MODEL_OPTIONS.keys()).index(default_provider)
        
        # Provider selector with synced state
        selected_provider = st.selectbox(
            'Choose Provider',
            options=list(MODEL_OPTIONS.keys()),
            index=default_index,
            key="provider_selection_tab",
            on_change=reset_connection_state,
            help="Select your preferred AI provider"
        )
        
        # Save new provider and its index
        if selected_provider:
            params['model_id'] = selected_provider
            params['provider_index'] = list(MODEL_OPTIONS.keys()).index(selected_provider)
            st.success(f"Selected Model: {MODEL_OPTIONS[selected_provider]}")

    # Credentials Status Section
    with st.container(border=True):
        st.subheader("🔐 Credentials Status")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if selected_provider == "OpenAI":
                openai_key = os.getenv("OPENAI_API_KEY")
                if openai_key:
                    st.success("✅ OpenAI API Key loaded")
                else:
                    st.error("❌ OpenAI API Key not found in .env")
                    st.info("Add OPENAI_API_KEY to your .env file")
                    
        with col2:
            if selected_provider == "Azure OpenAI":
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
                    st.info("Add the missing variables to your .env file")

    # Model Parameters Section
    with st.container(border=True):
        st.subheader("⚙️ Model Parameters")
        
        col1, col2 = st.columns(2)
        
        with col1:
            params['max_tokens'] = st.number_input(
                "Max tokens",
                min_value=1024,
                max_value=10240,
                value=params.get('max_tokens', 4096),
                step=512,
                help="Maximum number of tokens in the response"
            )
            
        with col2:
            params['temperature'] = st.slider(
                "Temperature", 
                0.0, 
                1.0, 
                step=0.05, 
                value=params.get('temperature', 1.0),
                help="Controls randomness: 0.0 = deterministic, 1.0 = creative"
            )

    # Environment Variables Guide
    with st.expander("📋 Environment Variables Guide", expanded=False):
        st.markdown("""
        ### Required Environment Variables
        
        Create a `.env` file in your project root with:
        
        **For OpenAI:**
        ```
        OPENAI_API_KEY=your_openai_api_key_here
        ```
        
        **For Azure OpenAI:**
        ```
        AZURE_API_KEY=your_azure_api_key
        AZURE_ENDPOINT=https://your-endpoint.openai.azure.com/
        AZURE_DEPLOYMENT=your_deployment_name
        AZURE_API_VERSION=2023-12-01-preview
        ```
        
        **For MCP Servers:**
        ```
        # Neo4j Configuration
        NEO4J_URI=bolt://localhost:7687
        NEO4J_USERNAME=neo4j
        NEO4J_PASSWORD=your_password
        NEO4J_DATABASE=neo4j
        
        # HubSpot Configuration
        PRIVATE_APP_ACCESS_TOKEN=your_hubspot_token
        
        # MSSQL Configuration
        MSSQL_HOST=localhost
        MSSQL_USER=your_username
        MSSQL_PASSWORD=your_password
        MSSQL_DATABASE=your_database
        MSSQL_DRIVER=ODBC Driver 18 for SQL Server
        TrustServerCertificate=yes
        Trusted_Connection=no
        ```
        """)


def create_connection_tab():
    """Create the Connections tab content."""
    st.header("🔌 MCP Server Connections")
    st.markdown("Manage connections to your Model Context Protocol servers.")
    
    # Current Connection Status
    with st.container(border=True):
        st.subheader("📊 Connection Status")
        
        if st.session_state.get("agent"):
            st.success(f"🟢 Connected to {len(st.session_state.servers)} MCP servers")
            st.info(f"🔧 Found {len(st.session_state.tools)} available tools")
            
            # Connection details
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Connected Servers", len(st.session_state.servers))
            with col2:
                st.metric("Available Tools", len(st.session_state.tools))
            with col3:
                # Count tools by server type
                neo4j_tools = len([tool for tool in st.session_state.tools if 'neo4j' in tool.name.lower()])
                hubspot_tools = len([tool for tool in st.session_state.tools if 'hubspot' in tool.name.lower()])
                mssql_tools = len([tool for tool in st.session_state.tools if any(keyword in tool.name.lower() for keyword in ['sql', 'mssql', 'execute_sql', 'list_tables'])])
                other_tools = len(st.session_state.tools) - neo4j_tools - hubspot_tools - mssql_tools
                
                if mssql_tools > 0:
                    st.metric("MSSQL Tools", mssql_tools)
                elif other_tools > 0:
                    st.metric("Other Tools", other_tools)
                
        else:
            st.warning("🟡 Not connected to MCP servers")
            st.info("Click 'Connect to MCP Servers' below to establish connections")

    # Server Configuration
    with st.container(border=True):
        st.subheader("🖥️ Server Configuration")
        
        # Display configured servers
        for name, config in st.session_state.servers.items():
            with st.expander(f"📡 {name} Server", expanded=False):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"**URL:** `{config['url']}`")
                    st.markdown(f"**Transport:** {config['transport']}")
                    st.markdown(f"**Timeout:** {config['timeout']}s")
                    st.markdown(f"**SSE Read Timeout:** {config['sse_read_timeout']}s")
                    
                    # Add server-specific info
                    if name == "Neo4j":
                        st.markdown("**Type:** Graph Database")
                        st.markdown("**Operations:** Cypher queries, schema discovery")
                    elif name == "HubSpot":
                        st.markdown("**Type:** CRM System")
                        st.markdown("**Operations:** Contacts, companies, deals, tickets")
                    elif name == "MSSQL":
                        st.markdown("**Type:** SQL Database")
                        st.markdown("**Operations:** SQL queries, table operations")
                
                with col2:
                    if st.button(f"🗑️ Remove", key=f"remove_{name}"):
                        del st.session_state.servers[name]
                        if st.session_state.get("agent"):
                            reset_connection_state()
                        st.rerun()

    # Connection Controls
    with st.container(border=True):
        st.subheader("🎛️ Connection Controls")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if not st.session_state.get("agent"):
                if st.button("🔗 Connect to MCP Servers", type="primary", use_container_width=True):
                    with st.spinner("🔄 Connecting to MCP servers..."):
                        try:
                            connect_to_mcp_servers()
                            st.success("✅ Successfully connected to MCP servers!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error connecting to MCP servers: {str(e)}")
                            with st.expander("🐛 Error Details"):
                                st.code(traceback.format_exc(), language="python")
            else:
                st.success("✅ Already connected")
        
        with col2:
            if st.session_state.get("agent"):
                if st.button("🔌 Disconnect from MCP Servers", use_container_width=True):
                    with st.spinner("🔄 Disconnecting from MCP servers..."):
                        try:
                            reset_connection_state()
                            st.success("✅ Successfully disconnected!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error disconnecting: {str(e)}")
                            with st.expander("🐛 Error Details"):
                                st.code(traceback.format_exc(), language="python")
            else:
                st.info("No active connections")

    # Server Health Check
    with st.container(border=True):
        st.subheader("🏥 Server Health Check")
        
        if st.button("🔍 Check Server Health", use_container_width=True):
            for name, config in st.session_state.servers.items():
                # Extract base URL for health check
                base_url = config['url'].replace('/sse', '/health')
                
                try:
                    import requests
                    response = requests.get(base_url, timeout=5)
                    if response.status_code == 200:
                        st.success(f"✅ {name}: Healthy (Status: {response.status_code})")
                    else:
                        st.warning(f"⚠️ {name}: Status {response.status_code}")
                except Exception as e:
                    st.error(f"❌ {name}: Connection failed - {str(e)}")

    # Troubleshooting Guide
    with st.expander("🛠️ Troubleshooting Guide", expanded=False):
        st.markdown("""
        ### Common Connection Issues
        
        **🔴 Connection Failed:**
        - Ensure MCP servers are running
        - Check if ports 8003 (Neo4j), 8004 (HubSpot), and 8008 (MSSQL) are accessible
        - Verify server URLs in `servers_config.json`
        
        **🟡 Authentication Issues:**
        - Check NEO4J_PASSWORD in .env file
        - Verify PRIVATE_APP_ACCESS_TOKEN for HubSpot
        - Check MSSQL_USER and MSSQL_PASSWORD for MSSQL server
        - Ensure tokens have required permissions
        
        **🟠 Timeout Issues:**
        - Increase timeout values in server configuration
        - Check network connectivity
        - Verify server performance
        
        **🔵 Tool Loading Issues:**
        - Restart MCP servers
        - Check server logs for errors
        - Verify server implementation
        
        **🟣 MSSQL Specific Issues:**
        - Verify ODBC driver is installed
        - Check SQL Server connectivity
        - Ensure TrustServerCertificate is set correctly
        - Verify database permissions
        """)


def create_tools_tab():
    """Create the Tools tab content."""
    st.header("🧰 Available Tools")
    st.markdown("Explore and understand the available MCP tools and their parameters.")
    
    if not st.session_state.tools:
        st.warning("🔧 No tools available. Please connect to MCP servers first.")
        st.info("👉 Go to the **Connections** tab to establish server connections.")
        return
    
    # Tools Overview
    with st.container(border=True):
        st.subheader("📊 Tools Overview")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Tools", len(st.session_state.tools))
        
        # Count tools by server (based on tool name prefixes/keywords)
        neo4j_tools = len([tool for tool in st.session_state.tools if 'neo4j' in tool.name.lower()])
        hubspot_tools = len([tool for tool in st.session_state.tools if 'hubspot' in tool.name.lower()])
        mssql_tools = len([tool for tool in st.session_state.tools if any(keyword in tool.name.lower() for keyword in ['sql', 'mssql', 'execute_sql', 'list_tables'])])
        other_tools = len(st.session_state.tools) - neo4j_tools - hubspot_tools - mssql_tools
        
        with col2:
            st.metric("Neo4j Tools", neo4j_tools)
        
        with col3:
            st.metric("HubSpot Tools", hubspot_tools)
            
        with col4:
            st.metric("MSSQL Tools", mssql_tools)
        
        if other_tools > 0:
            st.metric("Other Tools", other_tools)

    # Tool Categories
    st.subheader("🗂️ Tools by Category")
    
    # Create tabs for different tool categories
    neo4j_tab, hubspot_tab, mssql_tab, all_tab = st.tabs(["🗄️ Neo4j Tools", "🏢 HubSpot Tools", "🗃️ MSSQL Tools", "📋 All Tools"])
    
    with neo4j_tab:
        display_tools_category("neo4j", "Neo4j Database Operations")
    
    with hubspot_tab:
        display_tools_category("hubspot", "HubSpot CRM Operations")
        
    with mssql_tab:
        display_tools_category_mssql("MSSQL Database Operations")
    
    with all_tab:
        display_all_tools()


def display_tools_category(category_filter, category_title):
    """Display tools for a specific category."""
    filtered_tools = [tool for tool in st.session_state.tools if category_filter in tool.name.lower()]
    
    if not filtered_tools:
        st.info(f"No {category_filter} tools available.")
        return
    
    st.markdown(f"### {category_title}")
    st.write(f"Found **{len(filtered_tools)}** tools in this category.")
    
    # Tool selector
    selected_tool_name = st.selectbox(
        "Select a Tool",
        options=[tool.name for tool in filtered_tools],
        index=0,
        key=f"{category_filter}_tool_selector"
    )
    
    if selected_tool_name:
        selected_tool = next(
            (tool for tool in filtered_tools if tool.name == selected_tool_name),
            None
        )
        
        if selected_tool:
            display_tool_details(selected_tool)


def display_tools_category_mssql(category_title):
    """Display MSSQL tools specifically."""
    # Filter for MSSQL tools by looking for SQL-related keywords
    mssql_keywords = ['sql', 'mssql', 'execute_sql', 'list_tables']
    filtered_tools = [tool for tool in st.session_state.tools if any(keyword in tool.name.lower() for keyword in mssql_keywords)]
    
    if not filtered_tools:
        st.info("No MSSQL tools available.")
        return
    
    st.markdown(f"### {category_title}")
    st.write(f"Found **{len(filtered_tools)}** tools in this category.")
    
    # Tool selector
    selected_tool_name = st.selectbox(
        "Select a Tool",
        options=[tool.name for tool in filtered_tools],
        index=0,
        key="mssql_tool_selector"
    )
    
    if selected_tool_name:
        selected_tool = next(
            (tool for tool in filtered_tools if tool.name == selected_tool_name),
            None
        )
        
        if selected_tool:
            display_tool_details(selected_tool)


def display_all_tools():
    """Display all available tools."""
    st.markdown("### All Available Tools")
    st.write(f"Total of **{len(st.session_state.tools)}** tools available.")
    
    # Search functionality
    search_term = st.text_input("🔍 Search tools", placeholder="Enter tool name or description...")
    
    if search_term:
        filtered_tools = [
            tool for tool in st.session_state.tools 
            if search_term.lower() in tool.name.lower() or 
               search_term.lower() in tool.description.lower()
        ]
    else:
        filtered_tools = st.session_state.tools
    
    if not filtered_tools:
        st.warning("No tools match your search criteria.")
        return
    
    # Tool selector
    selected_tool_name = st.selectbox(
        "Select a Tool",
        options=[tool.name for tool in filtered_tools],
        index=0,
        key="all_tools_selector"
    )
    
    if selected_tool_name:
        selected_tool = next(
            (tool for tool in filtered_tools if tool.name == selected_tool_name),
            None
        )
        
        if selected_tool:
            display_tool_details(selected_tool)


def display_tool_details(tool):
    """Display detailed information about a specific tool."""
    with st.container(border=True):
        st.subheader(f"🔧 {tool.name}")
        
        # Description
        st.markdown("**Description:**")
        st.write(tool.description)
        
        # Parameters
        parameters = extract_tool_parameters(tool)
        
        if parameters:
            st.markdown("**Parameters:**")
            for param in parameters:
                st.code(param)
        else:
            st.info("This tool doesn't require any parameters.")
        
        # Additional details if available
        if hasattr(tool, 'args_schema'):
            with st.expander("📋 Raw Schema", expanded=False):
                schema = tool.args_schema
                if isinstance(schema, dict):
                    st.json(schema)
                else:
                    st.json(schema.schema())
        
        # Usage example
        st.markdown("**Usage Example:**")
        st.code(f'Ask the AI: "Use the {tool.name} tool to..."', language="text")
        
        # Tool category badge
        if 'neo4j' in tool.name.lower():
            st.success("🗄️ Neo4j Database Tool")
        elif 'hubspot' in tool.name.lower():
            st.info("🏢 HubSpot CRM Tool")
        elif any(keyword in tool.name.lower() for keyword in ['sql', 'mssql', 'execute_sql', 'list_tables']):
            st.warning("🗃️ MSSQL Database Tool")
        else:
            st.secondary("🔧 General Tool")