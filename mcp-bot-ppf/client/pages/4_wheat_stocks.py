import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
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
    page_title="Wheat Ending Stocks Dashboard",
    page_icon="🏢",
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
            st.switch_page("pages/1_wheat_production.py")
        if st.button("📥 Imports", use_container_width=True):
            st.switch_page("pages/3_wheat_imports.py")
        if st.button("🌾 Acreage", use_container_width=True):
            st.switch_page("pages/6_wheat_acreage.py")
    with col2:
        if st.button("📦 Exports", use_container_width=True):
            st.switch_page("pages/2_wheat_exports.py")
        if st.button("📊 S/U Ratio", use_container_width=True):
            st.switch_page("pages/5_stock_to_use_ratio.py")
        if st.button("🌱 Yield", use_container_width=True):
            st.switch_page("pages/7_wheat_yield.py")

    st.markdown("---")

    # AI Tools section
    st.markdown("### 🤖 AI & MCP Tools")
    if st.button("💬 Launch AI Chat", use_container_width=True):
        st.switch_page("pages/8_mcp_app.py")

    st.markdown("---")
    st.markdown("### 🏢 Stocks Dashboard")


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


# Load stocks data from database
@st.cache_data
def load_stocks_data():
    """Load ending stocks data from database"""
    db = get_database()
    if not db:
        return None, None

    try:
        # Get stocks data
        stocks_data = db.get_all_stocks_data()

        # Get metadata
        metadata = db.get_metadata()
        projection_metadata = {
            "last_updated": metadata.get("stocks_last_updated", "19 Sept'24"),
            "next_update": metadata.get("stocks_next_update", "17 Oct'24"),
        }

        return stocks_data, projection_metadata
    except Exception as e:
        st.error(f"❌ Error loading stocks data from database: {e}")
        return None, None


# Initialize session state
def initialize_session_state():
    """Initialize session state with database data"""
    if "stocks_data_loaded" not in st.session_state:
        stocks_data, projection_metadata = load_stocks_data()

        if stocks_data and projection_metadata:
            st.session_state.stocks_data = stocks_data
            st.session_state.stocks_projection_metadata = projection_metadata
            st.session_state.stocks_data_loaded = True
        else:
            # Fallback to sample data if database is not available
            st.session_state.stocks_data = {
                "WORLD": {
                    "2021/2022": 274.3,
                    "2021/2022_pct": None,
                    "2021/2022_s_u": 35.2,
                    "2022/2023": 283.9,
                    "2022/2023_change": 9.6,
                    "2022/2023_s_u": 35.3,
                    "2023/2024": 272.2,
                    "2023/2024_change": -11.7,
                    "2023/2024_s_u": 34.2,
                    "2024/2025": 267.0,
                    "2024/2025_change": -5.2,
                    "2024/2025_s_u": 33.5,
                },
                "China": {
                    "2021/2022": 132.9,
                    "2021/2022_pct": 48.5,
                    "2021/2022_s_u": 95.0,
                    "2022/2023": 140.3,
                    "2022/2023_change": 7.4,
                    "2022/2023_s_u": 100.2,
                    "2023/2024": 140.1,
                    "2023/2024_change": -0.2,
                    "2023/2024_s_u": 102.6,
                    "2024/2025": 142.9,
                    "2024/2025_change": 2.8,
                    "2024/2025_s_u": 102.1,
                },
            }
            st.session_state.stocks_projection_metadata = {
                "last_updated": "19 Sept'24",
                "next_update": "17 Oct'24",
            }
            st.session_state.stocks_data_loaded = False


# Initialize session state
initialize_session_state()

# Title and header
st.title("🏢 Wheat Ending Stocks Dashboard")
st.markdown("### Global Wheat Stocks Management and Analysis")

# Database status indicator
if st.session_state.stocks_data_loaded:
    st.sidebar.success("🗄️ Connected to Database")
else:
    st.sidebar.warning("⚠️ Using Local Data (No Database)")

# Sidebar for data management
create_projection_dates_sidebar(
    st.session_state.stocks_projection_metadata,
    "stocks_last_updated",
    "stocks_next_update",
)

# Main content area
tab1, tab2, tab3, tab4, tab5 = st.tabs(
    [
        "📈 Data Overview",
        "✏️ Edit Projections",
        "📊 Visualizations",
        "📐 Stock-to-Use Analysis",
        "💾 Data Export",
    ]
)

