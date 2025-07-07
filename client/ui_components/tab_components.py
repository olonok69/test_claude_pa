# Fixed ui_components/tab_components.py - Updated with Firecrawl tools

import streamlit as st
from config import MODEL_OPTIONS
import traceback
import os
from services.mcp_service import (
    connect_to_mcp_servers,
    test_stdio_server,
    get_resources_from_client,
)
from utils.tool_schema_parser import extract_tool_parameters
from utils.async_helpers import reset_connection_state, run_async


def create_configuration_tab():
    """Create the Configuration tab content."""
    # Import the enhanced configuration function
    from ui_components.enhanced_config import create_enhanced_configuration_tab

    # Check if enhanced mode is enabled
    enhanced_mode = st.session_state.get("enhanced_config_mode", False)

    # Mode toggle
    col1, col2 = st.columns([3, 1])
    with col1:
        st.header("⚙️ Configuration")
    with col2:
        enhanced_mode = st.toggle(
            "Enhanced Mode",
            value=enhanced_mode,
            help="Enable enhanced configuration with multiple provider support",
        )
        st.session_state["enhanced_config_mode"] = enhanced_mode

    if enhanced_mode:
        # Use enhanced configuration
        create_enhanced_configuration_tab()
    else:
        # Use original simple configuration
        create_simple_configuration_tab()


def create_simple_configuration_tab():
    """Create the original simple Configuration tab content."""
    st.markdown("Configure your AI provider and model parameters.")

    # Provider Configuration Section
    with st.container(border=True):
        st.subheader("🔎 AI Provider Selection")

        params = st.session_state.setdefault("params", {})

        # Load previously selected provider or default to the first
        default_provider = params.get("model_id", list(MODEL_OPTIONS.keys())[0])
        default_index = list(MODEL_OPTIONS.keys()).index(default_provider)

        # Provider selector with synced state
        selected_provider = st.selectbox(
            "Choose Provider",
            options=list(MODEL_OPTIONS.keys()),
            index=default_index,
            key="provider_selection_tab",
            on_change=reset_connection_state,
            help="Select your preferred AI provider",
        )

        # Save new provider and its index
        if selected_provider:
            params["model_id"] = selected_provider
            params["provider_index"] = list(MODEL_OPTIONS.keys()).index(
                selected_provider
            )
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
                    # Use container instead of expander to avoid nesting
                    if st.checkbox(
                        "Show Azure Config Details", key="show_azure_details"
                    ):
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
            params["max_tokens"] = st.number_input(
                "Max tokens",
                min_value=1024,
                max_value=10240,
                value=params.get("max_tokens", 4096),
                step=512,
                help="Maximum number of tokens in the response",
            )

        with col2:
            params["temperature"] = st.slider(
                "Temperature",
                0.0,
                1.0,
                step=0.05,
                value=params.get("temperature", 1.0),
                help="Controls randomness: 0.0 = deterministic, 1.0 = creative",
            )

    # Environment Variables Guide - Use checkbox instead of expander
    show_env_guide = st.checkbox(
        "📋 Show Environment Variables Guide", key="show_env_guide"
    )
    if show_env_guide:
        st.markdown(
            """
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
        
        **For Firecrawl MCP Server:**
        ```
        # Firecrawl Configuration
        FIRECRAWL_API_KEY=your_firecrawl_api_key
        FIRECRAWL_API_URL=https://api.firecrawl.dev  # Optional: for self-hosted instances
        ```
        
        **For Google Search MCP Server:**
        ```
        # Google Search Configuration
        GOOGLE_API_KEY=your_google_api_key
        GOOGLE_SEARCH_ENGINE_ID=your_custom_search_engine_id
        ```
        """
        )

    # Upgrade notice
    with st.container(border=True):
        st.info(
            "💡 **Want more providers and advanced features?** Enable **Enhanced Mode** above for support of Anthropic Claude, Google Gemini, Cohere, Mistral AI, and local Ollama models!"
        )


