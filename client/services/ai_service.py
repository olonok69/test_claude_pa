import json
import streamlit as st
import os
from dotenv import load_dotenv

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI, AzureChatOpenAI

from typing import Optional
from config import MODEL_OPTIONS

# Load environment variables
load_dotenv()

# Updated model mapping with O3/O3-mini support
UPDATED_MODEL_OPTIONS = {
    'Azure OpenAI': 'gpt-4.1',  # Using the deployment from .env
    'OpenAI': 'gpt-4o',
}

def is_reasoning_model(model_name: str) -> bool:
    """Check if a model is a reasoning model (O3/O1 series)."""
    if not model_name:
        return False
    reasoning_models = ['o3-mini', 'o1', 'o1-mini', 'o3', 'o1-preview']
    return any(rm in model_name.lower() for rm in reasoning_models)

def get_model_parameters(llm_provider: str, **kwargs) -> dict:
    """Get appropriate parameters for the model, filtering unsupported ones."""
    params = {}
    
    # Get the selected model from session state
    selected_model = st.session_state.get('params', {}).get('selected_model', '')
    
    if is_reasoning_model(selected_model):
        # For reasoning models (O3/O1 series)
        if 'max_completion_tokens' in kwargs:
            params['max_completion_tokens'] = kwargs['max_completion_tokens']
        elif 'max_tokens' in kwargs:
            # Convert max_tokens to max_completion_tokens for reasoning models
            params['max_completion_tokens'] = kwargs['max_tokens']
        
        if 'reasoning_effort' in kwargs:
            params['reasoning_effort'] = kwargs['reasoning_effort']
        elif 'temperature' in kwargs:
            # Map temperature to reasoning effort for reasoning models
            temp = kwargs['temperature']
            if temp <= 0.3:
                params['reasoning_effort'] = 'low'
            elif temp <= 0.7:
                params['reasoning_effort'] = 'medium'
            else:
                params['reasoning_effort'] = 'high'
        else:
            # Default reasoning effort
            params['reasoning_effort'] = kwargs.get('reasoning_effort', 'medium')
        
        # Add other supported parameters
        if 'stream' in kwargs:
            params['stream'] = kwargs['stream']
        if 'stop' in kwargs:
            params['stop'] = kwargs['stop']
        if 'seed' in kwargs:
            params['seed'] = kwargs['seed']
        if 'response_format' in kwargs:
            params['response_format'] = kwargs['response_format']
        
        # Exclude unsupported parameters for reasoning models
        # (temperature, top_p, presence_penalty, frequency_penalty, max_tokens)
        
    else:
        # For standard models (GPT-4, GPT-3.5, etc.)
        if 'temperature' in kwargs:
            params['temperature'] = kwargs['temperature']
        if 'max_tokens' in kwargs:
            params['max_tokens'] = kwargs['max_tokens']
        if 'top_p' in kwargs:
            params['top_p'] = kwargs['top_p']
        if 'presence_penalty' in kwargs:
            params['presence_penalty'] = kwargs['presence_penalty']
        if 'frequency_penalty' in kwargs:
            params['frequency_penalty'] = kwargs['frequency_penalty']
        if 'stream' in kwargs:
            params['stream'] = kwargs['stream']
        if 'stop' in kwargs:
            params['stop'] = kwargs['stop']
        if 'seed' in kwargs:
            params['seed'] = kwargs['seed']
        if 'response_format' in kwargs:
            params['response_format'] = kwargs['response_format']
    
    return params

