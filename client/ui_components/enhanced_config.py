# Fixed ui_components/enhanced_config.py for mcp-chatbot

import streamlit as st
import os
import json
from datetime import datetime
import traceback
from utils.async_helpers import reset_connection_state

# Enhanced model configuration with O3/O3-mini support
EXTENDED_MODEL_OPTIONS = {
    'OpenAI': {
        'models': ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'gpt-3.5-turbo', 'o3-mini', 'o1', 'o1-mini'],
        'default_model': 'gpt-4o',
        'required_env': ['OPENAI_API_KEY'],
        'optional_env': ['OPENAI_ORG_ID'],
        'base_url': 'https://api.openai.com/v1',
        'description': 'OpenAI GPT models with advanced reasoning capabilities',
        'status_check': 'openai_status',
        'reasoning_models': ['o3-mini', 'o1', 'o1-mini']  # Models that use reasoning_effort
    },
    'Azure OpenAI': {
        'models': ['gpt-4.1','gpt-4o', 'gpt-4o-mini', 'o3-mini', 'o1', 'o1-mini'],
        'default_model': 'gpt-4.1',
        'required_env': ['AZURE_API_KEY', 'AZURE_ENDPOINT', 'AZURE_DEPLOYMENT', 'AZURE_API_VERSION'],
        'optional_env': [],
        'base_url': 'Custom Azure endpoint',
        'description': 'Azure-hosted OpenAI models with enterprise features',
        'status_check': 'azure_status',
        'reasoning_models': ['o3-mini', 'o1', 'o1-mini']  # Models that use reasoning_effort
    }
}

def is_reasoning_model(model_name: str) -> bool:
    """Check if a model is a reasoning model (O3/O1 series)."""
    reasoning_models = ['o3-mini', 'o1', 'o1-mini', 'o3', 'o1-preview']
    return any(rm in model_name.lower() for rm in reasoning_models)

def get_model_supported_parameters(model_name: str) -> dict:
    """Get supported parameters for a specific model."""
    if is_reasoning_model(model_name):
        return {
            'max_completion_tokens': True,
            'reasoning_effort': True,
            'temperature': False,
            'top_p': False,
            'presence_penalty': False,
            'frequency_penalty': False,
            'max_tokens': False  # Use max_completion_tokens instead
        }
    else:
        return {
            'max_tokens': True,
            'temperature': True,
            'top_p': True,
            'presence_penalty': True,
            'frequency_penalty': True,
            'max_completion_tokens': False,
            'reasoning_effort': False
        }

def get_provider_status(provider_name, config):
    """Check if a provider is properly configured."""
    missing_vars = []
    configured_vars = []
    
    try:
        for var in config['required_env']:
            if os.getenv(var):
                configured_vars.append(var)
            else:
                missing_vars.append(var)
        
        for var in config['optional_env']:
            if os.getenv(var):
                configured_vars.append(var)
        
        status = "✅ Configured" if not missing_vars else "❌ Missing Keys"
        return status, configured_vars, missing_vars
    except Exception as e:
        st.error(f"Error checking provider status: {str(e)}")
        return "❌ Error", [], config.get('required_env', [])

