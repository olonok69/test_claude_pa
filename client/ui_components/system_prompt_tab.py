# client/ui_components/system_prompt_tab.py
import streamlit as st
import json
from datetime import datetime
from services.system_prompt_manager import SystemPromptManager
from services.mcp_service import connect_to_mcp_servers, disconnect_from_mcp_servers
from utils.async_helpers import reset_connection_state

def create_system_prompt_tab():
    """Create the System Prompt management tab."""
    st.header("🎯 System Prompt Management")
    st.markdown("Configure and customize the AI assistant's system prompt based on connected MCP tools.")
    
    # Check if MCP servers are connected
    if not st.session_state.get("agent") or not st.session_state.get("tools"):
        st.warning("🔌 MCP servers must be connected to manage system prompts.")
        st.info("👉 Go to the **Connections** tab to establish server connections first.")
        return
    
    # Initialize prompt manager
    prompt_manager = SystemPromptManager()
    
    # Create tabs within the prompt management
    overview_tab, editor_tab, templates_tab, settings_tab = st.tabs(["📋 Overview", "✏️ Editor", "📝 Templates", "⚙️ Settings"])
    
    with overview_tab:
        create_prompt_overview(prompt_manager)
    
    with editor_tab:
        create_prompt_editor(prompt_manager)
    
    with templates_tab:
        create_prompt_templates(prompt_manager)
    
    with settings_tab:
        create_prompt_settings(prompt_manager)