def create_connection_tab():
    """Create the Connections tab content."""
    st.header("🔌 MCP Server Connections")
    st.markdown("Manage connections to your Firecrawl and Google Search MCP servers.")

    # Current Connection Status
    with st.container(border=True):
        st.subheader("📊 Connection Status")

        if st.session_state.get("agent"):
            st.success(f"🟢 Connected to {len(st.session_state.servers)} MCP server(s)")

            # Categorize tools
            firecrawl_tools, google_search_tools, other_tools = categorize_tools(
                st.session_state.get("tools", [])
            )

            # Check for prompts and resources
            prompts_count = len(st.session_state.get("prompts", []))
            resources_count = len(st.session_state.get("resources", []))

            # Connection details - Enhanced metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Connected Servers", len(st.session_state.servers))
            with col2:
                st.metric("Total Tools", len(st.session_state.get("tools", [])))
            with col3:
                st.metric("Available Prompts", prompts_count)
            with col4:
                st.metric("Available Resources", resources_count)

            # Tool breakdown
            st.metric("🔥 Firecrawl Tools", len(firecrawl_tools))
            st.metric("🔍 Google Search Tools", len(google_search_tools))
            if other_tools:
                st.metric("🔧 Other Tools", len(other_tools))

        else:
            st.warning("🟡 Not connected to MCP servers")
            st.info("Click 'Connect to MCP Servers' below to establish connections")

    # Server Configuration - Use checkbox instead of nested expanders
    with st.container(border=True):
        st.subheader("🖥️ Server Configuration")

        show_server_details = st.checkbox(
            "Show Server Details", key="show_server_details"
        )
        if show_server_details:
            # Display configured servers
            for name, config in st.session_state.servers.items():
                st.markdown(f"### 📡 {name} Server")

                col1, col2 = st.columns([3, 1])

                with col1:
                    transport_type = config.get("transport", "unknown")
                    st.markdown(f"**Transport:** {transport_type}")

                    if transport_type == "sse":
                        st.markdown(f"**URL:** `{config['url']}`")
                        st.markdown(f"**Timeout:** {config['timeout']}s")
                        st.markdown(
                            f"**SSE Read Timeout:** {config['sse_read_timeout']}s"
                        )

                    # Add server-specific info
                    if name == "Firecrawl":
                        st.markdown("**Type:** Web Scraping & Content Extraction")
                        st.markdown(
                            "**Operations:** Web scraping, batch scraping, crawling, content extraction, map discovery"
                        )
                    elif name == "Google Search":
                        st.markdown("**Type:** Web Search Engine")
                        st.markdown(
                            "**Operations:** Web search, webpage content extraction"
                        )

                with col2:
                    if st.button(f"🗑️ Remove {name}", key=f"remove_{name}"):
                        del st.session_state.servers[name]
                        if st.session_state.get("agent"):
                            reset_connection_state()
                        st.rerun()

                st.divider()

    # Connection Controls
    with st.container(border=True):
        st.subheader("🎛️ Connection Controls")

        col1, col2 = st.columns(2)

        with col1:
            if not st.session_state.get("agent"):
                if st.button(
                    "🔗 Connect to MCP Servers",
                    type="primary",
                    use_container_width=True,
                ):
                    with st.spinner("🔄 Connecting to MCP servers..."):
                        try:
                            connect_to_mcp_servers()
                            st.success("✅ Successfully connected to MCP servers!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error connecting to MCP servers: {str(e)}")
                            show_error_details = st.checkbox(
                                "🐛 Show Error Details", key="show_connection_error"
                            )
                            if show_error_details:
                                st.code(traceback.format_exc(), language="python")
            else:
                st.success("✅ Already connected")

        with col2:
            if st.session_state.get("agent"):
                if st.button(
                    "🔌 Disconnect from MCP Servers", use_container_width=True
                ):
                    with st.spinner("🔄 Disconnecting from MCP servers..."):
                        try:
                            reset_connection_state()
                            st.success("✅ Successfully disconnected!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error disconnecting: {str(e)}")
                            show_error_details = st.checkbox(
                                "🐛 Show Error Details", key="show_disconnect_error"
                            )
                            if show_error_details:
                                st.code(traceback.format_exc(), language="python")
            else:
                st.info("No active connections")


