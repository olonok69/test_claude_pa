import os
import json
from dotenv import load_dotenv

load_dotenv()
env = os.getenv

# Enhanced model mapping with O3/O3-mini support
MODEL_OPTIONS = {
    'Azure OpenAI': 'gpt-4.1',  # Using the deployment from .env
    'OpenAI': 'gpt-4o',
}

# Extended model options with reasoning models
EXTENDED_MODEL_OPTIONS = {
    'OpenAI': {
        'models': {
            # Standard Models
            'gpt-4o': {
                'type': 'standard',
                'description': 'Most capable GPT-4 model for general use',
                'context_window': 128000,
                'supports': ['temperature', 'max_tokens', 'top_p', 'presence_penalty', 'frequency_penalty']
            },
            'gpt-4o-mini': {
                'type': 'standard',
                'description': 'Smaller, faster GPT-4 model',
                'context_window': 128000,
                'supports': ['temperature', 'max_tokens', 'top_p', 'presence_penalty', 'frequency_penalty']
            },
            'gpt-4-turbo': {
                'type': 'standard',
                'description': 'Latest GPT-4 Turbo model',
                'context_window': 128000,
                'supports': ['temperature', 'max_tokens', 'top_p', 'presence_penalty', 'frequency_penalty']
            },
            'gpt-3.5-turbo': {
                'type': 'standard',
                'description': 'Fast and efficient GPT-3.5 model',
                'context_window': 16384,
                'supports': ['temperature', 'max_tokens', 'top_p', 'presence_penalty', 'frequency_penalty']
            },
            # Reasoning Models
            'o3-mini': {
                'type': 'reasoning',
                'description': 'Fast reasoning model optimized for STEM and coding',
                'context_window': 200000,
                'supports': ['max_completion_tokens', 'reasoning_effort'],
                'reasoning_efforts': ['low', 'medium', 'high'],
                'default_reasoning_effort': 'medium',
                'cost_efficiency': 'high',
                'speed': 'fast'
            },
            'o1': {
                'type': 'reasoning',
                'description': 'Advanced reasoning model for complex problems',
                'context_window': 200000,
                'supports': ['max_completion_tokens', 'reasoning_effort'],
                'reasoning_efforts': ['low', 'medium', 'high'],
                'default_reasoning_effort': 'medium',
                'cost_efficiency': 'medium',
                'speed': 'medium'
            },
            'o1-mini': {
                'type': 'reasoning',
                'description': 'Smaller reasoning model',
                'context_window': 128000,
                'supports': ['max_completion_tokens', 'reasoning_effort'],
                'reasoning_efforts': ['low', 'medium', 'high'],
                'default_reasoning_effort': 'medium',
                'cost_efficiency': 'high',
                'speed': 'medium'
            }
        },
        'default_model': 'gpt-4o',
        'api_base': 'https://api.openai.com/v1'
    },
    'Azure OpenAI': {
        'models': {
            # Standard Models
            'gpt-4.1': {
                'type': 'standard',
                'description': 'Azure deployment of GPT-4',
                'context_window': 128000,
                'supports': ['temperature', 'max_tokens', 'top_p', 'presence_penalty', 'frequency_penalty']
            },
            'gpt-4o': {
                'type': 'standard',
                'description': 'Azure deployment of GPT-4o',
                'context_window': 128000,
                'supports': ['temperature', 'max_tokens', 'top_p', 'presence_penalty', 'frequency_penalty']
            },
            'gpt-4o-mini': {
                'type': 'standard',
                'description': 'Azure deployment of GPT-4o-mini',
                'context_window': 128000,
                'supports': ['temperature', 'max_tokens', 'top_p', 'presence_penalty', 'frequency_penalty']
            },
            # Reasoning Models
            'o3-mini': {
                'type': 'reasoning',
                'description': 'Azure deployment of O3-mini reasoning model',
                'context_window': 200000,
                'supports': ['max_completion_tokens', 'reasoning_effort'],
                'reasoning_efforts': ['low', 'medium', 'high'],
                'default_reasoning_effort': 'medium',
                'cost_efficiency': 'high',
                'speed': 'fast'
            },
            'o1': {
                'type': 'reasoning',
                'description': 'Azure deployment of O1 reasoning model',
                'context_window': 200000,
                'supports': ['max_completion_tokens', 'reasoning_effort'],
                'reasoning_efforts': ['low', 'medium', 'high'],
                'default_reasoning_effort': 'medium',
                'cost_efficiency': 'medium',
                'speed': 'medium'
            },
            'o1-mini': {
                'type': 'reasoning',
                'description': 'Azure deployment of O1-mini reasoning model',
                'context_window': 128000,
                'supports': ['max_completion_tokens', 'reasoning_effort'],
                'reasoning_efforts': ['low', 'medium', 'high'],
                'default_reasoning_effort': 'medium',
                'cost_efficiency': 'high',
                'speed': 'medium'
            }
        },
        'default_model': 'gpt-4.1',
        'api_base': 'azure_endpoint'
    }
}

