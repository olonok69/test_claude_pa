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
    create_change_visualization,
    style_change_column,
)

# Page configuration
st.set_page_config(
    page_title="Wheat World Demand Dashboard",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)
# Import AI Research components
from utils.enhanced_ai_research_tab import create_ai_research_tab

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

# Define demand categories
DEMAND_CATEGORIES = ["Food", "Feed", "Industrial", "Seed", "Other", "Total Consumption"]

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
        if st.button("🌿 Acreage", use_container_width=True):
            st.switch_page("pages/6_wheat_acreage.py")
    with col2:
        if st.button("📦 Exports", use_container_width=True):
            st.switch_page("pages/2_wheat_exports.py")
        if st.button("🏢 Stocks", use_container_width=True):
            st.switch_page("pages/4_wheat_stocks.py")
        if st.button("📊 S/U Ratio", use_container_width=True):
            st.switch_page("pages/5_stock_to_use_ratio.py")

    if st.button("🌱 Yield", use_container_width=True):
        st.switch_page("pages/7_wheat_yield.py")

    st.markdown("---")

    # AI Tools section
    st.markdown("### 🤖 AI & MCP Tools")
    if st.button("💬 Launch AI Chat", use_container_width=True):
        st.switch_page("pages/9_mcp_app.py")

    st.markdown("---")
    st.markdown("### 🌍 World Demand Dashboard")

    # Add current date in sidebar
    st.markdown("---")
    st.info(f"📅 **Current Date:** {datetime.now().strftime('%d %b %Y')}")


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


# Load world demand data from database
@st.cache_data
def load_world_demand_data():
    """Load world demand data from database"""
    db = get_database()
    if not db:
        return None, None, None

    try:
        conn = db.get_connection()
        cursor = conn.cursor()

        # Get all world demand data
        cursor.execute(
            """
            SELECT category, year, demand_value, percentage_total, change_value, 
                   change_percentage, status
            FROM wheat_world_demand
            ORDER BY 
                CASE category
                    WHEN 'Food' THEN 1
                    WHEN 'Feed' THEN 2
                    WHEN 'Industrial' THEN 3
                    WHEN 'Seed' THEN 4
                    WHEN 'Other' THEN 5
                    WHEN 'Total Consumption' THEN 6
                END,
                year
        """
        )

        rows = cursor.fetchall()

        # Convert to nested dictionary format
        demand_data = {}
        for category, year, value, pct_total, change, change_pct, status in rows:
            if category not in demand_data:
                demand_data[category] = {}

            demand_data[category][year] = value
            if pct_total is not None:
                demand_data[category][f"{year}_pct"] = pct_total
            if change is not None:
                demand_data[category][f"{year}_change"] = change
            if change_pct is not None:
                demand_data[category][f"{year}_change_pct"] = change_pct

        # Get metadata
        metadata = db.get_metadata()

        # Get current year configuration
        current_config = {
            "display_years": metadata.get(
                "world_demand_display_years", "2022/2023,2023/2024,2024/2025,2025/2026"
            ).split(","),
            "year_status": json.loads(
                metadata.get(
                    "world_demand_year_status",
                    '{"2022/2023": "actual", "2023/2024": "actual", "2024/2025": "estimate", "2025/2026": "projection"}',
                )
            ),
        }

        conn.close()
        return demand_data, metadata, current_config

    except Exception as e:
        st.error(f"❌ Error loading world demand data: {e}")
        return None, None, None


