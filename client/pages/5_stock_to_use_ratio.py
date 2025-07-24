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
    style_change_column,
)

# Import AI Research components
from utils.enhanced_ai_research_tab import create_ai_research_tab

# Page configuration
st.set_page_config(
    page_title="Stock-to-Use Ratio Dashboard",
    page_icon="📊",
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
        if st.button("🌾 Acreage", use_container_width=True):
            st.switch_page("pages/6_wheat_acreage.py")
        if st.button("🌍 World Demand", use_container_width=True):
            st.switch_page("pages/8_wheat_world_demand.py")
    with col2:
        if st.button("📦 Exports", use_container_width=True):
            st.switch_page("pages/2_wheat_exports.py")
        if st.button("🏢 Stocks", use_container_width=True):
            st.switch_page("pages/4_wheat_stocks.py")
        if st.button("🌱 Yield", use_container_width=True):
            st.switch_page("pages/7_wheat_yield.py")

    st.markdown("---")

    # AI Tools section
    st.markdown("### 🤖 AI & MCP Tools")
    if st.button("💬 Launch AI Chat", use_container_width=True):
        st.switch_page("pages/9_mcp_app.py")

    st.markdown("---")
    st.markdown("### 📊 S/U Ratio Dashboard")

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


# Load S/U ratio data from database with filtering
@st.cache_data
def load_su_ratio_data():
    """Load stock-to-use ratio data from database"""
    db = get_database()
    if not db:
        return None, None, None

    try:
        # Get all S/U ratio data
        all_su_data = db.get_all_su_ratio_data()

        # Filter to keep only allowed countries
        su_data = {
            country: data
            for country, data in all_su_data.items()
            if country in ALLOWED_COUNTRIES
        }

        # Get metadata
        metadata = db.get_metadata()

        # Get current year configuration - NOW WITH 2025/2026
        current_config = {
            "display_years": metadata.get(
                "su_ratio_display_years", "2022/2023,2023/2024,2024/2025,2025/2026"
            ).split(","),
            "year_status": json.loads(
                metadata.get(
                    "su_ratio_year_status",
                    '{"2022/2023": "actual", "2023/2024": "actual", "2024/2025": "estimate", "2025/2026": "projection"}',
                )
            ),
        }

        return su_data, metadata, current_config
    except Exception as e:
        st.error(f"❌ Error loading S/U ratio data from database: {e}")
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
    last_init = metadata.get("su_ratio_last_year_initialization")

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
    display_years = metadata.get("su_ratio_display_years", "").split(",")
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
            "su_ratio_display_years", "2022/2023,2023/2024,2024/2025,2025/2026"
        ).split(",")

        # Check what years actually exist in the database
        cursor.execute("SELECT DISTINCT year FROM wheat_su_ratio ORDER BY year")
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
                INSERT INTO wheat_su_ratio (country, year, su_ratio, change_value, category, status)
                SELECT country, ?, su_ratio, 0, category, 'projection'
                FROM wheat_su_ratio
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
                UPDATE wheat_su_ratio 
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
                "su_ratio_display_years",
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
                "su_ratio_year_status",
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
                "su_ratio_last_year_initialization",
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


# Function to get category for S/U ratio
def get_category(ratio):
    """Determine category based on S/U ratio value"""
    if ratio >= 50:
        return "Strategic Reserve"
    elif ratio >= 30:
        return "Comfortable"
    elif ratio >= 20:
        return "Adequate"
    elif ratio >= 10:
        return "Tight"
    else:
        return "Critical"


# Initialize session state
def initialize_session_state():
    """Initialize session state with database data"""
    if "su_ratio_data_loaded" not in st.session_state:
        su_data, metadata, current_config = load_su_ratio_data()

        if su_data and metadata:
            st.session_state.su_ratio_data = su_data
            st.session_state.su_ratio_metadata = metadata
            st.session_state.su_ratio_current_config = current_config
            st.session_state.su_ratio_data_loaded = True
        else:
            # Fallback to empty data
            st.session_state.su_ratio_data = {}
            st.session_state.su_ratio_metadata = {}
            st.session_state.su_ratio_current_config = {
                "display_years": ["2022/2023", "2023/2024", "2024/2025", "2025/2026"],
                "year_status": {
                    "2022/2023": "actual",
                    "2023/2024": "actual",
                    "2024/2025": "estimate",
                    "2025/2026": "projection",
                },
            }
            st.session_state.su_ratio_data_loaded = False


