import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import sys
import os
import json

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
    page_title="Wheat Imports Dashboard",
    page_icon="📥",
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
        if st.button("🌾 Production", use_container_width=True):
            st.switch_page("wheat_pages/1_wheat_production.py")
        if st.button("🏢 Stocks", use_container_width=True):
            st.switch_page("wheat_pages/4_wheat_stocks.py")
        if st.button("🌾 Acreage", use_container_width=True):
            st.switch_page("wheat_pages/6_wheat_acreage.py")
    with col2:
        if st.button("📦 Exports", use_container_width=True):
            st.switch_page("wheat_pages/2_wheat_exports.py")
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
    st.markdown("### 📥 Imports Dashboard")


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


# Load import data from database
@st.cache_data
def load_import_data():
    """Load import data from database"""
    db = get_database()
    if not db:
        return None, None

    try:
        # Get import data
        import_data = db.get_all_import_data()

        # Get metadata
        metadata = db.get_metadata()
        projection_metadata = {
            "last_updated": metadata.get("import_last_updated", "19 Sept'24"),
            "next_update": metadata.get("import_next_update", "17 Oct'24"),
        }

        return import_data, projection_metadata
    except Exception as e:
        st.error(f"❌ Error loading import data from database: {e}")
        return None, None


# Initialize session state
def initialize_session_state():
    """Initialize session state with database data"""
    if "import_data_loaded" not in st.session_state:
        import_data, projection_metadata = load_import_data()

        if import_data and projection_metadata:
            st.session_state.import_data = import_data
            st.session_state.import_projection_metadata = projection_metadata
            st.session_state.import_data_loaded = True
        else:
            # Fallback to sample data if database is not available
            st.session_state.import_data = {
                "Egypt": {
                    "2021/2022": 12.0,
                    "2021/2022_pct": None,
                    "2022/2023": 12.9,
                    "2022/2023_change": 0.9,
                    "2023/2024": 12.8,
                    "2023/2024_change": -0.1,
                    "2024/2025": 12.3,
                    "2024/2025_change": -0.5,
                },
                "Indonesia": {
                    "2021/2022": 10.5,
                    "2021/2022_pct": None,
                    "2022/2023": 9.6,
                    "2022/2023_change": -0.9,
                    "2023/2024": 13.1,
                    "2023/2024_change": 3.5,
                    "2024/2025": 10.9,
                    "2024/2025_change": -2.2,
                },
            }
            st.session_state.import_projection_metadata = {
                "last_updated": "19 Sept'24",
                "next_update": "17 Oct'24",
            }
            st.session_state.import_data_loaded = False


# Initialize session state
initialize_session_state()

# Title and header
st.title("📥 Wheat Imports Dashboard")
st.markdown("### Major Wheat Importers Data Management")

# Database status indicator
if st.session_state.import_data_loaded:
    st.sidebar.success("🗄️ Connected to Database")
else:
    st.sidebar.warning("⚠️ Using Local Data (No Database)")

# Sidebar for data management
create_projection_dates_sidebar(
    st.session_state.import_projection_metadata,
    "import_last_updated",
    "import_next_update",
)

# Main content area
tab1, tab2, tab3, tab4 = st.tabs(
    ["📈 Data Overview", "✏️ Edit Projections", "📊 Visualizations", "💾 Data Export"]
)

