import streamlit as st
import os
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="Wheat Dashboard",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Hide the default navigation with more specific CSS
st.markdown("""
<style>
    /* Hide Streamlit's default page navigation */
    [data-testid="stSidebarNav"] {
        display: none !important;
    }
    
    /* Also hide the navigation container */
    section[data-testid="stSidebarNav"] {
        display: none !important;
    }
    
    /* Hide navigation links if they still appear */
    [data-testid="stSidebarNav"] > ul {
        display: none !important;
    }
    
    /* Remove the default app header in sidebar */
    [data-testid="stSidebarNav"] > div:first-child {
        display: none !important;
    }
    
    /* Adjust sidebar spacing */
    .css-1d391kg {
        padding-top: 1rem;
    }
    
    /* Hide any remaining navigation elements */
    [kind="navlink"] {
        display: none !important;
    }
</style>
""", unsafe_allow_html=True)

# Custom page navigation
def navigate_to_page(page_path):
    """Navigate to a specific page"""
    st.switch_page(page_path)

# Sidebar navigation
with st.sidebar:
    st.title("🌾 Navigation")
    
    # Supply & Demand Section
    with st.expander("📊 Supply & Demand", expanded=True):
        if st.button("🌾 Production", use_container_width=True):
            navigate_to_page("pages/1_wheat_production.py")
        if st.button("📦 Exports", use_container_width=True):
            navigate_to_page("pages/2_wheat_exports.py")
        if st.button("📥 Imports", use_container_width=True):
            navigate_to_page("pages/3_wheat_imports.py")
        if st.button("🏢 Ending Stocks", use_container_width=True):
            navigate_to_page("pages/4_wheat_stocks.py")
        if st.button("📊 Stock-to-Use Ratio", use_container_width=True):
            navigate_to_page("pages/5_stock_to_use_ratio.py")
        if st.button("🌾 Acreage", use_container_width=True):
            navigate_to_page("pages/6_wheat_acreage.py")
        if st.button("🌱 Yield", use_container_width=True):
            navigate_to_page("pages/7_wheat_yield.py")
    
    # Future sections can be added here
    with st.expander("📈 Analysis (Coming Soon)", expanded=False):
        st.info("Price Analysis, Trade Flows, and Market Forecasting coming soon!")

# Main page content
st.title("🌾 Wheat Market Analysis Dashboard")
st.markdown("### Supply & Demand Analysis Platform")

# Introduction
st.markdown("""
Welcome to the Wheat Market Analysis Dashboard. This platform provides comprehensive data management
and visualization tools for wheat production and export statistics across major producing and exporting countries.
""")

# Check database status
db_exists = os.path.exists("wheat_production.db")

if db_exists:
    st.success("✅ Database is connected and ready")
else:
    st.warning("⚠️ Database not found. Please run `python database_setup.py` to initialize the database.")
    
    st.markdown("### Setup Instructions")
    st.code("""
# 1. Create the database
python database_setup.py

# 2. Restart the Streamlit app
streamlit run app.py
    """, language="bash")

# Features overview with Supply & Demand grouping
st.markdown("---")
st.markdown("## 📊 Supply & Demand Dashboards")

# Create 2x2 grid for Supply & Demand features
col1, col2 = st.columns(2)
col3, col4 = st.columns(2)

with col1:
    st.markdown("""
    ### 🌾 [Global Wheat Production](/wheat_production)
    - Track production data for major wheat-producing countries
    - View historical trends from 2021/2022 to 2024/2025
    - Edit and update 2024/2025 projections
    - Visualize production trends and changes
    """)
    
    if st.button("Go to Production Dashboard", key="prod_btn"):
        st.switch_page("pages/1_🌾_Supply_&_Demand/1_wheat_production.py")

with col2:
    st.markdown("""
    ### 📦 [Wheat Exports](/wheat_exports)
    - Monitor export volumes from major exporting countries
    - Analyze market share and export trends
    - Update export projections for 2024/2025
    - Compare changes across different periods
    """)
    
    if st.button("Go to Exports Dashboard", key="exp_btn"):
        st.switch_page("pages/1_🌾_Supply_&_Demand/2_wheat_exports.py")