# Initialize session state
initialize_session_state()

# Title and header
st.title("📊 Stock-to-Use Ratio Dashboard")
st.markdown("### Global Wheat Market Tightness Analysis")

# Database status indicator
if st.session_state.su_ratio_data_loaded:
    st.sidebar.success("🗄️ Connected to Database")
else:
    st.sidebar.warning("⚠️ Using Local Data (No Database)")


# Create tabs with AI Research
tab_names = [
    "📈 Data Overview",
    "✏️ Edit Projections",
    "📊 Visualizations",
    "🤖 AI Research",
    "🌍 Regional Insights",
    "💾 Data Export",
]
# Create tabs with AI Research
tab_names = ["📈 Data Overview", "✏️ Edit Projections", "📊 Visualizations", "🤖 AI Research", "💾 Data Export"]
tabs = st.tabs(tab_names)

with tabs[0]:
    st.header("Global Stock-to-Use Ratios")

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
    if "su_ratio_current_config" in st.session_state:
        st.markdown("### Status Information")
        status_cols = st.columns(4)

        display_years = st.session_state.su_ratio_current_config["display_years"]
        year_status = st.session_state.su_ratio_current_config["year_status"]

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

    # Key insights and explanation
    col1, col2 = st.columns([2, 1])

    with col1:
        st.info(
            """
        **Stock-to-Use (S/U) Ratio** measures ending stocks as a percentage of total consumption.
        It's a critical indicator of market supply security and price volatility risk.
        
        The ratio helps assess whether markets are:
        - **Well-supplied** (high ratio) → Lower price volatility
        - **Tight** (low ratio) → Higher price volatility risk
        """
        )

    with col2:
        st.markdown("### Category Thresholds")
        st.markdown(
            """
        - 🟢 **Strategic Reserve**: ≥50%
        - 🔵 **Comfortable**: 30-50%
        - 🟡 **Adequate**: 20-30%
        - 🟠 **Tight**: 10-20%
        - 🔴 **Critical**: <10%
        """
        )

    # Create enhanced table
    st.markdown("### Stock-to-Use Ratio Data (%)")

    # Get display years from configuration
    display_years = st.session_state.su_ratio_current_config.get(
        "display_years", ["2022/2023", "2023/2024", "2024/2025", "2025/2026"]
    )

    # Create the data table with proper formatting and change calculations
    table_data = []

    for country, data in st.session_state.su_ratio_data.items():
        if country not in ALLOWED_COUNTRIES:
            continue

        row = {"Country": country}

        # Add data for display years only
        for i, year in enumerate(display_years):
            if year in data:
                row[year] = f"{data[year]:.1f}%"

                if i > 0:
                    # Calculate change from previous year
                    prev_year = display_years[i - 1]
                    if prev_year in data:
                        change = data[year] - data[prev_year]
                        row[f"Change{' ' * i}"] = format_change(change)
                    else:
                        row[f"Change{' ' * i}"] = "-"

        # Get current category
        latest_year = display_years[-1]
        if latest_year in data:
            row["Category"] = get_category(data[latest_year])

        table_data.append(row)

    df_display = pd.DataFrame(table_data)

    # Apply styling to the dataframe
    change_columns = [
        col for col in df_display.columns if col.strip().startswith("Change")
    ]

    def style_category(val):
        """Style function for category column"""
        if val == "Strategic Reserve":
            return "background-color: #90EE90"
        elif val == "Comfortable":
            return "background-color: #87CEEB"
        elif val == "Adequate":
            return "background-color: #F0E68C"
        elif val == "Tight":
            return "background-color: #FFB366"
        elif val == "Critical":
            return "background-color: #FFB6C1"
        return ""

    styled_df = df_display.style

    # Style change columns
    for col in change_columns:
        styled_df = styled_df.map(style_change_column, subset=[col])

    # Style category column if it exists
    if "Category" in df_display.columns:
        styled_df = styled_df.map(style_category, subset=["Category"])

    # Apply general styling
    styled_df = styled_df.set_properties(**{"text-align": "center"}).set_properties(
        **{"text-align": "left"}, subset=["Country"]
    )

    st.dataframe(styled_df, use_container_width=True, hide_index=True)

    # Summary statistics
    st.markdown("### Key Metrics")
    col1, col2, col3, col4 = st.columns(4)

    # Get the latest projection year
    latest_year = display_years[-1]
    prev_year = display_years[-2] if len(display_years) > 1 else None

    with col1:
        if (
            "WORLD" in st.session_state.su_ratio_data
            and latest_year in st.session_state.su_ratio_data["WORLD"]
        ):
            world_su = st.session_state.su_ratio_data["WORLD"][latest_year]
            world_change = 0
            if prev_year and prev_year in st.session_state.su_ratio_data["WORLD"]:
                world_change = (
                    world_su - st.session_state.su_ratio_data["WORLD"][prev_year]
                )
            st.metric("Global S/U Ratio", f"{world_su:.1f}%", f"{world_change:+.1f}%")

    with col2:
        # Count critical countries
        critical_count = sum(
            1
            for country, data in st.session_state.su_ratio_data.items()
            if country in ALLOWED_COUNTRIES
            and country != "WORLD"
            and latest_year in data
            and get_category(data[latest_year]) == "Critical"
        )
        st.metric(
            "Critical Countries",
            critical_count,
            help="Countries with S/U ratio below 10%",
        )

    with col3:
        # Highest S/U ratio (excluding WORLD)
        countries_only = {
            k: v
            for k, v in st.session_state.su_ratio_data.items()
            if k != "WORLD" and k in ALLOWED_COUNTRIES
        }
        if countries_only and latest_year in next(iter(countries_only.values())):
            max_country = max(
                countries_only.items(), key=lambda x: x[1].get(latest_year, 0)
            )
            st.metric(
                "Highest S/U Ratio",
                f"{max_country[0]}: {max_country[1][latest_year]:.1f}%",
            )

    with col4:
        # Lowest S/U ratio (excluding WORLD)
        if countries_only and latest_year in next(iter(countries_only.values())):
            min_country = min(
                countries_only.items(), key=lambda x: x[1].get(latest_year, 100)
            )
            st.metric(
                "Lowest S/U Ratio",
                f"{min_country[0]}: {min_country[1][latest_year]:.1f}%",
            )