def create_tools_tab():
    """Create the Tools tab content with resources and prompts support."""
    st.header("🧰 Available Tools, Resources & Prompts")
    st.markdown(
        "Explore available Firecrawl and Google Search tools, resources, and prompts."
    )

    # Check if we have tools, prompts, or resources
    has_tools = bool(st.session_state.get("tools"))
    has_prompts = bool(st.session_state.get("prompts"))
    has_resources = bool(st.session_state.get("resources"))

    if not has_tools and not has_prompts and not has_resources:
        st.warning(
            "🔧 No tools, resources, or prompts available. Please connect to the MCP servers first."
        )
        st.info("👉 Go to the **Connections** tab to establish server connections.")
        return

    # Overview section
    with st.container(border=True):
        st.subheader("📊 Overview")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Tools", len(st.session_state.get("tools", [])))
        with col2:
            st.metric("Available Prompts", len(st.session_state.get("prompts", [])))
        with col3:
            st.metric("Available Resources", len(st.session_state.get("resources", [])))
        with col4:
            total_items = (
                len(st.session_state.get("tools", []))
                + len(st.session_state.get("prompts", []))
                + len(st.session_state.get("resources", []))
            )
            st.metric("Total Items", total_items)

    # Create main tabs for different categories
    main_tabs = []
    tab_names = []

    if has_tools:
        # Categorize tools
        firecrawl_tools, google_search_tools, other_tools = categorize_tools(
            st.session_state.get("tools", [])
        )

        # Tool category tabs
        if firecrawl_tools:
            tab_names.append("🔥 Firecrawl")
        if google_search_tools:
            tab_names.append("🔍 Google Search")
        if other_tools:
            tab_names.append("🔧 Other Tools")

    # Add tabs for prompts and resources
    if has_prompts:
        tab_names.append("📝 Prompts")
    if has_resources:
        tab_names.append("📁 Resources")

    # Add overview tab
    tab_names.append("📋 All Items")

    # Create the actual tabs
    if tab_names:
        tabs = st.tabs(tab_names)
        tab_index = 0

        # Tool tabs
        if has_tools:
            firecrawl_tools, google_search_tools, other_tools = categorize_tools(
                st.session_state.get("tools", [])
            )

            if firecrawl_tools:
                with tabs[tab_index]:
                    display_tools_list(
                        firecrawl_tools, "Firecrawl Operations", "firecrawl"
                    )
                tab_index += 1

            if google_search_tools:
                with tabs[tab_index]:
                    display_tools_list(
                        google_search_tools, "Google Search Operations", "google_search"
                    )
                tab_index += 1

            if other_tools:
                with tabs[tab_index]:
                    display_tools_list(
                        other_tools, "Other Available Tools", "other_tools"
                    )
                tab_index += 1

        # Prompts tab
        if has_prompts:
            with tabs[tab_index]:
                display_prompts_list()
            tab_index += 1

        # Resources tab
        if has_resources:
            with tabs[tab_index]:
                display_resources_list()
            tab_index += 1

        # All items tab
        with tabs[tab_index]:
            display_all_items()


def categorize_tools(tools):
    """Categorize tools by server type."""
    firecrawl_tools = []
    google_search_tools = []
    other_tools = []

    for tool in tools:
        tool_name = tool.name.lower()

        # Firecrawl tools
        if any(
            keyword in tool_name
            for keyword in [
                "firecrawl",
                "scrape",
                "batch_scrape",
                "crawl",
                "map",
                "extract",
                "deep_research",
                "llmstxt",
                "check_crawl_status",
                "check_batch_status",
            ]
        ):
            firecrawl_tools.append(tool)
        # Google Search tools
        elif any(
            keyword in tool_name
            for keyword in ["google-search", "read-webpage", "google_search", "webpage"]
        ):
            google_search_tools.append(tool)
        else:
            other_tools.append(tool)

    return firecrawl_tools, google_search_tools, other_tools


def display_tools_list(tools_list, category_title, category_key):
    """Display tools for a specific category."""
    if not tools_list:
        st.info(f"No {category_title.lower()} available.")
        return

    st.markdown(f"### {category_title}")
    st.write(f"Found **{len(tools_list)}** tools in this category.")

    # Tool selector
    selected_tool_name = st.selectbox(
        "Select a Tool",
        options=[tool.name for tool in tools_list],
        index=0,
        key=f"{category_key}_tool_selector",
    )

    if selected_tool_name:
        selected_tool = next(
            (tool for tool in tools_list if tool.name == selected_tool_name), None
        )

        if selected_tool:
            display_tool_details(selected_tool)


