I'll help you integrate the wheat application into the mcp-bot-ppf client. This will create a unified application with authentication from mcp-bot-ppf and functionality from both applications.

## Integration Guide: Wheat into MCP-Bot-PPF

### Overview
This guide will walk you through integrating the wheat application into the mcp-bot-ppf client, creating a single application with:
- SSL, login, and session management from mcp-bot-ppf
- Navigation from wheat application
- MCP functionality as a section within the wheat navigation
- Everything running in a single Docker container

### Step-by-Step Integration Process

#### 1. Copy Wheat Files to MCP-Bot-PPF Client

First, copy the wheat application files into the mcp-bot-ppf client directory:

```bash
# From the root directory containing both projects
cp -r wheat/pages mcp-bot-ppf/client/wheat_pages/
cp -r wheat/helpers mcp-bot-ppf/client/wheat_helpers/
cp wheat/wheat_production.db mcp-bot-ppf/client/
cp -r wheat/database_setup mcp-bot-ppf/client/
```

#### 2. Update Requirements

Update `mcp-bot-ppf/client/requirements.txt` to include wheat dependencies:

```python
# Add to existing requirements.txt
plotly>=6.2.0
```

#### 3. Create New Main App Structure

Create a new `app.py` in `mcp-bot-ppf/client/`:

```python
import streamlit as st
import os
from datetime import datetime
import nest_asyncio
import atexit
import yaml
import streamlit_authenticator as stauth
from yaml.loader import SafeLoader
import logging

# Apply nest_asyncio
nest_asyncio.apply()

# Page configuration
st.set_page_config(
    page_title="PPF Europe Dashboard",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Hide default navigation
st.markdown("""
<style>
    /* Hide Streamlit's default page navigation */
    [data-testid="stSidebarNav"] {
        display: none !important;
    }
    
    section[data-testid="stSidebarNav"] {
        display: none !important;
    }
    
    [data-testid="stSidebarNav"] > ul {
        display: none !important;
    }
    
    [data-testid="stSidebarNav"] > div:first-child {
        display: none !important;
    }
    
    .css-1d391kg {
        padding-top: 1rem;
    }
    
    [kind="navlink"] {
        display: none !important;
    }
</style>
""", unsafe_allow_html=True)

# Authentication functions
def load_config():
    """Load authentication configuration from YAML file."""
    config_path = os.path.join("keys", "config.yaml")
    try:
        with open(config_path, "r") as file:
            return yaml.load(file, Loader=SafeLoader)
    except FileNotFoundError:
        st.error("❌ Configuration file not found at keys/config.yaml")
        st.stop()
    except Exception as e:
        st.error(f"❌ Error loading configuration: {str(e)}")
        st.stop()

def initialize_authentication_state():
    """Initialize authentication-related session state variables."""
    if "authentication_status" not in st.session_state:
        st.session_state["authentication_status"] = None
    if "name" not in st.session_state:
        st.session_state["name"] = None
    if "username" not in st.session_state:
        st.session_state["username"] = None

def handle_authentication():
    """Handle user authentication and return status."""
    config = load_config()
    initialize_authentication_state()
    
    authenticator = stauth.Authenticate(
        config["credentials"],
        config["cookie"]["name"],
        config["cookie"]["key"],
        config["cookie"]["expiry_days"],
    )
    
    return authenticator, config

# Navigation functions
def navigate_to_page(page_path):
    """Navigate to a specific page"""
    st.switch_page(page_path)

# Main application
def main():
    """Main application with integrated navigation."""
    
    # Initialize authentication
    authenticator, config = handle_authentication()
    
    # Create sidebar with authentication and navigation
    with st.sidebar:
        # Logo section
        logo_path = os.path.join(".", "icons", "Logo.png")
        if os.path.exists(logo_path):
            col1, col2 = st.columns([1, 3])
            with col1:
                st.image(logo_path, width=60)
            with col2:
                st.markdown("""
                <div style="padding-top: 10px;">
                    <h3 style="margin: 0; color: #2F2E78;">PPF Europe</h3>
                    <p style="margin: 0; font-size: 12px; color: #666;">Analysis Platform</p>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Authentication section
        st.markdown("## 🔐 Authentication")
        
        if st.session_state["authentication_status"] is None:
            try:
                authenticator.login()
            except Exception as e:
                st.error(f"Authentication error: {str(e)}")
            
            if st.session_state["authentication_status"] is False:
                st.error("❌ Username/password is incorrect")
            elif st.session_state["authentication_status"] is None:
                st.warning("⚠️ Please enter your username and password")
        
        elif st.session_state["authentication_status"]:
            st.success(f"✅ Welcome, **{st.session_state['name']}**!")
            st.info(f"👤 Username: {st.session_state['username']}")
            
            # Logout button
            authenticator.logout("Logout")
            
            st.markdown("---")
            
            # Navigation section (only shown when authenticated)
            st.title("🌾 Navigation")
            
            # Supply & Demand Section
            with st.expander("📊 Supply & Demand", expanded=True):
                if st.button("🌾 Production", use_container_width=True):
                    navigate_to_page("wheat_pages/1_wheat_production.py")
                if st.button("📦 Exports", use_container_width=True):
                    navigate_to_page("wheat_pages/2_wheat_exports.py")
                if st.button("📥 Imports", use_container_width=True):
                    navigate_to_page("wheat_pages/3_wheat_imports.py")
                if st.button("🏢 Ending Stocks", use_container_width=True):
                    navigate_to_page("wheat_pages/4_wheat_stocks.py")
                if st.button("📊 Stock-to-Use Ratio", use_container_width=True):
                    navigate_to_page("wheat_pages/5_stock_to_use_ratio.py")
                if st.button("🌾 Acreage", use_container_width=True):
                    navigate_to_page("wheat_pages/6_wheat_acreage.py")
                if st.button("🌱 Yield", use_container_width=True):
                    navigate_to_page("wheat_pages/7_wheat_yield.py")
            
            # MCP Tools Section
            with st.expander("🤖 AI & MCP Tools", expanded=False):
                if st.button("💬 MCP Chat Interface", use_container_width=True):
                    navigate_to_page("mcp_pages/mcp_app.py")
                if st.button("🔥 Firecrawl Tools", use_container_width=True):
                    navigate_to_page("mcp_pages/mcp_app.py")
                if st.button("🔍 Google Search", use_container_width=True):
                    navigate_to_page("mcp_pages/mcp_app.py")
                if st.button("🔮 Perplexity Search", use_container_width=True):
                    navigate_to_page("mcp_pages/mcp_app.py")
            
            # Future sections
            with st.expander("📈 Analysis (Coming Soon)", expanded=False):
                st.info("Price Analysis, Trade Flows, and Market Forecasting coming soon!")
    
    # Main page content
    if st.session_state["authentication_status"]:
        show_authenticated_content()
    else:
        show_unauthenticated_content()

def show_authenticated_content():
    """Show content for authenticated users."""
    st.title("🌾 PPF Europe Analysis Platform")
    st.markdown("### Integrated Wheat Market Analysis & AI Tools")
    
    # Check database status
    db_exists = os.path.exists("wheat_production.db")
    
    if db_exists:
        st.success("✅ Database is connected and ready")
    else:
        st.warning("⚠️ Database not found. Please run `python database_setup.py` to initialize the database.")
    
    # Dashboard overview
    st.markdown("---")
    st.markdown("## 📊 Available Dashboards")
    
    # Supply & Demand dashboards
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### 📊 Supply & Demand Analysis
        - **🌾 Production**: Track global wheat production
        - **📦 Exports**: Monitor export volumes and trends
        - **📥 Imports**: Analyze import patterns
        - **🏢 Stocks**: Ending stocks and reserves
        - **📊 S/U Ratio**: Stock-to-use analysis
        - **🌾 Acreage**: Area harvested trends
        - **🌱 Yield**: Productivity analysis
        """)
        
        if st.button("Start Supply & Demand Analysis", type="primary"):
            st.switch_page("wheat_pages/1_wheat_production.py")
    
    with col2:
        st.markdown("""
        ### 🤖 AI & MCP Tools
        - **💬 Chat Interface**: AI-powered conversations
        - **🔥 Firecrawl**: Web scraping and extraction
        - **🔍 Google Search**: Comprehensive web search
        - **🔮 Perplexity**: AI-powered search
        - **📄 Content Analysis**: Extract and analyze
        - **🔧 Tool Management**: Execute specialized tools
        - **💾 Smart Caching**: Optimized performance
        """)
        
        if st.button("Launch AI Tools", type="primary"):
            st.switch_page("mcp_pages/mcp_app.py")
    
    # Key metrics if database exists
    if db_exists:
        st.markdown("---")
        st.markdown("## 📈 Key Metrics")
        
        from wheat_helpers.database_helper import WheatProductionDB
        
        db = WheatProductionDB()
        
        # Get latest data
        production_data = db.get_all_production_data()
        export_data = db.get_all_export_data()
        import_data = db.get_all_import_data()
        stocks_data = db.get_all_stocks_data()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if production_data and 'WORLD' in production_data:
                world_prod = production_data['WORLD'].get('2024/2025', 0)
                st.metric("Global Production", f"{world_prod:.1f} Mt")
        
        with col2:
            if export_data and 'TOTAL MAJOR EXPORTERS' in export_data:
                total_exports = export_data['TOTAL MAJOR EXPORTERS'].get('2024/2025', 0)
                st.metric("Major Exports", f"{total_exports:.1f} Mt")
        
        with col3:
            if import_data and 'TOTAL MAJOR IMPORTERS' in import_data:
                total_imports = import_data['TOTAL MAJOR IMPORTERS'].get('2024/2025', 0)
                st.metric("Major Imports", f"{total_imports:.1f} Mt")
        
        with col4:
            if stocks_data and 'WORLD' in stocks_data:
                world_stocks = stocks_data['WORLD'].get('2024/2025', 0)
                st.metric("Global Stocks", f"{world_stocks:.1f} Mt")

def show_unauthenticated_content():
    """Show content for unauthenticated users."""
    st.title("🌾 PPF Europe Analysis Platform")
    st.markdown("### Welcome to the Integrated Analysis Platform")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Logo
        logo_path = os.path.join(".", "icons", "Logo.png")
        if os.path.exists(logo_path):
            col_a, col_b, col_c = st.columns([1, 1, 1])
            with col_b:
                st.image(logo_path, width=120)
            st.markdown("<br>", unsafe_allow_html=True)
        
        st.markdown("""
        This platform combines comprehensive wheat market analysis with advanced AI-powered tools 
        for web scraping, search, and content analysis.
        
        **Please authenticate using the sidebar to access the platform.**
        
        ---
        
        #### 🚀 Features Available After Login:
        
        **📊 Supply & Demand Analysis**
        - Global wheat production tracking
        - Export/import monitoring
        - Stock levels and S/U ratios
        - Acreage and yield analysis
        
        **🤖 AI & MCP Tools**
        - AI chat interface
        - Firecrawl web scraping
        - Google Search integration
        - Perplexity AI search
        - Content extraction and analysis
        
        ---
        
        #### 🔑 Authentication
        
        Use the **Authentication** section in the sidebar to log in with your credentials.
        """)
        
        st.info("👈 Use the sidebar to authenticate and start using the platform")

if __name__ == "__main__":
    main()
```

