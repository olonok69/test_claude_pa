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

# Import AI Research components
from utils.enhanced_ai_research_tab import create_ai_research_tab


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
    page_title="Wheat Acreage Dashboard",
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

# Define allowed countries (exactly as requested)
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

    # Quick Navigation
    st.markdown("### 🌾 Quick Navigation")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🌾 Production", use_container_width=True):
            st.switch_page("pages/1_wheat_production.py")
        if st.button("📥 Imports", use_container_width=True):
            st.switch_page("pages/3_wheat_imports.py")
        if st.button("🌱 Yield", use_container_width=True):
            st.switch_page("pages/7_wheat_yield.py")
        if st.button("🌍 World Demand", use_container_width=True):
            st.switch_page("pages/8_wheat_world_demand.py")
    with col2:
        if st.button("📦 Exports", use_container_width=True):
            st.switch_page("pages/2_wheat_exports.py")
        if st.button("🏢 Stocks", use_container_width=True):
            st.switch_page("pages/4_wheat_stocks.py")
        if st.button("📊 S/U Ratio", use_container_width=True):
            st.switch_page("pages/5_stock_to_use_ratio.py")

    st.markdown("---")

    # AI Tools section
    st.markdown("### 🤖 AI & MCP Tools")
    if st.button("💬 Launch AI Chat", use_container_width=True):
        st.switch_page("pages/9_mcp_app.py")

    st.markdown("---")
    st.markdown("### 🌾 Acreage Dashboard")

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


# Load acreage data from database with filtering
@st.cache_data
def load_acreage_data():
    """Load acreage data from database"""
    db = get_database()
    if not db:
        return None, None, None

    try:
        # Get all acreage data
        all_acreage_data = db.get_all_acreage_data()

        # Filter to keep only allowed countries
        acreage_data = {
            country: data
            for country, data in all_acreage_data.items()
            if country in ALLOWED_COUNTRIES
        }

        # Get metadata
        metadata = db.get_metadata()

        # Get current year configuration - NOW WITH 2025/2026
        current_config = {
            "display_years": metadata.get(
                "acreage_display_years", "2022/2023,2023/2024,2024/2025,2025/2026"
            ).split(","),
            "year_status": json.loads(
                metadata.get(
                    "acreage_year_status",
                    '{"2022/2023": "actual", "2023/2024": "actual", "2024/2025": "estimate", "2025/2026": "projection"}',
                )
            ),
        }

        return acreage_data, metadata, current_config
    except Exception as e:
        st.error(f"❌ Error loading acreage data from database: {e}")
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
    last_init = metadata.get("acreage_last_year_initialization")

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
    display_years = metadata.get("acreage_display_years", "").split(",")
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
            "acreage_display_years", "2022/2023,2023/2024,2024/2025,2025/2026"
        ).split(",")

        # Check what years actually exist in the database
        cursor.execute("SELECT DISTINCT year FROM wheat_acreage ORDER BY year")
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
                INSERT INTO wheat_acreage (country, year, acreage_value, percentage_world, change_value, yield_per_hectare, status)
                SELECT country, ?, acreage_value, percentage_world, 0, yield_per_hectare, 'projection'
                FROM wheat_acreage
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
                UPDATE wheat_acreage 
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
                "acreage_display_years",
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
                "acreage_year_status",
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
                "acreage_last_year_initialization",
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
    if "acreage_data_loaded" not in st.session_state:
        acreage_data, metadata, current_config = load_acreage_data()

        if acreage_data and metadata:
            st.session_state.acreage_data = acreage_data
            st.session_state.acreage_metadata = metadata
            st.session_state.acreage_current_config = current_config
            st.session_state.acreage_data_loaded = True
        else:
            # Fallback to empty data
            st.session_state.acreage_data = {}
            st.session_state.acreage_metadata = {}
            st.session_state.acreage_current_config = {
                "display_years": ["2022/2023", "2023/2024", "2024/2025", "2025/2026"],
                "year_status": {
                    "2022/2023": "actual",
                    "2023/2024": "actual",
                    "2024/2025": "estimate",
                    "2025/2026": "projection",
                },
            }
            st.session_state.acreage_data_loaded = False