def display_prompts_list():
    """Display available prompts."""
    prompts = st.session_state.get("prompts", [])

    if not prompts:
        st.info("No prompts available.")
        return

    st.markdown("### Available Prompts")
    st.write(f"Found **{len(prompts)}** prompts.")

    # Prompt selector
    prompt_names = []
    for prompt in prompts:
        if hasattr(prompt, "name"):
            prompt_names.append(prompt.name)
        else:
            prompt_names.append(str(prompt))

    if prompt_names:
        selected_prompt_name = st.selectbox(
            "Select a Prompt", options=prompt_names, index=0, key="prompt_selector"
        )

        if selected_prompt_name:
            selected_prompt = next(
                (
                    prompt
                    for prompt in prompts
                    if (hasattr(prompt, "name") and prompt.name == selected_prompt_name)
                    or str(prompt) == selected_prompt_name
                ),
                None,
            )

            if selected_prompt:
                display_prompt_details(selected_prompt)


def display_resources_list():
    """Display available resources."""
    resources = st.session_state.get("resources", [])

    if not resources:
        st.info("No resources available.")
        return

    st.markdown("### Available Resources")
    st.write(f"Found **{len(resources)}** resources.")

    # Resource selector
    resource_names = []
    for resource in resources:
        if hasattr(resource, "name"):
            resource_names.append(resource.name)
        else:
            resource_names.append(str(resource))

    if resource_names:
        selected_resource_name = st.selectbox(
            "Select a Resource",
            options=resource_names,
            index=0,
            key="resource_selector",
        )

        if selected_resource_name:
            selected_resource = next(
                (
                    resource
                    for resource in resources
                    if (
                        hasattr(resource, "name")
                        and resource.name == selected_resource_name
                    )
                    or str(resource) == selected_resource_name
                ),
                None,
            )

            if selected_resource:
                display_resource_details(selected_resource)


def display_all_items():
    """Display all available tools, prompts, and resources."""
    st.markdown("### All Available Items")

    tools = st.session_state.get("tools", [])
    prompts = st.session_state.get("prompts", [])
    resources = st.session_state.get("resources", [])

    total_items = len(tools) + len(prompts) + len(resources)
    st.write(f"Total of **{total_items}** items available.")

    # Search functionality
    search_term = st.text_input(
        "🔍 Search tools, prompts, and resources",
        placeholder="Enter name or description...",
    )

    # Filter items based on search
    filtered_tools = []
    filtered_prompts = []
    filtered_resources = []

    if search_term:
        search_lower = search_term.lower()

        # Filter tools
        filtered_tools = [
            tool
            for tool in tools
            if search_lower in tool.name.lower()
            or (
                hasattr(tool, "description")
                and tool.description
                and search_lower in tool.description.lower()
            )
        ]

        # Filter prompts
        filtered_prompts = [
            prompt
            for prompt in prompts
            if (hasattr(prompt, "name") and search_lower in prompt.name.lower())
            or (
                hasattr(prompt, "description")
                and prompt.description
                and search_lower in prompt.description.lower()
            )
        ]

        # Filter resources
        filtered_resources = [
            resource
            for resource in resources
            if (hasattr(resource, "name") and search_lower in resource.name.lower())
            or (
                hasattr(resource, "description")
                and resource.description
                and search_lower in resource.description.lower()
            )
        ]
    else:
        filtered_tools = tools
        filtered_prompts = prompts
        filtered_resources = resources

    total_filtered = (
        len(filtered_tools) + len(filtered_prompts) + len(filtered_resources)
    )

    if total_filtered == 0:
        st.warning("No items match your search criteria.")
        return

    # Display filtered results by category - using containers instead of expanders
    if filtered_tools:
        st.subheader(f"🔧 Tools ({len(filtered_tools)})")
        for i, tool in enumerate(filtered_tools):
            if st.button(f"🔧 {tool.name}", key=f"tool_button_{i}"):
                st.session_state[f"show_tool_{i}"] = not st.session_state.get(
                    f"show_tool_{i}", False
                )

            if st.session_state.get(f"show_tool_{i}", False):
                display_tool_details(tool)

    if filtered_prompts:
        st.subheader(f"📝 Prompts ({len(filtered_prompts)})")
        for i, prompt in enumerate(filtered_prompts):
            prompt_name = prompt.name if hasattr(prompt, "name") else str(prompt)
            if st.button(f"📝 {prompt_name}", key=f"prompt_button_{i}"):
                st.session_state[f"show_prompt_{i}"] = not st.session_state.get(
                    f"show_prompt_{i}", False
                )

            if st.session_state.get(f"show_prompt_{i}", False):
                display_prompt_details(prompt)

    if filtered_resources:
        st.subheader(f"📁 Resources ({len(filtered_resources)})")
        for i, resource in enumerate(filtered_resources):
            resource_name = (
                resource.name if hasattr(resource, "name") else str(resource)
            )
            if st.button(f"📁 {resource_name}", key=f"resource_button_{i}"):
                st.session_state[f"show_resource_{i}"] = not st.session_state.get(
                    f"show_resource_{i}", False
                )

            if st.session_state.get(f"show_resource_{i}", False):
                display_resource_details(resource)