def test_model_connection(provider_name, model_name):
    """Test connection to a specific model with proper parameter handling."""
    try:
        # Import and test based on provider
        if provider_name == "OpenAI":
            try:
                import openai
                client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
                
                # Use appropriate parameters based on model type
                if is_reasoning_model(model_name):
                    response = client.chat.completions.create(
                        model=model_name,
                        messages=[{"role": "user", "content": "Hello"}],
                        max_completion_tokens=5,
                        reasoning_effort="low"
                    )
                else:
                    response = client.chat.completions.create(
                        model=model_name,
                        messages=[{"role": "user", "content": "Hello"}],
                        max_tokens=5
                    )
                return True, "Connection successful"
            except ImportError:
                return False, "OpenAI library not installed. Run: pip install openai"
            except Exception as e:
                if "Unsupported parameter" in str(e):
                    return False, f"Model {model_name} doesn't support the parameters used. Please check model configuration."
                return False, str(e)
        
        elif provider_name == "Azure OpenAI":
            try:
                import openai
                client = openai.AzureOpenAI(
                    api_key=os.getenv("AZURE_API_KEY"),
                    azure_endpoint=os.getenv("AZURE_ENDPOINT"),
                    api_version=os.getenv("AZURE_API_VERSION")
                )
                
                deployment_name = os.getenv("AZURE_DEPLOYMENT")
                
                # Use appropriate parameters based on model type
                if is_reasoning_model(model_name):
                    response = client.chat.completions.create(
                        model=deployment_name,  # Use deployment name for Azure
                        messages=[{"role": "user", "content": "Hello"}],
                        max_completion_tokens=5,
                        reasoning_effort="low"
                    )
                else:
                    response = client.chat.completions.create(
                        model=deployment_name,  # Use deployment name for Azure
                        messages=[{"role": "user", "content": "Hello"}],
                        max_tokens=5
                    )
                return True, "Connection successful"
            except ImportError:
                return False, "OpenAI library not installed. Run: pip install openai"
            except Exception as e:
                if "Unsupported parameter" in str(e):
                    return False, f"Model {model_name} doesn't support the parameters used. Please check model configuration."
                return False, str(e)
        
        else:
            return False, f"Testing not implemented for {provider_name}"
            
    except Exception as e:
        return False, str(e)

def save_model_configuration(config_data):
    """Save model configuration to file with error handling."""
    try:
        config_path = "model_configs.json"
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        # Validate config_data
        if not isinstance(config_data, dict):
            return False, "Invalid configuration data format"
        
        with open(config_path, 'w') as f:
            json.dump(config_data, f, indent=2)
        return True, "Configuration saved successfully"
    except Exception as e:
        return False, f"Failed to save configuration: {str(e)}"

def load_model_configuration():
    """Load model configuration from file."""
    try:
        config_path = "model_configs.json"
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return json.load(f)
        return {}
    except Exception as e:
        st.warning(f"Error loading model configuration: {str(e)}")
        return {}

def create_enhanced_configuration_tab():
    """Create the enhanced Configuration tab with model management and improved error handling."""
    st.markdown("Configure, test, and manage multiple AI model connections.")
    
    # Load existing configurations with error handling
    try:
        saved_configs = load_model_configuration()
    except Exception as e:
        st.error(f"Error loading configurations: {str(e)}")
        saved_configs = {}
    
    # Main configuration modes
    config_mode = st.radio(
        "Configuration Mode",
        ["Quick Setup", "Advanced Setup", "Manage Connections"],
        horizontal=True,
        help="Choose your configuration approach"
    )
    
    if config_mode == "Quick Setup":
        create_quick_setup_section(saved_configs)
    elif config_mode == "Advanced Setup":
        create_advanced_setup_section(saved_configs)
    else:
        create_connection_management_section(saved_configs)

