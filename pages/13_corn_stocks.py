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

from corn_helpers.database_helper import CornProductionDB
from corn_helpers.common_functions import (
    format_change,
    create_status_indicators,
    create_change_visualization,
    style_change_column,
)


def style_percentage_column(val):
    """Style function for percentage columns"""
    if pd.isna(val) or val == "-" or val == "":
        return ""
    try:
        # Extract numeric value
        if isinstance(val, str) and "%" in val:
            return "color: #1f77b4; font-weight: normal"
        return ""
    except:
        return ""


# Page configuration
st.set_page_config(
    page_title="Corn Ending Stocks Dashboard",
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

# Define allowed countries (based on create_corn_database.py)
ALLOWED_COUNTRIES = [
    "WORLD",
    "China",
    "European Union",
    "India",
    "Russia",
    "United States",
    "Australia",
    "Canada",
]

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

    # Quick Navigation - Corn
    st.markdown("### 🌽 Corn - Quick Navigation")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🌽 Production", use_container_width=True):
            st.switch_page("pages/10_corn_production.py")
        if st.button("📥 Imports", use_container_width=True):
            st.switch_page("pages/12_corn_imports.py")
        if st.button("📊 S/U Ratio", use_container_width=True):
            st.switch_page("pages/14_corn_stock_to_use_ratio.py")
        st.info("🌍 World Demand - Coming Soon")
    with col2:
        if st.button("📦 Exports", use_container_width=True):
            st.switch_page("pages/11_corn_exports.py")
        st.info("🌽 Acreage - Coming Soon")
        st.info("🌱 Yield - Coming Soon")

    st.markdown("---")

    # AI Tools section
    st.markdown("### 🤖 AI & MCP Tools")
    if st.button("💬 Launch AI Chat", use_container_width=True):
        st.switch_page("pages/9_mcp_app.py")

    st.markdown("---")
    st.markdown("### 🏢 Corn Stocks Dashboard")

    # Add current date in sidebar
    st.markdown("---")
    st.info(f"📅 **Current Date:** {datetime.now().strftime('%d %b %Y')}")


# Initialize database
@st.cache_resource
def get_database():
    """Initialize and return database instance"""
    if not os.path.exists("corn_production.db"):
        st.error(
            "❌ Database not found. Please run 'python create_corn_database.py' first to create the database."
        )
        return None
    return CornProductionDB()


# Load stocks data from database with filtering
@st.cache_data
def load_stocks_data():
    """Load ending stocks data from database"""
    db = get_database()
    if not db:
        return None, None, None

    try:
        # Get all stocks data
        all_stocks_data = db.get_all_stocks_data()

        # Filter to keep only allowed countries
        stocks_data = {
            country: data
            for country, data in all_stocks_data.items()
            if country in ALLOWED_COUNTRIES
        }

        # Get metadata
        metadata = db.get_metadata()

        # Get current year configuration
        current_config = {
            "display_years": metadata.get(
                "stocks_display_years", "2022/2023,2023/2024,2024/2025,2025/2026"
            ).split(","),
            "year_status": json.loads(
                metadata.get(
                    "stocks_year_status",
                    '{"2022/2023": "actual", "2023/2024": "actual", "2024/2025": "estimate", "2025/2026": "projection"}',
                )
            ),
        }

        return stocks_data, metadata, current_config
    except Exception as e:
        st.error(f"❌ Error loading stocks data from database: {e}")
        return None, None, None


# Function to check if year can be initialized
def can_initialize_year():
    """Check if year initialization is allowed based on current year"""
    import datetime

    current_date = datetime.datetime.now()
    current_year = current_date.year
    current_month = current_date.month

    # Get metadata to check last initialization
    db = get_database()
    if not db:
        return False, "Database not available"

    metadata = db.get_metadata()
    last_init = metadata.get("stocks_last_year_initialization")

    # Check if already initialized this year
    if last_init:
        try:
            last_init_date = datetime.datetime.fromisoformat(last_init)
            if last_init_date.year == current_year:
                return (
                    False,
                    f"Year already initialized on {last_init_date.strftime('%d %b %Y')}",
                )
        except:
            pass

    # Get current configuration
    display_years = metadata.get("stocks_display_years", "").split(",")
    if not display_years:
        return False, "No year configuration found"

    # Get the projection year (last year in display)
    projection_year = display_years[-1] if display_years else ""
    if "/" not in projection_year:
        return False, "Invalid year format"

    # Extract the second part of the projection year
    _, proj_end_year = projection_year.split("/")
    proj_end_year_full = "20" + proj_end_year

    # Allow initialization if we're in the same year as the projection end year
    # and it's after June (mid-year)
    if current_year == int(proj_end_year_full) and current_month >= 6:
        return True, "Ready to initialize new year"

    return False, f"Not yet time to initialize (current projection: {projection_year})"


# Function to initialize new year
def initialize_new_year():
    """Initialize a new year by shifting the year window"""
    db = get_database()
    if not db:
        return False, "Database not available"

    try:
        conn = db.get_connection()
        cursor = conn.cursor()

        # Get current configuration from metadata
        metadata = db.get_metadata()
        current_display_years = metadata.get(
            "stocks_display_years", "2022/2023,2023/2024,2024/2025,2025/2026"
        ).split(",")

        # Check what years actually exist in the database
        cursor.execute("SELECT DISTINCT year FROM corn_stocks ORDER BY year")
        all_years = [row[0] for row in cursor.fetchall()]

        print(f"Current display years: {current_display_years}")
        print(f"All years in database: {all_years}")

        # Calculate new years
        # Extract numeric parts to increment
        last_year = current_display_years[-1]
        start_yr, end_yr = last_year.split("/")
        new_year = f"20{int(end_yr):02d}/20{int(end_yr)+1:02d}"

        # Shift display years forward
        new_display_years = current_display_years[1:] + [new_year]

        # Define new status mapping
        new_year_status = {
            new_display_years[0]: "actual",
            new_display_years[1]: "actual",
            new_display_years[2]: "estimate",
            new_display_years[3]: "projection",
        }

        # Check if new year data needs to be created
        if new_year not in all_years:
            print(f"Creating {new_year} data...")

            # Get the previous year data to copy
            prev_year = new_display_years[2]  # Current estimate year

            # Insert data for new year by copying from previous year
            cursor.execute(
                """
                INSERT INTO corn_stocks (country, year, stock_value, percentage_world, change_value, stock_to_use_ratio, status)
                SELECT country, ?, stock_value, percentage_world, 0, stock_to_use_ratio, 'projection'
                FROM corn_stocks
                WHERE year = ? AND country IN ({})
            """.format(
                    ",".join(["?"] * len(ALLOWED_COUNTRIES))
                ),
                [new_year, prev_year] + ALLOWED_COUNTRIES,
            )

        # Update statuses for all years
        for year, status in new_year_status.items():
            cursor.execute(
                """
                UPDATE corn_stocks 
                SET status = ?, updated_at = ?
                WHERE year = ?
            """,
                (status, datetime.now().isoformat(), year),
            )
            print(f"Updated {year} status to {status}")

        # Update metadata with new configuration
        cursor.execute(
            """
            INSERT OR REPLACE INTO metadata (key, value, updated_at)
            VALUES (?, ?, ?)
        """,
            (
                "stocks_display_years",
                ",".join(new_display_years),
                datetime.now().isoformat(),
            ),
        )

        cursor.execute(
            """
            INSERT OR REPLACE INTO metadata (key, value, updated_at)
            VALUES (?, ?, ?)
        """,
            (
                "stocks_year_status",
                json.dumps(new_year_status),
                datetime.now().isoformat(),
            ),
        )

        cursor.execute(
            """
            INSERT OR REPLACE INTO metadata (key, value, updated_at)
            VALUES (?, ?, ?)
        """,
            (
                "stocks_last_year_initialization",
                datetime.now().isoformat(),
                datetime.now().isoformat(),
            ),
        )

        conn.commit()
        conn.close()

        print(f"Successfully updated to display years: {new_display_years}")

        # Clear all caches to force reload
        st.cache_data.clear()
        st.cache_resource.clear()

        return True, f"Successfully initialized year {new_year}"

    except Exception as e:
        if conn:
            conn.rollback()
            conn.close()
        st.error(f"❌ Error initializing new year: {e}")
        import traceback

        traceback.print_exc()
        return False, str(e)


# Initialize session state
def initialize_session_state():
    """Initialize session state with database data"""
    if "corn_stocks_data_loaded" not in st.session_state:
        stocks_data, metadata, current_config = load_stocks_data()

        if stocks_data and metadata:
            st.session_state.corn_stocks_data = stocks_data
            st.session_state.corn_stocks_metadata = metadata
            st.session_state.corn_stocks_current_config = current_config
            st.session_state.corn_stocks_data_loaded = True
        else:
            # Fallback to empty data
            st.session_state.corn_stocks_data = {}
            st.session_state.corn_stocks_metadata = {}
            st.session_state.corn_stocks_current_config = {
                "display_years": ["2022/2023", "2023/2024", "2024/2025", "2025/2026"],
                "year_status": {
                    "2022/2023": "actual",
                    "2023/2024": "actual",
                    "2024/2025": "estimate",
                    "2025/2026": "projection",
                },
            }
            st.session_state.corn_stocks_data_loaded = False


# Initialize session state
initialize_session_state()

# Title and header
st.title("🏢 Corn Ending Stocks Dashboard")
st.markdown("### Global Corn Stocks Management and Analysis")

# Database status indicator
if st.session_state.corn_stocks_data_loaded:
    st.sidebar.success("🗄️ Connected to Database")
else:
    st.sidebar.warning("⚠️ Using Local Data (No Database)")

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
    st.header("Global Corn Ending Stocks")

    # Year initialization section
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.info("📅 Current Year Configuration")
    with col2:
        can_init, message = can_initialize_year()
        if st.button(
            "🔄 Initialize New Year",
            type="primary" if can_init else "secondary",
            help=message,
            disabled=not can_init,
        ):
            success, init_message = initialize_new_year()
            if success:
                st.success(f"✅ {init_message}")
                st.rerun()
            else:
                st.error(f"❌ {init_message}")
    with col3:
        if st.button("🔄 Refresh Data"):
            st.cache_data.clear()
            st.rerun()

    # Display dynamic status indicators based on current configuration
    if "corn_stocks_current_config" in st.session_state:
        st.markdown("### Status Information")
        status_cols = st.columns(4)

        display_years = st.session_state.corn_stocks_current_config["display_years"]
        year_status = st.session_state.corn_stocks_current_config["year_status"]

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
    **Key Insights:**
    - Ending stocks represent the total quantity of corn held in storage at the end of each marketing year
    - China holds over 60% of global corn stocks
    - Stock-to-use ratio indicates supply security (higher = more buffer)
    """
    )

    # Create enhanced table
    st.markdown("### Ending Stocks Data (Million Metric Tons)")

    # Get display years from configuration
    display_years = st.session_state.corn_stocks_current_config.get(
        "display_years", ["2022/2023", "2023/2024", "2024/2025", "2025/2026"]
    )

    # Create the data table with proper formatting and change calculations
    table_data = []

    # First, get WORLD total for the first year to calculate percentages
    world_total_first_year = None
    if (
        "WORLD" in st.session_state.corn_stocks_data
        and display_years[0] in st.session_state.corn_stocks_data["WORLD"]
    ):
        world_total_first_year = st.session_state.corn_stocks_data["WORLD"][
            display_years[0]
        ]

    for country, data in st.session_state.corn_stocks_data.items():
        if country not in ALLOWED_COUNTRIES:
            continue

        row = {"Country": country}

        # Add data for display years only
        for i, year in enumerate(display_years):
            if year in data:
                row[year] = f"{data[year]:.1f}"

                if i == 0:
                    # For first year, show % World instead of Change
                    if (
                        country != "WORLD"
                        and world_total_first_year
                        and world_total_first_year > 0
                    ):
                        percentage = (data[year] / world_total_first_year) * 100
                        row["% World"] = f"{percentage:.1f}%"
                    else:
                        row["% World"] = "-"
                else:
                    # For other years, calculate change from previous year
                    prev_year = display_years[i - 1]
                    if prev_year in data:
                        change = data[year] - data[prev_year]
                        row[f"Change{' ' * i}"] = format_change(change)
                    else:
                        row[f"Change{' ' * i}"] = "-"

        table_data.append(row)

    df_display = pd.DataFrame(table_data)

    # Apply styling to the dataframe
    change_columns = [
        col for col in df_display.columns if col.strip().startswith("Change")
    ]

    # Apply different styling to % World and Change columns
    styled_df = df_display.style

    # Style change columns
    for col in change_columns:
        styled_df = styled_df.map(style_change_column, subset=[col])

    # Style % World column if it exists
    if "% World" in df_display.columns:
        styled_df = styled_df.map(style_percentage_column, subset=["% World"])

    # Apply general styling
    styled_df = styled_df.set_properties(**{"text-align": "center"}).set_properties(
        **{"text-align": "left"}, subset=["Country"]
    )

    st.dataframe(styled_df, use_container_width=True, hide_index=True)

    # Summary statistics
    st.markdown("### Summary Statistics")
    col1, col2, col3, col4 = st.columns(4)

    # Get the latest projection year
    latest_year = display_years[-1]
    prev_year = display_years[-2] if len(display_years) > 1 else None

    with col1:
        if (
            "WORLD" in st.session_state.corn_stocks_data
            and latest_year in st.session_state.corn_stocks_data["WORLD"]
        ):
            world_latest = st.session_state.corn_stocks_data["WORLD"][latest_year]
            st.metric(f"Global Stocks {latest_year}", f"{world_latest:.1f} Mt")

    with col2:
        if (
            "WORLD" in st.session_state.corn_stocks_data
            and latest_year in st.session_state.corn_stocks_data["WORLD"]
            and prev_year in st.session_state.corn_stocks_data["WORLD"]
        ):
            world_change = (
                st.session_state.corn_stocks_data["WORLD"][latest_year]
                - st.session_state.corn_stocks_data["WORLD"][prev_year]
            )
            st.metric("Change from Previous Year", f"{world_change:+.1f} Mt")

    with col3:
        # China's share of global stocks
        if (
            "China" in st.session_state.corn_stocks_data
            and latest_year in st.session_state.corn_stocks_data["China"]
            and "WORLD" in st.session_state.corn_stocks_data
            and latest_year in st.session_state.corn_stocks_data["WORLD"]
        ):
            china_stocks = st.session_state.corn_stocks_data["China"][latest_year]
            world_stocks = st.session_state.corn_stocks_data["WORLD"][latest_year]
            china_share = (china_stocks / world_stocks * 100) if world_stocks > 0 else 0
            st.metric("China's Share of Stocks", f"{china_share:.1f}%")

    with col4:
        # Find country with highest stocks (excluding WORLD)
        countries_only = {
            k: v
            for k, v in st.session_state.corn_stocks_data.items()
            if k != "WORLD" and k in ALLOWED_COUNTRIES
        }
        if countries_only and latest_year in next(iter(countries_only.values())):
            top_holder = max(
                countries_only.items(), key=lambda x: x[1].get(latest_year, 0)
            )
            st.metric(f"Top Stock Holder", top_holder[0])

with tab2:
    # Get the projection year (last year in display_years)
    display_years = st.session_state.corn_stocks_current_config.get(
        "display_years", ["2022/2023", "2023/2024", "2024/2025", "2025/2026"]
    )
    projection_year = display_years[-1]
    estimate_year = display_years[-2]

    st.header(f"Edit {projection_year} Stock Projections")
    st.markdown(
        f"**Note:** Historical data ({', '.join(display_years[:-1])}) is static and cannot be modified."
    )

    # Create form for editing projections
    with st.form("corn_stocks_projection_form"):
        st.markdown(f"### Update Stock Projections for {projection_year}")

        # Create input fields for each country
        updated_values = {}

        # Filter countries to allowed list only (excluding WORLD for editing)
        filtered_countries = [
            c
            for c in st.session_state.corn_stocks_data.keys()
            if c in ALLOWED_COUNTRIES and c != "WORLD"
        ]

        for country in filtered_countries:
            if projection_year not in st.session_state.corn_stocks_data[country]:
                continue

            current_value = st.session_state.corn_stocks_data[country][projection_year]

            # Calculate change from estimate year
            estimate_value = st.session_state.corn_stocks_data[country].get(
                estimate_year, 0
            )
            current_change = current_value - estimate_value if estimate_value else 0

            # Show historical trend
            historical_values = []
            for year in display_years[:-1]:
                if year in st.session_state.corn_stocks_data[country]:
                    historical_values.append(
                        st.session_state.corn_stocks_data[country][year]
                    )

            st.subheader(f"{country}")
            col1, col2 = st.columns([2, 1])

            with col1:
                updated_values[country] = st.number_input(
                    f"Stocks (Mt)",
                    value=float(current_value),
                    min_value=0.0,
                    step=0.1,
                    format="%.1f",
                    key=f"corn_stocks_{country}",
                    help=(
                        f"Historical: {' → '.join([f'{v:.1f}' for v in historical_values])}"
                        if historical_values
                        else "No historical data"
                    ),
                )

            with col2:
                # Display calculated change
                if estimate_value:
                    calc_change = updated_values[country] - estimate_value
                    if calc_change > 0:
                        st.success(f"Change: +{calc_change:.1f}")
                    elif calc_change < 0:
                        st.error(f"Change: {calc_change:.1f}")
                    else:
                        st.info("Change: 0.0")

        # Submit button
        if st.form_submit_button("Update Stock Projections", type="primary"):
            # Update the data
            db = get_database()

            # Update individual countries
            for country, value in updated_values.items():
                st.session_state.corn_stocks_data[country][projection_year] = value

                # Calculate change from estimate year
                if estimate_year in st.session_state.corn_stocks_data[country]:
                    change = (
                        value
                        - st.session_state.corn_stocks_data[country][estimate_year]
                    )
                else:
                    change = 0

                # Save to database
                if db:
                    db.update_stocks_value(
                        country, projection_year, value, change, None
                    )

            # Calculate and update WORLD total
            world_total = sum(updated_values.values())
            if estimate_year in st.session_state.corn_stocks_data.get("WORLD", {}):
                world_change = (
                    world_total
                    - st.session_state.corn_stocks_data["WORLD"][estimate_year]
                )
            else:
                world_change = 0

            if "WORLD" not in st.session_state.corn_stocks_data:
                st.session_state.corn_stocks_data["WORLD"] = {}

            st.session_state.corn_stocks_data["WORLD"][projection_year] = world_total

            if db:
                db.update_stocks_value(
                    "WORLD", projection_year, world_total, world_change, None
                )

            st.success("✅ Stock projections updated successfully!")
            if db:
                st.info("💾 Changes saved to database")
            st.rerun()

with tab3:
    st.header("Stock Visualizations")

    # Get display years from configuration
    display_years = st.session_state.corn_stocks_current_config.get(
        "display_years", ["2022/2023", "2023/2024", "2024/2025", "2025/2026"]
    )

    # Time series plot
    st.subheader("Ending Stocks Trends Over Time")

    # Select countries to display - filtered to allowed countries only
    available_countries = [
        c for c in st.session_state.corn_stocks_data.keys() if c in ALLOWED_COUNTRIES
    ]

    countries_to_plot = st.multiselect(
        "Select countries/regions to display:",
        options=available_countries,
        default=[
            c
            for c in [
                "WORLD",
                "China",
                "United States",
                "European Union",
                "India",
                "Russia",
            ]
            if c in available_countries
        ],
    )

    if countries_to_plot:
        # Create time series plot
        fig = go.Figure()

        for country in countries_to_plot:
            values = []
            years_with_data = []

            for year in display_years:
                if year in st.session_state.corn_stocks_data[country]:
                    values.append(st.session_state.corn_stocks_data[country][year])
                    years_with_data.append(year)

            if values:
                fig.add_trace(
                    go.Scatter(
                        x=years_with_data,
                        y=values,
                        mode="lines+markers",
                        name=country,
                        hovertemplate=f"<b>{country}</b><br>"
                        + "Year: %{x}<br>"
                        + "Stocks: %{y:.1f} Mt<extra></extra>",
                    )
                )

        fig.update_layout(
            title="Corn Ending Stocks Trends",
            xaxis_title="Year",
            yaxis_title="Ending Stocks (Million Metric Tons)",
            hovermode="x unified",
            height=500,
        )

        # Add vertical line to separate historical from projection
        if len(display_years) > 1:
            # Find the index where projection starts
            for i, year in enumerate(display_years):
                if (
                    st.session_state.corn_stocks_current_config["year_status"].get(year)
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

    # Stock distribution pie chart
    st.subheader(f"Global Stock Distribution ({display_years[-1]})")

    # Prepare data for pie chart (excluding WORLD)
    countries_only = {
        k: v
        for k, v in st.session_state.corn_stocks_data.items()
        if k != "WORLD" and k in ALLOWED_COUNTRIES
    }

    latest_year = display_years[-1]
    pie_data = []
    pie_labels = []

    for country, data in countries_only.items():
        if latest_year in data:
            pie_data.append(data[latest_year])
            pie_labels.append(country)

    if pie_data:
        fig_pie = go.Figure(
            data=[
                go.Pie(
                    labels=pie_labels,
                    values=pie_data,
                    hovertemplate="<b>%{label}</b><br>"
                    + "Stocks: %{value:.1f} Mt<br>"
                    + "Share: %{percent}<extra></extra>",
                )
            ]
        )

        fig_pie.update_layout(
            title=f"Distribution of Global Corn Stocks - {latest_year} Projection",
            height=500,
        )

        st.plotly_chart(fig_pie, use_container_width=True)

    # Change analysis - filtered to allowed countries
    filtered_data = {
        k: v
        for k, v in st.session_state.corn_stocks_data.items()
        if k in ALLOWED_COUNTRIES
    }

    # Calculate changes for visualization
    for country, data in filtered_data.items():
        for i, year in enumerate(display_years):
            if i > 0 and year in data and display_years[i - 1] in data:
                data[f"{year}_change"] = data[year] - data[display_years[i - 1]]

    create_change_visualization(filtered_data, "Stocks", exclude=["WORLD"])

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

    # Get display years from configuration
    display_years = st.session_state.corn_stocks_current_config.get(
        "display_years", ["2022/2023", "2023/2024", "2024/2025", "2025/2026"]
    )
    latest_year = display_years[-1]

    # S/U Ratio comparison
    st.subheader(f"Stock-to-Use Ratios by Country ({latest_year})")

    # For now, show a placeholder message since S/U ratios may need separate calculation
    st.info(
        "Stock-to-Use ratios require additional data (domestic consumption, exports) for calculation. "
        "Please see the dedicated S/U Ratio page for detailed analysis."
    )

    if st.button("Go to S/U Ratio Analysis", type="primary"):
        st.switch_page("pages/14_corn_stock_to_use_ratio.py")

with tab5:
    st.header("Stock Data Management")

    # Export options
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Export Current Data")

        # Filter data for export
        export_stocks_data = {
            country: data
            for country, data in st.session_state.corn_stocks_data.items()
            if country in ALLOWED_COUNTRIES
        }

        # Prepare export data
        export_data = {
            "corn_stocks_data": export_stocks_data,
            "metadata": st.session_state.corn_stocks_metadata,
            "current_config": st.session_state.corn_stocks_current_config,
            "export_timestamp": datetime.now().isoformat(),
            "data_source": (
                "database" if st.session_state.corn_stocks_data_loaded else "local"
            ),
            "user": st.session_state.get("username", "unknown"),
        }

        # JSON export
        st.download_button(
            label="📥 Download Stocks Data as JSON",
            data=json.dumps(export_data, indent=2),
            file_name=f"corn_stocks_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
        )

        # CSV export
        df_export = pd.DataFrame(export_stocks_data).T
        csv_data = df_export.to_csv()
        st.download_button(
            label="📥 Download Stocks Data as CSV",
            data=csv_data,
            file_name=f"corn_stocks_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
        )

    with col2:
        st.subheader("Import Data")

        uploaded_file = st.file_uploader("Upload JSON stocks data file", type=["json"])

        if uploaded_file is not None:
            try:
                uploaded_data = json.load(uploaded_file)

                if st.button("Import Stocks Data"):
                    if "corn_stocks_data" in uploaded_data:
                        # Filter imported data to allowed countries
                        filtered_data = {
                            country: data
                            for country, data in uploaded_data[
                                "corn_stocks_data"
                            ].items()
                            if country in ALLOWED_COUNTRIES
                        }
                        st.session_state.corn_stocks_data = filtered_data

                    if "metadata" in uploaded_data:
                        st.session_state.corn_stocks_metadata = uploaded_data[
                            "metadata"
                        ]

                    if "current_config" in uploaded_data:
                        st.session_state.corn_stocks_current_config = uploaded_data[
                            "current_config"
                        ]

                    st.success("Stocks data imported successfully!")
                    st.rerun()

            except json.JSONDecodeError:
                st.error("Invalid JSON file format")

# Footer
st.markdown("---")
status_text = (
    "🗄️ Database Connected"
    if st.session_state.corn_stocks_data_loaded
    else "💾 Local Data Mode"
)
user_info = f"👤 {st.session_state.get('name', 'User')}"
st.markdown(
    f"""
    <div style='text-align: center; color: #666; font-size: 0.8em;'>
    🏢 Corn Ending Stocks Dashboard | {status_text} | {user_info} | PPF Europe Analysis Platform
    </div>
    """,
    unsafe_allow_html=True,
)
