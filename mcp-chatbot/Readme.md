# AI-Powered MSSQL Database Integration Platform

A comprehensive full-stack application that provides AI-powered interactions with MSSQL databases through Model Context Protocol (MCP) servers. This platform enables seamless data analysis, management, and automation across your SQL Server infrastructure with optional HTTPS security.

## 🚀 System Overview

This application consists of two integrated components:

1. **Streamlit Client** - AI chat interface with multi-provider support, authentication, and SSL support
2. **MSSQL MCP Server** - SQL Server database operations with full CRUD support

## ⚡ Quick Start

### Prerequisites
- Docker & Docker Compose
- MSSQL Server database
- OpenAI API key or Azure OpenAI configuration

### 1. Environment Setup

Create a `.env` file in the project root:

```env
# AI Provider Configuration (choose one)
OPENAI_API_KEY=your_openai_api_key_here

# OR Azure OpenAI Configuration
AZURE_API_KEY=your_azure_api_key
AZURE_ENDPOINT=https://your-endpoint.openai.azure.com/
AZURE_DEPLOYMENT=your_deployment_name
AZURE_API_VERSION=2023-12-01-preview

# MSSQL Configuration
MSSQL_HOST=host.docker.internal
MSSQL_USER=your_mssql_username
MSSQL_PASSWORD=your_mssql_password
MSSQL_DATABASE=your_database_name
MSSQL_DRIVER=ODBC Driver 18 for SQL Server
TrustServerCertificate=yes
Trusted_Connection=no

# SSL Configuration (Optional)
SSL_ENABLED=true