def display_tool_details(tool):
    """Display detailed information about a specific tool."""
    with st.container(border=True):
        st.subheader(f"🔧 {tool.name}")

        # Description
        st.markdown("**Description:**")
        if hasattr(tool, "description") and tool.description:
            st.write(tool.description)
        else:
            st.write("No description available.")

        # Parameters
        parameters = extract_tool_parameters(tool)

        if parameters:
            st.markdown("**Parameters:**")
            for param in parameters:
                st.code(param)
        else:
            st.info("This tool doesn't require any parameters.")

        # Additional details if available - use checkbox instead of expander
        if hasattr(tool, "args_schema"):
            show_schema = st.checkbox(
                "📋 Show Raw Schema", key=f"show_schema_{tool.name}"
            )
            if show_schema:
                schema = tool.args_schema
                if isinstance(schema, dict):
                    st.json(schema)
                else:
                    st.json(
                        schema.schema() if hasattr(schema, "schema") else str(schema)
                    )

        # Usage example
        st.markdown("**Usage Example:**")
        st.code(f'Ask the AI: "Use the {tool.name} tool to..."', language="text")

        # Tool category badge
        tool_name_lower = tool.name.lower()

        if any(
            keyword in tool_name_lower
            for keyword in [
                "firecrawl",
                "scrape",
                "batch_scrape",
                "crawl",
                "map",
                "extract",
                "deep_research",
                "llmstxt",
            ]
        ):
            st.success("🔥 Firecrawl Tool")
        elif any(
            keyword in tool_name_lower
            for keyword in ["google-search", "read-webpage", "google_search", "webpage"]
        ):
            st.success("🔍 Google Search Tool")
        else:
            st.warning("🔧 General Tool")


def display_prompt_details(prompt):
    """Display detailed information about a specific prompt."""
    with st.container(border=True):
        prompt_name = prompt.name if hasattr(prompt, "name") else str(prompt)
        st.subheader(f"📝 {prompt_name}")

        # Description
        if hasattr(prompt, "description") and prompt.description:
            st.markdown("**Description:**")
            st.write(prompt.description)

        # Arguments
        if hasattr(prompt, "arguments") and prompt.arguments:
            st.markdown("**Arguments:**")
            for arg in prompt.arguments:
                required_text = (
                    " (required)" if arg.get("required", False) else " (optional)"
                )
                st.markdown(
                    f"- **{arg.get('name', 'unnamed')}**{required_text}: {arg.get('description', 'No description')}"
                )

        # Usage
        st.markdown("**Usage:**")
        st.code(f'Ask the AI: "Use the {prompt_name} prompt to..."', language="text")


def display_resource_details(resource):
    """Display detailed information about a specific resource."""
    with st.container(border=True):
        resource_name = resource.name if hasattr(resource, "name") else str(resource)
        st.subheader(f"📁 {resource_name}")

        # Description
        if hasattr(resource, "description") and resource.description:
            st.markdown("**Description:**")
            st.write(resource.description)

        # URI
        if hasattr(resource, "uri"):
            st.markdown("**URI:**")
            st.code(resource.uri)

        # MIME Type
        if hasattr(resource, "mimeType"):
            st.markdown("**MIME Type:**")
            st.code(resource.mimeType)

        # Additional properties - use checkbox instead of expander
        if hasattr(resource, "__dict__"):
            other_props = {
                k: v
                for k, v in resource.__dict__.items()
                if k not in ["name", "description", "uri", "mimeType"]
            }
            if other_props:
                show_props = st.checkbox(
                    "📋 Show Additional Properties", key=f"show_props_{resource_name}"
                )
                if show_props:
                    for key, value in other_props.items():
                        st.markdown(f"**{key}:** {value}")

        # Usage
        st.markdown("**Usage:**")
        st.info(
            "This resource can be accessed by the AI when performing relevant operations."
        )