with col3:
    st.markdown("""
    ### 📥 [Wheat Imports](/wheat_imports)
    - Track import volumes for major importing countries
    - Monitor import dependency trends
    - Update import projections for 2024/2025
    - Analyze top importers and market dynamics
    """)
    
    if st.button("Go to Imports Dashboard", key="imp_btn"):
        st.switch_page("pages/1_🌾_Supply_&_Demand/3_wheat_imports.py")

with col4:
    st.markdown("""
    ### 🏢 [Ending Stocks](/wheat_stocks)
    - Monitor global wheat stock levels
    - Analyze stock-to-use ratios for supply security
    - Track stock distribution by country
    - Update stock projections and S/U ratios
    """)
    
    if st.button("Go to Stocks Dashboard", key="stocks_btn"):
        st.switch_page("pages/1_🌾_Supply_&_Demand/4_wheat_stocks.py")

# Additional Supply & Demand features
st.markdown("### 📈 Additional Supply & Demand Analysis")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    ### 📊 [Stock-to-Use Ratio](/stock_to_use_ratio)
    - Monitor market tightness indicators
    - Analyze supply security by country
    - Track S/U ratio trends and categories
    """)
    
    if st.button("Go to S/U Ratio Dashboard", key="su_btn"):
        st.switch_page("pages/1_🌾_Supply_&_Demand/5_stock_to_use_ratio.py")

with col2:
    st.markdown("""
    ### 🌾 [Wheat Acreage](/wheat_acreage)
    - Track area harvested by country
    - Monitor yield trends
    - Analyze productivity changes
    """)
    
    if st.button("Go to Acreage Dashboard", key="acreage_btn"):
        st.switch_page("pages/1_🌾_Supply_&_Demand/6_wheat_acreage.py")

with col3:
    st.markdown("""
    ### 🌱 [Wheat Yield](/wheat_yield)
    - Track productivity trends
    - Analyze weather impacts
    - Compare yield performance
    """)
    
    if st.button("Go to Yield Dashboard", key="yield_btn"):
        st.switch_page("pages/1_🌾_Supply_&_Demand/7_wheat_yield.py")

# Key metrics summary
if db_exists:
    st.markdown("---")
    st.markdown("## 📈 Key Supply & Demand Metrics")
    
    from helpers.database_helper import WheatProductionDB
    
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
    
    # Supply & Demand Balance
    st.markdown("---")
    st.markdown("## 🔄 Supply & Demand Balance Overview")
    
    if production_data and export_data and import_data and stocks_data:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Production + Beginning Stocks = Total Supply
            prod_2024 = production_data['WORLD'].get('2024/2025', 0)
            begin_stocks = stocks_data['WORLD'].get('2023/2024', 0)
            total_supply = prod_2024 + begin_stocks
            st.metric("Total Supply", f"{total_supply:.1f} Mt",
                     help="Production + Beginning Stocks")
        
        with col2:
            # Trade Balance
            exports_2024 = export_data['TOTAL MAJOR EXPORTERS'].get('2024/2025', 0)
            imports_2024 = import_data['TOTAL MAJOR IMPORTERS'].get('2024/2025', 0)
            trade_balance = exports_2024 - imports_2024
            st.metric("Trade Balance", f"{trade_balance:+.1f} Mt",
                     help="Major Exports - Major Imports")
        
        with col3:
            # Stock Change
            end_stocks = stocks_data['WORLD'].get('2024/2025', 0)
            stock_change = end_stocks - begin_stocks
            st.metric("Stock Change", f"{stock_change:+.1f} Mt",
                     delta_color="inverse",
                     help="Ending Stocks - Beginning Stocks")

# Coming soon section
st.markdown("---")
st.info("""
    **Coming Soon - Additional Analysis Modules:**
    - 💰 Price Monitoring & Analysis
    - 🗺️ Trade Flow Visualization
    - 📊 Complete Supply & Demand Balance Sheets
    - 📈 Market Forecasting & Scenarios
    - 🌍 Regional Market Analysis
    """)

# Footer
st.markdown("---")
st.markdown(
    f"""
    <div style='text-align: center; color: #666; font-size: 0.8em;'>
    🌾 Wheat Market Analysis Dashboard | Supply & Demand Focus | Version 2.0 | {datetime.now().strftime('%Y')}
    </div>
    """,
    unsafe_allow_html=True
)