# Initialize session state
initialize_session_state()

# Title and header
st.title("🌾 Wheat Acreage Dashboard")
st.markdown("### Global Wheat Area Harvested Analysis")

# Database status indicator
if st.session_state.acreage_data_loaded:
    st.sidebar.success("🗄️ Connected to Database")
else:
    st.sidebar.warning("⚠️ Using Local Data (No Database)")

# Create tabs with AI Research
tab_names = [
    "📈 Data Overview",
    "✏️ Edit Projections",
    "📊 Visualizations",
    "🤖 AI Research",
    "🌱 Yield Analysis",
    "💾 Data Export",
]
# Create tabs with AI Research
tab_names = ["📈 Data Overview", "✏️ Edit Projections", "📊 Visualizations", "🤖 AI Research", "💾 Data Export"]
tabs = st.tabs(tab_names)

with tabs[0]:
    st.header("Global Wheat Acreage (Area Harvested)")

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
    if "acreage_current_config" in st.session_state:
        st.markdown("### Status Information")
        status_cols = st.columns(4)

        display_years = st.session_state.acreage_current_config["display_years"]
        year_status = st.session_state.acreage_current_config["year_status"]

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
    **Acreage (Area Harvested)** represents the total land area from which wheat is harvested.
    - Measured in Million Hectares (Mha)
    - Key driver of production along with yield
    - Influenced by: crop prices, weather, government policies, competing crops
    """
    )

    # Create enhanced table
    st.markdown("### Acreage Data (Million Hectares)")

    # Get display years from configuration
    display_years = st.session_state.acreage_current_config.get(
        "display_years", ["2022/2023", "2023/2024", "2024/2025", "2025/2026"]
    )

    # Create the data table with proper formatting and change calculations
    table_data = []

    # First, get WORLD total for the first year to calculate percentages
    world_total_first_year = None
    if (
        "WORLD" in st.session_state.acreage_data
        and display_years[0] in st.session_state.acreage_data["WORLD"]
    ):
        world_total_first_year = st.session_state.acreage_data["WORLD"][
            display_years[0]
        ]

    for country, data in st.session_state.acreage_data.items():
        if country not in ALLOWED_COUNTRIES:
            continue

        row = {"Country": country}

        # Add data for display years only
        for i, year in enumerate(display_years):
            if year in data:
                row[year] = f"{data[year]:.2f}"

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

        # Add yield for latest year
        latest_year = display_years[-1]
        yield_key = f"{latest_year}_yield"
        if yield_key in data:
            row["Yield (t/ha)"] = f"{data[yield_key]:.2f}"
        else:
            row["Yield (t/ha)"] = "-"

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
            "WORLD" in st.session_state.acreage_data
            and latest_year in st.session_state.acreage_data["WORLD"]
        ):
            world_latest = st.session_state.acreage_data["WORLD"][latest_year]
            st.metric(f"Global Acreage {latest_year}", f"{world_latest:.1f} Mha")

    with col2:
        if (
            "WORLD" in st.session_state.acreage_data
            and latest_year in st.session_state.acreage_data["WORLD"]
            and prev_year in st.session_state.acreage_data["WORLD"]
        ):
            world_change = (
                st.session_state.acreage_data["WORLD"][latest_year]
                - st.session_state.acreage_data["WORLD"][prev_year]
            )
            st.metric("Change from Previous Year", f"{world_change:+.1f} Mha")

    with col3:
        # Average yield
        world_yield_key = f"{latest_year}_yield"
        if (
            "WORLD" in st.session_state.acreage_data
            and world_yield_key in st.session_state.acreage_data["WORLD"]
        ):
            world_yield = st.session_state.acreage_data["WORLD"][world_yield_key]
            st.metric("Global Avg Yield", f"{world_yield:.2f} t/ha")

    with col4:
        # Top country by acreage (excluding WORLD)
        countries_only = {
            k: v
            for k, v in st.session_state.acreage_data.items()
            if k != "WORLD" and k in ALLOWED_COUNTRIES
        }
        if countries_only and latest_year in next(iter(countries_only.values())):
            top_country = max(
                countries_only.items(), key=lambda x: x[1].get(latest_year, 0)
            )
            st.metric(f"Largest Area", f"{top_country[0]}")

with tabs[1]:
    # Get the projection year (last year in display_years)
    display_years = st.session_state.acreage_current_config.get(
        "display_years", ["2022/2023", "2023/2024", "2024/2025", "2025/2026"]
    )
    projection_year = display_years[-1]
    estimate_year = display_years[-2]

    st.header(f"Edit {projection_year} Acreage Projections")
    st.markdown(
        f"**Note:** Historical data ({', '.join(display_years[:-1])}) is static and cannot be modified."
    )

    # Create form for editing projections
    with st.form("acreage_projection_form"):
        st.markdown(f"### Update Acreage Projections for {projection_year}")

        # Create input fields for each country
        updated_values = {}
        updated_yields = {}

        # Filter countries to allowed list only (excluding WORLD for editing)
        filtered_countries = [
            c
            for c in st.session_state.acreage_data.keys()
            if c in ALLOWED_COUNTRIES and c != "WORLD"
        ]

        for country in filtered_countries:
            if projection_year not in st.session_state.acreage_data[country]:
                continue

            current_value = st.session_state.acreage_data[country][projection_year]
            yield_key = f"{projection_year}_yield"
            current_yield = st.session_state.acreage_data[country].get(yield_key, 0)

            # Calculate change from estimate year
            estimate_value = st.session_state.acreage_data[country].get(
                estimate_year, 0
            )
            current_change = current_value - estimate_value if estimate_value else 0

            # Show historical trend
            historical_values = []
            for year in display_years[:-1]:
                if year in st.session_state.acreage_data[country]:
                    historical_values.append(
                        st.session_state.acreage_data[country][year]
                    )

            st.subheader(f"{country}")
            col1, col2, col3 = st.columns([2, 1, 1])

            with col1:
                updated_values[country] = st.number_input(
                    f"Acreage (Mha)",
                    value=float(current_value),
                    min_value=0.0,
                    step=0.1,
                    format="%.2f",
                    key=f"acreage_{country}",
                    help=(
                        f"Historical: {' → '.join([f'{v:.2f}' for v in historical_values])}"
                        if historical_values
                        else "No historical data"
                    ),
                )

            with col2:
                updated_yields[country] = st.number_input(
                    f"Yield (t/ha)",
                    value=float(current_yield),
                    min_value=0.0,
                    max_value=10.0,
                    step=0.01,
                    format="%.2f",
                    key=f"yield_{country}",
                    help="Tonnes per hectare",
                )

            with col3:
                # Display calculated change
                if estimate_value:
                    calc_change = updated_values[country] - estimate_value
                    if calc_change > 0:
                        st.success(f"Change: +{calc_change:.2f}")
                    elif calc_change < 0:
                        st.error(f"Change: {calc_change:.2f}")
                    else:
                        st.info("Change: 0.00")

        # Submit button
        if st.form_submit_button("Update Acreage Projections", type="primary"):
            # Update the data
            db = get_database()

            # Update individual countries
            for country, value in updated_values.items():
                st.session_state.acreage_data[country][projection_year] = value
                st.session_state.acreage_data[country][f"{projection_year}_yield"] = (
                    updated_yields[country]
                )

                # Calculate change from estimate year
                if estimate_year in st.session_state.acreage_data[country]:
                    change = (
                        value - st.session_state.acreage_data[country][estimate_year]
                    )
                else:
                    change = 0

                # Save to database
                if db:
                    db.update_acreage_value(
                        country,
                        projection_year,
                        value,
                        change,
                        updated_yields[country],
                    )

            # Calculate and update WORLD total
            world_total = sum(updated_values.values())
            world_yield = (
                sum(updated_yields.values()) / len(updated_yields)
                if updated_yields
                else 0
            )

            if estimate_year in st.session_state.acreage_data.get("WORLD", {}):
                world_change = (
                    world_total - st.session_state.acreage_data["WORLD"][estimate_year]
                )
            else:
                world_change = 0

            if "WORLD" not in st.session_state.acreage_data:
                st.session_state.acreage_data["WORLD"] = {}

            st.session_state.acreage_data["WORLD"][projection_year] = world_total
            st.session_state.acreage_data["WORLD"][
                f"{projection_year}_yield"
            ] = world_yield

            if db:
                db.update_acreage_value(
                    "WORLD", projection_year, world_total, world_change, world_yield
                )

            st.success("✅ Acreage projections updated successfully!")
            if db:
                st.info("💾 Changes saved to database")
            st.rerun()

with tabs[2]:
    st.header("Acreage Visualizations")

    # Get display years from configuration
    display_years = st.session_state.acreage_current_config.get(
        "display_years", ["2022/2023", "2023/2024", "2024/2025", "2025/2026"]
    )

    # Time series plot
    st.subheader("Acreage Trends Over Time")

    # Select countries to display - filtered to allowed countries only
    available_countries = [
        c for c in st.session_state.acreage_data.keys() if c in ALLOWED_COUNTRIES
    ]

    countries_to_plot = st.multiselect(
        "Select countries/regions to display:",
        options=available_countries,
        default=[
            c
            for c in [
                "WORLD",
                "India",
                "Russia",
                "China",
                "European Union",
                "United States",
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
                if year in st.session_state.acreage_data[country]:
                    values.append(st.session_state.acreage_data[country][year])
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
                        + "Acreage: %{y:.2f} Mha<extra></extra>",
                    )
                )

        fig.update_layout(
            title="Wheat Acreage Trends",
            xaxis_title="Year",
            yaxis_title="Area Harvested (Million Hectares)",
            hovermode="x unified",
            height=500,
        )

        # Add vertical line to separate historical from projection
        if len(display_years) > 1:
            # Find the index where projection starts
            for i, year in enumerate(display_years):
                if (
                    st.session_state.acreage_current_config["year_status"].get(year)
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

    # Top countries by acreage
    st.subheader(f"Top Countries by Wheat Acreage ({display_years[-1]})")

    # Get top countries (excluding WORLD)
    countries_only = {
        k: v
        for k, v in st.session_state.acreage_data.items()
        if k != "WORLD" and k in ALLOWED_COUNTRIES
    }

    latest_year = display_years[-1]
    top_countries = sorted(
        countries_only.items(), key=lambda x: x[1].get(latest_year, 0), reverse=True
    )

    if top_countries:
        fig_bar = go.Figure(
            data=[
                go.Bar(
                    x=[country for country, _ in top_countries],
                    y=[data.get(latest_year, 0) for _, data in top_countries],
                    text=[
                        f"{data.get(latest_year, 0):.1f}" for _, data in top_countries
                    ],
                    textposition="auto",
                    marker_color="darkgreen",
                    hovertemplate="<b>%{x}</b><br>"
                    + "Acreage: %{y:.2f} Mha<br>"
                    + "<extra></extra>",
                )
            ]
        )

        fig_bar.update_layout(
            title=f"Wheat Growing Countries by Area - {latest_year}",
            xaxis_title="Country",
            yaxis_title="Area Harvested (Million Hectares)",
            height=400,
        )

        st.plotly_chart(fig_bar, use_container_width=True)

    # Change analysis - filtered to allowed countries
    filtered_data = {
        k: v for k, v in st.session_state.acreage_data.items() if k in ALLOWED_COUNTRIES
    }

    # Calculate changes for visualization
    for country, data in filtered_data.items():
        for i, year in enumerate(display_years):
            if i > 0 and year in data and display_years[i - 1] in data:
                data[f"{year}_change"] = data[year] - data[display_years[i - 1]]

    create_change_visualization(filtered_data, "Acreage", exclude=["WORLD"])

with tabs[3]:  # AI Research tab
    create_ai_research_tab(
        commodity="wheat",
        data_type="acreage",
        current_data=st.session_state.acreage_data,
        db_helper=get_database(
    
    ),
        update_method_name="update_acreage_value",
    )

with tabs[4]:  # Regional Analysis tab
    st.header("Yield Analysis")

    st.markdown(
        """
    **Yield** (tonnes per hectare) is a key productivity indicator that combines with acreage to determine production.
    Higher yields indicate:
    - Better farming practices
    - Favorable weather conditions
    - Improved seed varieties
    - Better irrigation and inputs
    """
    )

    # Get display years from configuration
    display_years = st.session_state.acreage_current_config.get(
        "display_years", ["2022/2023", "2023/2024", "2024/2025", "2025/2026"]
    )
    latest_year = display_years[-1]

    # Yield comparison chart
    st.subheader(f"Yield Comparison by Country ({latest_year})")

    # Get yield data
    yield_data = []
    for country, data in st.session_state.acreage_data.items():
        if country in ALLOWED_COUNTRIES and country != "WORLD":
            yield_key = f"{latest_year}_yield"
            if yield_key in data and latest_year in data:
                yield_data.append(
                    {
                        "Country": country,
                        "Yield": data[yield_key],
                        "Acreage": data[latest_year],
                    }
                )

    if yield_data:
        df_yield = pd.DataFrame(yield_data)
        df_yield = df_yield.sort_values("Yield", ascending=False)

        # Create yield bar chart
        fig_yield = px.bar(
            df_yield,
            x="Country",
            y="Yield",
            title=f"Wheat Yields by Country - {latest_year}",
            color="Yield",
            color_continuous_scale="Greens",
        )

        fig_yield.update_layout(
            xaxis_title="Country", yaxis_title="Yield (tonnes per hectare)", height=400
        )

        # Add world average line
        world_yield_key = f"{latest_year}_yield"
        world_yield = st.session_state.acreage_data.get("WORLD", {}).get(
            world_yield_key, 3.52
        )
        fig_yield.add_hline(
            y=world_yield,
            line_dash="dash",
            line_color="red",
            annotation_text=f"World Average: {world_yield:.2f} t/ha",
        )

        st.plotly_chart(fig_yield, use_container_width=True)

        # Scatter plot: Acreage vs Yield
        st.subheader("Acreage vs Yield Analysis")

        fig_scatter = px.scatter(
            df_yield,
            x="Acreage",
            y="Yield",
            text="Country",
            size="Acreage",
            title=f"Wheat Acreage vs Yield ({latest_year})",
            labels={"Acreage": "Area Harvested (Mha)", "Yield": "Yield (t/ha)"},
        )

        fig_scatter.update_traces(textposition="top center")
        fig_scatter.update_layout(height=500)

        # Add quadrant lines
        fig_scatter.add_hline(y=world_yield, line_dash="dash", line_color="gray")
        fig_scatter.add_vline(x=15, line_dash="dash", line_color="gray")

        # Add quadrant labels
        fig_scatter.add_annotation(
            x=5, y=5.5, text="High Yield<br>Small Area", showarrow=False
        )
        fig_scatter.add_annotation(
            x=25, y=5.5, text="High Yield<br>Large Area", showarrow=False
        )
        fig_scatter.add_annotation(
            x=5, y=1.5, text="Low Yield<br>Small Area", showarrow=False
        )
        fig_scatter.add_annotation(
            x=25, y=1.5, text="Low Yield<br>Large Area", showarrow=False
        )

        st.plotly_chart(fig_scatter, use_container_width=True)

        # Yield statistics
        col1, col2, col3 = st.columns(3)

        with col1:
            avg_yield = df_yield["Yield"].mean()
            st.metric("Average Yield", f"{avg_yield:.2f} t/ha")

        with col2:
            max_yield_country = df_yield.iloc[0]
            st.metric(
                "Highest Yield",
                f"{max_yield_country['Country']}: {max_yield_country['Yield']:.2f} t/ha",
            )

        with col3:
            min_yield_country = df_yield.iloc[-1]
            st.metric(
                "Lowest Yield",
                f"{min_yield_country['Country']}: {min_yield_country['Yield']:.2f} t/ha",
            )

with tabs[5]:  # Data Export tab
    st.header("Acreage Data Management")

    # Export options
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Export Current Data")

        # Filter data for export
        export_acreage_data = {
            country: data
            for country, data in st.session_state.acreage_data.items()
            if country in ALLOWED_COUNTRIES
        }

        # Prepare export data
        export_data = {
            "wheat_acreage_data": export_acreage_data,
            "metadata": st.session_state.acreage_metadata,
            "current_config": st.session_state.acreage_current_config,
            "export_timestamp": datetime.now().isoformat(),
            "data_source": (
                "database" if st.session_state.acreage_data_loaded else "local"
            ),
            "user": st.session_state.get("username", "unknown"),
        }

        # JSON export
        st.download_button(
            label="📥 Download Acreage Data as JSON",
            data=json.dumps(export_data, indent=2),
            file_name=f"wheat_acreage_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
        )

        # CSV export
        df_export = pd.DataFrame(export_acreage_data).T
        csv_data = df_export.to_csv()
        st.download_button(
            label="📥 Download Acreage Data as CSV",
            data=csv_data,
            file_name=f"wheat_acreage_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
        )

    with col2:
        st.subheader("Import Data")

        uploaded_file = st.file_uploader("Upload JSON acreage data file", type=["json"])

        if uploaded_file is not None:
            try:
                uploaded_data = json.load(uploaded_file)

                if st.button("Import Acreage Data"):
                    if "wheat_acreage_data" in uploaded_data:
                        # Filter imported data to allowed countries
                        filtered_data = {
                            country: data
                            for country, data in uploaded_data[
                                "wheat_acreage_data"
                            ].items()
                            if country in ALLOWED_COUNTRIES
                        }
                        st.session_state.acreage_data = filtered_data

                    if "metadata" in uploaded_data:
                        st.session_state.acreage_metadata = uploaded_data["metadata"]

                    if "current_config" in uploaded_data:
                        st.session_state.acreage_current_config = uploaded_data[
                            "current_config"
                        ]

                    st.success("Acreage data imported successfully!")
                    st.rerun()

            except json.JSONDecodeError:
                st.error("Invalid JSON file format")

# Footer
st.markdown("---")
status_text = (
    "🗄️ Database Connected"
    if st.session_state.acreage_data_loaded
    else "💾 Local Data Mode"
)
user_info = f"👤 {st.session_state.get('name', 'User')}"
st.markdown(
    f"""
    <div style='text-align: center; color: #666; font-size: 0.8em;'>
    🌾 Wheat Acreage Dashboard | {status_text} | {user_info} | PPF Europe Analysis Platform
    </div>
    """,
    unsafe_allow_html=True,
)

with tabs[3]:  # AI Research tab
    create_ai_research_tab(
        commodity="wheat",
        data_type="acreage",
        current_data=st.session_state.acreage_data,
        db_helper=get_database(
    
    ),
        update_method_name="update_acreage_value"
    )
