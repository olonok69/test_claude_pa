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

# Load server configuration
config_path = os.path.join('.', 'servers_config.json')
if os.path.exists(config_path):
    with open(config_path, 'r') as f:
        SERVER_CONFIG = json.load(f)