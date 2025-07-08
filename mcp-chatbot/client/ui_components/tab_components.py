# Fixed section of ui_components/tab_components.py for Configuration tab

import streamlit as st
from config import MODEL_OPTIONS
import traceback
import os
from services.mcp_service import connect_to_mcp_servers
from utils.tool_schema_parser import extract_tool_parameters
from utils.async_helpers import safe_reset_connection_state, handle_provider_change

def create_configuration_tab():
    """Create the Configuration tab content with improved error handling."""
    # Import the enhanced configuration function
    try:
        from ui_components.enhanced_config import create_enhanced_configuration_tab
        enhanced_available = True
    except ImportError:
        enhanced_available = False
    
    # Check if enhanced mode is enabled
    enhanced_mode = st.session_state.get('enhanced_config_mode', False)
    
    # Mode toggle
    col1, col2 = st.columns([3, 1])
    with col1:
        st.header("⚙️ Configuration")
    with col2:
        if enhanced_available:
            enhanced_mode = st.toggle(
                "Enhanced Mode",
                value=enhanced_mode,
                help="Enable enhanced configuration with multiple provider support",
                key="config_enhanced_mode_toggle"
            )
            st.session_state['enhanced_config_mode'] = enhanced_mode
        else:
            st.info("Enhanced mode not available")
    
    if enhanced_mode and enhanced_available:
        # Use enhanced configuration
        create_enhanced_configuration_tab()
    else:
        # Use original simple configuration
        create_simple_configuration_tab()

def create_simple_configuration_tab():
    """Create the original simple Configuration tab content with improved provider handling."""
    st.markdown("Configure your AI provider and model parameters.")
    
    # Provider Configuration Section
    with st.container(border=True):
        st.subheader("🔎 AI Provider Selection")
        
        params = st.session_state.setdefault('params', {})
        
        # Load previously selected provider or default to the first
        default_provider = params.get("model_id", list(MODEL_OPTIONS.keys())[0])
        
        try:
            default_index = list(MODEL_OPTIONS.keys()).index(default_provider)
        except ValueError:
            default_index = 0
            default_provider = list(MODEL_OPTIONS.keys())[0]
        
        # Provider selector with improved change handling
        selected_provider = st.selectbox(
            'Choose Provider',
            options=list(MODEL_OPTIONS.keys()),
            index=default_index,
            key="provider_selection_tab",
            help="Select your preferred AI provider"
        )
        
        # Handle provider change
        if selected_provider != params.get("model_id"):
            handle_provider_change_safely(selected_provider, params)

def handle_provider_change_safely(selected_provider, params):
    """Handle provider change with proper error handling."""
    try:
        # Show loading message
        with st.spinner("🔄 Changing AI provider..."):
            # Update parameters
            params['model_id'] = selected_provider
            params['provider_index'] = list(MODEL_OPTIONS.keys()).index(selected_provider)
            
            # Handle connection reset safely
            handle_provider_change()
            
            # Show success message
            st.success(f"✅ Provider changed to: {MODEL_OPTIONS[selected_provider]}")
            
    except Exception as e:
        st.error(f"❌ Error changing provider: {str(e)}")
        
        # Show detailed error in expander
        with st.expander("🐛 Error Details", expanded=False):
            st.code(traceback.format_exc())
        
        # Try to recover by resetting everything
        try:
            safe_reset_connection_state()
            st.warning("⚠️ Connections reset. Please reconnect in the Connections tab.")
        except Exception as recovery_error:
            st.error(f"❌ Recovery failed: {str(recovery_error)}")

