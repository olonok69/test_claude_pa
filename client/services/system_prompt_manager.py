# client/services/system_prompt_manager.py
import streamlit as st
import os
import json
from typing import Dict, List, Optional
from datetime import datetime
import logging

class SystemPromptManager:
    """Manages system prompts for MCP client with tool-specific generation."""
    
    def __init__(self):
        self.config_path = "keys/system_prompts.json"
        self.ensure_config_directory()
    
    def ensure_config_directory(self):
        """Ensure the config directory exists."""
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
    
    def generate_default_system_prompt(self, tools: List, servers: Dict) -> str:
        """Generate a default system prompt based on connected tools and servers."""
        # Analyze available tools
        tool_analysis = self._analyze_tools(tools)
        server_info = self._analyze_servers(servers)
        
        # Build the system prompt
        prompt_parts = [
            "You are an AI assistant with access to specialized tools through MCP (Model Context Protocol) servers.",
            "",
            "**Your Capabilities:**"
        ]
        
        # Add server-specific capabilities
        if server_info['mssql_available']:
            prompt_parts.extend([
                "- **MSSQL Database Operations**: Execute SQL queries, explore tables, and manage database data",
                "  * Use proper SQL Server syntax (TOP instead of LIMIT)",
                "  * Available tools: " + ", ".join(tool_analysis['mssql_tools'])
            ])
        
        if server_info['other_servers']:
            prompt_parts.extend([
                "- **Additional Services**: " + ", ".join(server_info['other_servers']),
                "  * Available tools: " + ", ".join(tool_analysis['other_tools'])
            ])
        
        # Add usage guidelines
        prompt_parts.extend([
            "",
            "**Usage Guidelines:**",
            "1. Always use the appropriate tool for the user's request",
            "2. For database operations, use proper SQL syntax for the target system",
            "3. Provide clear explanations of what you're doing and why",
            "4. If you need to explore or understand data structure, use schema/listing tools first",
            "5. Handle errors gracefully and suggest alternatives when needed"
        ])
        
        # Add tool-specific instructions
        if tool_analysis['mssql_tools']:
            prompt_parts.extend([
                "",
                "**MSSQL Specific Instructions:**",
                "- Use SELECT TOP n instead of LIMIT",
                "- Use GETDATE() for current date/time",
                "- Use LEN() instead of LENGTH()",
                "- Use CHARINDEX() instead of LOCATE()",
                "- Always explore table structure before complex queries"
            ])
        
        prompt_parts.extend([
            "",
            "**Remember**: You can see the full conversation history, so maintain context across interactions."
        ])
        
        return "\n".join(prompt_parts)
    
    def _analyze_tools(self, tools: List) -> Dict:
        """Analyze available tools and categorize them."""
        mssql_tools = []
        other_tools = []
        
        for tool in tools:
            tool_name = tool.name.lower()
            
            # Check if it's an MSSQL tool
            if any(keyword in tool_name for keyword in ['sql', 'mssql', 'execute_sql', 'list_tables', 'describe_table', 'get_table_sample']):
                mssql_tools.append(tool.name)
            else:
                other_tools.append(tool.name)
        
        return {
            'mssql_tools': mssql_tools,
            'other_tools': other_tools,
            'total_tools': len(tools)
        }
    
    def _analyze_servers(self, servers: Dict) -> Dict:
        """Analyze connected servers."""
        mssql_available = 'MSSQL' in servers
        other_servers = [name for name in servers.keys() if name != 'MSSQL']
        
        return {
            'mssql_available': mssql_available,
            'other_servers': other_servers,
            'total_servers': len(servers)
        }
    
    def save_system_prompt(self, prompt: str, is_custom: bool = False) -> bool:
        """Save system prompt to configuration."""
        try:
            config = self.load_config()
            config['system_prompt'] = prompt
            config['is_custom'] = is_custom
            config['last_updated'] = datetime.now().isoformat()
            
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            # Store in session state for immediate use
            st.session_state['system_prompt'] = prompt
            st.session_state['system_prompt_is_custom'] = is_custom
            
            logging.info(f"System prompt saved - Custom: {is_custom}")
            return True
            
        except Exception as e:
            logging.error(f"Error saving system prompt: {str(e)}")
            return False
    
    def load_system_prompt(self) -> Optional[str]:
        """Load system prompt from configuration."""
        try:
            config = self.load_config()
            prompt = config.get('system_prompt')
            
            if prompt:
                # Store in session state
                st.session_state['system_prompt'] = prompt
                st.session_state['system_prompt_is_custom'] = config.get('is_custom', False)
                
            return prompt
            
        except Exception as e:
            logging.error(f"Error loading system prompt: {str(e)}")
            return None
    
    def load_config(self) -> Dict:
        """Load configuration from file."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}
    
    def get_current_prompt(self) -> Optional[str]:
        """Get the current system prompt from session state or config."""
        # First check session state
        if 'system_prompt' in st.session_state:
            return st.session_state['system_prompt']
        
        # Then check config file
        return self.load_system_prompt()
    
    def is_custom_prompt(self) -> bool:
        """Check if current prompt is custom (user-modified)."""
        return st.session_state.get('system_prompt_is_custom', False)
    
    def reset_to_default(self) -> bool:
        """Reset to default system prompt based on current tools/servers."""
        try:
            tools = st.session_state.get('tools', [])
            servers = st.session_state.get('servers', {})
            
            if not tools or not servers:
                logging.warning("No tools or servers available for prompt generation")
                return False
            
            default_prompt = self.generate_default_system_prompt(tools, servers)
            return self.save_system_prompt(default_prompt, is_custom=False)
            
        except Exception as e:
            logging.error(f"Error resetting to default prompt: {str(e)}")
            return False
    
    def get_prompt_stats(self) -> Dict:
        """Get statistics about the current prompt."""
        prompt = self.get_current_prompt()
        if not prompt:
            return {}
        
        return {
            'character_count': len(prompt),
            'word_count': len(prompt.split()),
            'line_count': len(prompt.split('\n')),
            'is_custom': self.is_custom_prompt(),
            'last_updated': self.load_config().get('last_updated', 'Unknown')
        }
    
    def validate_prompt(self, prompt: str) -> tuple[bool, List[str]]:
        """Validate a system prompt."""
        issues = []
        
        if not prompt or not prompt.strip():
            issues.append("Prompt cannot be empty")
        
        if len(prompt) < 50:
            issues.append("Prompt seems too short (less than 50 characters)")
        
        if len(prompt) > 10000:
            issues.append("Prompt is very long (over 10,000 characters)")
        
        # Check for basic AI assistant elements
        prompt_lower = prompt.lower()
        if 'assistant' not in prompt_lower and 'ai' not in prompt_lower:
            issues.append("Consider mentioning that you are an AI assistant")
        
        if 'tool' not in prompt_lower and 'mcp' not in prompt_lower:
            issues.append("Consider mentioning tool capabilities")
        
        return len(issues) == 0, issues
    
    def export_prompt_config(self) -> str:
        """Export current prompt configuration as JSON."""
        config = self.load_config()
        config['exported_at'] = datetime.now().isoformat()
        config['tools_info'] = {
            'total_tools': len(st.session_state.get('tools', [])),
            'total_servers': len(st.session_state.get('servers', {}))
        }
        
        return json.dumps(config, indent=2)
    
    def import_prompt_config(self, config_json: str) -> bool:
        """Import prompt configuration from JSON."""
        try:
            config = json.loads(config_json)
            
            if 'system_prompt' not in config:
                return False
            
            # Validate the imported prompt
            is_valid, issues = self.validate_prompt(config['system_prompt'])
            if not is_valid:
                logging.error(f"Invalid imported prompt: {issues}")
                return False
            
            # Save the imported config
            return self.save_system_prompt(
                config['system_prompt'], 
                config.get('is_custom', True)
            )
            
        except Exception as e:
            logging.error(f"Error importing prompt config: {str(e)}")
            return False