with tab1:
    st.header("Global Wheat Ending Stocks")

    # Display status indicators
    create_status_indicators()

    # Display projection dates
    st.markdown(
        f"**Projection Dates**: {st.session_state.stocks_projection_metadata['last_updated']} | {st.session_state.stocks_projection_metadata['next_update']}"
    )

    st.markdown("---")

    # Key insights
    st.info(
        """
    **Key Insights:**
    - Ending stocks represent the total quantity of wheat held in storage at the end of each marketing year
    - China holds over 50% of global wheat stocks
    - Stock-to-use ratio indicates supply security (higher = more buffer)
    """
    )

    # Create enhanced table
    st.markdown("### Ending Stocks Data (Million Metric Tons)")

    # Create the data table with proper formatting
    table_data = []
    for country, data in st.session_state.stocks_data.items():
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
            "S/U Ratio": (
                f"{data.get('2024/2025_s_u', 0):.1f}%"
                if data.get("2024/2025_s_u")
                else "-"
            ),
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
        world_stocks = st.session_state.stocks_data.get("WORLD", {}).get("2024/2025", 0)
        st.metric("Global Stocks 2024/2025", f"{world_stocks:.1f} Mt")

    with col2:
        world_change = st.session_state.stocks_data.get("WORLD", {}).get(
            "2024/2025_change", 0
        )
        st.metric("Change from 2023/2024", f"{world_change:+.1f} Mt")

    with col3:
        world_su_ratio = st.session_state.stocks_data.get("WORLD", {}).get(
            "2024/2025_s_u", 0
        )
        st.metric("Global Stock-to-Use Ratio", f"{world_su_ratio:.1f}%")

    with col4:
        # China's share of global stocks
        china_stocks = st.session_state.stocks_data.get("China", {}).get("2024/2025", 0)
        china_share = (china_stocks / world_stocks * 100) if world_stocks > 0 else 0
        st.metric("China's Share of Stocks", f"{china_share:.1f}%")

with tab2:
    st.header("Edit 2024/2025 Stock Projections")
    st.markdown(
        "**Note:** Historical data (2021/2022 - 2023/2024) is static and cannot be modified."
    )

    # Create form for editing projections
    with st.form("stocks_projection_form"):
        st.markdown("### Update Stock Projections and Changes")

        # Create input fields for each country
        updated_values = {}
        updated_changes = {}
        updated_su_ratios = {}

        for country in st.session_state.stocks_data.keys():
            if country == "Others":
                continue  # Skip others as it should be calculated

            current_value = st.session_state.stocks_data[country]["2024/2025"]
            current_change = st.session_state.stocks_data[country].get(
                "2024/2025_change", 0
            )
            current_su = st.session_state.stocks_data[country].get("2024/2025_s_u", 0)

            # Show historical trend
            historical_values = [
                st.session_state.stocks_data[country]["2021/2022"],
                st.session_state.stocks_data[country]["2022/2023"],
                st.session_state.stocks_data[country]["2023/2024"],
            ]

            st.subheader(f"{country}")
            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

            with col1:
                updated_values[country] = st.number_input(
                    f"Stocks (Mt)",
                    value=float(current_value),
                    min_value=0.0,
                    step=0.1,
                    format="%.1f",
                    key=f"stocks_{country}",
                    help=f"Historical: {historical_values[0]:.1f} → {historical_values[1]:.1f} → {historical_values[2]:.1f}",
                )

            with col2:
                updated_changes[country] = st.number_input(
                    f"Change from 2023/2024",
                    value=float(current_change),
                    step=0.1,
                    format="%.1f",
                    key=f"stocks_change_{country}",
                    help="Positive for increase, negative for decrease",
                )

            with col3:
                if current_su > 0:
                    updated_su_ratios[country] = st.number_input(
                        f"S/U Ratio (%)",
                        value=float(current_su),
                        min_value=0.0,
                        step=0.1,
                        format="%.1f",
                        key=f"stocks_su_{country}",
                        help="Stock-to-Use ratio as percentage",
                    )
                else:
                    updated_su_ratios[country] = 0
                    st.text("N/A")

            with col4:
                # Calculate and display automatic change
                auto_change = (
                    updated_values[country]
                    - st.session_state.stocks_data[country]["2023/2024"]
                )
                if auto_change > 0:
                    st.success(f"Auto: +{auto_change:.1f}")
                elif auto_change < 0:
                    st.error(f"Auto: {auto_change:.1f}")
                else:
                    st.info("Auto: 0.0")

        # Submit button
        if st.form_submit_button("Update Stock Projections", type="primary"):
            # Update the data
            db = get_database()

            # Update individual countries
            for country, value in updated_values.items():
                st.session_state.stocks_data[country]["2024/2025"] = value
                st.session_state.stocks_data[country]["2024/2025_change"] = (
                    updated_changes[country]
                )
                if country in updated_su_ratios:
                    st.session_state.stocks_data[country]["2024/2025_s_u"] = (
                        updated_su_ratios[country]
                    )

                # Save to database
                if db:
                    db.update_stocks_value(
                        country,
                        "2024/2025",
                        value,
                        updated_changes[country],
                        updated_su_ratios.get(country),
                    )

            st.success("✅ Stock projections updated successfully!")
            if db:
                st.info("💾 Changes saved to database")
            st.rerun()

