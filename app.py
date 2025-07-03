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

# Features overview
st.markdown("---")
st.markdown("## 📊 Available Dashboards")

col1, col2 = st.columns(2)
col3, col4 = st.columns(2)

with col1:
    st.markdown("""
    ### 🌾 [Global Wheat Production](/wheat_production)
    - Track production data for major wheat-producing countries
    - View historical trends from 2021/2022 to 2024/2025
    - Edit and update 2024/2025 projections
    - Visualize production trends and changes
    - Export data in JSON and CSV formats
    """)
    
    if st.button("Go to Production Dashboard", key="prod_btn"):
        st.switch_page("pages/1_wheat_production.py")

with col2:
    st.markdown("""
    ### 📦 [Wheat Exports](/wheat_exports)
    - Monitor export volumes from major exporting countries
    - Analyze market share and export trends
    - Update export projections for 2024/2025
    - Compare changes across different periods
    - Export and import data for analysis
    """)
    
    if st.button("Go to Exports Dashboard", key="exp_btn"):
        st.switch_page("pages/2_wheat_exports.py")

with col3:
    st.markdown("""
    ### 📥 [Wheat Imports](/wheat_imports)
    - Track import volumes for major importing countries
    - Monitor import dependency trends
    - Update import projections for 2024/2025
    - Analyze top importers and market dynamics
    - Export and import data management
    """)
    
    if st.button("Go to Imports Dashboard", key="imp_btn"):
        st.switch_page("pages/3_wheat_imports.py")

with col4:
    st.markdown("""
    ### 🏢 [Ending Stocks](/wheat_stocks)
    - Monitor global wheat stock levels
    - Analyze stock-to-use ratios for supply security
    - Track stock distribution by country
    - Update stock projections and S/U ratios
    - Strategic reserve analysis
    """)
    
    if st.button("Go to Stocks Dashboard", key="stocks_btn"):
        st.switch_page("pages/4_wheat_stocks.py")

# Key metrics summary
st.markdown("---")
st.markdown("## 📈 Key Metrics Overview")

if db_exists:
    from helpers.database_helper import WheatProductionDB
    
    db = WheatProductionDB()
    
    # Get latest data
    production_data = db.get_all_production_data()
    export_data = db.get_all_export_data()
    import_data = db.get_all_import_data()
    stocks_data = db.get_all_stocks_data()
    su_ratio_data = db.get_all_su_ratio_data()
    acreage_data = db.get_all_acreage_data()
    yield_data = db.get_all_yield_data()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if production_data and 'WORLD' in production_data:
            world_prod = production_data['WORLD'].get('2024/2025', 0)
            st.metric("Global Production 2024/2025", f"{world_prod:.1f} Mt")
    
    with col2:
        if export_data and 'TOTAL MAJOR EXPORTERS' in export_data:
            total_exports = export_data['TOTAL MAJOR EXPORTERS'].get('2024/2025', 0)
            st.metric("Total Major Exports 2024/2025", f"{total_exports:.1f} Mt")
    
    with col3:
        if import_data and 'TOTAL MAJOR IMPORTERS' in import_data:
            total_imports = import_data['TOTAL MAJOR IMPORTERS'].get('2024/2025', 0)
            st.metric("Total Major Imports 2024/2025", f"{total_imports:.1f} Mt")
    
    with col4:
        metadata = db.get_metadata()
        last_update = metadata.get('production_last_updated', 'N/A')
        st.metric("Last Update", last_update)

# Additional features
st.markdown("---")
st.markdown("## 🚀 Additional Features")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    ### 📊 [Stock-to-Use Ratio](/stock_to_use_ratio)
    - Monitor market tightness indicators
    - Analyze supply security by country
    - Track S/U ratio trends and categories
    - Identify countries at risk
    - Regional market analysis
    """)
    
    if st.button("Go to S/U Ratio Dashboard", key="su_btn"):
        st.switch_page("pages/5_stock_to_use_ratio.py")

with col2:
    st.markdown("""
    ### 🌾 [Wheat Acreage](/wheat_acreage)
    - Track area harvested by country
    - Monitor yield trends
    - Analyze productivity changes
    - Compare acreage vs yield
    - Project future planting areas
    """)
    
    if st.button("Go to Acreage Dashboard", key="acreage_btn"):
        st.switch_page("pages/6_wheat_acreage.py")

with col3:
    st.markdown("""
    ### 🌱 [Wheat Yield](/wheat_yield)
    - Track productivity trends
    - Analyze weather impacts
    - Compare yield performance
    - Identify yield gaps
    - Monitor efficiency gains
    """)
    
    if st.button("Go to Yield Dashboard", key="yield_btn"):
        st.switch_page("pages/7_wheat_yield.py")

# Coming soon section
st.markdown("---")
st.info("""
    **Coming Soon:**
    - 📊 Supply & Demand balance
    - 💰 Price monitoring
    - 🗺️ Regional analysis
    - 📈 Trade flows visualization
    - 📉 Market forecasting
    """)

# Trade Balance Analysis
if db_exists:
    st.markdown("---")
    st.markdown("## 🔄 Trade Balance Overview")
    
    # Calculate trade balance and supply metrics if data is available
    try:
        if export_data and import_data and stocks_data:
            if 'TOTAL MAJOR EXPORTERS' in export_data and 'TOTAL MAJOR IMPORTERS' in import_data:
                exports_2024 = export_data['TOTAL MAJOR EXPORTERS'].get('2024/2025', 0)
                imports_2024 = import_data['TOTAL MAJOR IMPORTERS'].get('2024/2025', 0)
                world_stocks = stocks_data['WORLD'].get('2024/2025', 0)
                world_stocks_change = stocks_data['WORLD'].get('2024/2025_change', 0)
                
                trade_balance = exports_2024 - imports_2024
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Major Exporters Volume", f"{exports_2024:.1f} Mt")
                with col2:
                    st.metric("Major Importers Volume", f"{imports_2024:.1f} Mt")
                with col3:
                    st.metric("Trade Balance", f"{trade_balance:+.1f} Mt",
                             help="Positive means exports exceed imports among major traders")
                with col4:
                    st.metric("Stock Change", f"{world_stocks_change:+.1f} Mt",
                             delta_color="inverse",
                             help="Change in global ending stocks")
    except:
        pass

# Footer
st.markdown("---")
st.markdown(
    f"""
    <div style='text-align: center; color: #666; font-size: 0.8em;'>
    🌾 Wheat Market Analysis Dashboard | Version 2.0 | {datetime.now().strftime('%Y')}
    </div>
    """,
    unsafe_allow_html=True
)