# Model type detection functions
def is_reasoning_model(model_name: str) -> bool:
    """Check if a model is a reasoning model (O3/O1 series)."""
    if not model_name:
        return False
    reasoning_models = ['o3-mini', 'o1', 'o1-mini', 'o3', 'o1-preview']
    return any(rm in model_name.lower() for rm in reasoning_models)

def get_model_config(provider: str, model_name: str) -> dict:
    """Get configuration for a specific model."""
    if provider in EXTENDED_MODEL_OPTIONS:
        models = EXTENDED_MODEL_OPTIONS[provider]['models']
        if model_name in models:
            return models[model_name]
    
    # Fallback for unknown models
    if is_reasoning_model(model_name):
        return {
            'type': 'reasoning',
            'description': f'Reasoning model: {model_name}',
            'supports': ['max_completion_tokens', 'reasoning_effort'],
            'reasoning_efforts': ['low', 'medium', 'high'],
            'default_reasoning_effort': 'medium'
        }
    else:
        return {
            'type': 'standard',
            'description': f'Standard model: {model_name}',
            'supports': ['temperature', 'max_tokens', 'top_p', 'presence_penalty', 'frequency_penalty']
        }

def get_supported_parameters(provider: str, model_name: str) -> list:
    """Get list of supported parameters for a model."""
    config = get_model_config(provider, model_name)
    return config.get('supports', [])

def get_default_parameters(provider: str, model_name: str) -> dict:
    """Get default parameters for a model."""
    config = get_model_config(provider, model_name)
    
    if config.get('type') == 'reasoning':
        return {
            'max_completion_tokens': 4096,
            'reasoning_effort': config.get('default_reasoning_effort', 'medium')
        }
    else:
        return {
            'temperature': 1.0,
            'max_tokens': 4096,
            'top_p': 1.0
        }

# Streamlit defaults (updated for reasoning models)
DEFAULT_MAX_TOKENS = 4096
DEFAULT_MAX_COMPLETION_TOKENS = 4096
DEFAULT_TEMPERATURE = 1.0
DEFAULT_REASONING_EFFORT = 'medium'

# Parameter mapping for backward compatibility
PARAMETER_MAPPING = {
    'reasoning_models': {
        'max_tokens': 'max_completion_tokens',  # Map old parameter to new
        'temperature': 'reasoning_effort_mapping'  # Special mapping function
    },
    'standard_models': {
        'max_completion_tokens': 'max_tokens',  # Map new parameter to old
        'reasoning_effort': 'temperature_mapping'  # Special mapping function
    }
}

def map_temperature_to_reasoning_effort(temperature: float) -> str:
    """Map temperature values to reasoning effort levels."""
    if temperature <= 0.3:
        return 'low'
    elif temperature <= 0.7:
        return 'medium'
    else:
        return 'high'

def map_reasoning_effort_to_temperature(reasoning_effort: str) -> float:
    """Map reasoning effort to temperature values (for compatibility)."""
    mapping = {
        'low': 0.2,
        'medium': 0.5,
        'high': 0.8
    }
    return mapping.get(reasoning_effort.lower(), 0.5)

# UI Configuration
TAB_CONFIG = {
    "chat": {
        "title": "💬 Chat",
        "description": "Main conversation interface"
    },
    "configuration": {
        "title": "⚙️ Configuration", 
        "description": "AI provider and model settings"
    },
    "connections": {
        "title": "🔌 Connections",
        "description": "MCP server management"
    },
    "tools": {
        "title": "🧰 Tools",
        "description": "Available MCP tools"
    }
}

# Load server configuration - MSSQL only
config_path = os.path.join('.', 'servers_config.json')
if os.path.exists(config_path):
    with open(config_path, 'r') as f:
        SERVER_CONFIG = json.load(f)
else:
    # Default server configuration if file doesn't exist - MSSQL only
    SERVER_CONFIG = {
        "mcpServers": {
            "MSSQL": {
                "transport": "sse",
                "url": "http://mcpserver3:8008/sse",
                "timeout": 600,
                "headers": None,
                "sse_read_timeout": 900
            }
        }
    }