#### 4. Move MCP App to Separate Directory

Create `mcp-bot-ppf/client/mcp_pages/` directory and move the MCP app:

```bash
mkdir -p mcp-bot-ppf/client/mcp_pages
mv mcp-bot-ppf/client/apps/mcp_app.py mcp-bot-ppf/client/mcp_pages/
```

#### 5. Update Wheat Pages

Update each wheat page to work within the new structure. For example, update `wheat_pages/1_wheat_production.py`:

```python
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import json
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wheat_helpers.database_helper import WheatProductionDB
from wheat_helpers.common_functions import (
    format_change, 
    create_status_indicators,
    create_projection_dates_sidebar,
    create_change_visualization,
    style_change_column
)

# Page configuration
st.set_page_config(
    page_title="Wheat Production Dashboard",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Hide the navigation on this page
st.markdown("""
<style>
    /* Hide Streamlit's default page navigation */
    [data-testid="stSidebarNav"] {
        display: none !important;
    }
    
    /* Hide navigation container */
    section[data-testid="stSidebarNav"] {
        display: none !important;
    }
    
    /* Adjust sidebar spacing */
    .css-1d391kg {
        padding-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Check authentication
if not st.session_state.get("authentication_status"):
    st.error("🔐 Authentication required. Please log in to access this page.")
    if st.button("Return to Login"):
        st.switch_page("app.py")
    st.stop()

# Add unified sidebar navigation
with st.sidebar:
    # Logo section
    logo_path = os.path.join(".", "icons", "Logo.png")
    if os.path.exists(logo_path):
        col1, col2 = st.columns([1, 3])
        with col1:
            st.image(logo_path, width=60)
        with col2:
            st.markdown("""
            <div style="padding-top: 10px;">
                <h3 style="margin: 0; color: #2F2E78;">PPF Europe</h3>
                <p style="margin: 0; font-size: 12px; color: #666;">Analysis Platform</p>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # User info
    st.success(f"✅ Welcome, **{st.session_state['name']}**!")
    
    if st.button("🏠 Return to Main Dashboard", use_container_width=True, type="primary"):
        st.switch_page("app.py")
    
    st.markdown("---")
    
    # Quick Navigation
    st.markdown("### 🌾 Quick Navigation")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📦 Exports", use_container_width=True):
            st.switch_page("wheat_pages/2_wheat_exports.py")
        if st.button("🏢 Stocks", use_container_width=True):
            st.switch_page("wheat_pages/4_wheat_stocks.py")
    with col2:
        if st.button("📥 Imports", use_container_width=True):
            st.switch_page("wheat_pages/3_wheat_imports.py")
        if st.button("🤖 AI Tools", use_container_width=True):
            st.switch_page("mcp_pages/mcp_app.py")

# Rest of the wheat production page code remains the same...
# (Include all the existing wheat production functionality here)
```