with tab3:
    st.header("Stock Visualizations")

    # Time series plot
    st.subheader("Ending Stocks Trends Over Time")

    # Select countries to display
    countries_to_plot = st.multiselect(
        "Select countries/regions to display:",
        options=[c for c in st.session_state.stocks_data.keys() if c != "Others"],
        default=[
            "WORLD",
            "China",
            "United States",
            "European Union 27 (FR, DE)",
            "India",
            "Russia",
        ],
    )

    if countries_to_plot:
        # Create time series plot
        fig = go.Figure()

        years = ["2021/2022", "2022/2023", "2023/2024", "2024/2025"]

        for country in countries_to_plot:
            values = [st.session_state.stocks_data[country][year] for year in years]

            fig.add_trace(
                go.Scatter(
                    x=years,
                    y=values,
                    mode="lines+markers",
                    name=country,
                    hovertemplate=f"<b>{country}</b><br>"
                    + "Year: %{x}<br>"
                    + "Stocks: %{y:.1f} Mt<extra></extra>",
                )
            )

        fig.update_layout(
            title="Wheat Ending Stocks Trends",
            xaxis_title="Year",
            yaxis_title="Ending Stocks (Million Metric Tons)",
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

    # Stock distribution pie chart
    st.subheader("Global Stock Distribution (2024/2025)")

    # Prepare data for pie chart (excluding WORLD)
    countries_only = {
        k: v for k, v in st.session_state.stocks_data.items() if k != "WORLD"
    }

    fig_pie = go.Figure(
        data=[
            go.Pie(
                labels=list(countries_only.keys()),
                values=[data["2024/2025"] for data in countries_only.values()],
                hovertemplate="<b>%{label}</b><br>"
                + "Stocks: %{value:.1f} Mt<br>"
                + "Share: %{percent}<extra></extra>",
            )
        ]
    )

    fig_pie.update_layout(
        title="Distribution of Global Wheat Stocks - 2024/2025 Projection", height=500
    )

    st.plotly_chart(fig_pie, use_container_width=True)

    # Change analysis
    create_change_visualization(
        st.session_state.stocks_data, "Stocks", exclude=["WORLD", "Others"]
    )

with tab4:
    st.header("Stock-to-Use Ratio Analysis")

    st.markdown(
        """
    **Stock-to-Use (S/U) Ratio** indicates the level of carryover stock as a percentage of total use.
    - **< 20%**: Tight supplies, potential price volatility
    - **20-30%**: Adequate supplies for most countries
    - **> 30%**: Comfortable buffer stocks
    - **> 50%**: High stock levels (common for strategic reserves)
    """
    )

    # S/U Ratio comparison
    st.subheader("Stock-to-Use Ratios by Country (2024/2025)")

    # Get S/U data for countries that have it
    su_data = []
    for country, data in st.session_state.stocks_data.items():
        if country != "Others" and data.get("2024/2025_s_u"):
            su_data.append(
                {
                    "Country": country,
                    "S/U Ratio": data["2024/2025_s_u"],
                    "Category": (
                        "Strategic Reserve"
                        if data["2024/2025_s_u"] > 50
                        else (
                            "Comfortable"
                            if data["2024/2025_s_u"] > 30
                            else "Adequate" if data["2024/2025_s_u"] > 20 else "Tight"
                        )
                    ),
                }
            )

    df_su = pd.DataFrame(su_data)
    df_su = df_su.sort_values("S/U Ratio", ascending=False)

    # Create bar chart with color coding
    fig_su = px.bar(
        df_su,
        x="Country",
        y="S/U Ratio",
        color="Category",
        color_discrete_map={
            "Strategic Reserve": "#2ca02c",
            "Comfortable": "#1f77b4",
            "Adequate": "#ff7f0e",
            "Tight": "#d62728",
        },
        title="Stock-to-Use Ratios by Country",
    )

    fig_su.update_layout(
        xaxis_title="Country", yaxis_title="Stock-to-Use Ratio (%)", height=400
    )

    # Add reference lines
    fig_su.add_hline(
        y=20,
        line_dash="dash",
        line_color="red",
        annotation_text="Tight Supplies",
        annotation_position="right",
    )
    fig_su.add_hline(
        y=30,
        line_dash="dash",
        line_color="orange",
        annotation_text="Adequate",
        annotation_position="right",
    )
    fig_su.add_hline(
        y=50,
        line_dash="dash",
        line_color="green",
        annotation_text="Strategic Reserve",
        annotation_position="right",
    )

    st.plotly_chart(fig_su, use_container_width=True)

    # S/U Ratio trends
    st.subheader("Stock-to-Use Ratio Trends")

    countries_su = st.multiselect(
        "Select countries to compare S/U trends:",
        options=[
            c
            for c in st.session_state.stocks_data.keys()
            if st.session_state.stocks_data[c].get("2021/2022_s_u")
        ],
        default=["WORLD", "China", "United States", "India"],
    )

    if countries_su:
        fig_su_trend = go.Figure()

        years = ["2021/2022", "2022/2023", "2023/2024", "2024/2025"]

        for country in countries_su:
            su_values = []
            for year in years:
                su_key = f"{year}_s_u"
                su_values.append(st.session_state.stocks_data[country].get(su_key, 0))

            fig_su_trend.add_trace(
                go.Scatter(
                    x=years,
                    y=su_values,
                    mode="lines+markers",
                    name=country,
                    hovertemplate=f"<b>{country}</b><br>"
                    + "Year: %{x}<br>"
                    + "S/U Ratio: %{y:.1f}%<extra></extra>",
                )
            )

        fig_su_trend.update_layout(
            title="Stock-to-Use Ratio Trends",
            xaxis_title="Year",
            yaxis_title="Stock-to-Use Ratio (%)",
            hovermode="x unified",
            height=400,
        )

        st.plotly_chart(fig_su_trend, use_container_width=True)

with tab5:
    st.header("Stock Data Management")

    # Export options
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Export Current Data")

        # Prepare export data
        export_data = {
            "wheat_stocks_data": st.session_state.stocks_data,
            "metadata": st.session_state.stocks_projection_metadata,
            "export_timestamp": datetime.now().isoformat(),
            "data_source": (
                "database" if st.session_state.stocks_data_loaded else "local"
            ),
            "user": st.session_state.get("username", "unknown"),
        }

        # JSON export
        st.download_button(
            label="📥 Download Stocks Data as JSON",
            data=json.dumps(export_data, indent=2),
            file_name=f"wheat_stocks_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
        )

        # CSV export
        df_export = pd.DataFrame(st.session_state.stocks_data).T
        csv_data = df_export.to_csv()
        st.download_button(
            label="📥 Download Stocks Data as CSV",
            data=csv_data,
            file_name=f"wheat_stocks_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
        )

    with col2:
        st.subheader("Import Data")

        uploaded_file = st.file_uploader("Upload JSON stocks data file", type=["json"])

        if uploaded_file is not None:
            try:
                uploaded_data = json.load(uploaded_file)

                if st.button("Import Stocks Data"):
                    if "wheat_stocks_data" in uploaded_data:
                        st.session_state.stocks_data = uploaded_data[
                            "wheat_stocks_data"
                        ]

                    if "metadata" in uploaded_data:
                        st.session_state.stocks_projection_metadata = uploaded_data[
                            "metadata"
                        ]

                    st.success("Stocks data imported successfully!")
                    st.rerun()

            except json.JSONDecodeError:
                st.error("Invalid JSON file format")

# Footer
st.markdown("---")
status_text = (
    "🗄️ Database Connected"
    if st.session_state.stocks_data_loaded
    else "💾 Local Data Mode"
)
user_info = f"👤 {st.session_state.get('name', 'User')}"
st.markdown(
    f"""
    <div style='text-align: center; color: #666; font-size: 0.8em;'>
    🏢 Wheat Ending Stocks Dashboard | {status_text} | {user_info} | PPF Europe Analysis Platform
    </div>
    """,
    unsafe_allow_html=True,
)