def create_provider_credentials_section(selected_provider):
    """Create the credentials status section with improved error handling."""
    st.subheader("🔐 Credentials Status")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if selected_provider == "OpenAI":
            try:
                openai_key = os.getenv("OPENAI_API_KEY")
                if openai_key:
                    st.success("✅ OpenAI API Key loaded")
                    # Show partial key for verification
                    masked_key = f"{openai_key[:8]}...{openai_key[-4:]}" if len(openai_key) > 12 else "***"
                    st.caption(f"Key: {masked_key}")
                else:
                    st.error("❌ OpenAI API Key not found in .env")
                    st.info("Add OPENAI_API_KEY to your .env file")
            except Exception as e:
                st.error(f"❌ Error checking OpenAI credentials: {str(e)}")
                    
    with col2:
        if selected_provider == "Azure OpenAI":
            try:
                azure_key = os.getenv("AZURE_API_KEY")
                azure_endpoint = os.getenv("AZURE_ENDPOINT")
                azure_deployment = os.getenv("AZURE_DEPLOYMENT")
                azure_version = os.getenv("AZURE_API_VERSION")
                
                if all([azure_key, azure_endpoint, azure_deployment, azure_version]):
                    st.success("✅ Azure OpenAI configuration loaded")
                    
                    # Show configuration details
                    if st.checkbox("Show Azure Config Details", key="show_azure_config_details"):
                        st.text(f"Endpoint: {azure_endpoint}")
                        st.text(f"Deployment: {azure_deployment}")
                        st.text(f"API Version: {azure_version}")
                        
                        # Show masked key
                        if azure_key:
                            masked_key = f"{azure_key[:8]}...{azure_key[-4:]}" if len(azure_key) > 12 else "***"
                            st.text(f"Key: {masked_key}")
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
            except Exception as e:
                st.error(f"❌ Error checking Azure credentials: {str(e)}")

def create_model_parameters_section(params):
    """Create the model parameters section with validation."""
    st.subheader("⚙️ Model Parameters")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Max tokens with validation
        try:
            current_max_tokens = params.get('max_tokens', 4096)
            max_tokens = st.number_input(
                "Max tokens",
                min_value=512,
                max_value=32000,
                value=current_max_tokens,
                step=512,
                help="Maximum number of tokens in the response",
                key="config_max_tokens"
            )
            params['max_tokens'] = max_tokens
        except Exception as e:
            st.error(f"Error with max tokens: {str(e)}")
            params['max_tokens'] = 4096
            
    with col2:
        # Temperature with validation
        try:
            current_temperature = params.get('temperature', 1.0)
            temperature = st.slider(
                "Temperature", 
                0.0, 
                2.0, 
                step=0.05, 
                value=current_temperature,
                help="Controls randomness: 0.0 = deterministic, 2.0 = very creative",
                key="config_temperature"
            )
            params['temperature'] = temperature
        except Exception as e:
            st.error(f"Error with temperature: {str(e)}")
            params['temperature'] = 1.0

def create_connection_test_section(selected_provider):
    """Create connection test section."""
    st.subheader("🧪 Test Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        test_button = st.button(
            "🔍 Test AI Provider Connection",
            type="secondary",
            use_container_width=True,
            help="Test if the AI provider credentials are working"
        )
        
        if test_button:
            test_ai_provider_connection(selected_provider)
    
    with col2:
        if st.session_state.get("agent"):
            st.success("🟢 MCP Agent Connected")
            
            test_full_button = st.button(
                "🔄 Test Full Pipeline",
                type="primary",
                use_container_width=True,
                help="Test AI provider + MCP connection"
            )
            
            if test_full_button:
                test_full_pipeline(selected_provider)
        else:
            st.info("🔌 Connect to MCP servers first")