#### 6. Update MCP App Page

Update `mcp_pages/mcp_app.py` to include authentication check and unified navigation:

```python
import os
import datetime
import streamlit as st
from langchain_core.messages import HumanMessage, ToolMessage, AIMessage

# Import all necessary functions from services and helpers
from services.ai_service import get_response_stream
from services.mcp_service import run_agent, use_prompt
from services.chat_service import (
    get_current_chat,
    _append_message_to_session,
    get_clean_conversation_memory,
    init_session
)
# ... other imports ...

# Check authentication
if not st.session_state.get("authentication_status"):
    st.error("🔐 Authentication required. Please log in to access this page.")
    if st.button("Return to Login"):
        st.switch_page("app.py")
    st.stop()

# Add unified sidebar navigation
with st.sidebar:
    # Logo section
    logo_path = os.path.join(".", "icons", "Logo.png")
    if os.path.exists(logo_path):
        col1, col2 = st.columns([1, 3])
        with col1:
            st.image(logo_path, width=60)
        with col2:
            st.markdown("""
            <div style="padding-top: 10px;">
                <h3 style="margin: 0; color: #2F2E78;">PPF Europe</h3>
                <p style="margin: 0; font-size: 12px; color: #666;">MCP Tools</p>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # User info
    st.success(f"✅ Welcome, **{st.session_state['name']}**!")
    
    if st.button("🏠 Return to Main Dashboard", use_container_width=True, type="primary"):
        st.switch_page("app.py")
    
    st.markdown("---")
    
    # Quick Navigation to Wheat pages
    st.markdown("### 🌾 Wheat Analysis")
    if st.button("📊 Supply & Demand", use_container_width=True):
        st.switch_page("wheat_pages/1_wheat_production.py")

# Initialize session for MCP
init_session()

# Title
st.title("🔥 AI & MCP Tools Interface")

# Rest of the MCP app functionality...
# (Include all the existing MCP app code here)
```

#### 7. Update Dockerfile

Update `mcp-bot-ppf/client/Dockerfile`:

```dockerfile
FROM python:3.11-slim-bullseye

WORKDIR /app

# Install system dependencies including OpenSSL and curl for health checks
RUN apt-get update && apt-get install -y \
    openssl \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create directories for authentication config, SSL certificates, MCP servers, and wheat data
RUN mkdir -p keys ssl mcp_servers/company_tagging/categories wheat_pages wheat_helpers mcp_pages

# Copy the application code
COPY . .

# Copy wheat-specific files
COPY wheat_pages/ ./wheat_pages/
COPY wheat_helpers/ ./wheat_helpers/
COPY database_setup/ ./database_setup/
COPY wheat_production.db ./wheat_production.db

# Copy MCP pages
COPY mcp_pages/ ./mcp_pages/

# Copy SSL-related scripts and make them executable
COPY generate_ssl_certificate.sh startup_ssl.sh ./
RUN chmod +x generate_ssl_certificate.sh startup_ssl.sh

# Ensure proper permissions for directories
RUN chmod 755 keys ssl mcp_servers wheat_pages wheat_helpers mcp_pages

# Initialize the wheat database if it doesn't exist
RUN if [ ! -f wheat_production.db ]; then \
        cd database_setup && \
        python database_setup.py && \
        python database_setup_exports.py && \
        python database_setup_imports.py && \
        python database_setup_stocks.py && \
        python database_setup_su_ratio.py && \
        python database_setup_acreage.py && \
        python database_setup_yield.py && \
        cd ..; \
    fi

# Expose both HTTP and HTTPS ports
EXPOSE 8501
EXPOSE 8503

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8501 || exit 1

# Run as root to avoid SSL permission issues
CMD ["./startup_ssl.sh"]
```

#### 8. Update Directory Structure

Final directory structure should look like:

```
mcp-bot-ppf/
├── client/
│   ├── app.py                      # New unified main app
│   ├── wheat_pages/                # Wheat application pages
│   │   ├── 1_wheat_production.py
│   │   ├── 2_wheat_exports.py
│   │   ├── 3_wheat_imports.py
│   │   ├── 4_wheat_stocks.py
│   │   ├── 5_stock_to_use_ratio.py
│   │   ├── 6_wheat_acreage.py
│   │   └── 7_wheat_yield.py
│   ├── mcp_pages/                  # MCP application pages
│   │   └── mcp_app.py
│   ├── wheat_helpers/              # Wheat helper functions
│   │   ├── __init__.py
│   │   ├── database_helper.py
│   │   └── common_functions.py
│   ├── database_setup/             # Database setup scripts
│   │   └── *.py
│   ├── services/                   # MCP services
│   ├── helpers/                    # MCP helpers
│   ├── utils/                      # MCP utils
│   ├── ui_components/              # MCP UI components
│   ├── keys/                       # Authentication config
│   ├── icons/                      # Icons
│   ├── wheat_production.db         # Wheat database
│   ├── requirements.txt            # Updated requirements
│   ├── Dockerfile                  # Updated Dockerfile
│   └── startup_ssl.sh              # SSL startup script
├── servers/                        # MCP servers (unchanged)
└── docker-compose.yaml             # Docker compose (unchanged)
```

#### 9. Build and Run

Build and run the integrated application:

```bash
# Build the Docker image
cd mcp-bot-ppf
docker-compose build mcp-client

# Run the application
docker-compose up
```

#### 10. Testing Checklist

After integration, test the following:

1. **Authentication**:
   - [ ] Login works correctly
   - [ ] Session management persists across pages
   - [ ] Logout works from any page

2. **Navigation**:
   - [ ] All wheat pages are accessible from sidebar
   - [ ] MCP tools are accessible from sidebar
   - [ ] Return to main dashboard works
   - [ ] Quick navigation between pages works

3. **Functionality**:
   - [ ] Wheat production data loads correctly
   - [ ] All wheat dashboards function properly
   - [ ] MCP chat interface works
   - [ ] Tool connections work

4. **SSL & Security**:
   - [ ] SSL certificates are generated
   - [ ] HTTPS access works
   - [ ] Authentication is enforced on all pages

### Summary

This integration creates a unified application that:
- Uses MCP-bot-ppf's authentication and session management
- Incorporates all wheat dashboards as primary navigation
- Includes MCP tools as a section within the navigation
- Runs everything in a single Docker container
- Maintains SSL support and security features

The sidebar now contains:
1. Logo and branding
2. Authentication (login/logout)
3. Navigation panel with:
   - Supply & Demand section (wheat pages)
   - AI & MCP Tools section
   - Future sections placeholder

All pages check for authentication before allowing access, ensuring security across the entire application.