def create_llm_model(llm_provider: str, **kwargs):
    """Create a language model based on the selected provider with proper parameter handling."""
    
    # Get session state parameters
    session_params = st.session_state.get('params', {})
    selected_model = session_params.get('selected_model', '')
    
    if llm_provider == "OpenAI":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            st.error("❌ OpenAI API key not found in environment variables")
            st.stop()
        
        # Get the model name - use selected_model if available, otherwise use default
        model_name = selected_model or UPDATED_MODEL_OPTIONS.get('OpenAI', 'gpt-4o')
        
        # Filter parameters based on model type
        filtered_params = get_model_parameters(llm_provider, **kwargs)
        
        # Create the client with appropriate parameters
        try:
            return ChatOpenAI(
                openai_api_key=api_key,
                model=model_name,
                **filtered_params
            )
        except Exception as e:
            if "Unsupported parameter" in str(e):
                st.error(f"❌ Model {model_name} doesn't support the parameters used. This might be a reasoning model (O3/O1) that requires different parameters.")
                st.info("💡 Reasoning models use 'reasoning_effort' instead of 'temperature' and 'max_completion_tokens' instead of 'max_tokens'")
            raise e
        
    elif llm_provider == "Azure OpenAI":
        azure_api_key = os.getenv("AZURE_API_KEY")
        azure_endpoint = os.getenv("AZURE_ENDPOINT")
        azure_deployment = os.getenv("AZURE_DEPLOYMENT")
        azure_api_version = os.getenv("AZURE_API_VERSION")
        
        if not all([azure_api_key, azure_endpoint, azure_deployment, azure_api_version]):
            st.error("❌ Azure OpenAI configuration incomplete. Please check your environment variables.")
            st.stop()
        
        # Get the deployment name - Azure uses deployment names instead of model names
        deployment_name = azure_deployment
        
        # Filter parameters based on model type (check if the selected model is a reasoning model)
        filtered_params = get_model_parameters(llm_provider, **kwargs)
        
        # Create the Azure client with appropriate parameters
        try:
            return AzureChatOpenAI(
                azure_endpoint=azure_endpoint,
                api_key=azure_api_key,
                azure_deployment=deployment_name,
                api_version=azure_api_version,
                **filtered_params
            )
        except Exception as e:
            if "Unsupported parameter" in str(e):
                st.error(f"❌ Azure deployment {deployment_name} doesn't support the parameters used. This might be a reasoning model (O3/O1) that requires different parameters.")
                st.info("💡 Reasoning models use 'reasoning_effort' instead of 'temperature' and 'max_completion_tokens' instead of 'max_tokens'")
            raise e
    else:
        raise ValueError(f"Unsupported LLM provider: {llm_provider}")

def get_response(prompt: str, llm_provider: str):
    """Get a response from the LLM using the standard LangChain interface."""
    try:
        # Create the LLM instance dynamically
        llm = create_llm_model(llm_provider)

        # Wrap prompt in a HumanMessage
        message = HumanMessage(content=prompt)

        # Invoke model and return the output content
        response = llm.invoke([message])
        return response.content

    except Exception as e:
        return f"Error during LLM invocation: {str(e)}"

def get_response_stream(
    prompt: str,
    llm_provider: str,
    system: Optional[str] = '',
    temperature: float = 1.0,
    max_tokens: int = 4096,
    **kwargs,
    ):
    """
    Get a streaming response from the selected LLM provider with proper parameter handling.
    All provider-specific connection/auth should be handled via environment variables.
    """
    try:
        # Get session parameters for model-specific handling
        session_params = st.session_state.get('params', {})
        selected_model = session_params.get('selected_model', '')
        
        # Prepare parameters based on model type
        if is_reasoning_model(selected_model):
            # For reasoning models, use appropriate parameters
            model_kwargs = {
                "max_completion_tokens": max_tokens,
                "reasoning_effort": session_params.get('reasoning_effort', 'medium'),
                "streaming": True
            }
            # Don't include temperature for reasoning models
        else:
            # For standard models, use traditional parameters
            model_kwargs = {
                "temperature": temperature,
                "max_tokens": max_tokens,
                "streaming": True
            }
        
        # Add any additional kwargs
        model_kwargs.update(kwargs)

        # Create the LLM with streaming enabled and appropriate parameters
        llm = create_llm_model(llm_provider, **model_kwargs)

        # Compose messages
        messages = []
        if system:
            if is_reasoning_model(selected_model):
                # For reasoning models, use developer role instead of system
                messages.append(HumanMessage(content=f"[INSTRUCTIONS] {system}"))
            else:
                messages.append(SystemMessage(content=system))
        messages.append(HumanMessage(content=prompt))

        # Stream the response
        stream_response = llm.stream(messages)
        return stream_response
    except Exception as e:
        error_msg = f"[Error during streaming: {str(e)}]"
        
        # Provide helpful error messages for common issues
        if "Unsupported parameter" in str(e):
            if is_reasoning_model(selected_model):
                error_msg += "\n💡 This is a reasoning model (O3/O1 series). These models use different parameters than standard models."
            else:
                error_msg += "\n💡 Please check if the selected model supports the parameters being used."
        
        st.error(error_msg)
        st.stop()

