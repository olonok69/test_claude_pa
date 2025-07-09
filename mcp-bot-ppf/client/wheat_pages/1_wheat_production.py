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
    style_change_column,
)

# Page configuration
st.set_page_config(
    page_title="Wheat Production Dashboard",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Hide the navigation on this page
st.markdown(
    """
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
""",
    unsafe_allow_html=True,
)

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
            st.markdown(
                """
            <div style="padding-top: 10px;">
                <h3 style="margin: 0; color: #2F2E78;">PPF Europe</h3>
                <p style="margin: 0; font-size: 12px; color: #666;">Analysis Platform</p>
            </div>
            """,
                unsafe_allow_html=True,
            )

    st.markdown("---")

    # User info
    st.success(f"✅ Welcome, **{st.session_state['name']}**!")

    if st.button(
        "🏠 Return to Main Dashboard", use_container_width=True, type="primary"
    ):
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
        if st.button("🌾 Acreage", use_container_width=True):
            st.switch_page("wheat_pages/6_wheat_acreage.py")
    with col2:
        if st.button("📥 Imports", use_container_width=True):
            st.switch_page("wheat_pages/3_wheat_imports.py")
        if st.button("📊 S/U Ratio", use_container_width=True):
            st.switch_page("wheat_pages/5_stock_to_use_ratio.py")
        if st.button("🌱 Yield", use_container_width=True):
            st.switch_page("wheat_pages/7_wheat_yield.py")

    st.markdown("---")

    # AI Tools section
    st.markdown("### 🤖 AI & MCP Tools")
    if st.button("💬 Launch AI Chat", use_container_width=True):
        st.switch_page("mcp_pages/mcp_app.py")

    st.markdown("---")
    st.markdown("### 🌾 Production Dashboard")


# Initialize database
@st.cache_resource
def get_database():
    """Initialize and return database instance"""
    if not os.path.exists("wheat_production.db"):
        st.error(
            "❌ Database not found. Please run 'python database_setup.py' first to create the database."
        )
        return None
    return WheatProductionDB()


# Load data from database
@st.cache_data
def load_data_from_db():
    """Load data from database"""
    db = get_database()
    if not db:
        return None, None

    try:
        # Get production data
        wheat_data = db.get_all_production_data()

        # Get metadata
        metadata = db.get_metadata()
        projection_metadata = {
            "last_updated": metadata.get("production_last_updated", "19 Sept'24"),
            "next_update": metadata.get("production_next_update", "17 Oct'24"),
        }

        return wheat_data, projection_metadata
    except Exception as e:
        st.error(f"❌ Error loading data from database: {e}")
        return None, None


# Initialize session state
def initialize_session_state():
    """Initialize session state with database data"""
    if "production_data_loaded" not in st.session_state:
        wheat_data, projection_metadata = load_data_from_db()

        if wheat_data and projection_metadata:
            st.session_state.wheat_data = wheat_data
            st.session_state.production_projection_metadata = projection_metadata
            st.session_state.production_data_loaded = True
        else:
            # Fallback to hardcoded data if database is not available
            st.session_state.wheat_data = {
                "WORLD": {
                    "2021/2022": 779.7,
                    "2021/2022_pct": None,
                    "2022/2023": 803.9,
                    "2022/2023_change": 24.2,
                    "2023/2024": 795.0,
                    "2023/2024_change": -8.9,
                    "2024/2025": 798.0,
                    "2024/2025_change": 3.0,
                }
            }
            st.session_state.production_projection_metadata = {
                "last_updated": "19 Sept'24",
                "next_update": "17 Oct'24",
            }
            st.session_state.production_data_loaded = False


# Initialize session state
initialize_session_state()

# Title and header
st.title("🌾 Wheat Production Dashboard")
st.markdown("### Global Wheat Production Data Management")

# Database status indicator
if st.session_state.production_data_loaded:
    st.sidebar.success("🗄️ Connected to Database")
else:
    st.sidebar.warning("⚠️ Using Local Data (No Database)")

# Sidebar for data management
create_projection_dates_sidebar(
    st.session_state.production_projection_metadata,
    "production_last_updated",
    "production_next_update",
)

# Main content area
tab1, tab2, tab3, tab4 = st.tabs(
    ["📈 Data Overview", "✏️ Edit Projections", "📊 Visualizations", "💾 Data Export"]
)

with tab1:
    st.header("Global Wheat Production")

    # Display status indicators
    create_status_indicators()

    # Display projection dates
    st.markdown(
        f"**Projection Dates**: {st.session_state.production_projection_metadata['last_updated']} | {st.session_state.production_projection_metadata['next_update']}"
    )

    st.markdown("---")

    # Create enhanced table
    st.markdown("### Production Data (Million Metric Tons)")

    # Create the data table with proper formatting
    table_data = []
    for country, data in st.session_state.wheat_data.items():
        row = {
            "Country/Region": country,
            "2021/2022": f"{data['2021/2022']:.1f}",
            "% World": (
                f"{data['2021/2022_pct']:.1f}%"
                if data.get("2021/2022_pct") is not None
                else "-"
            ),
            "2022/2023": f"{data['2022/2023']:.1f}",
            "Change": format_change(data.get("2022/2023_change")),
            "2023/2024": f"{data['2023/2024']:.1f}",
            "Change ": format_change(data.get("2023/2024_change")),
            "2024/2025": f"{data['2024/2025']:.1f}",
            "Change  ": format_change(data.get("2024/2025_change")),
        }
        table_data.append(row)

    df_display = pd.DataFrame(table_data)

    # Apply styling to the dataframe
    styled_df = (
        df_display.style.map(
            style_change_column, subset=["Change", "Change ", "Change  "]
        )
        .set_properties(**{"text-align": "center"})
        .set_properties(**{"text-align": "left"}, subset=["Country/Region"])
    )

    st.dataframe(styled_df, use_container_width=True, hide_index=True)

    # Summary statistics
    st.markdown("### Summary Statistics")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        world_2024 = st.session_state.wheat_data["WORLD"]["2024/2025"]
        st.metric("Global Production 2024/2025", f"{world_2024:.1f} Mt")

    with col2:
        world_change = st.session_state.wheat_data["WORLD"].get("2024/2025_change", 0)
        st.metric("Change from 2023/2024", f"{world_change:+.1f} Mt")

    with col3:
        # Find top producer (excluding WORLD)
        countries_only = {
            k: v for k, v in st.session_state.wheat_data.items() if k != "WORLD"
        }
        if countries_only:
            top_producer = max(countries_only.items(), key=lambda x: x[1]["2024/2025"])
            st.metric("Top Producer 2024/2025", f"{top_producer[0][:15]}...")

    with col4:
        if countries_only:
            top_production = top_producer[1]["2024/2025"]
            st.metric("Top Production", f"{top_production:.1f} Mt")

with tab2:
    st.header("Edit 2024/2025 Projections")
    st.markdown(
        "**Note:** Historical data (2021/2022 - 2023/2024) is static and cannot be modified."
    )

    # Create form for editing projections
    with st.form("projection_form"):
        st.markdown("### Update Production Projections and Changes")

        # Create input fields for each country
        updated_values = {}
        updated_changes = {}

        for country in st.session_state.wheat_data.keys():
            current_value = st.session_state.wheat_data[country]["2024/2025"]
            current_change = st.session_state.wheat_data[country].get(
                "2024/2025_change", 0
            )

            # Show historical trend
            historical_values = [
                st.session_state.wheat_data[country]["2021/2022"],
                st.session_state.wheat_data[country]["2022/2023"],
                st.session_state.wheat_data[country]["2023/2024"],
            ]

            st.subheader(f"{country}")
            col1, col2, col3 = st.columns([2, 1, 1])

            with col1:
                updated_values[country] = st.number_input(
                    f"Production (Mt)",
                    value=float(current_value),
                    min_value=0.0,
                    step=0.1,
                    format="%.1f",
                    key=f"prod_{country}",
                    help=f"Historical: {historical_values[0]:.1f} → {historical_values[1]:.1f} → {historical_values[2]:.1f}",
                )

            with col2:
                updated_changes[country] = st.number_input(
                    f"Change from 2023/2024",
                    value=float(current_change),
                    step=0.1,
                    format="%.1f",
                    key=f"change_{country}",
                    help="Positive for increase, negative for decrease",
                )

            with col3:
                # Calculate and display automatic change
                auto_change = (
                    updated_values[country]
                    - st.session_state.wheat_data[country]["2023/2024"]
                )
                if auto_change > 0:
                    st.success(f"Auto: +{auto_change:.1f}")
                elif auto_change < 0:
                    st.error(f"Auto: {auto_change:.1f}")
                else:
                    st.info("Auto: 0.0")

        # Submit button
        if st.form_submit_button("Update Projections", type="primary"):
            # Update the data
            db = get_database()
            for country, value in updated_values.items():
                st.session_state.wheat_data[country]["2024/2025"] = value
                st.session_state.wheat_data[country]["2024/2025_change"] = (
                    updated_changes[country]
                )

                # Save to database
                if db:
                    db.update_production_value(
                        country, "2024/2025", value, updated_changes[country]
                    )

            st.success("✅ Projections updated successfully!")
            if db:
                st.info("💾 Changes saved to database")
            st.rerun()

with tab3:
    st.header("Production Visualizations")

    # Time series plot
    st.subheader("Production Trends Over Time")

    # Select countries to display
    countries_to_plot = st.multiselect(
        "Select countries/regions to display:",
        options=list(st.session_state.wheat_data.keys()),
        default=[
            "WORLD",
            "China",
            "European Union (FR, DE)",
            "India",
            "Russia",
            "United States",
        ],
    )

    if countries_to_plot:
        # Create time series plot
        fig = go.Figure()

        years = ["2021/2022", "2022/2023", "2023/2024", "2024/2025"]

        for country in countries_to_plot:
            values = [st.session_state.wheat_data[country][year] for year in years]

            fig.add_trace(
                go.Scatter(
                    x=years,
                    y=values,
                    mode="lines+markers",
                    name=country,
                    hovertemplate=f"<b>{country}</b><br>"
                    + "Year: %{x}<br>"
                    + "Production: %{y:.1f} Mt<extra></extra>",
                )
            )

        fig.update_layout(
            title="Wheat Production Trends",
            xaxis_title="Year",
            yaxis_title="Production (Million Metric Tons)",
            hovermode="x unified",
            height=500,
        )

        # Add vertical line to separate historical from projection
        fig.add_vline(
            x=2.5,
            line_dash="dot",
            line_color="gray",
            annotation_text="Historical | Projection",
            annotation_position="top",
        )

        st.plotly_chart(fig, use_container_width=True)

    # Change analysis
    create_change_visualization(
        st.session_state.wheat_data, "Production", exclude=["WORLD"]
    )

with tab4:
    st.header("Data Export & Import")

    # Export options
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Export Current Data")

        # Export data
        export_data = {
            "wheat_production_data": st.session_state.wheat_data,
            "metadata": st.session_state.production_projection_metadata,
            "export_timestamp": datetime.now().isoformat(),
            "data_source": (
                "database" if st.session_state.production_data_loaded else "local"
            ),
            "user": st.session_state.get("username", "unknown"),
        }

        # JSON export
        st.download_button(
            label="📥 Download as JSON",
            data=json.dumps(export_data, indent=2),
            file_name=f"wheat_production_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
        )

        # CSV export
        df_export = pd.DataFrame(st.session_state.wheat_data).T
        csv_data = df_export.to_csv()
        st.download_button(
            label="📥 Download as CSV",
            data=csv_data,
            file_name=f"wheat_production_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
        )

    with col2:
        st.subheader("Import Data")

        uploaded_file = st.file_uploader("Upload JSON data file", type=["json"])

        if uploaded_file is not None:
            try:
                uploaded_data = json.load(uploaded_file)

                if st.button("Import Data"):
                    if "wheat_production_data" in uploaded_data:
                        st.session_state.wheat_data = uploaded_data[
                            "wheat_production_data"
                        ]

                    if "metadata" in uploaded_data:
                        st.session_state.production_projection_metadata = uploaded_data[
                            "metadata"
                        ]

                    st.success("Data imported successfully!")
                    st.rerun()

            except json.JSONDecodeError:
                st.error("Invalid JSON file format")

# Footer
st.markdown("---")
status_text = (
    "🗄️ Database Connected"
    if st.session_state.production_data_loaded
    else "💾 Local Data Mode"
)
user_info = f"👤 {st.session_state.get('name', 'User')}"
st.markdown(
    f"""
    <div style='text-align: center; color: #666; font-size: 0.8em;'>
    🌾 Wheat Production Dashboard | {status_text} | {user_info} | PPF Europe Analysis Platform
    </div>
    """,
    unsafe_allow_html=True,
)