# Function to update demand value in database
def update_demand_value_in_db(category, year, value, change=None, change_pct=None):
    """Update demand value in database"""
    db = get_database()
    if not db:
        return False

    try:
        conn = db.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE wheat_world_demand
            SET demand_value = ?, change_value = ?, change_percentage = ?, updated_at = ?
            WHERE category = ? AND year = ?
        """,
            (value, change, change_pct, datetime.now().isoformat(), category, year),
        )

        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"❌ Error updating demand value: {e}")
        return False


# Initialize session state
def initialize_session_state():
    """Initialize session state with database data"""
    if "demand_data_loaded" not in st.session_state:
        demand_data, metadata, current_config = load_world_demand_data()

        if demand_data and metadata:
            st.session_state.demand_data = demand_data
            st.session_state.demand_metadata = metadata
            st.session_state.demand_current_config = current_config
            st.session_state.demand_data_loaded = True
        else:
            # Fallback to empty data
            st.session_state.demand_data = {}
            st.session_state.demand_metadata = {}
            st.session_state.demand_current_config = {
                "display_years": ["2022/2023", "2023/2024", "2024/2025", "2025/2026"],
                "year_status": {
                    "2022/2023": "actual",
                    "2023/2024": "actual",
                    "2024/2025": "estimate",
                    "2025/2026": "projection",
                },
            }
            st.session_state.demand_data_loaded = False


# Initialize session state
initialize_session_state()

# Title and header
st.title("🌍 Wheat World Demand Dashboard")
st.markdown("### Global Wheat Consumption Analysis by Category")

# Database status indicator
if st.session_state.demand_data_loaded:
    st.sidebar.success("🗄️ Connected to Database")
else:
    st.sidebar.warning("⚠️ Using Local Data (No Database)")

# Main content area

tab_names = [
    "📈 Data Overview",
    "✏️ Edit Projections",
    "📊 Visualizations",
    "🤖 AI Research",
    "🌍 Category Analysis",
    "💾 Data Export",
]
tabs = st.tabs(tab_names)

with tabs[0]:
    st.header("Global Wheat Demand by Category")

    # Refresh button
    col1, col2, col3 = st.columns([2, 1, 1])
    with col3:
        if st.button("🔄 Refresh Data"):
            st.cache_data.clear()
            st.rerun()

    # Display dynamic status indicators based on current configuration
    if "demand_current_config" in st.session_state:
        st.markdown("### Status Information")
        status_cols = st.columns(4)

        display_years = st.session_state.demand_current_config["display_years"]
        year_status = st.session_state.demand_current_config["year_status"]

        for i, year in enumerate(display_years):
            if i < len(status_cols):
                with status_cols[i]:
                    status = year_status.get(year, "unknown")
                    if status == "actual":
                        st.info(f"**{year}**: actual")
                    elif status == "estimate":
                        st.warning(f"**{year}**: estimate")
                    elif status == "projection":
                        st.success(f"**{year}**: projection")

    st.markdown("---")

    # Key insights
    st.info(
        """
    **World Demand** represents global wheat consumption across different categories:
    - **Food**: Human consumption (largest category ~70%)
    - **Feed**: Animal feed consumption
    - **Industrial**: Industrial uses (ethanol, starch, etc.)
    - **Seed**: Planting seeds for next season
    - **Other**: Miscellaneous uses and losses
    """
    )

    # Create enhanced table
    st.markdown("### Demand Data (Million Metric Tons)")

    # Get display years from configuration
    display_years = st.session_state.demand_current_config.get(
        "display_years", ["2022/2023", "2023/2024", "2024/2025", "2025/2026"]
    )

    # Create the data table
    table_data = []

    for category in DEMAND_CATEGORIES:
        if category not in st.session_state.demand_data:
            continue

        row = {"Category": category}

        # Add data for display years only
        for i, year in enumerate(display_years):
            if year in st.session_state.demand_data[category]:
                value = st.session_state.demand_data[category][year]
                row[year] = f"{value:.1f}"

                # Add percentage for first year if available
                if i == 0 and f"{year}_pct" in st.session_state.demand_data[category]:
                    pct = st.session_state.demand_data[category][f"{year}_pct"]
                    row[year] += f" ({pct}%)"

                # Calculate change from previous year (except for first year)
                if i > 0:
                    prev_year = display_years[i - 1]
                    if prev_year in st.session_state.demand_data[category]:
                        change = st.session_state.demand_data[category].get(
                            f"{year}_change", 0
                        )
                        row[f"Change{' ' * i}"] = format_change(change)
                    else:
                        row[f"Change{' ' * i}"] = "-"

        table_data.append(row)

    df_display = pd.DataFrame(table_data)

    # Apply styling to the dataframe
    change_columns = [
        col for col in df_display.columns if col.strip().startswith("Change")
    ]

    styled_df = df_display.style
    for col in change_columns:
        styled_df = styled_df.map(style_change_column, subset=[col])

    styled_df = styled_df.set_properties(**{"text-align": "center"})
    styled_df = styled_df.set_properties(**{"text-align": "left"}, subset=["Category"])

    st.dataframe(styled_df, use_container_width=True, hide_index=True)

    # Summary statistics
    st.markdown("### Summary Statistics")
    col1, col2, col3, col4 = st.columns(4)

    # Get the latest projection year
    latest_year = display_years[-1]
    prev_year = display_years[-2] if len(display_years) > 1 else None

    with col1:
        if (
            "Total Consumption" in st.session_state.demand_data
            and latest_year in st.session_state.demand_data["Total Consumption"]
        ):
            total_demand = st.session_state.demand_data["Total Consumption"][
                latest_year
            ]
            st.metric(f"Total Demand {latest_year}", f"{total_demand:.1f} Mt")

    with col2:
        if (
            "Total Consumption" in st.session_state.demand_data
            and latest_year in st.session_state.demand_data["Total Consumption"]
            and prev_year in st.session_state.demand_data["Total Consumption"]
        ):
            change = (
                st.session_state.demand_data["Total Consumption"][latest_year]
                - st.session_state.demand_data["Total Consumption"][prev_year]
            )
            st.metric("Change from Previous Year", f"{change:+.1f} Mt")

    with col3:
        if (
            "Food" in st.session_state.demand_data
            and latest_year in st.session_state.demand_data["Food"]
        ):
            food_demand = st.session_state.demand_data["Food"][latest_year]
            st.metric("Food Demand", f"{food_demand:.1f} Mt")

    with col4:
        if (
            "Feed" in st.session_state.demand_data
            and latest_year in st.session_state.demand_data["Feed"]
        ):
            feed_demand = st.session_state.demand_data["Feed"][latest_year]
            st.metric("Feed Demand", f"{feed_demand:.1f} Mt")

with tabs[1]:
    # Get the projection year (last year in display_years)
    display_years = st.session_state.demand_current_config.get(
        "display_years", ["2022/2023", "2023/2024", "2024/2025", "2025/2026"]
    )
    projection_year = display_years[-1]
    estimate_year = display_years[-2]

    st.header(f"Edit {projection_year} Demand Projections")
    st.markdown(
        f"**Note:** Historical data ({', '.join(display_years[:-1])}) is static and cannot be modified."
    )

    # Create form for editing projections
    with st.form("demand_projection_form"):
        st.markdown(f"### Update Demand Projections for {projection_year}")

        # Create input fields for each category
        updated_values = {}

        # Exclude Total Consumption from manual editing
        editable_categories = [
            cat for cat in DEMAND_CATEGORIES if cat != "Total Consumption"
        ]

        for category in editable_categories:
            if projection_year not in st.session_state.demand_data.get(category, {}):
                continue

            current_value = st.session_state.demand_data[category][projection_year]

            # Show historical trend
            historical_values = []
            for year in display_years[:-1]:
                if year in st.session_state.demand_data[category]:
                    historical_values.append(
                        st.session_state.demand_data[category][year]
                    )

            st.subheader(f"{category}")
            col1, col2, col3 = st.columns([2, 1, 1])

            with col1:
                updated_values[category] = st.number_input(
                    f"Demand (Mt)",
                    value=float(current_value),
                    min_value=0.0,
                    max_value=1000.0,
                    step=0.1,
                    format="%.1f",
                    key=f"demand_{category}",
                    help=(
                        f"Historical: {' → '.join([f'{v:.1f}' for v in historical_values])}"
                        if historical_values
                        else "No historical data"
                    ),
                )

            with col2:
                # Display calculated change
                if estimate_year in st.session_state.demand_data[category]:
                    calc_change = (
                        updated_values[category]
                        - st.session_state.demand_data[category][estimate_year]
                    )
                    change_pct = (
                        (
                            calc_change
                            / st.session_state.demand_data[category][estimate_year]
                        )
                        * 100
                        if st.session_state.demand_data[category][estimate_year] > 0
                        else 0
                    )

                    if calc_change > 0:
                        st.success(f"Change: +{calc_change:.1f} ({change_pct:+.1f}%)")
                    elif calc_change < 0:
                        st.error(f"Change: {calc_change:.1f} ({change_pct:.1f}%)")
                    else:
                        st.info("Change: 0.0 (0.0%)")

            with col3:
                # Category percentage of total
                total_demand = sum(updated_values.values())
                pct_of_total = (
                    (updated_values[category] / total_demand * 100)
                    if total_demand > 0
                    else 0
                )
                st.info(f"{pct_of_total:.1f}% of total")

        # Submit button
        if st.form_submit_button("Update Demand Projections", type="primary"):
            # Calculate total consumption
            total_consumption = sum(updated_values.values())

            # Update individual categories
            for category, value in updated_values.items():
                if estimate_year in st.session_state.demand_data[category]:
                    change = (
                        value - st.session_state.demand_data[category][estimate_year]
                    )
                    change_pct = (
                        (change / st.session_state.demand_data[category][estimate_year])
                        * 100
                        if st.session_state.demand_data[category][estimate_year] > 0
                        else 0
                    )
                else:
                    change = 0
                    change_pct = 0

                # Update in session state
                st.session_state.demand_data[category][projection_year] = value
                st.session_state.demand_data[category][
                    f"{projection_year}_change"
                ] = change
                st.session_state.demand_data[category][
                    f"{projection_year}_change_pct"
                ] = change_pct

                # Save to database
                update_demand_value_in_db(
                    category, projection_year, value, change, change_pct
                )

            # Update Total Consumption
            if estimate_year in st.session_state.demand_data.get(
                "Total Consumption", {}
            ):
                total_change = (
                    total_consumption
                    - st.session_state.demand_data["Total Consumption"][estimate_year]
                )
                total_change_pct = (
                    (
                        total_change
                        / st.session_state.demand_data["Total Consumption"][
                            estimate_year
                        ]
                    )
                    * 100
                    if st.session_state.demand_data["Total Consumption"][estimate_year]
                    > 0
                    else 0
                )
            else:
                total_change = 0
                total_change_pct = 0

            if "Total Consumption" not in st.session_state.demand_data:
                st.session_state.demand_data["Total Consumption"] = {}

            st.session_state.demand_data["Total Consumption"][
                projection_year
            ] = total_consumption
            st.session_state.demand_data["Total Consumption"][
                f"{projection_year}_change"
            ] = total_change
            st.session_state.demand_data["Total Consumption"][
                f"{projection_year}_change_pct"
            ] = total_change_pct

            update_demand_value_in_db(
                "Total Consumption",
                projection_year,
                total_consumption,
                total_change,
                total_change_pct,
            )

            st.success("✅ Demand projections updated successfully!")
            st.info("💾 Changes saved to database")
            st.rerun()

with tabs[2]:
    st.header("Demand Visualizations")

    # Get display years from configuration
    display_years = st.session_state.demand_current_config.get(
        "display_years", ["2022/2023", "2023/2024", "2024/2025", "2025/2026"]
    )

    # Time series plot
    st.subheader("Demand Trends Over Time")

    # Select categories to display
    categories_to_plot = st.multiselect(
        "Select categories to display:",
        options=[
            cat for cat in DEMAND_CATEGORIES if cat in st.session_state.demand_data
        ],
        default=["Food", "Feed", "Total Consumption"],
    )

    if categories_to_plot:
        # Create time series plot
        fig = go.Figure()

        for category in categories_to_plot:
            values = []
            years_with_data = []

            for year in display_years:
                if year in st.session_state.demand_data[category]:
                    values.append(st.session_state.demand_data[category][year])
                    years_with_data.append(year)

            if values:
                fig.add_trace(
                    go.Scatter(
                        x=years_with_data,
                        y=values,
                        mode="lines+markers",
                        name=category,
                        hovertemplate=f"<b>{category}</b><br>"
                        + "Year: %{x}<br>"
                        + "Demand: %{y:.1f} Mt<extra></extra>",
                    )
                )

        fig.update_layout(
            title="Wheat Demand Trends by Category",
            xaxis_title="Year",
            yaxis_title="Demand (Million Metric Tons)",
            hovermode="x unified",
            height=500,
        )

        # Add vertical line to separate historical from projection
        if len(display_years) > 1:
            for i, year in enumerate(display_years):
                if (
                    st.session_state.demand_current_config["year_status"].get(year)
                    == "projection"
                ):
                    fig.add_vline(
                        x=i - 0.5,
                        line_dash="dot",
                        line_color="gray",
                        annotation_text="Historical | Projection",
                        annotation_position="top",
                    )
                    break

        st.plotly_chart(fig, use_container_width=True)

    # Demand composition chart
    st.subheader(f"Demand Composition - {display_years[-1]}")

    # Prepare data for pie chart
    latest_year = display_years[-1]
    composition_data = []

    for category in DEMAND_CATEGORIES:
        if category != "Total Consumption" and category in st.session_state.demand_data:
            if latest_year in st.session_state.demand_data[category]:
                composition_data.append(
                    {
                        "Category": category,
                        "Demand": st.session_state.demand_data[category][latest_year],
                    }
                )

    if composition_data:
        df_composition = pd.DataFrame(composition_data)

        # Create pie chart
        fig_pie = px.pie(
            df_composition,
            values="Demand",
            names="Category",
            title=f"Wheat Demand Composition - {latest_year}",
            hole=0.3,
        )

        fig_pie.update_traces(textposition="inside", textinfo="percent+label")
        st.plotly_chart(fig_pie, use_container_width=True)

    # Change analysis
    st.subheader("Demand Changes by Category")

    change_data = []
    for category in DEMAND_CATEGORIES:
        if category in st.session_state.demand_data:
            row = {"Category": category}

            for i in range(1, len(display_years)):
                year = display_years[i]
                prev_year = display_years[i - 1]

                if (
                    year in st.session_state.demand_data[category]
                    and prev_year in st.session_state.demand_data[category]
                ):
                    change = (
                        st.session_state.demand_data[category][year]
                        - st.session_state.demand_data[category][prev_year]
                    )
                    row[f"{year} Change"] = change

            change_data.append(row)

    if change_data:
        df_changes = pd.DataFrame(change_data)

        # Create grouped bar chart
        fig_changes = go.Figure()

        change_columns = [col for col in df_changes.columns if "Change" in col]
        colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"]

        for i, col in enumerate(change_columns):
            fig_changes.add_trace(
                go.Bar(
                    name=col,
                    x=df_changes["Category"],
                    y=df_changes[col],
                    marker_color=colors[i % len(colors)],
                )
            )

        fig_changes.update_layout(
            title="Demand Changes by Category",
            xaxis_title="Category",
            yaxis_title="Change (Million Metric Tons)",
            barmode="group",
            height=400,
        )

        fig_changes.add_hline(y=0, line_dash="dash", line_color="gray")

        st.plotly_chart(fig_changes, use_container_width=True)

with tabs[3]:  # AI Research tab
    create_ai_research_tab(
        commodity="wheat",
        data_type="world_demand",
        current_data=st.session_state.demand_data,
        db_helper=get_database(),
        update_method_name="update_world_demand_value",
    )

with tabs[4]:
    st.header("Category Analysis")

    # Get display years from configuration
    display_years = st.session_state.demand_current_config.get(
        "display_years", ["2022/2023", "2023/2024", "2024/2025", "2025/2026"]
    )
    latest_year = display_years[-1]

    # Growth rate analysis
    st.subheader("Growth Rate Analysis by Category")

    growth_data = []
    for category in DEMAND_CATEGORIES:
        if category in st.session_state.demand_data:
            # Calculate average growth rate
            growth_rates = []
            for i in range(1, len(display_years)):
                year = display_years[i]
                prev_year = display_years[i - 1]

                if (
                    year in st.session_state.demand_data[category]
                    and prev_year in st.session_state.demand_data[category]
                ):
                    prev_value = st.session_state.demand_data[category][prev_year]
                    curr_value = st.session_state.demand_data[category][year]
                    if prev_value > 0:
                        growth_rate = ((curr_value - prev_value) / prev_value) * 100
                        growth_rates.append(growth_rate)

            if growth_rates:
                avg_growth = sum(growth_rates) / len(growth_rates)
                latest_value = st.session_state.demand_data[category].get(
                    latest_year, 0
                )

                growth_data.append(
                    {
                        "Category": category,
                        "Latest Demand": latest_value,
                        "Avg Growth Rate": avg_growth,
                        "Trend": (
                            "📈" if avg_growth > 0 else "📉" if avg_growth < 0 else "➡️"
                        ),
                    }
                )

    if growth_data:
        df_growth = pd.DataFrame(growth_data)

        # Create bubble chart
        fig_bubble = go.Figure()

        for _, row in df_growth.iterrows():
            color = (
                "green"
                if row["Avg Growth Rate"] > 0
                else "red" if row["Avg Growth Rate"] < 0 else "gray"
            )

            fig_bubble.add_trace(
                go.Scatter(
                    x=[row["Category"]],
                    y=[row["Avg Growth Rate"]],
                    mode="markers+text",
                    name=row["Category"],
                    marker=dict(
                        size=row["Latest Demand"] / 5,  # Scale bubble size
                        color=color,
                        opacity=0.6,
                    ),
                    text=[f"{row['Latest Demand']:.1f} Mt"],
                    textposition="top center",
                    showlegend=False,
                )
            )

        fig_bubble.update_layout(
            title="Demand Growth Analysis (Bubble size = Current Demand)",
            xaxis_title="Category",
            yaxis_title="Average Growth Rate (%)",
            height=500,
        )

        fig_bubble.add_hline(y=0, line_dash="dash", line_color="gray")

        st.plotly_chart(fig_bubble, use_container_width=True)

        # Display growth table
        st.markdown("### Growth Summary")
        df_growth_display = df_growth.copy()
        df_growth_display["Latest Demand"] = df_growth_display["Latest Demand"].apply(
            lambda x: f"{x:.1f} Mt"
        )
        df_growth_display["Avg Growth Rate"] = df_growth_display[
            "Avg Growth Rate"
        ].apply(lambda x: f"{x:.2f}%")

        st.dataframe(df_growth_display, use_container_width=True, hide_index=True)

    # Category insights
    st.subheader("Category Insights")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🍞 Food Demand")
        if "Food" in st.session_state.demand_data:
            food_latest = st.session_state.demand_data["Food"].get(latest_year, 0)
            food_pct = (
                food_latest
                / st.session_state.demand_data.get("Total Consumption", {}).get(
                    latest_year, 1
                )
            ) * 100

            st.metric("Current Demand", f"{food_latest:.1f} Mt")
            st.metric("% of Total", f"{food_pct:.1f}%")
            st.info(
                "Food remains the largest demand category, driven by population growth and dietary changes."
            )

    with col2:
        st.markdown("### 🐄 Feed Demand")
        if "Feed" in st.session_state.demand_data:
            feed_latest = st.session_state.demand_data["Feed"].get(latest_year, 0)
            feed_pct = (
                feed_latest
                / st.session_state.demand_data.get("Total Consumption", {}).get(
                    latest_year, 1
                )
            ) * 100

            st.metric("Current Demand", f"{feed_latest:.1f} Mt")
            st.metric("% of Total", f"{feed_pct:.1f}%")
            st.info(
                "Feed demand fluctuates based on livestock numbers and alternative feed availability."
            )

with tabs[5]:
    st.header("Demand Data Management")

    # Export options
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Export Current Data")

        # Prepare export data
        export_data = {
            "wheat_world_demand_data": st.session_state.demand_data,
            "metadata": st.session_state.demand_metadata,
            "current_config": st.session_state.demand_current_config,
            "export_timestamp": datetime.now().isoformat(),
            "data_source": (
                "database" if st.session_state.demand_data_loaded else "local"
            ),
            "user": st.session_state.get("username", "unknown"),
        }

        # JSON export
        st.download_button(
            label="📥 Download Demand Data as JSON",
            data=json.dumps(export_data, indent=2),
            file_name=f"wheat_world_demand_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
        )

        # CSV export
        df_export = pd.DataFrame(st.session_state.demand_data).T
        csv_data = df_export.to_csv()
        st.download_button(
            label="📥 Download Demand Data as CSV",
            data=csv_data,
            file_name=f"wheat_world_demand_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
        )

    with col2:
        st.subheader("Import Data")

        uploaded_file = st.file_uploader("Upload JSON demand data file", type=["json"])

        if uploaded_file is not None:
            try:
                uploaded_data = json.load(uploaded_file)

                if st.button("Import Demand Data"):
                    if "wheat_world_demand_data" in uploaded_data:
                        st.session_state.demand_data = uploaded_data[
                            "wheat_world_demand_data"
                        ]

                    if "metadata" in uploaded_data:
                        st.session_state.demand_metadata = uploaded_data["metadata"]

                    if "current_config" in uploaded_data:
                        st.session_state.demand_current_config = uploaded_data[
                            "current_config"
                        ]

                    st.success("Demand data imported successfully!")
                    st.rerun()

            except json.JSONDecodeError:
                st.error("Invalid JSON file format")

# Footer
st.markdown("---")
status_text = (
    "🗄️ Database Connected"
    if st.session_state.demand_data_loaded
    else "💾 Local Data Mode"
)
user_info = f"👤 {st.session_state.get('name', 'User')}"
st.markdown(
    f"""
    <div style='text-align: center; color: #666; font-size: 0.8em;'>
    🌍 Wheat World Demand Dashboard | {status_text} | {user_info} | PPF Europe Analysis Platform
    </div>
    """,
    unsafe_allow_html=True,
)