def create_quick_setup_section(saved_configs):
    """Create quick setup section for common providers with improved error handling."""
    st.subheader("🚀 Quick Setup")
    st.markdown("Fast configuration for popular AI providers.")
    
    # Provider selection
    col1, col2 = st.columns([2, 1])
    
    with col1:
        selected_provider = st.selectbox(
            "Choose AI Provider",
            options=list(EXTENDED_MODEL_OPTIONS.keys()),
            help="Select your preferred AI provider",
            key="quick_provider_select"
        )
    
    with col2:
        provider_config = EXTENDED_MODEL_OPTIONS[selected_provider]
        status, configured_vars, missing_vars = get_provider_status(selected_provider, provider_config)
        st.metric("Status", status)
    
    # Provider information
    with st.container(border=True):
        st.markdown(f"**{selected_provider}**")
        st.markdown(provider_config['description'])
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"**Base URL:** `{provider_config['base_url']}`")
        with col2:
            st.markdown(f"**Available Models:** {len(provider_config['models'])}")
        with col3:
            st.markdown(f"**Default Model:** `{provider_config['default_model']}`")
    
    # Environment variables setup with improved error handling
    st.subheader("🔐 Environment Variables")
    
    with st.container(border=True):
        st.markdown("**Required Variables:**")
        
        # Initialize session state for form data if not exists
        if 'env_form_data' not in st.session_state:
            st.session_state['env_form_data'] = {}
        
        env_changed = False
        for var in provider_config['required_env']:
            current_value = os.getenv(var, "")
            
            col1, col2 = st.columns([3, 1])
            with col1:
                new_value = st.text_input(
                    f"{var}",
                    value=current_value,
                    type="password" if "KEY" in var else "default",
                    key=f"quick_{var}",
                    help=f"Enter your {var}"
                )
                if new_value != current_value:
                    try:
                        os.environ[var] = new_value
                        st.session_state['env_form_data'][var] = new_value
                        env_changed = True
                    except Exception as e:
                        st.error(f"Error setting {var}: {str(e)}")
            
            with col2:
                if current_value:
                    st.success("✅ Set")
                else:
                    st.error("❌ Missing")
        
        # Optional variables
        if provider_config['optional_env']:
            st.markdown("**Optional Variables:**")
            for var in provider_config['optional_env']:
                current_value = os.getenv(var, "")
                new_value = st.text_input(
                    f"{var} (Optional)",
                    value=current_value,
                    type="password" if "KEY" in var else "default",
                    key=f"quick_opt_{var}",
                    help=f"Optional: {var}"
                )
                if new_value != current_value:
                    try:
                        os.environ[var] = new_value
                        st.session_state['env_form_data'][var] = new_value
                        env_changed = True
                    except Exception as e:
                        st.error(f"Error setting {var}: {str(e)}")
    
    # Model selection and testing with reasoning model support
    st.subheader("🤖 Model Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        selected_model = st.selectbox(
            "Choose Model",
            options=provider_config['models'],
            index=provider_config['models'].index(provider_config['default_model']) if provider_config['default_model'] in provider_config['models'] else 0,
            help="Select the specific model to use",
            key="quick_model_select"
        )
        
        # Show model type information
        if is_reasoning_model(selected_model):
            st.info("🧠 This is a reasoning model (O3/O1 series)")
            st.markdown("**Reasoning models features:**")
            st.markdown("- Use `reasoning_effort` instead of `temperature`")
            st.markdown("- Use `max_completion_tokens` instead of `max_tokens`")
            st.markdown("- Perform internal step-by-step thinking")
            st.markdown("- Optimized for STEM, coding, and logical reasoning")
    
    with col2:
        if st.button("🧪 Test Connection", type="primary", use_container_width=True, key="quick_test"):
            with st.spinner(f"Testing connection to {selected_provider} - {selected_model}..."):
                try:
                    success, message = test_model_connection(selected_provider, selected_model)
                    if success:
                        st.success(f"✅ {message}")
                    else:
                        st.error(f"❌ {message}")
                except Exception as e:
                    st.error(f"❌ Test failed: {str(e)}")
    
    # Model Parameters with reasoning model support
    st.subheader("⚙️ Model Parameters")
    
    supported_params = get_model_supported_parameters(selected_model)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if supported_params.get('max_tokens'):
            max_tokens_value = st.number_input(
                "Max Tokens",
                min_value=1,
                max_value=32000,
                value=4096,
                step=256,
                help="Maximum number of tokens in the response",
                key="quick_max_tokens"
            )
        elif supported_params.get('max_completion_tokens'):
            max_completion_tokens_value = st.number_input(
                "Max Completion Tokens",
                min_value=1,
                max_value=32000,
                value=4096,
                step=256,
                help="Maximum completion tokens for reasoning models",
                key="quick_max_completion_tokens"
            )
    
    with col2:
        if supported_params.get('temperature'):
            temperature_value = st.slider(
                "Temperature", 
                0.0, 
                2.0, 
                step=0.05, 
                value=1.0,
                help="Controls randomness: 0.0 = deterministic, 2.0 = very creative",
                key="quick_temperature"
            )
        elif supported_params.get('reasoning_effort'):
            reasoning_effort_value = st.selectbox(
                "Reasoning Effort",
                options=["low", "medium", "high"],
                index=1,  # Default to medium
                help="Controls thinking depth: low=faster, high=more thorough",
                key="quick_reasoning_effort"
            )
    
    # Save configuration with improved error handling
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 Save Configuration", use_container_width=True, key="quick_save"):
            try:
                # Prepare configuration data
                config_data = {
                    "provider": selected_provider,
                    "model": selected_model,
                    "configured_at": datetime.now().isoformat(),
                    "environment_vars": {var: bool(os.getenv(var)) for var in provider_config['required_env'] + provider_config['optional_env']},
                    "is_reasoning_model": is_reasoning_model(selected_model),
                    "supported_parameters": supported_params
                }
                
                # Add model-specific parameters
                if supported_params.get('max_tokens'):
                    config_data["max_tokens"] = max_tokens_value
                if supported_params.get('max_completion_tokens'):
                    config_data["max_completion_tokens"] = max_completion_tokens_value
                if supported_params.get('temperature'):
                    config_data["temperature"] = temperature_value
                if supported_params.get('reasoning_effort'):
                    config_data["reasoning_effort"] = reasoning_effort_value
                
                all_configs = load_model_configuration()
                all_configs[selected_provider] = config_data
                
                success, message = save_model_configuration(all_configs)
                if success:
                    st.success(message)
                    # Update session state safely
                    try:
                        if 'params' not in st.session_state:
                            st.session_state['params'] = {}
                        st.session_state['params']['model_id'] = selected_provider
                        st.session_state['params']['selected_model'] = selected_model
                        
                        # Add model-specific parameters to session state
                        if supported_params.get('max_tokens'):
                            st.session_state['params']['max_tokens'] = max_tokens_value
                        if supported_params.get('max_completion_tokens'):
                            st.session_state['params']['max_completion_tokens'] = max_completion_tokens_value
                        if supported_params.get('temperature'):
                            st.session_state['params']['temperature'] = temperature_value
                        if supported_params.get('reasoning_effort'):
                            st.session_state['params']['reasoning_effort'] = reasoning_effort_value
                        
                    except Exception as e:
                        st.warning(f"Configuration saved but session update failed: {str(e)}")
                else:
                    st.error(message)
            except Exception as e:
                st.error(f"Failed to save configuration: {str(e)}")
                st.info("Please check your inputs and try again.")
    
    with col2:
        if st.button("🔄 Set as Active", use_container_width=True, key="quick_activate"):
            try:
                if 'params' not in st.session_state:
                    st.session_state['params'] = {}
                st.session_state['params']['model_id'] = selected_provider
                st.session_state['params']['selected_model'] = selected_model
                
                # Add model-specific parameters
                if supported_params.get('max_tokens') and 'max_tokens_value' in locals():
                    st.session_state['params']['max_tokens'] = max_tokens_value
                if supported_params.get('max_completion_tokens') and 'max_completion_tokens_value' in locals():
                    st.session_state['params']['max_completion_tokens'] = max_completion_tokens_value
                if supported_params.get('temperature') and 'temperature_value' in locals():
                    st.session_state['params']['temperature'] = temperature_value
                if supported_params.get('reasoning_effort') and 'reasoning_effort_value' in locals():
                    st.session_state['params']['reasoning_effort'] = reasoning_effort_value
                
                reset_connection_state()
                st.success(f"Activated {selected_provider} - {selected_model}")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to activate configuration: {str(e)}")

