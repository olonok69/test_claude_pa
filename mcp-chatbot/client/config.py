import os
import json
from dotenv import load_dotenv

load_dotenv()
env = os.getenv

# Model mapping - only OpenAI and Azure OpenAI
MODEL_OPTIONS = {
    'OpenAI': 'gpt-4o',
    'Azure OpenAI': 'gpt-4o-mini',  # Using the deployment from .env
}

# Streamlit defaults
DEFAULT_MAX_TOKENS = 4096
DEFAULT_TEMPERATURE = 1.0

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

# Load server configuration
config_path = os.path.join('.', 'servers_config.json')
if os.path.exists(config_path):
    with open(config_path, 'r') as f:
        SERVER_CONFIG = json.load(f)
else:
    # Default server configuration if file doesn't exist
    SERVER_CONFIG = {
        "mcpServers": {
            "Neo4j": {
                "transport": "sse",
                "url": "http://mcpserver4:8003/sse",
                "timeout": 600,
                "headers": None,
                "sse_read_timeout": 900
            },
            "HubSpot": {
                "transport": "sse",
                "url": "http://mcpserver5:8004/sse", 
                "timeout": 600,
                "headers": None,
                "sse_read_timeout": 900
            },
            "MSSQL": {
                "transport": "sse",
                "url": "http://mcpserver3:8008/sse",
                "timeout": 600,
                "headers": None,
                "sse_read_timeout": 900
            }
        }
    }