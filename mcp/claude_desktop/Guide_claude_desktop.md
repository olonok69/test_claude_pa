# Claude Desktop Application Documentation Guide

## Table of Contents
1. [Introduction](#introduction)
2. [System Requirements](#system-requirements)
3. [Installation Guide](#installation-guide)
4. [Getting Started](#getting-started)
5. [Core Features](#core-features)
6. [Model Context Protocol (MCP)](#model-context-protocol-mcp)
7. [Projects Functionality](#projects-functionality)
8. [Interface Navigation](#interface-navigation)
9. [Desktop vs Web Version](#desktop-vs-web-version)
10. [Configuration and Settings](#configuration-and-settings)
11. [Best Practices](#best-practices)
12. [Troubleshooting](#troubleshooting)

## Introduction

The Claude desktop application is a native desktop client that brings Claude AI's capabilities directly to your desktop with enhanced performance, Model Context Protocol (MCP) support, and advanced productivity features. Available for Windows and macOS, it offers a more integrated and efficient workflow compared to the web version.

## System Requirements

### Windows
- **Operating System**: Windows 10 (64-bit) or later
- **Processor**: Modern multi-core CPU (8+ cores recommended)
- **Memory**: Minimum 16 GB RAM (32 GB+ recommended)
- **Storage**: SSD with at least 100 GB free space
- **Graphics**: NVIDIA GPU with CUDA support recommended
- **Dependencies**: Node.js required for MCP functionality

### macOS
- **Operating System**: macOS 11 (Big Sur) or later
- **Processor**: Apple Silicon or Intel (both supported)
- **Memory**: 16 GB RAM minimum (32 GB+ recommended)
- **Storage**: SSD with 100 GB+ free space
- **Dependencies**: Node.js for MCP servers

### Linux (Community Support)
- **Note**: No official support from Anthropic
- **Distributions**: Ubuntu 20.04 LTS+, Debian 10+, Fedora, Arch Linux
- **Available through**: Community-maintained build scripts

## Installation Guide

### Windows Installation

1. **Download the installer**
   - Visit [claude.ai/download](https://claude.ai/download)
   - Download the Windows installer (typically "ClaudeSetup.exe")

2. **Run the installation**
   ```
   - Double-click the installer
   - Follow the installation wizard
   - Choose installation directory
   - Complete the installation
   ```

3. **Launch and sign in**
   - Find Claude in Start menu
   - Sign in with your Claude account

### macOS Installation

1. **Download the application**
   - Visit [claude.ai/download](https://claude.ai/download)
   - Download the macOS disk image ("Claude.dmg")

2. **Install the application**
   ```
   - Double-click the .dmg file
   - Drag Claude to Applications folder
   - Unmount the disk image
   ```

3. **First launch**
   - Open from Applications folder
   - May need to approve in System Preferences > Security & Privacy
   - Enable microphone access for voice features

### Linux Installation (Community)

**Debian/Ubuntu:**
```bash
# Clone repository
git clone https://github.com/aaddrick/claude-desktop-debian.git
cd claude-desktop-debian

# Build and install
./build.sh
sudo dpkg -i ./claude-desktop_VERSION_ARCHITECTURE.deb
sudo apt --fix-broken install
```

## Getting Started

### Initial Setup

1. **Sign in** with your Claude account
2. **Choose your default model** (Sonnet, Haiku, or Opus)
3. **Configure preferences**:
   - Theme (dark/light mode)
   - Keyboard shortcuts
   - Privacy settings

### Basic Navigation

- **Main chat area**: Central conversation interface
- **Sidebar**: Projects, chat history, and navigation
- **Input area**: Text input with tool access
- **Settings**: Accessed via Claude menu (not in-app settings)

## Core Features

### Essential Capabilities

- **Multi-model support**: Claude 3.5 Sonnet, Haiku, and Opus
- **File handling**: Upload documents, images, PDFs (up to 30MB)
- **Artifacts**: Generate and refine interactive content
- **Voice dictation**: Speak to Claude using microphone
- **Projects**: Organize conversations with persistent context
- **Analysis tool**: Execute code for calculations
- **Screenshot tool**: Capture images from screen

### Keyboard Shortcuts

- **Global hotkey**:
  - macOS: `Option + Space`
  - Windows: `Ctrl + Alt + Space`
- **New chat**: `Ctrl/Cmd + K`
- **Send message**: `Enter`
- **New line**: `Shift + Enter`

## Model Context Protocol (MCP)

### What is MCP?

MCP is an open standard that enables secure communication between Claude and external tools. Think of it as a "USB port for AI" - it provides standardized connections to various data sources and tools.

### Setting Up MCP

1. **Prerequisites**
   - Node.js version 16 or higher
   - Latest Claude Desktop version

2. **Access configuration**
   ```
   Claude menu → Settings → Developer → Edit Config
   ```

3. **Configuration file location**
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

### Basic MCP Configuration

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "/Users/username/Desktop",
        "/Users/username/Documents"
      ]
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "your_token_here"
      }
    }
  }
}
```

### Available MCP Servers

**Official Servers:**
- Filesystem - Local file operations
- GitHub - Repository management
- Slack - Team communication
- Google Drive - Cloud storage access
- PostgreSQL - Database operations
- Puppeteer - Browser automation

**Community Servers:**
- AWS, Docker, MongoDB, Notion, Discord, Firebase, Kubernetes, and more

### Using MCP Features

1. **Tool discovery**: Look for the slider icon in the input area
2. **Permission requests**: Claude asks before executing tools
3. **Example commands**:
   - "Create a new file called notes.txt"
   - "Show recent commits in my repository"
   - "Search my Google Drive for project documents"

## Projects Functionality

### Creating Projects (Pro/Team/Enterprise only)

1. Click **"Projects"** in the upper left corner
2. Select **"New Project"**
3. Provide name and description
4. Set visibility (Team plans only)

### Project Features

- **200K token context window** (~500 pages)
- **Custom instructions**: Define Claude's behavior per project
- **Knowledge base**: Upload and manage documents
- **Persistent context**: Maintains conversation history
- **Team collaboration**: Share projects with team members

### Managing Knowledge Base

1. **Add content** via "Add Content" button
2. **Supported formats**: PDF, DOCX, CSV, TXT, HTML, RTF, EPUB
3. **File size limit**: 30MB per file
4. **Automatic RAG mode**: Activates when approaching token limits

### Custom Instructions Example

```
Role: Senior Python Developer
Focus: Clean, efficient code with comprehensive documentation
Style: Professional but approachable
Output: Include type hints and docstrings
```

## Interface Navigation

### Main Layout

```
┌─────────────┬──────────────────────┬─────────────┐
│   Sidebar   │     Chat Area        │  Knowledge  │
│             │                      │    Panel    │
│ • Projects  │   Conversation       │             │
│ • History   │                      │ • Documents │
│ • Starred   │                      │ • Settings  │
└─────────────┴──────────────────────┴─────────────┘
                  [Input Area with Tools]
```

### Key Interface Elements

- **Tool slider**: Bottom left of input (when MCP configured)
- **Project selector**: Dropdown in main chat interface
- **Three-dot menu**: Project settings and options
- **Star icon**: Quick project favoriting
- **Activity feed**: Team collaboration updates

## Desktop vs Web Version

### Desktop Advantages

| Feature | Desktop | Web |
|---------|---------|-----|
| MCP Integration | ✓ | ✗ |
| Native Performance | ✓ | ✗ |
| System Integration | ✓ | ✗ |
| Offline Prep | ✓ | ✗ |
| Global Shortcuts | ✓ | ✗ |
| File System Access | ✓ | Limited |

### Desktop Limitations

- No Computer Use feature (web/API only)
- Limited to Windows/macOS officially
- Same core AI models as web

## Configuration and Settings

### Accessing Settings

- **Windows**: `Ctrl + ,`
- **macOS**: `Cmd + ,`
- **Developer settings**: Claude menu → Settings → Developer

### Configuration Options

```json
{
  "mcpServers": {
    // MCP server configurations
  },
  "theme": "dark",
  "shortcuts": {
    "globalHotkey": "Alt+Space"
  },
  "privacy": {
    "optOutTraining": true
  }
}
```

### Security Configuration

- **File access restrictions**: Limit MCP to specific directories
- **API key management**: Store securely in config
- **Permission controls**: Explicit approval for operations
- **Environment isolation**: MCP servers run sandboxed

## Best Practices

### Effective Usage

1. **Model Selection**
   - Use Haiku for simple tasks
   - Use Sonnet for balanced performance
   - Use Opus for complex reasoning

2. **Prompt Engineering**
   - Be specific and clear
   - Use XML tags for structure
   - Provide context in Projects

3. **MCP Integration**
   - Start with filesystem access
   - Add servers incrementally
   - Monitor performance impact

### Workflow Optimization

- **Batch related tasks** for efficiency
- **Use keyboard shortcuts** for speed
- **Organize with Projects** for context
- **Create templates** for common patterns

### Performance Tips

- **Close unnecessary apps** to free resources
- **Limit concurrent MCP servers**
- **Clear cache regularly**
- **Update dependencies** frequently

## Troubleshooting

### Common Issues and Solutions

#### Installation Problems

**Issue**: App won't launch
```
Solutions:
- Verify OS compatibility
- Update to latest OS version
- Check system requirements
- Run as Administrator (Windows)
```

**Issue**: macOS security block
```
Solution:
System Preferences → Security & Privacy → General → "Open Anyway"
```

#### MCP Connection Issues

**Issue**: MCP servers not connecting
```
Solutions:
1. Verify Node.js installation: node --version
2. Check config file syntax (valid JSON)
3. Use absolute paths in configuration
4. Restart Claude after config changes
5. Check logs in Developer settings
```

#### Performance Issues

**Issue**: Slow performance
```
Solutions:
- Check system resources (RAM/CPU)
- Reduce number of active MCP servers
- Clear application cache
- Update to latest version
```

### Error Messages

| Error | Solution |
|-------|----------|
| "MCP server failed to start" | Check Node.js installation and paths |
| "Invalid configuration" | Validate JSON syntax in config file |
| "Permission denied" | Grant necessary file system permissions |
| "Token limit exceeded" | Reduce project knowledge base size |

### Getting Help

- **Official support**: status.anthropic.com
- **Community**: r/ClaudeAI, r/AnthropicAI
- **Documentation**: Official quickstart guides
- **Logs**: Developer settings → View logs

---

This documentation guide provides comprehensive coverage of the Claude desktop application. For the latest updates and features, always refer to the official Anthropic documentation and release notes.