def create_advanced_setup_section(saved_configs):
    """Create advanced setup section for custom configurations."""
    st.subheader("🔧 Advanced Setup")
    st.markdown("Custom configuration for specialized setups.")
    
    # Model parameters configuration with reasoning model support
    show_model_params = st.checkbox("⚙️ Model Parameters", key="show_model_params", value=True)
    if show_model_params:
        st.markdown("Configure default parameters for all models.")
        
        # Get current session state parameters
        current_params = st.session_state.get('params', {})
        current_model = current_params.get('selected_model', 'gpt-4o')
        supported_params = get_model_supported_parameters(current_model)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if supported_params.get('max_tokens'):
                default_max_tokens = st.number_input(
                    "Max Tokens",
                    min_value=1,
                    max_value=32000,
                    value=current_params.get('max_tokens', 4096),
                    step=256,
                    help="Maximum tokens in response",
                    key="adv_max_tokens"
                )
                # Update session state
                if 'params' not in st.session_state:
                    st.session_state['params'] = {}
                st.session_state['params']['max_tokens'] = default_max_tokens
            
            elif supported_params.get('max_completion_tokens'):
                default_max_completion_tokens = st.number_input(
                    "Max Completion Tokens",
                    min_value=1,
                    max_value=32000,
                    value=current_params.get('max_completion_tokens', 4096),
                    step=256,
                    help="Maximum completion tokens for reasoning models",
                    key="adv_max_completion_tokens"
                )
                # Update session state
                if 'params' not in st.session_state:
                    st.session_state['params'] = {}
                st.session_state['params']['max_completion_tokens'] = default_max_completion_tokens
        
        with col2:
            if supported_params.get('temperature'):
                default_temperature = st.slider(
                    "Temperature",
                    min_value=0.0,
                    max_value=2.0,
                    value=current_params.get('temperature', 1.0),
                    step=0.1,
                    help="Creativity level (0=deterministic, 2=very creative)",
                    key="adv_temperature"
                )
                # Update session state
                if 'params' not in st.session_state:
                    st.session_state['params'] = {}
                st.session_state['params']['temperature'] = default_temperature
            
            elif supported_params.get('reasoning_effort'):
                default_reasoning_effort = st.selectbox(
                    "Reasoning Effort",
                    options=["low", "medium", "high"],
                    index=["low", "medium", "high"].index(current_params.get('reasoning_effort', 'medium')),
                    help="Thinking depth (low=faster, high=more thorough)",
                    key="adv_reasoning_effort"
                )
                # Update session state
                if 'params' not in st.session_state:
                    st.session_state['params'] = {}
                st.session_state['params']['reasoning_effort'] = default_reasoning_effort
        
        with col3:
            default_timeout = st.number_input(
                "Timeout (seconds)",
                min_value=10,
                max_value=300,
                value=60,
                step=10,
                help="Request timeout duration",
                key="adv_timeout"
            )
            # Update session state
            if 'params' not in st.session_state:
                st.session_state['params'] = {}
            st.session_state['params']['timeout'] = default_timeout
        
        # Show current model information
        if current_model:
            st.info(f"📝 Current model: **{current_model}** ({'Reasoning Model' if is_reasoning_model(current_model) else 'Standard Model'})")