# Model recommendations based on use case
MODEL_RECOMMENDATIONS = {
    'coding': {
        'reasoning': ['o3-mini', 'o1'],
        'standard': ['gpt-4o', 'gpt-4-turbo'],
        'description': 'For programming tasks, algorithm design, and code analysis'
    },
    'mathematics': {
        'reasoning': ['o3-mini', 'o1'],
        'standard': ['gpt-4o'],
        'description': 'For mathematical problem solving and STEM calculations'
    },
    'general_conversation': {
        'reasoning': [],
        'standard': ['gpt-4o', 'gpt-4o-mini', 'gpt-3.5-turbo'],
        'description': 'For general chat, creative writing, and broad knowledge tasks'
    },
    'logical_reasoning': {
        'reasoning': ['o3-mini', 'o1'],
        'standard': ['gpt-4o'],
        'description': 'For complex reasoning, problem solving, and analytical tasks'
    },
    'fast_responses': {
        'reasoning': ['o3-mini'],
        'standard': ['gpt-4o-mini', 'gpt-3.5-turbo'],
        'description': 'For applications requiring quick response times'
    }
}

def get_model_recommendation(use_case: str, prefer_reasoning: bool = False) -> list:
    """Get model recommendations for a specific use case."""
    if use_case not in MODEL_RECOMMENDATIONS:
        return []
    
    rec = MODEL_RECOMMENDATIONS[use_case]
    
    if prefer_reasoning and rec['reasoning']:
        return rec['reasoning']
    elif rec['standard']:
        return rec['standard']
    else:
        return rec['reasoning']

# Cost and performance information
MODEL_PERFORMANCE = {
    'o3-mini': {
        'cost_tier': 'low',
        'speed_tier': 'fast',
        'reasoning_capability': 'high',
        'best_for': ['STEM', 'coding', 'logical reasoning'],
        'relative_cost': 0.1  # Relative to GPT-4
    },
    'o1': {
        'cost_tier': 'medium',
        'speed_tier': 'medium',
        'reasoning_capability': 'very high',
        'best_for': ['complex reasoning', 'advanced mathematics', 'research'],
        'relative_cost': 0.5
    },
    'o1-mini': {
        'cost_tier': 'low',
        'speed_tier': 'medium',
        'reasoning_capability': 'high',
        'best_for': ['coding', 'STEM', 'moderate complexity reasoning'],
        'relative_cost': 0.2
    },
    'gpt-4o': {
        'cost_tier': 'medium',
        'speed_tier': 'fast',
        'reasoning_capability': 'medium',
        'best_for': ['general conversation', 'creative writing', 'broad knowledge'],
        'relative_cost': 1.0
    },
    'gpt-4o-mini': {
        'cost_tier': 'low',
        'speed_tier': 'very fast',
        'reasoning_capability': 'medium',
        'best_for': ['quick responses', 'simple tasks', 'high volume'],
        'relative_cost': 0.15
    }
}

def get_model_performance_info(model_name: str) -> dict:
    """Get performance information for a model."""
    return MODEL_PERFORMANCE.get(model_name, {
        'cost_tier': 'unknown',
        'speed_tier': 'unknown',
        'reasoning_capability': 'unknown',
        'best_for': ['general use'],
        'relative_cost': 1.0
    })

# Helper functions for parameter validation
def validate_parameters_for_model(provider: str, model_name: str, params: dict) -> tuple[bool, list]:
    """Validate parameters for a specific model."""
    config = get_model_config(provider, model_name)
    supported = config.get('supports', [])
    
    errors = []
    
    for param in params:
        if param not in supported:
            if config.get('type') == 'reasoning':
                if param in ['temperature', 'max_tokens']:
                    errors.append(f"Parameter '{param}' not supported for reasoning model {model_name}. Use 'reasoning_effort' instead of 'temperature' and 'max_completion_tokens' instead of 'max_tokens'.")
                else:
                    errors.append(f"Parameter '{param}' not supported for reasoning model {model_name}")
            else:
                if param in ['reasoning_effort', 'max_completion_tokens']:
                    errors.append(f"Parameter '{param}' only supported for reasoning models, not {model_name}")
                else:
                    errors.append(f"Parameter '{param}' not supported for model {model_name}")
    
    return len(errors) == 0, errors