def get_default_parameters(llm_provider: str) -> dict:
    """Get default parameters for a provider based on the selected model."""
    session_params = st.session_state.get('params', {})
    selected_model = session_params.get('selected_model', '')
    
    if is_reasoning_model(selected_model):
        return {
            'max_completion_tokens': session_params.get('max_completion_tokens', 4096),
            'reasoning_effort': session_params.get('reasoning_effort', 'medium'),
        }
    else:
        return {
            'temperature': session_params.get('temperature', 1.0),
            'max_tokens': session_params.get('max_tokens', 4096),
        }

def validate_model_parameters(llm_provider: str, **kwargs) -> tuple[bool, str]:
    """Validate parameters for the selected model."""
    session_params = st.session_state.get('params', {})
    selected_model = session_params.get('selected_model', '')
    
    if is_reasoning_model(selected_model):
        # Check for unsupported parameters in reasoning models
        unsupported = ['temperature', 'top_p', 'presence_penalty', 'frequency_penalty', 'max_tokens']
        found_unsupported = [param for param in unsupported if param in kwargs]
        
        if found_unsupported:
            return False, f"Reasoning model {selected_model} doesn't support: {', '.join(found_unsupported)}. Use 'max_completion_tokens' and 'reasoning_effort' instead."
        
        # Check for required parameters
        if 'max_completion_tokens' not in kwargs and 'max_tokens' not in kwargs:
            return False, "Reasoning models require 'max_completion_tokens' parameter."
        
    else:
        # Validate standard model parameters
        if 'reasoning_effort' in kwargs:
            return False, f"Standard model {selected_model} doesn't support 'reasoning_effort'. Use 'temperature' instead."
    
    return True, "Parameters are valid"

# Helper function to get model information
def get_model_info(model_name: str) -> dict:
    """Get information about a specific model."""
    return {
        'name': model_name,
        'is_reasoning_model': is_reasoning_model(model_name),
        'supported_parameters': {
            'max_completion_tokens': is_reasoning_model(model_name),
            'reasoning_effort': is_reasoning_model(model_name),
            'temperature': not is_reasoning_model(model_name),
            'max_tokens': not is_reasoning_model(model_name),
            'top_p': not is_reasoning_model(model_name),
            'presence_penalty': not is_reasoning_model(model_name),
            'frequency_penalty': not is_reasoning_model(model_name),
        },
        'recommended_use': {
            'reasoning_models': "STEM problems, coding, mathematics, logical reasoning",
            'standard_models': "General conversation, creative writing, broad knowledge tasks"
        }[('reasoning_models' if is_reasoning_model(model_name) else 'standard_models')]
    }

# Usage examples and documentation
def get_usage_examples():
    """Get usage examples for different model types."""
    return {
        'reasoning_models': {
            'description': 'O3/O1 series models optimized for step-by-step reasoning',
            'example_params': {
                'max_completion_tokens': 4096,
                'reasoning_effort': 'medium',  # low, medium, high
                'stream': True
            },
            'unsupported_params': ['temperature', 'top_p', 'presence_penalty', 'frequency_penalty', 'max_tokens']
        },
        'standard_models': {
            'description': 'GPT-4/3.5 series models for general conversation',
            'example_params': {
                'temperature': 1.0,
                'max_tokens': 4096,
                'top_p': 1.0,
                'stream': True
            },
            'unsupported_params': ['reasoning_effort', 'max_completion_tokens']
        }
    }