def create_prompt_overview(prompt_manager: SystemPromptManager):
    """Create the overview section."""
    st.subheader("📊 Current System Prompt Status")
    
    # Get current prompt and stats
    current_prompt = prompt_manager.get_current_prompt()
    stats = prompt_manager.get_prompt_stats()
    
    if not current_prompt:
        # No prompt exists, offer to create default
        st.warning("⚠️ No system prompt is currently configured.")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔧 Generate Default Prompt", type="primary", use_container_width=True):
                if prompt_manager.reset_to_default():
                    st.success("✅ Default system prompt generated!")
                    st.rerun()
                else:
                    st.error("❌ Failed to generate default prompt")
        
        with col2:
            if st.button("📝 Create Custom Prompt", use_container_width=True):
                st.session_state['create_custom_prompt'] = True
                st.rerun()
        
        return
    
    # Display prompt statistics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Characters", stats.get('character_count', 0))
    
    with col2:
        st.metric("Words", stats.get('word_count', 0))
    
    with col3:
        st.metric("Lines", stats.get('line_count', 0))
    
    with col4:
        prompt_type = "Custom" if stats.get('is_custom', False) else "Default"
        st.metric("Type", prompt_type)
    
    # Show current prompt preview
    st.subheader("📖 Current Prompt Preview")
    
    # Truncate for preview
    preview_text = current_prompt[:500] + "..." if len(current_prompt) > 500 else current_prompt
    
    st.text_area(
        "System Prompt Preview",
        value=preview_text,
        height=200,
        disabled=True,
        label_visibility="collapsed"
    )
    
    # Action buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("✏️ Edit Prompt", use_container_width=True):
            st.session_state['edit_prompt_mode'] = True
            st.rerun()
    
    with col2:
        if st.button("🔄 Reset to Default", use_container_width=True):
            st.session_state['confirm_reset_prompt'] = True
            st.rerun()
    
    with col3:
        if st.button("📤 Export Config", use_container_width=True):
            export_config = prompt_manager.export_prompt_config()
            st.download_button(
                label="💾 Download Config",
                data=export_config,
                file_name=f"system_prompt_config_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
    
    # Handle confirmation dialogs
    if st.session_state.get('confirm_reset_prompt'):
        st.warning("⚠️ This will reset the system prompt to default based on current tools and reconnect to MCP servers.")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Confirm Reset", type="primary"):
                if reset_prompt_and_reconnect(prompt_manager):
                    st.success("✅ System prompt reset and reconnected!")
                    st.session_state['confirm_reset_prompt'] = False
                    st.rerun()
                else:
                    st.error("❌ Failed to reset prompt")
        
        with col2:
            if st.button("❌ Cancel"):
                st.session_state['confirm_reset_prompt'] = False
                st.rerun()

def create_prompt_editor(prompt_manager: SystemPromptManager):
    """Create the prompt editor section."""
    st.subheader("✏️ System Prompt Editor")
    
    # Get current prompt
    current_prompt = prompt_manager.get_current_prompt()
    
    if not current_prompt:
        st.info("No system prompt loaded. Create one in the Overview tab first.")
        return
    
    # Editor
    st.markdown("**Edit System Prompt:**")
    
    edited_prompt = st.text_area(
        "System Prompt",
        value=current_prompt,
        height=400,
        help="Edit the system prompt that will be used by the AI assistant",
        label_visibility="collapsed"
    )
    
    # Validation
    if edited_prompt != current_prompt:
        is_valid, issues = prompt_manager.validate_prompt(edited_prompt)
        
        if not is_valid:
            st.error("❌ Prompt validation issues:")
            for issue in issues:
                st.error(f"  • {issue}")
        else:
            st.success("✅ Prompt validation passed")
    
    # Save controls
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("💾 Save Changes", type="primary", use_container_width=True):
            if edited_prompt != current_prompt:
                is_valid, issues = prompt_manager.validate_prompt(edited_prompt)
                
                if is_valid:
                    if save_prompt_and_reconnect(prompt_manager, edited_prompt):
                        st.success("✅ Prompt saved and system reconnected!")
                        st.rerun()
                    else:
                        st.error("❌ Failed to save prompt")
                else:
                    st.error("❌ Cannot save invalid prompt")
            else:
                st.info("No changes to save")
    
    with col2:
        if st.button("🔄 Reload Original", use_container_width=True):
            st.rerun()
    
    with col3:
        if st.button("👁️ Preview Changes", use_container_width=True):
            st.session_state['preview_prompt'] = edited_prompt
            st.rerun()
    
    # Preview section
    if st.session_state.get('preview_prompt'):
        st.markdown("---")
        st.subheader("👁️ Prompt Preview")
        
        preview_prompt = st.session_state['preview_prompt']
        
        # Show differences
        if preview_prompt != current_prompt:
            st.markdown("**Changes detected:**")
            st.info(f"Characters: {len(current_prompt)} → {len(preview_prompt)} ({len(preview_prompt) - len(current_prompt):+d})")
            st.info(f"Words: {len(current_prompt.split())} → {len(preview_prompt.split())} ({len(preview_prompt.split()) - len(current_prompt.split()):+d})")
        
        # Show preview
        st.text_area(
            "Preview",
            value=preview_prompt,
            height=200,
            disabled=True,
            label_visibility="collapsed"
        )
        
        if st.button("❌ Close Preview"):
            del st.session_state['preview_prompt']
            st.rerun()

def create_prompt_templates(prompt_manager: SystemPromptManager):
    """Create the templates section."""
    st.subheader("📝 System Prompt Templates")
    
    # Get current tools and servers for template generation
    tools = st.session_state.get('tools', [])
    servers = st.session_state.get('servers', {})
    
    if not tools or not servers:
        st.warning("No tools or servers available for template generation.")
        return
    
    # Analyze current setup
    tool_analysis = prompt_manager._analyze_tools(tools)
    server_info = prompt_manager._analyze_servers(servers)
    
    # Show current setup
    st.markdown("**Current MCP Setup:**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Connected Servers:**")
        for server_name in servers.keys():
            st.write(f"• {server_name}")
    
    with col2:
        st.markdown("**Available Tools:**")
        st.write(f"• MSSQL Tools: {len(tool_analysis['mssql_tools'])}")
        st.write(f"• Other Tools: {len(tool_analysis['other_tools'])}")
    
    # Template options
    st.markdown("---")
    st.subheader("📋 Template Options")
    
    template_options = {
        "Default": "Standard template based on current tools",
        "MSSQL Focused": "Optimized for database operations",
        "Minimal": "Minimal prompt for basic functionality",
        "Detailed": "Comprehensive prompt with detailed instructions"
    }
    
    selected_template = st.selectbox(
        "Choose Template Type",
        options=list(template_options.keys()),
        help="Select a template type to generate"
    )
    
    st.info(f"📝 {template_options[selected_template]}")
    
    # Generate template
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔧 Generate Template", type="primary", use_container_width=True):
            template = generate_template(prompt_manager, selected_template, tool_analysis, server_info)
            st.session_state['generated_template'] = template
            st.rerun()
    
    with col2:
        if st.button("📋 Use Current as Template", use_container_width=True):
            current_prompt = prompt_manager.get_current_prompt()
            if current_prompt:
                st.session_state['generated_template'] = current_prompt
                st.rerun()
    
    # Show generated template
    if st.session_state.get('generated_template'):
        st.markdown("---")
        st.subheader("📄 Generated Template")
        
        template_text = st.session_state['generated_template']
        
        st.text_area(
            "Template",
            value=template_text,
            height=300,
            disabled=True,
            label_visibility="collapsed"
        )
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("✅ Use This Template", type="primary"):
                if save_prompt_and_reconnect(prompt_manager, template_text):
                    st.success("✅ Template applied and system reconnected!")
                    del st.session_state['generated_template']
                    st.rerun()
                else:
                    st.error("❌ Failed to apply template")
        
        with col2:
            if st.button("✏️ Edit Template"):
                st.session_state['edit_template'] = template_text
                del st.session_state['generated_template']
                st.rerun()
        
        with col3:
            if st.button("❌ Discard Template"):
                del st.session_state['generated_template']
                st.rerun()
    
    # Edit template
    if st.session_state.get('edit_template'):
        st.markdown("---")
        st.subheader("✏️ Edit Template")
        
        edited_template = st.text_area(
            "Edit Template",
            value=st.session_state['edit_template'],
            height=300,
            label_visibility="collapsed"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("💾 Save Edited Template", type="primary"):
                if save_prompt_and_reconnect(prompt_manager, edited_template):
                    st.success("✅ Template saved and system reconnected!")
                    del st.session_state['edit_template']
                    st.rerun()
                else:
                    st.error("❌ Failed to save template")
        
        with col2:
            if st.button("❌ Cancel Edit"):
                del st.session_state['edit_template']
                st.rerun()

def create_prompt_settings(prompt_manager: SystemPromptManager):
    """Create the settings section."""
    st.subheader("⚙️ System Prompt Settings")
    
    # Import/Export
    st.markdown("**Import/Export Configuration:**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Export Current Config:**")
        if st.button("📤 Export Configuration", use_container_width=True):
            config = prompt_manager.export_prompt_config()
            st.download_button(
                label="💾 Download Config File",
                data=config,
                file_name=f"system_prompt_config_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
    
    with col2:
        st.markdown("**Import Configuration:**")
        uploaded_file = st.file_uploader(
            "Choose config file",
            type=['json'],
            help="Upload a previously exported configuration file"
        )
        
        if uploaded_file is not None:
            try:
                config_content = uploaded_file.read().decode('utf-8')
                
                if st.button("📥 Import Configuration", type="primary"):
                    if prompt_manager.import_prompt_config(config_content):
                        st.success("✅ Configuration imported successfully!")
                        st.info("🔄 Reconnecting to MCP servers with new prompt...")
                        
                        # Reconnect with new prompt
                        if reconnect_mcp_servers():
                            st.success("✅ System reconnected with imported prompt!")
                            st.rerun()
                        else:
                            st.error("❌ Failed to reconnect with imported prompt")
                    else:
                        st.error("❌ Failed to import configuration")
                        
            except Exception as e:
                st.error(f"❌ Error reading config file: {str(e)}")
    
    # Advanced settings
    st.markdown("---")
    st.subheader("🔧 Advanced Settings")
    
    # Auto-regenerate prompt on tool changes
    auto_regenerate = st.checkbox(
        "Auto-regenerate prompt when tools change",
        value=st.session_state.get('auto_regenerate_prompt', False),
        help="Automatically update the system prompt when MCP tools change"
    )
    st.session_state['auto_regenerate_prompt'] = auto_regenerate
    
    # Backup settings
    backup_prompts = st.checkbox(
        "Backup prompts before changes",
        value=st.session_state.get('backup_prompts', True),
        help="Create backups of prompts before making changes"
    )
    st.session_state['backup_prompts'] = backup_prompts
    
    # Validation settings
    strict_validation = st.checkbox(
        "Strict prompt validation",
        value=st.session_state.get('strict_validation', False),
        help="Apply stricter validation rules for system prompts"
    )
    st.session_state['strict_validation'] = strict_validation
    
    # Debug settings
    st.markdown("---")
    st.subheader("🐛 Debug Settings")
    
    show_prompt_debug = st.checkbox(
        "Show prompt debug information",
        value=st.session_state.get('show_prompt_debug', False),
        help="Display debug information about prompt usage"
    )
    st.session_state['show_prompt_debug'] = show_prompt_debug
    
    if show_prompt_debug:
        current_prompt = prompt_manager.get_current_prompt()
        if current_prompt:
            st.markdown("**Debug Information:**")
            
            debug_info = {
                "Prompt Length": len(current_prompt),
                "Word Count": len(current_prompt.split()),
                "Line Count": len(current_prompt.split('\n')),
                "Is Custom": prompt_manager.is_custom_prompt(),
                "Tools Available": len(st.session_state.get('tools', [])),
                "Servers Connected": len(st.session_state.get('servers', {}))
            }
            
            for key, value in debug_info.items():
                st.write(f"**{key}:** {value}")
    
    # Reset all settings
    st.markdown("---")
    if st.button("🔄 Reset All Settings", help="Reset all prompt settings to defaults"):
        settings_keys = [
            'auto_regenerate_prompt',
            'backup_prompts', 
            'strict_validation',
            'show_prompt_debug'
        ]
        
        for key in settings_keys:
            if key in st.session_state:
                del st.session_state[key]
        
        st.success("✅ All settings reset to defaults")
        st.rerun()

def generate_template(prompt_manager: SystemPromptManager, template_type: str, tool_analysis: dict, server_info: dict) -> str:
    """Generate a template based on the selected type."""
    if template_type == "Default":
        return prompt_manager.generate_default_system_prompt(
            st.session_state.get('tools', []),
            st.session_state.get('servers', {})
        )
    
    elif template_type == "MSSQL Focused":
        return generate_mssql_focused_template(tool_analysis, server_info)
    
    elif template_type == "Minimal":
        return generate_minimal_template(tool_analysis, server_info)
    
    elif template_type == "Detailed":
        return generate_detailed_template(tool_analysis, server_info)
    
    else:
        return prompt_manager.generate_default_system_prompt(
            st.session_state.get('tools', []),
            st.session_state.get('servers', {})
        )

def generate_mssql_focused_template(tool_analysis: dict, server_info: dict) -> str:
    """Generate MSSQL-focused template."""
    template = """You are an expert MSSQL database assistant with access to database tools through MCP servers.

**Your Primary Role:**
- Execute SQL queries and database operations
- Analyze database structure and data
- Provide database insights and recommendations

**MSSQL Tools Available:**
""" + "\n".join(f"- {tool}" for tool in tool_analysis['mssql_tools']) + """

**Key MSSQL Guidelines:**
- Always use SELECT TOP n instead of LIMIT n
- Use GETDATE() for current date/time
- Use LEN() instead of LENGTH()
- Use CHARINDEX() instead of LOCATE()
- Explore table structure before complex queries
- Use proper SQL Server data types and functions

**Workflow:**
1. Understand the user's database question
2. Explore schema/structure if needed
3. Execute appropriate SQL queries
4. Explain results clearly
5. Suggest optimizations when relevant

Always provide clear explanations of your SQL queries and their results."""
    
    return template

def generate_minimal_template(tool_analysis: dict, server_info: dict) -> str:
    """Generate minimal template."""
    template = """You are an AI assistant with database tools.

Available tools: """ + ", ".join(tool_analysis['mssql_tools'] + tool_analysis['other_tools']) + """

Use the appropriate tool for each request and explain your actions clearly."""
    
    return template

def generate_detailed_template(tool_analysis: dict, server_info: dict) -> str:
    """Generate detailed template."""
    template = """You are an advanced AI assistant with comprehensive database and system capabilities through MCP (Model Context Protocol) servers.

**DETAILED CAPABILITIES:**

**Database Operations (MSSQL):**
""" + "\n".join(f"- {tool}: Database operation tool" for tool in tool_analysis['mssql_tools']) + """

**Additional Tools:**
""" + "\n".join(f"- {tool}: System operation tool" for tool in tool_analysis['other_tools']) + """

**COMPREHENSIVE GUIDELINES:**

**Database Query Best Practices:**
1. Always examine table structure before complex queries
2. Use proper SQL Server syntax and functions
3. Optimize queries for performance
4. Handle errors gracefully
5. Provide clear explanations of all operations

**SQL Server Specific Instructions:**
- SELECT TOP n instead of LIMIT n
- Use GETDATE() for timestamps
- Use LEN() for string length
- Use CHARINDEX() for string searching
- Use ISNULL() for null handling
- Use proper JOIN syntax
- Consider indexes and performance

**Communication Style:**
- Explain what you're doing step by step
- Provide context for your decisions
- Offer alternatives when appropriate
- Ask clarifying questions if needed

**Error Handling:**
- Gracefully handle database errors
- Suggest fixes for common issues
- Provide alternative approaches
- Explain error meanings to users

**Security Considerations:**
- Use parameterized queries when possible
- Avoid SQL injection risks
- Respect data privacy
- Follow least privilege principles

Remember: You have access to the full conversation history, so maintain context and build upon previous interactions naturally."""
    
    return template

def save_prompt_and_reconnect(prompt_manager: SystemPromptManager, prompt: str) -> bool:
    """Save prompt and reconnect to MCP servers."""
    try:
        # Save the prompt
        if not prompt_manager.save_system_prompt(prompt, is_custom=True):
            return False
        
        # Reconnect to MCP servers
        return reconnect_mcp_servers()
        
    except Exception as e:
        st.error(f"Error saving prompt and reconnecting: {str(e)}")
        return False

def reset_prompt_and_reconnect(prompt_manager: SystemPromptManager) -> bool:
    """Reset prompt to default and reconnect to MCP servers."""
    try:
        # Reset to default
        if not prompt_manager.reset_to_default():
            return False
        
        # Reconnect to MCP servers
        return reconnect_mcp_servers()
        
    except Exception as e:
        st.error(f"Error resetting prompt and reconnecting: {str(e)}")
        return False

def reconnect_mcp_servers() -> bool:
    """Reconnect to MCP servers with new system prompt."""
    try:
        # Disconnect first
        reset_connection_state()
        
        # Small delay to ensure cleanup
        import time
        time.sleep(1)
        
        # Reconnect
        return connect_to_mcp_servers()
        
    except Exception as e:
        st.error(f"Error reconnecting to MCP servers: {str(e)}")
        return False