with tab1:
    st.header("Global Wheat Imports")

    # Display custom status indicators for imports
    st.markdown("### Status Information")
    status_cols = st.columns(4)
    with status_cols[0]:
        st.info("**2021/2022**: act")
    with status_cols[1]:
        st.info("**2022/2023**: act")
    with status_cols[2]:
        st.warning("**2023/2024**: act+fc")
    with status_cols[3]:
        st.success("**2024/2025**: projection")

    # Display projection dates
    st.markdown(
        f"**Projection Dates**: {st.session_state.import_projection_metadata['last_updated']} | {st.session_state.import_projection_metadata['next_update']}"
    )

    st.markdown("---")

    # Create enhanced table
    st.markdown("### Import Data (Million Metric Tons)")

    # Create the data table with proper formatting
    table_data = []
    for country, data in st.session_state.import_data.items():
        if country != "TOTAL MAJOR IMPORTERS":  # Show total at the end
            row = {
                "Country": country,
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

    # Add total row if it exists
    if "TOTAL MAJOR IMPORTERS" in st.session_state.import_data:
        data = st.session_state.import_data["TOTAL MAJOR IMPORTERS"]
        total_row = {
            "Country": "TOTAL MAJOR IMPORTERS",
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
        table_data.append(total_row)

    df_display = pd.DataFrame(table_data)

    # Apply styling to the dataframe
    styled_df = (
        df_display.style.map(
            style_change_column, subset=["Change", "Change ", "Change  "]
        )
        .set_properties(**{"text-align": "center"})
        .set_properties(**{"text-align": "left"}, subset=["Country"])
    )

    st.dataframe(styled_df, use_container_width=True, hide_index=True)

    # Summary statistics
    st.markdown("### Summary Statistics")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_imports = st.session_state.import_data.get(
            "TOTAL MAJOR IMPORTERS", {}
        ).get("2024/2025", 0)
        st.metric("Total Major Imports 2024/2025", f"{total_imports:.1f} Mt")

    with col2:
        total_change = st.session_state.import_data.get(
            "TOTAL MAJOR IMPORTERS", {}
        ).get("2024/2025_change", 0)
        st.metric("Change from 2023/2024", f"{total_change:+.1f} Mt")

    with col3:
        # Find top importer (excluding TOTAL)
        countries_only = {
            k: v
            for k, v in st.session_state.import_data.items()
            if k != "TOTAL MAJOR IMPORTERS"
        }
        if countries_only:
            top_importer = max(countries_only.items(), key=lambda x: x[1]["2024/2025"])
            st.metric("Top Importer 2024/2025", top_importer[0])

    with col4:
        if countries_only:
            top_import = top_importer[1]["2024/2025"]
            st.metric("Top Import Volume", f"{top_import:.1f} Mt")

with tab2:
    st.header("Edit 2024/2025 Import Projections")
    st.markdown(
        "**Note:** Historical data (2021/2022 - 2023/2024) is static and cannot be modified."
    )

    # Create form for editing projections
    with st.form("import_projection_form"):
        st.markdown("### Update Import Projections and Changes")

        # Create input fields for each country
        updated_values = {}
        updated_changes = {}

        for country in st.session_state.import_data.keys():
            if country == "TOTAL MAJOR IMPORTERS":
                continue  # Skip total as it should be calculated

            current_value = st.session_state.import_data[country]["2024/2025"]
            current_change = st.session_state.import_data[country].get(
                "2024/2025_change", 0
            )

            # Show historical trend
            historical_values = [
                st.session_state.import_data[country]["2021/2022"],
                st.session_state.import_data[country]["2022/2023"],
                st.session_state.import_data[country]["2023/2024"],
            ]

            st.subheader(f"{country}")
            col1, col2, col3 = st.columns([2, 1, 1])

            with col1:
                updated_values[country] = st.number_input(
                    f"Imports (Mt)",
                    value=float(current_value),
                    min_value=0.0,
                    step=0.1,
                    format="%.1f",
                    key=f"import_{country}",
                    help=f"Historical: {historical_values[0]:.1f} → {historical_values[1]:.1f} → {historical_values[2]:.1f}",
                )

            with col2:
                updated_changes[country] = st.number_input(
                    f"Change from 2023/2024",
                    value=float(current_change),
                    step=0.1,
                    format="%.1f",
                    key=f"import_change_{country}",
                    help="Positive for increase, negative for decrease",
                )

            with col3:
                # Calculate and display automatic change
                auto_change = (
                    updated_values[country]
                    - st.session_state.import_data[country]["2023/2024"]
                )
                if auto_change > 0:
                    st.success(f"Auto: +{auto_change:.1f}")
                elif auto_change < 0:
                    st.error(f"Auto: {auto_change:.1f}")
                else:
                    st.info("Auto: 0.0")

        # Submit button
        if st.form_submit_button("Update Import Projections", type="primary"):
            # Update the data
            db = get_database()

            # Update individual countries
            for country, value in updated_values.items():
                st.session_state.import_data[country]["2024/2025"] = value
                st.session_state.import_data[country]["2024/2025_change"] = (
                    updated_changes[country]
                )

                # Save to database
                if db:
                    db.update_import_value(
                        country, "2024/2025", value, updated_changes[country]
                    )

            # Calculate and update total
            total_imports = sum(updated_values.values())
            total_change = sum(updated_changes.values())

            if "TOTAL MAJOR IMPORTERS" in st.session_state.import_data:
                st.session_state.import_data["TOTAL MAJOR IMPORTERS"][
                    "2024/2025"
                ] = total_imports
                st.session_state.import_data["TOTAL MAJOR IMPORTERS"][
                    "2024/2025_change"
                ] = total_change

                if db:
                    db.update_import_value(
                        "TOTAL MAJOR IMPORTERS",
                        "2024/2025",
                        total_imports,
                        total_change,
                    )

            st.success("✅ Import projections updated successfully!")
            if db:
                st.info("💾 Changes saved to database")
            st.rerun()

with tab3:
    st.header("Import Visualizations")

    # Time series plot
    st.subheader("Import Trends Over Time")

    # Select countries to display
    countries_to_plot = st.multiselect(
        "Select countries to display:",
        options=[
            c
            for c in st.session_state.import_data.keys()
            if c != "TOTAL MAJOR IMPORTERS"
        ],
        default=(
            ["Egypt", "Indonesia", "EU-27", "Turkey", "China", "Philippines"][:6]
            if len(st.session_state.import_data) > 7
            else list(st.session_state.import_data.keys())[:6]
        ),
    )

    if countries_to_plot:
        # Create time series plot
        fig = go.Figure()

        years = ["2021/2022", "2022/2023", "2023/2024", "2024/2025"]

        for country in countries_to_plot:
            if country in st.session_state.import_data:
                values = [st.session_state.import_data[country][year] for year in years]

                fig.add_trace(
                    go.Scatter(
                        x=years,
                        y=values,
                        mode="lines+markers",
                        name=country,
                        hovertemplate=f"<b>{country}</b><br>"
                        + "Year: %{x}<br>"
                        + "Imports: %{y:.1f} Mt<extra></extra>",
                    )
                )

        # Add total line if requested
        if st.checkbox("Show Total Major Importers"):
            if "TOTAL MAJOR IMPORTERS" in st.session_state.import_data:
                total_values = [
                    st.session_state.import_data["TOTAL MAJOR IMPORTERS"][year]
                    for year in years
                ]
                fig.add_trace(
                    go.Scatter(
                        x=years,
                        y=total_values,
                        mode="lines+markers",
                        name="TOTAL MAJOR IMPORTERS",
                        line=dict(dash="dash", width=3),
                        hovertemplate="<b>TOTAL</b><br>"
                        + "Year: %{x}<br>"
                        + "Imports: %{y:.1f} Mt<extra></extra>",
                    )
                )

        fig.update_layout(
            title="Wheat Import Trends by Major Importers",
            xaxis_title="Year",
            yaxis_title="Imports (Million Metric Tons)",
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

    # Top importers bar chart
    st.subheader("Top 10 Wheat Importers (2024/2025)")

    # Get top 10 importers
    countries_only = {
        k: v
        for k, v in st.session_state.import_data.items()
        if k != "TOTAL MAJOR IMPORTERS"
    }
    top_importers = sorted(
        countries_only.items(), key=lambda x: x[1]["2024/2025"], reverse=True
    )[:10]

    if top_importers:
        fig_bar = go.Figure(
            data=[
                go.Bar(
                    x=[country for country, _ in top_importers],
                    y=[data["2024/2025"] for _, data in top_importers],
                    text=[f"{data['2024/2025']:.1f}" for _, data in top_importers],
                    textposition="auto",
                    marker_color="lightblue",
                    hovertemplate="<b>%{x}</b><br>"
                    + "Imports: %{y:.1f} Mt<extra></extra>",
                )
            ]
        )

        fig_bar.update_layout(
            title="Top 10 Wheat Importers - 2024/2025 Projection",
            xaxis_title="Country",
            yaxis_title="Imports (Million Metric Tons)",
            height=400,
        )

        st.plotly_chart(fig_bar, use_container_width=True)

    # Change analysis
    create_change_visualization(
        st.session_state.import_data, "Imports", exclude=["TOTAL MAJOR IMPORTERS"]
    )

with tab4:
    st.header("Import Data Management")

    # Export options
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Export Current Data")

        # Prepare export data
        export_data = {
            "wheat_import_data": st.session_state.import_data,
            "metadata": st.session_state.import_projection_metadata,
            "export_timestamp": datetime.now().isoformat(),
            "data_source": (
                "database" if st.session_state.import_data_loaded else "local"
            ),
            "user": st.session_state.get("username", "unknown"),
        }

        # JSON export
        st.download_button(
            label="📥 Download Import Data as JSON",
            data=json.dumps(export_data, indent=2),
            file_name=f"wheat_import_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
        )

        # CSV export
        df_export = pd.DataFrame(st.session_state.import_data).T
        csv_data = df_export.to_csv()
        st.download_button(
            label="📥 Download Import Data as CSV",
            data=csv_data,
            file_name=f"wheat_import_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
        )

    with col2:
        st.subheader("Import Data")

        uploaded_file = st.file_uploader("Upload JSON import data file", type=["json"])

        if uploaded_file is not None:
            try:
                uploaded_data = json.load(uploaded_file)

                if st.button("Import Import Data"):
                    if "wheat_import_data" in uploaded_data:
                        st.session_state.import_data = uploaded_data[
                            "wheat_import_data"
                        ]

                    if "metadata" in uploaded_data:
                        st.session_state.import_projection_metadata = uploaded_data[
                            "metadata"
                        ]

                    st.success("Import data imported successfully!")
                    st.rerun()

            except json.JSONDecodeError:
                st.error("Invalid JSON file format")

# Footer
st.markdown("---")
status_text = (
    "🗄️ Database Connected"
    if st.session_state.import_data_loaded
    else "💾 Local Data Mode"
)
user_info = f"👤 {st.session_state.get('name', 'User')}"
st.markdown(
    f"""
    <div style='text-align: center; color: #666; font-size: 0.8em;'>
    📥 Wheat Imports Dashboard | {status_text} | {user_info} | PPF Europe Analysis Platform
    </div>
    """,
    unsafe_allow_html=True,
)