with tabs[1]:
    # Get the projection year (last year in display_years)
    display_years = st.session_state.su_ratio_current_config.get(
        "display_years", ["2022/2023", "2023/2024", "2024/2025", "2025/2026"]
    )
    projection_year = display_years[-1]
    estimate_year = display_years[-2]

    st.header(f"Edit {projection_year} S/U Ratio Projections")
    st.markdown(
        f"**Note:** Historical data ({', '.join(display_years[:-1])}) is static and cannot be modified."
    )

    # Create form for editing projections
    with st.form("su_ratio_projection_form"):
        st.markdown(f"### Update S/U Ratio Projections for {projection_year}")

        # Create input fields for each country
        updated_values = {}

        # Filter countries to allowed list only (excluding WORLD for editing)
        filtered_countries = [
            c
            for c in st.session_state.su_ratio_data.keys()
            if c in ALLOWED_COUNTRIES and c != "WORLD"
        ]

        for country in filtered_countries:
            if projection_year not in st.session_state.su_ratio_data[country]:
                continue

            current_value = st.session_state.su_ratio_data[country][projection_year]

            # Calculate change from estimate year
            estimate_value = st.session_state.su_ratio_data[country].get(
                estimate_year, 0
            )
            current_change = current_value - estimate_value if estimate_value else 0

            # Show historical trend
            historical_values = []
            for year in display_years[:-1]:
                if year in st.session_state.su_ratio_data[country]:
                    historical_values.append(
                        st.session_state.su_ratio_data[country][year]
                    )

            st.subheader(f"{country}")
            col1, col2, col3 = st.columns([2, 1, 1])

            with col1:
                updated_values[country] = st.number_input(
                    f"S/U Ratio (%)",
                    value=float(current_value),
                    min_value=0.0,
                    max_value=200.0,
                    step=0.1,
                    format="%.1f",
                    key=f"su_{country}",
                    help=(
                        f"Historical: {' → '.join([f'{v:.1f}%' for v in historical_values])}"
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

            with col3:
                # Show new category
                new_category = get_category(updated_values[country])
                category_color = {
                    "Strategic Reserve": "🟢",
                    "Comfortable": "🔵",
                    "Adequate": "🟡",
                    "Tight": "🟠",
                    "Critical": "🔴",
                }.get(new_category, "⚪")
                st.markdown(f"**Category**: {category_color} {new_category}")

        # Submit button
        if st.form_submit_button("Update S/U Ratio Projections", type="primary"):
            # Update the data
            db = get_database()

            # Update individual countries
            for country, value in updated_values.items():
                st.session_state.su_ratio_data[country][projection_year] = value

                # Calculate change from estimate year
                if estimate_year in st.session_state.su_ratio_data[country]:
                    change = (
                        value - st.session_state.su_ratio_data[country][estimate_year]
                    )
                else:
                    change = 0

                # Save to database
                if db:
                    db.update_su_ratio_value(country, projection_year, value, change)

            # Calculate and update WORLD average
            world_avg = sum(updated_values.values()) / len(updated_values)
            if estimate_year in st.session_state.su_ratio_data.get("WORLD", {}):
                world_change = (
                    world_avg - st.session_state.su_ratio_data["WORLD"][estimate_year]
                )
            else:
                world_change = 0

            if "WORLD" not in st.session_state.su_ratio_data:
                st.session_state.su_ratio_data["WORLD"] = {}

            st.session_state.su_ratio_data["WORLD"][projection_year] = world_avg

            if db:
                db.update_su_ratio_value(
                    "WORLD", projection_year, world_avg, world_change
                )

            st.success("✅ S/U ratio projections updated successfully!")
            if db:
                st.info("💾 Changes saved to database")
            st.rerun()

with tabs[2]:
    st.header("S/U Ratio Visualizations")

    # Get display years from configuration
    display_years = st.session_state.su_ratio_current_config.get(
        "display_years", ["2022/2023", "2023/2024", "2024/2025", "2025/2026"]
    )

    # Time series plot
    st.subheader("S/U Ratio Trends Over Time")

    # Select countries to display - filtered to allowed countries only
    available_countries = [
        c for c in st.session_state.su_ratio_data.keys() if c in ALLOWED_COUNTRIES
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
                if year in st.session_state.su_ratio_data[country]:
                    values.append(st.session_state.su_ratio_data[country][year])
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
                        + "S/U Ratio: %{y:.1f}%<extra></extra>",
                    )
                )

        # Add reference lines for categories
        fig.add_hline(
            y=50,
            line_dash="dash",
            line_color="green",
            annotation_text="Strategic Reserve (≥50%)",
            annotation_position="right",
        )
        fig.add_hline(
            y=30,
            line_dash="dash",
            line_color="blue",
            annotation_text="Comfortable (30%)",
            annotation_position="right",
        )
        fig.add_hline(
            y=20,
            line_dash="dash",
            line_color="orange",
            annotation_text="Adequate (20%)",
            annotation_position="right",
        )
        fig.add_hline(
            y=10,
            line_dash="dash",
            line_color="red",
            annotation_text="Tight (10%)",
            annotation_position="right",
        )

        fig.update_layout(
            title="Stock-to-Use Ratio Trends",
            xaxis_title="Year",
            yaxis_title="Stock-to-Use Ratio (%)",
            hovermode="x unified",
            height=500,
        )

        # Add vertical line to separate historical from projection
        if len(display_years) > 1:
            # Find the index where projection starts
            for i, year in enumerate(display_years):
                if (
                    st.session_state.su_ratio_current_config["year_status"].get(year)
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

    # Category distribution
    st.subheader(f"S/U Ratio Category Distribution ({display_years[-1]})")

    # Count countries by category
    category_counts = {}
    latest_year = display_years[-1]

    # Filter countries to allowed list only (excluding WORLD)
    countries_only = {
        k: v
        for k, v in st.session_state.su_ratio_data.items()
        if k != "WORLD" and k in ALLOWED_COUNTRIES
    }

    for country, data in countries_only.items():
        if latest_year in data:
            category = get_category(data[latest_year])
            category_counts[category] = category_counts.get(category, 0) + 1

    if category_counts:
        # Create pie chart
        fig_pie = go.Figure(
            data=[
                go.Pie(
                    labels=list(category_counts.keys()),
                    values=list(category_counts.values()),
                    marker_colors=[
                        "#90EE90",
                        "#87CEEB",
                        "#F0E68C",
                        "#FFB366",
                        "#FFB6C1",
                    ],
                    hovertemplate="<b>%{label}</b><br>"
                    + "Countries: %{value}<br>"
                    + "Share: %{percent}<extra></extra>",
                )
            ]
        )

        fig_pie.update_layout(
            title=f"Distribution of Countries by S/U Ratio Category - {latest_year}",
            height=400,
        )

        st.plotly_chart(fig_pie, use_container_width=True)

    # Scatter plot: S/U Ratio vs Change
    st.subheader("S/U Ratio vs Year-over-Year Change")

    scatter_data = []
    prev_year = display_years[-2] if len(display_years) > 1 else None

    for country, data in countries_only.items():
        if latest_year in data:
            change = 0
            if prev_year and prev_year in data:
                change = data[latest_year] - data[prev_year]

            scatter_data.append(
                {
                    "Country": country,
                    "S/U Ratio": data[latest_year],
                    "Change": change,
                    "Category": get_category(data[latest_year]),
                }
            )

    if scatter_data:
        df_scatter = pd.DataFrame(scatter_data)

        fig_scatter = px.scatter(
            df_scatter,
            x="S/U Ratio",
            y="Change",
            color="Category",
            size=[10] * len(df_scatter),
            hover_data=["Country"],
            color_discrete_map={
                "Strategic Reserve": "#90EE90",
                "Comfortable": "#87CEEB",
                "Adequate": "#F0E68C",
                "Tight": "#FFB366",
                "Critical": "#FFB6C1",
            },
        )

        fig_scatter.update_layout(
            title=f"S/U Ratio vs Change ({latest_year})",
            xaxis_title="Stock-to-Use Ratio (%)",
            yaxis_title="Year-over-Year Change (%)",
            height=400,
        )

        # Add quadrant lines
        fig_scatter.add_hline(y=0, line_dash="dash", line_color="gray")
        fig_scatter.add_vline(x=30, line_dash="dash", line_color="gray")

        st.plotly_chart(fig_scatter, use_container_width=True)

with tabs[3]:  # AI Research tab
    create_ai_research_tab(
        commodity="wheat",
        data_type="stock_to_use_ratio",
        current_data=st.session_state.su_ratio_data,
        db_helper=get_database(
    
    ),
        update_method_name="update_su_ratio_value",
    )

with tabs[4]:  # Regional Analysis tab
    st.header("Regional S/U Ratio Insights")

    # Get display years from configuration
    display_years = st.session_state.su_ratio_current_config.get(
        "display_years", ["2022/2023", "2023/2024", "2024/2025", "2025/2026"]
    )
    latest_year = display_years[-1]

    # Regional groupings - only include allowed countries
    regions = {
        "Major Exporters": [
            c
            for c in ["United States", "Canada", "Australia", "Russia"]
            if c in ALLOWED_COUNTRIES
        ],
        "Major Importers": [
            c for c in ["China", "India", "European Union"] if c in ALLOWED_COUNTRIES
        ],
    }

    # Display regional analysis
    for region_name, countries in regions.items():
        if not countries:
            continue

        st.subheader(f"{region_name}")

        # Calculate regional metrics
        region_data = []
        for country in countries:
            if (
                country in st.session_state.su_ratio_data
                and latest_year in st.session_state.su_ratio_data[country]
            ):
                data = st.session_state.su_ratio_data[country]
                region_data.append(
                    {
                        "Country": country,
                        f"{latest_year} S/U Ratio": data[latest_year],
                        "Category": get_category(data[latest_year]),
                    }
                )

        if region_data:
            df_region = pd.DataFrame(region_data)

            # Create bar chart
            fig_region = px.bar(
                df_region,
                x="Country",
                y=f"{latest_year} S/U Ratio",
                color="Category",
                color_discrete_map={
                    "Strategic Reserve": "#90EE90",
                    "Comfortable": "#87CEEB",
                    "Adequate": "#F0E68C",
                    "Tight": "#FFB366",
                    "Critical": "#FFB6C1",
                },
                title=f"{region_name} - S/U Ratios {latest_year}",
            )

            fig_region.update_layout(
                xaxis_title="Country", yaxis_title="Stock-to-Use Ratio (%)", height=300
            )

            # Add reference line at 30%
            fig_region.add_hline(
                y=30,
                line_dash="dash",
                line_color="gray",
                annotation_text="Comfortable threshold",
            )

            st.plotly_chart(fig_region, use_container_width=True)

            # Summary metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                avg_su = df_region[f"{latest_year} S/U Ratio"].mean()
                st.metric(f"Average S/U Ratio", f"{avg_su:.1f}%")
            with col2:
                max_su = df_region[f"{latest_year} S/U Ratio"].max()
                max_country = df_region[
                    df_region[f"{latest_year} S/U Ratio"] == max_su
                ]["Country"].values[0]
                st.metric("Highest", f"{max_country}: {max_su:.1f}%")
            with col3:
                min_su = df_region[f"{latest_year} S/U Ratio"].min()
                min_country = df_region[
                    df_region[f"{latest_year} S/U Ratio"] == min_su
                ]["Country"].values[0]
                st.metric("Lowest", f"{min_country}: {min_su:.1f}%")

        st.markdown("---")

with tabs[5]:  # Data Export tab
    st.header("S/U Ratio Data Management")

    # Export options
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Export Current Data")

        # Filter data for export
        export_su_data = {
            country: data
            for country, data in st.session_state.su_ratio_data.items()
            if country in ALLOWED_COUNTRIES
        }

        # Prepare export data
        export_data = {
            "wheat_su_ratio_data": export_su_data,
            "metadata": st.session_state.su_ratio_metadata,
            "current_config": st.session_state.su_ratio_current_config,
            "export_timestamp": datetime.now().isoformat(),
            "data_source": (
                "database" if st.session_state.su_ratio_data_loaded else "local"
            ),
            "user": st.session_state.get("username", "unknown"),
        }

        # JSON export
        st.download_button(
            label="📥 Download S/U Ratio Data as JSON",
            data=json.dumps(export_data, indent=2),
            file_name=f"wheat_su_ratio_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
        )

        # CSV export
        df_export = pd.DataFrame(export_su_data).T
        csv_data = df_export.to_csv()
        st.download_button(
            label="📥 Download S/U Ratio Data as CSV",
            data=csv_data,
            file_name=f"wheat_su_ratio_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
        )

    with col2:
        st.subheader("Import Data")

        uploaded_file = st.file_uploader(
            "Upload JSON S/U ratio data file", type=["json"]
        )

        if uploaded_file is not None:
            try:
                uploaded_data = json.load(uploaded_file)

                if st.button("Import S/U Ratio Data"):
                    if "wheat_su_ratio_data" in uploaded_data:
                        # Filter imported data to allowed countries
                        filtered_data = {
                            country: data
                            for country, data in uploaded_data[
                                "wheat_su_ratio_data"
                            ].items()
                            if country in ALLOWED_COUNTRIES
                        }
                        st.session_state.su_ratio_data = filtered_data

                    if "metadata" in uploaded_data:
                        st.session_state.su_ratio_metadata = uploaded_data["metadata"]

                    if "current_config" in uploaded_data:
                        st.session_state.su_ratio_current_config = uploaded_data[
                            "current_config"
                        ]

                    st.success("S/U ratio data imported successfully!")
                    st.rerun()

            except json.JSONDecodeError:
                st.error("Invalid JSON file format")

# Footer
st.markdown("---")
status_text = (
    "🗄️ Database Connected"
    if st.session_state.su_ratio_data_loaded
    else "💾 Local Data Mode"
)
user_info = f"👤 {st.session_state.get('name', 'User')}"
st.markdown(
    f"""
    <div style='text-align: center; color: #666; font-size: 0.8em;'>
    📊 Stock-to-Use Ratio Dashboard | {status_text} | {user_info} | PPF Europe Analysis Platform
    </div>
    """,
    unsafe_allow_html=True,
)

with tabs[3]:  # AI Research tab
    create_ai_research_tab(
        commodity="wheat",
        data_type="su_ratio",
        current_data=st.session_state.su_ratio_data,
        db_helper=get_database(
    
    ),
        update_method_name="update_su_ratio_value"
    )
