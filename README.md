# LinkedIn MCP Server

A Model Context Protocol (MCP) server that provides LinkedIn API functionality using the `open_linkedin_api` library. This server allows you to interact with LinkedIn data through Claude Desktop and other MCP-compatible clients.

## Features

### Tools Available
- **get_profile**: Get LinkedIn profile information by public ID or URN ID
- **get_profile_contact_info**: Get contact information for a LinkedIn profile
- **get_profile_connections**: Get connections for a LinkedIn profile
- **search_people**: Search for people on LinkedIn with various filters
- **search_companies**: Search for companies on LinkedIn
- **get_company**: Get detailed company information
- **get_profile_posts**: Get posts from a LinkedIn profile
- **send_message**: Send messages on LinkedIn
- **get_conversations**: Get list of LinkedIn conversations
- **get_conversation_details**: Get conversation details for a specific profile
- **add_connection**: Send connection requests
- **get_current_user_profile**: Get your own profile information

### Resources Available
- **linkedin://profile/{public_id}**: Get formatted profile data as a resource
- **linkedin://company/{public_id}**: Get formatted company data as a resource

## Prerequisites

- Python 3.10 or higher
- uv package manager
- LinkedIn account credentials
- Claude Desktop (for integration)

## Installation

### Option 1: Quick Installation with uv (Recommended)

1. **Install uv** (if not already installed):
   
   **Windows:**
   ```powershell
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```
   
   **Linux/macOS:**
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Create project directory:**
   ```bash
   mkdir linkedin-mcp-server
   cd linkedin-mcp-server
   ```

3. **Download the server files** (copy the content from the artifacts above):
   - Save the main server code as `linkedin_server.py`
   - Save the requirements as `requirements.txt`
   - Save the environment template as `.env.example`
   - Save the project config as `pyproject.toml`

4. **Create virtual environment and install dependencies:**
   ```bash
   uv venv
   # Activate the virtual environment
   # Windows:
   .venv\Scripts\activate
   # Linux/macOS:
   source .venv/bin/activate
   
   # Install dependencies
   uv pip install -r requirements.txt
   ```

### Option 2: Manual Setup

1. **Clone or create the project directory:**
   ```bash
   mkdir linkedin-mcp-server
   cd linkedin-mcp-server
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv .venv
   # Activate the virtual environment
   # Windows:
   .venv\Scripts\activate
   # Linux/macOS:
   source .venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

1. **Create environment file:**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` file with your LinkedIn credentials:**
   ```bash
   LINKEDIN_USERNAME=your_email@example.com
   LINKEDIN_PASSWORD=your_linkedin_password
   DEBUG_MODE=false
   ```

   **⚠️ Security Note:** Keep your credentials secure and never commit the `.env` file to version control.

## Testing the Server

1. **Test with MCP Inspector** (recommended for development):
   ```bash
   uv run mcp dev linkedin_server.py
   ```
   
   This will open an interactive interface where you can test all the tools and resources.

2. **Test direct execution:**
   ```bash
   python linkedin_server.py
   ```

## Claude Desktop Integration

### Step 1: Find Claude Desktop Configuration

The configuration file location depends on your operating system:

**Windows:**
```
%APPDATA%\Claude\claude_desktop_config.json
```

**macOS:**
```
~/Library/Application Support/Claude/claude_desktop_config.json
```

**Linux:**
```
~/.config/Claude/claude_desktop_config.json
```

### Step 2: Update Configuration

Add the LinkedIn MCP server to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "linkedin": {
      "command": "python",
      "args": ["/absolute/path/to/your/linkedin_server.py"],
      "env": {
        "LINKEDIN_USERNAME": "your_email@example.com",
        "LINKEDIN_PASSWORD": "your_linkedin_password"
      }
    }
  }
}
```

**Alternative using uv:**
```json
{
  "mcpServers": {
    "linkedin": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/absolute/path/to/your/linkedin-mcp-server",
        "python",
        "linkedin_server.py"
      ]
    }
  }
}
```

### Step 3: Restart Claude Desktop

After updating the configuration, completely restart Claude Desktop for the changes to take effect.

### Step 4: Verify Integration

1. Open Claude Desktop
2. Look for the MCP tools icon (⚒️) in the input area
3. You should see "LinkedIn API Server" listed with all available tools
4. Test a simple tool like `get_current_user_profile` to verify the connection

## Usage Examples

Once integrated with Claude Desktop, you can use natural language to interact with LinkedIn:

- "Get my LinkedIn profile information"
- "Search for people who work at Microsoft in the AI field"
- "Find companies in the technology industry"
- "Get the profile of John Doe on LinkedIn"
- "Send a connection request to user with public ID 'john-doe-123'"

## Available Tools Reference

### Profile Tools
- `get_profile(public_id, urn_id)` - Get detailed profile information
- `get_profile_contact_info(public_id, urn_id)` - Get contact details
- `get_profile_connections(urn_id, limit)` - Get profile connections
- `get_profile_posts(public_id, urn_id, post_count)` - Get profile posts
- `get_current_user_profile()` - Get your own profile

### Search Tools
- `search_people(keywords, filters...)` - Search for people with various filters
- `search_companies(keywords, limit)` - Search for companies

### Company Tools
- `get_company(public_id)` - Get detailed company information

### Messaging Tools
- `send_message(message_body, conversation_urn_id, recipients)` - Send messages
- `get_conversations()` - Get conversation list
- `get_conversation_details(profile_urn_id)` - Get conversation details

### Connection Tools
- `add_connection(profile_public_id, message, profile_urn)` - Send connection requests

## Troubleshooting

### Common Issues

1. **Authentication Errors:**
   - Verify LinkedIn credentials in `.env` file
   - Check if your LinkedIn account has any restrictions
   - Try logging in manually to LinkedIn to ensure account is active

2. **Module Import Errors:**
   - Ensure all dependencies are installed: `uv pip install -r requirements.txt`
   - Verify virtual environment is activated

3. **Claude Desktop Integration Issues:**
   - Check the configuration file path is correct
   - Ensure the path to `linkedin_server.py` is absolute
   - Restart Claude Desktop completely
   - Check Claude Desktop logs for errors

4. **Rate Limiting:**
   - LinkedIn may impose rate limits on API calls
   - Wait between requests if you encounter rate limiting
   - Consider implementing delays in your usage

### Logging

Enable debug mode in your `.env` file to get more detailed logs:
```bash
DEBUG_MODE=true
```

### Getting Help

If you encounter issues:
1. Check the console output for error messages
2. Verify your LinkedIn credentials are correct
3. Test the server independently before integrating with Claude
4. Check Claude Desktop logs for integration issues

## Security Considerations

- Never commit your `.env` file or credentials to version control
- Use strong, unique passwords for your LinkedIn account
- Consider using LinkedIn's two-factor authentication
- Monitor your LinkedIn account for unusual activity
- Be mindful of LinkedIn's terms of service when using automation

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## Disclaimer

This project is not officially affiliated with LinkedIn. Use responsibly and in accordance with LinkedIn's terms of service and API usage policies.