def get_parameter_suggestions(provider: str, model_name: str, invalid_params: list) -> dict:
    """Get suggestions for replacing invalid parameters."""
    config = get_model_config(provider, model_name)
    suggestions = {}
    
    for param in invalid_params:
        if config.get('type') == 'reasoning':
            if param == 'temperature':
                suggestions[param] = {
                    'replacement': 'reasoning_effort',
                    'note': 'Use "low", "medium", or "high" for reasoning effort'
                }
            elif param == 'max_tokens':
                suggestions[param] = {
                    'replacement': 'max_completion_tokens',
                    'note': 'Same function, different parameter name for reasoning models'
                }
        else:
            if param == 'reasoning_effort':
                suggestions[param] = {
                    'replacement': 'temperature',
                    'note': 'Use temperature values 0.0-2.0 for standard models'
                }
            elif param == 'max_completion_tokens':
                suggestions[param] = {
                    'replacement': 'max_tokens',
                    'note': 'Same function, different parameter name for standard models'
                }
    
    return suggestions

# Environment variable validation
def validate_environment_variables(provider: str) -> tuple[bool, list, list]:
    """Validate required environment variables for a provider."""
    if provider not in EXTENDED_MODEL_OPTIONS:
        return False, [], [f"Unknown provider: {provider}"]
    
    config = EXTENDED_MODEL_OPTIONS[provider]
    missing = []
    present = []
    
    # Check required variables
    for var in config.get('required_env', []):
        if os.getenv(var):
            present.append(var)
        else:
            missing.append(var)
    
    # Check optional variables
    for var in config.get('optional_env', []):
        if os.getenv(var):
            present.append(var)
    
    return len(missing) == 0, present, missing

# Configuration templates for different setups
CONFIGURATION_TEMPLATES = {
    'development': {
        'description': 'Fast, cost-effective setup for development',
        'recommended_models': {
            'OpenAI': 'gpt-4o-mini',
            'Azure OpenAI': 'gpt-4o-mini'
        },
        'default_params': {
            'temperature': 0.7,
            'max_tokens': 2048
        }
    },
    'production': {
        'description': 'Balanced setup for production use',
        'recommended_models': {
            'OpenAI': 'gpt-4o',
            'Azure OpenAI': 'gpt-4o'
        },
        'default_params': {
            'temperature': 1.0,
            'max_tokens': 4096
        }
    },
    'reasoning_focused': {
        'description': 'Optimized for complex reasoning tasks',
        'recommended_models': {
            'OpenAI': 'o3-mini',
            'Azure OpenAI': 'o3-mini'
        },
        'default_params': {
            'reasoning_effort': 'medium',
            'max_completion_tokens': 4096
        }
    },
    'high_performance': {
        'description': 'Maximum capability for demanding tasks',
        'recommended_models': {
            'OpenAI': 'o1',
            'Azure OpenAI': 'o1'
        },
        'default_params': {
            'reasoning_effort': 'high',
            'max_completion_tokens': 8192
        }
    }
}

def get_configuration_template(template_name: str) -> dict:
    """Get a configuration template."""
    return CONFIGURATION_TEMPLATES.get(template_name, {})

def list_available_templates() -> list:
    """List all available configuration templates."""
    return list(CONFIGURATION_TEMPLATES.keys())

# Model migration helpers
def migrate_parameters_to_reasoning_model(params: dict) -> dict:
    """Convert standard model parameters to reasoning model parameters."""
    new_params = params.copy()
    
    if 'max_tokens' in new_params:
        new_params['max_completion_tokens'] = new_params.pop('max_tokens')
    
    if 'temperature' in new_params:
        temp = new_params.pop('temperature')
        new_params['reasoning_effort'] = map_temperature_to_reasoning_effort(temp)
    
    # Remove unsupported parameters
    unsupported = ['top_p', 'presence_penalty', 'frequency_penalty']
    for param in unsupported:
        new_params.pop(param, None)
    
    return new_params

def migrate_parameters_to_standard_model(params: dict) -> dict:
    """Convert reasoning model parameters to standard model parameters."""
    new_params = params.copy()
    
    if 'max_completion_tokens' in new_params:
        new_params['max_tokens'] = new_params.pop('max_completion_tokens')
    
    if 'reasoning_effort' in new_params:
        effort = new_params.pop('reasoning_effort')
        new_params['temperature'] = map_reasoning_effort_to_temperature(effort)
    
    return new_params

# Export functions for other modules
__all__ = [
    'MODEL_OPTIONS',
    'EXTENDED_MODEL_OPTIONS', 
    'is_reasoning_model',
    'get_model_config',
    'get_supported_parameters',
    'get_default_parameters',
    'validate_parameters_for_model',
    'get_parameter_suggestions',
    'validate_environment_variables',
    'get_configuration_template',
    'migrate_parameters_to_reasoning_model',
    'migrate_parameters_to_standard_model',
    'map_temperature_to_reasoning_effort',
    'map_reasoning_effort_to_temperature',
    'get_model_recommendation',
    'get_model_performance_info',
    'SERVER_CONFIG',
    'TAB_CONFIG'
]