def test_ai_provider_connection(provider):
    """Test AI provider connection."""
    try:
        with st.spinner(f"Testing {provider} connection..."):
            from services.ai_service import create_llm_model
            
            # Get current parameters
            params = st.session_state.get('params', {})
            
            # Try to create LLM model
            llm = create_llm_model(provider, 
                                 temperature=params.get('temperature', 0.7),
                                 max_tokens=min(params.get('max_tokens', 4096), 100))  # Limit for test
            
            # Simple test message
            from langchain_core.messages import HumanMessage
            test_message = HumanMessage(content="Hello, this is a test. Please respond with 'Test successful'.")
            
            response = llm.invoke([test_message])
            
            if response and hasattr(response, 'content'):
                st.success(f"✅ {provider} connection successful!")
                st.info(f"Response: {response.content[:100]}...")
            else:
                st.warning("⚠️ Connection established but response format unexpected")
                
    except Exception as e:
        st.error(f"❌ {provider} connection failed: {str(e)}")
        
        # Show troubleshooting tips
        with st.expander("🔧 Troubleshooting Tips"):
            if provider == "OpenAI":
                st.markdown("""
                **Common OpenAI issues:**
                - Check if OPENAI_API_KEY is set correctly
                - Verify API key has sufficient credits
                - Ensure no rate limiting is active
                """)
            elif provider == "Azure OpenAI":
                st.markdown("""
                **Common Azure OpenAI issues:**
                - Verify all Azure environment variables are set
                - Check deployment name matches your Azure setup
                - Ensure endpoint URL is correct
                - Verify API version is supported
                """)

def test_full_pipeline(provider):
    """Test the full AI + MCP pipeline."""
    try:
        with st.spinner("Testing full pipeline..."):
            # Test if we can get tools
            tools = st.session_state.get("tools", [])
            if not tools:
                st.error("❌ No MCP tools available")
                return
            
            # Test a simple query
            from services.chat_service import ChatService
            chat_service = ChatService()
            
            test_query = "List the available tools"
            response = chat_service.process_message(test_query)
            
            if response and "error" not in response.lower():
                st.success("✅ Full pipeline test successful!")
                st.info(f"Response preview: {response[:200]}...")
            else:
                st.warning("⚠️ Pipeline test completed but response may indicate issues")
                st.text(f"Response: {response[:500]}...")
                
    except Exception as e:
        st.error(f"❌ Full pipeline test failed: {str(e)}")
        st.info("💡 Try reconnecting to MCP servers in the Connections tab")

# Update the main configuration function to use the improved sections
def create_simple_configuration_tab_complete():
    """Complete simple configuration tab with all improved sections."""
    st.markdown("Configure your AI provider and model parameters.")
    
    # Provider Configuration Section
    with st.container(border=True):
        st.subheader("🔎 AI Provider Selection")
        
        params = st.session_state.setdefault('params', {})
        
        # Load previously selected provider or default to the first
        default_provider = params.get("model_id", list(MODEL_OPTIONS.keys())[0])
        
        try:
            default_index = list(MODEL_OPTIONS.keys()).index(default_provider)
        except ValueError:
            default_index = 0
            default_provider = list(MODEL_OPTIONS.keys())[0]
        
        # Provider selector with improved change handling
        selected_provider = st.selectbox(
            'Choose Provider',
            options=list(MODEL_OPTIONS.keys()),
            index=default_index,
            key="provider_selection_tab",
            help="Select your preferred AI provider"
        )
        
        # Handle provider change
        if selected_provider != params.get("model_id"):
            handle_provider_change_safely(selected_provider, params)
        else:
            # Show current selection
            st.success(f"Selected Model: {MODEL_OPTIONS[selected_provider]}")

    # Credentials Status Section
    with st.container(border=True):
        create_provider_credentials_section(selected_provider)

    # Model Parameters Section
    with st.container(border=True):
        create_model_parameters_section(params)

    # Connection Test Section
    with st.container(border=True):
        create_connection_test_section(selected_provider)

    # Environment Variables Guide
    show_env_guide = st.checkbox("📋 Show Environment Variables Guide", key="config_show_env_guide")
    if show_env_guide:
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
        
        **For MSSQL Server:**
        ```
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

    # Upgrade notice
    with st.container(border=True):
        st.info("💡 **Want more providers and advanced features?** Enable **Enhanced Mode** above for support of Anthropic Claude, Google Gemini, Cohere, Mistral AI, and local Ollama models!")

# Make sure to use the complete version
def create_simple_configuration_tab():
    """Use the complete improved configuration tab."""
    create_simple_configuration_tab_complete()