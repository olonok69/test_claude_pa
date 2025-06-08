import os
import json
from dotenv import load_dotenv

load_dotenv()
env = os.getenv

# Model mapping
MODEL_OPTIONS = {
    'OpenAI': 'gpt-4o',
    'Antropic': 'claude-opus-4-20250514',
    'Google': 'gemini-2.0-flash-001',

    }
 #'Bedrock': 'us.anthropic.claude-3-7-sonnet-20250219-v1:0'
# Streamlit defaults
DEFAULT_MAX_TOKENS = 4096
DEFAULT_TEMPERATURE = 1.0

# Load server configuration
config_path = os.path.join('.', 'servers_config.json')
if os.path.exists(config_path):
    with open(config_path, 'r') as f:
        SERVER_CONFIG = json.load(f)