def create_connection_management_section(saved_configs):
    """Create connection management section with improved error handling."""
    st.subheader("🔌 Connection Management")
    st.markdown("Manage and test existing AI model connections.")
    
    # Current active connection
    current_provider = st.session_state.get('params', {}).get('model_id')
    current_model = st.session_state.get('params', {}).get('selected_model')
    
    if current_provider:
        st.success(f"**Active Provider:** {current_provider}")
        if current_model:
            model_type = "🧠 Reasoning Model" if is_reasoning_model(current_model) else "🤖 Standard Model"
            st.info(f"**Active Model:** {current_model} ({model_type})")
    else:
        st.warning("No active provider selected")
    
    # Connection testing with improved error handling
    st.markdown("### 🧪 Connection Testing")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        test_provider = st.selectbox(
            "Select Provider to Test",
            options=list(EXTENDED_MODEL_OPTIONS.keys()),
            key="test_provider_select"
        )
    
    with col2:
        if test_provider:
            provider_config = EXTENDED_MODEL_OPTIONS[test_provider]
            test_model = st.selectbox(
                "Select Model",
                options=provider_config['models'],
                key="test_model_select"
            )
    
    with col3:
        if st.button("🧪 Test Connection", use_container_width=True, key="test_connection"):
            if test_provider and test_model:
                with st.spinner(f"Testing {test_provider} - {test_model}..."):
                    try:
                        success, message = test_model_connection(test_provider, test_model)
                        if success:
                            st.success(f"✅ {message}")
                        else:
                            st.error(f"❌ {message}")
                    except Exception as e:
                        st.error(f"❌ Test failed: {str(e)}")
            else:
                st.warning("Please select both provider and model")

# Error boundary decorator
def with_error_boundary(func):
    """Decorator to add error boundary to functions."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            with st.expander("🐛 Error Details"):
                st.code(traceback.format_exc())
            return None
    return wrapper

# Apply error boundary to main functions
create_enhanced_configuration_tab = with_error_boundary(create_enhanced_configuration_tab)
create_quick_setup_section = with_error_boundary(create_quick_setup_section)
create_advanced_setup_section = with_error_boundary(create_advanced_setup_section)
create_connection_management_section = with_error_boundary(create_connection_management_section)