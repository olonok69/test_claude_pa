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

# Import AI Research components
from utils.enhanced_ai_research_tab import create_ai_research_tab

# Page configuration
st.set_page_config(
    page_title="Corn Yield Dashboard",
    page_icon="🌱",
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
        if st.button("🏢 Stocks", use_container_width=True):
            st.switch_page("pages/13_corn_stocks.py")
        if st.button("🌽 Acreage", use_container_width=True):
            st.switch_page("pages/15_corn_acreage.py")
    with col2:
        if st.button("📦 Exports", use_container_width=True):
            st.switch_page("pages/11_corn_exports.py")
        if st.button("📊 S/U Ratio", use_container_width=True):
            st.switch_page("pages/14_corn_stock_to_use_ratio.py")
        if st.button("🌍 World Demand", use_container_width=True):
            st.switch_page("pages/17_corn_world_demand.py")

    st.markdown("---")

    # AI Tools section
    st.markdown("### 🤖 AI & MCP Tools")
    if st.button("💬 Launch AI Chat", use_container_width=True):
        st.switch_page("pages/9_mcp_app.py")

    st.markdown("---")
    st.markdown("### 🌱 Yield Dashboard")

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


# Load yield data from database with filtering
@st.cache_data
def load_yield_data():
    """Load yield data from database"""
    db = get_database()
    if not db:
        return None, None, None

    try:
        # Get all yield data
        all_yield_data = db.get_all_yield_data()

        # Filter to keep only allowed countries
        yield_data = {
            country: data
            for country, data in all_yield_data.items()
            if country in ALLOWED_COUNTRIES
        }

        # Get metadata
        metadata = db.get_metadata()

        # Get current year configuration
        current_config = {
            "display_years": metadata.get(
                "yield_display_years", "2022/2023,2023/2024,2024/2025,2025/2026"
            ).split(","),
            "year_status": json.loads(
                metadata.get(
                    "yield_year_status",
                    '{"2022/2023": "actual", "2023/2024": "actual", "2024/2025": "estimate", "2025/2026": "projection"}',
                )
            ),
        }

        return yield_data, metadata, current_config
    except Exception as e:
        st.error(f"❌ Error loading yield data from database: {e}")
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
    last_init = metadata.get("yield_last_year_initialization")

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
    display_years = metadata.get("yield_display_years", "").split(",")
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
            "yield_display_years", "2022/2023,2023/2024,2024/2025,2025/2026"
        ).split(",")

        # Check what years actually exist in the database
        cursor.execute("SELECT DISTINCT year FROM corn_yield ORDER BY year")
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
                INSERT INTO corn_yield (country, year, yield_value, change_value, change_percentage, yield_category, weather_impact, status)
                SELECT country, ?, yield_value, 0, 0, yield_category, NULL, 'projection'
                FROM corn_yield
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
                UPDATE corn_yield 
                SET status = ?, updated_at = ?
                WHERE year = ?
            """,
                (status, datetime.now().isoformat(), year),
            )
            print(f"Updated {year} status to {status}")

        # Recalculate change values for all display years
        for i, year in enumerate(new_display_years):
            if i > 0:
                prev_year = new_display_years[i - 1]
                cursor.execute(
                    """
                    UPDATE corn_yield AS w1
                    SET change_value = w1.yield_value - (
                        SELECT yield_value FROM corn_yield w2 
                        WHERE w2.country = w1.country AND w2.year = ?
                    ),
                    change_percentage = CASE 
                        WHEN (SELECT yield_value FROM corn_yield w2 WHERE w2.country = w1.country AND w2.year = ?) > 0
                        THEN ((w1.yield_value - (SELECT yield_value FROM corn_yield w2 WHERE w2.country = w1.country AND w2.year = ?)) / 
                              (SELECT yield_value FROM corn_yield w2 WHERE w2.country = w1.country AND w2.year = ?)) * 100
                        ELSE 0
                    END,
                    updated_at = ?
                    WHERE year = ?
                """,
                    (
                        prev_year,
                        prev_year,
                        prev_year,
                        prev_year,
                        datetime.now().isoformat(),
                        year,
                    ),
                )

        # Update metadata with new configuration
        cursor.execute(
            """
            INSERT OR REPLACE INTO metadata (key, value, updated_at)
            VALUES (?, ?, ?)
        """,
            (
                "yield_display_years",
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
                "yield_year_status",
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
                "yield_last_year_initialization",
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
    if "corn_yield_data_loaded" not in st.session_state:
        yield_data, metadata, current_config = load_yield_data()

        if yield_data and metadata:
            st.session_state.corn_yield_data = yield_data
            st.session_state.corn_yield_metadata = metadata
            st.session_state.corn_yield_current_config = current_config
            st.session_state.corn_yield_data_loaded = True
        else:
            # Fallback to empty data
            st.session_state.corn_yield_data = {}
            st.session_state.corn_yield_metadata = {}
            st.session_state.corn_yield_current_config = {
                "display_years": ["2022/2023", "2023/2024", "2024/2025", "2025/2026"],
                "year_status": {
                    "2022/2023": "actual",
                    "2023/2024": "actual",
                    "2024/2025": "estimate",
                    "2025/2026": "projection",
                },
            }
            st.session_state.corn_yield_data_loaded = False


# Initialize session state
initialize_session_state()

# Title and header
st.title("🌱 Corn Yield Dashboard")
st.markdown("### Global Corn Productivity Analysis")

# Database status indicator
if st.session_state.corn_yield_data_loaded:
    st.sidebar.success("🗄️ Connected to Database")
else:
    st.sidebar.warning("⚠️ Using Local Data (No Database)")


# Create tabs with AI Research
tab_names = [
    "📈 Data Overview",
    "✏️ Edit Projections",
    "📊 Visualizations",
    "🤖 AI Research",
    "🌍 Regional Analysis",
    "💾 Data Export",
]
tabs = st.tabs(tab_names)

with tabs[0]:
    st.header("Global Corn Yields")

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
    if "corn_yield_current_config" in st.session_state:
        st.markdown("### Status Information")
        status_cols = st.columns(4)

        display_years = st.session_state.corn_yield_current_config["display_years"]
        year_status = st.session_state.corn_yield_current_config["year_status"]

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
    **Yield** (tonnes per hectare) measures corn productivity and farming efficiency.
    - Key driver of production along with acreage
    - Influenced by: weather, technology, inputs, management practices
    - Global average: ~5.9 t/ha with significant regional variation
    - USA leads with yields above 11 t/ha due to advanced technology
    """
    )

    # Create enhanced table
    st.markdown("### Yield Data (tonnes per hectare)")

    # Get display years from configuration
    display_years = st.session_state.corn_yield_current_config.get(
        "display_years", ["2022/2023", "2023/2024", "2024/2025", "2025/2026"]
    )

    # Create the data table with proper formatting
    table_data = []

    for country, data in st.session_state.corn_yield_data.items():
        if country not in ALLOWED_COUNTRIES:
            continue

        row = {"Country": country}

        # Add data for display years only
        for i, year in enumerate(display_years):
            if year in data:
                row[year] = f"{data[year]:.2f}"

                # Calculate change from previous year (except for first year)
                if i > 0:
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

    styled_df = df_display.style
    for col in change_columns:
        styled_df = styled_df.map(style_change_column, subset=[col])

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
            "WORLD" in st.session_state.corn_yield_data
            and latest_year in st.session_state.corn_yield_data["WORLD"]
        ):
            world_yield = st.session_state.corn_yield_data["WORLD"][latest_year]
            st.metric(f"Global Avg Yield {latest_year}", f"{world_yield:.2f} t/ha")

    with col2:
        if (
            "WORLD" in st.session_state.corn_yield_data
            and latest_year in st.session_state.corn_yield_data["WORLD"]
            and prev_year in st.session_state.corn_yield_data["WORLD"]
        ):
            world_change = (
                st.session_state.corn_yield_data["WORLD"][latest_year]
                - st.session_state.corn_yield_data["WORLD"][prev_year]
            )
            st.metric("Change from Previous Year", f"{world_change:+.2f} t/ha")

    with col3:
        # Find highest yield country (excluding WORLD)
        countries_only = {
            k: v
            for k, v in st.session_state.corn_yield_data.items()
            if k != "WORLD" and k in ALLOWED_COUNTRIES
        }
        if countries_only and latest_year in next(iter(countries_only.values())):
            max_country = max(
                countries_only.items(), key=lambda x: x[1].get(latest_year, 0)
            )
            st.metric(
                f"Highest Yield", f"{max_country[0]}: {max_country[1][latest_year]:.2f}"
            )

    with col4:
        # Count improving countries
        improving = sum(
            1
            for country, data in countries_only.items()
            if latest_year in data
            and prev_year in data
            and data[latest_year] > data[prev_year]
        )
        st.metric("Countries Improving", improving)

with tabs[1]:
    # Get the projection year (last year in display_years)
    display_years = st.session_state.corn_yield_current_config.get(
        "display_years", ["2022/2023", "2023/2024", "2024/2025", "2025/2026"]
    )
    projection_year = display_years[-1]
    estimate_year = display_years[-2]

    st.header(f"Edit {projection_year} Yield Projections")
    st.markdown(
        f"**Note:** Historical data ({', '.join(display_years[:-1])}) is static and cannot be modified."
    )

    # Create form for editing projections
    with st.form("corn_yield_projection_form"):
        st.markdown(f"### Update Yield Projections for {projection_year}")

        # Create input fields for each country
        updated_values = {}

        # Filter countries to allowed list only (excluding WORLD for editing)
        filtered_countries = [
            c
            for c in st.session_state.corn_yield_data.keys()
            if c in ALLOWED_COUNTRIES and c != "WORLD"
        ]

        for country in filtered_countries:
            if projection_year not in st.session_state.corn_yield_data[country]:
                continue

            current_value = st.session_state.corn_yield_data[country][projection_year]

            # Show historical trend
            historical_values = []
            for year in display_years[:-1]:
                if year in st.session_state.corn_yield_data[country]:
                    historical_values.append(
                        st.session_state.corn_yield_data[country][year]
                    )

            st.subheader(f"{country}")
            col1, col2, col3 = st.columns([2, 1, 1])

            with col1:
                updated_values[country] = st.number_input(
                    f"Yield (t/ha)",
                    value=float(current_value),
                    min_value=0.0,
                    max_value=25.0,
                    step=0.01,
                    format="%.2f",
                    key=f"corn_yield_{country}",
                    help=(
                        f"Historical: {' → '.join([f'{v:.2f}' for v in historical_values])}"
                        if historical_values
                        else "No historical data"
                    ),
                )

            with col2:
                # Display calculated change
                if estimate_year in st.session_state.corn_yield_data[country]:
                    calc_change = (
                        updated_values[country]
                        - st.session_state.corn_yield_data[country][estimate_year]
                    )
                    if calc_change > 0:
                        st.success(f"Change: +{calc_change:.2f}")
                    elif calc_change < 0:
                        st.error(f"Change: {calc_change:.2f}")
                    else:
                        st.info("Change: 0.00")

            with col3:
                # Show yield category
                yield_val = updated_values[country]
                if yield_val >= 10.0:
                    st.markdown("🟣 **Very High**")
                elif yield_val >= 7.0:
                    st.markdown("🟢 **High**")
                elif yield_val >= 5.0:
                    st.markdown("🔵 **Medium**")
                elif yield_val >= 3.0:
                    st.markdown("🟡 **Low**")
                else:
                    st.markdown("🔴 **Very Low**")

        # Submit button
        if st.form_submit_button("Update Yield Projections", type="primary"):
            # Update the data
            db = get_database()

            # Update individual countries
            for country, value in updated_values.items():
                st.session_state.corn_yield_data[country][projection_year] = value

                # Calculate change from estimate year
                if estimate_year in st.session_state.corn_yield_data[country]:
                    change = (
                        value - st.session_state.corn_yield_data[country][estimate_year]
                    )
                    change_pct = (
                        (
                            change
                            / st.session_state.corn_yield_data[country][estimate_year]
                        )
                        * 100
                        if st.session_state.corn_yield_data[country][estimate_year] > 0
                        else 0
                    )
                else:
                    change = 0
                    change_pct = 0

                # Save to database
                if db:
                    db.update_yield_value(
                        country,
                        projection_year,
                        value,
                        change,
                        change_pct,
                        None,  # No weather impact
                    )

            # Calculate and update WORLD average
            world_avg = sum(updated_values.values()) / len(updated_values)

            if estimate_year in st.session_state.corn_yield_data.get("WORLD", {}):
                world_change = (
                    world_avg - st.session_state.corn_yield_data["WORLD"][estimate_year]
                )
                world_change_pct = (
                    (
                        world_change
                        / st.session_state.corn_yield_data["WORLD"][estimate_year]
                    )
                    * 100
                    if st.session_state.corn_yield_data["WORLD"][estimate_year] > 0
                    else 0
                )
            else:
                world_change = 0
                world_change_pct = 0

            if "WORLD" not in st.session_state.corn_yield_data:
                st.session_state.corn_yield_data["WORLD"] = {}

            st.session_state.corn_yield_data["WORLD"][projection_year] = world_avg

            if db:
                db.update_yield_value(
                    "WORLD",
                    projection_year,
                    world_avg,
                    world_change,
                    world_change_pct,
                    None,
                )

            st.success("✅ Yield projections updated successfully!")
            if db:
                st.info("💾 Changes saved to database")
            st.rerun()

with tabs[2]:
    st.header("Yield Visualizations")

    # Get display years from configuration
    display_years = st.session_state.corn_yield_current_config.get(
        "display_years", ["2022/2023", "2023/2024", "2024/2025", "2025/2026"]
    )

    # Time series plot
    st.subheader("Yield Trends Over Time")

    # Select countries to display - filtered to allowed countries only
    available_countries = [
        c for c in st.session_state.corn_yield_data.keys() if c in ALLOWED_COUNTRIES
    ]

    countries_to_plot = st.multiselect(
        "Select countries/regions to display:",
        options=available_countries,
        default=[
            c
            for c in [
                "WORLD",
                "United States",
                "China",
                "European Union",
                "India",
                "Russia",
                "Australia",
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
                if year in st.session_state.corn_yield_data[country]:
                    values.append(st.session_state.corn_yield_data[country][year])
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
                        + "Yield: %{y:.2f} t/ha<extra></extra>",
                    )
                )

        fig.update_layout(
            title="Corn Yield Trends",
            xaxis_title="Year",
            yaxis_title="Yield (tonnes per hectare)",
            hovermode="x unified",
            height=500,
        )

        # Add vertical line to separate historical from projection
        if len(display_years) > 1:
            # Find the index where projection starts
            for i, year in enumerate(display_years):
                if (
                    st.session_state.corn_yield_current_config["year_status"].get(year)
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

    # Yield comparison chart
    st.subheader(f"Yield Comparison by Country ({display_years[-1]})")

    # Get yield data for countries (excluding WORLD)
    countries_only = {
        k: v
        for k, v in st.session_state.corn_yield_data.items()
        if k != "WORLD" and k in ALLOWED_COUNTRIES
    }

    latest_year = display_years[-1]
    yield_comparison = []

    for country, data in countries_only.items():
        if latest_year in data:
            yield_comparison.append({"Country": country, "Yield": data[latest_year]})

    if yield_comparison:
        df_yield = pd.DataFrame(yield_comparison)
        df_yield = df_yield.sort_values("Yield", ascending=False)

        # Create bar chart with color coding
        fig_comparison = px.bar(
            df_yield,
            x="Country",
            y="Yield",
            title=f"Corn Yields by Country - {latest_year}",
            color="Yield",
            color_continuous_scale="Oranges",
        )

        # Add world average line
        world_yield = st.session_state.corn_yield_data.get("WORLD", {}).get(
            latest_year, 6.20
        )
        fig_comparison.add_hline(
            y=world_yield,
            line_dash="dash",
            line_color="red",
            annotation_text=f"World Average: {world_yield:.2f} t/ha",
        )

        fig_comparison.update_layout(
            xaxis_title="Country", yaxis_title="Yield (t/ha)", height=400
        )

        st.plotly_chart(fig_comparison, use_container_width=True)

    # Change analysis - filtered to allowed countries
    filtered_data = {
        k: v
        for k, v in st.session_state.corn_yield_data.items()
        if k in ALLOWED_COUNTRIES
    }

    # Calculate changes for visualization
    for country, data in filtered_data.items():
        for i, year in enumerate(display_years):
            if i > 0 and year in data and display_years[i - 1] in data:
                data[f"{year}_change"] = data[year] - data[display_years[i - 1]]

    create_change_visualization(filtered_data, "Yield", exclude=["WORLD"])

with tabs[3]:  # AI Research tab
    create_ai_research_tab(
        commodity="corn",
        data_type="yield",
        current_data=st.session_state.corn_yield_data,
        db_helper=get_database(),
        update_method_name="update_yield_value",
    )

with tabs[4]:
    st.header("Regional Yield Analysis")

    # Get display years from configuration
    display_years = st.session_state.corn_yield_current_config.get(
        "display_years", ["2022/2023", "2023/2024", "2024/2025", "2025/2026"]
    )
    latest_year = display_years[-1]

    # Yield gap analysis
    st.subheader("Yield Gap Analysis")

    # Get yield data for all countries except WORLD
    countries_only = {
        k: v
        for k, v in st.session_state.corn_yield_data.items()
        if k != "WORLD" and k in ALLOWED_COUNTRIES
    }

    # Create dataframe for analysis
    yield_data = []
    for country, data in countries_only.items():
        if latest_year in data:
            yield_data.append({"Country": country, "Yield": data[latest_year]})

    if yield_data:
        df_yield = pd.DataFrame(yield_data)

        # Calculate yield gaps relative to best performer
        max_yield = df_yield["Yield"].max()
        df_yield["Yield_Gap"] = max_yield - df_yield["Yield"]
        df_yield["Potential_Increase_Pct"] = (
            df_yield["Yield_Gap"] / df_yield["Yield"] * 100
        ).round(1)

        # Sort by yield gap
        df_yield = df_yield.sort_values("Yield_Gap", ascending=False)

        # Create gap analysis chart
        fig_gap = go.Figure()

        # Add current yield bars
        fig_gap.add_trace(
            go.Bar(
                name="Current Yield",
                x=df_yield["Country"],
                y=df_yield["Yield"],
                marker_color="lightblue",
            )
        )

        # Add potential yield bars
        fig_gap.add_trace(
            go.Bar(
                name="Yield Gap",
                x=df_yield["Country"],
                y=df_yield["Yield_Gap"],
                marker_color="lightcoral",
            )
        )

        fig_gap.update_layout(
            title="Yield Improvement Potential by Country",
            xaxis_title="Country",
            yaxis_title="Yield (t/ha)",
            barmode="stack",
            height=400,
        )

        st.plotly_chart(fig_gap, use_container_width=True)

        # Summary metrics
        col1, col2, col3 = st.columns(3)

        with col1:
            avg_gap = df_yield["Yield_Gap"].mean()
            st.metric("Average Yield Gap", f"{avg_gap:.2f} t/ha")

        with col2:
            world_yield = st.session_state.corn_yield_data.get("WORLD", {}).get(
                latest_year, 6.20
            )
            countries_below_avg = len(df_yield[df_yield["Yield"] < world_yield])
            st.metric("Countries Below Average", countries_below_avg)

        with col3:
            max_gap_country = df_yield.iloc[0]
            st.metric(
                "Largest Gap",
                f"{max_gap_country['Country']}: {max_gap_country['Yield_Gap']:.2f} t/ha",
            )

    # Yield distribution
    st.subheader("Yield Distribution Analysis")

    if yield_data:
        # Create box plot
        fig_box = go.Figure()

        fig_box.add_trace(
            go.Box(
                y=df_yield["Yield"],
                name="All Countries",
                boxpoints="all",
                jitter=0.3,
                pointpos=-1.8,
                marker_color="orange",
            )
        )

        fig_box.update_layout(
            title=f"Yield Distribution - {latest_year}",
            yaxis_title="Yield (t/ha)",
            height=400,
        )

        # Add world average line
        world_yield = st.session_state.corn_yield_data.get("WORLD", {}).get(
            latest_year, 6.20
        )
        fig_box.add_hline(
            y=world_yield,
            line_dash="dash",
            line_color="red",
            annotation_text=f"World Average: {world_yield:.2f}",
        )

        st.plotly_chart(fig_box, use_container_width=True)

        # Statistics table
        st.markdown("### Statistical Summary")
        stats_df = pd.DataFrame(
            {
                "Metric": ["Mean", "Median", "Std Dev", "Min", "Max"],
                "Value": [
                    f"{df_yield['Yield'].mean():.2f} t/ha",
                    f"{df_yield['Yield'].median():.2f} t/ha",
                    f"{df_yield['Yield'].std():.2f} t/ha",
                    f"{df_yield['Yield'].min():.2f} t/ha ({df_yield.loc[df_yield['Yield'].idxmin(), 'Country']})",
                    f"{df_yield['Yield'].max():.2f} t/ha ({df_yield.loc[df_yield['Yield'].idxmax(), 'Country']})",
                ],
            }
        )
        st.table(stats_df)

        # Yield category breakdown
        st.markdown("### Yield Categories")
        category_counts = {
            "Very High (≥10)": len(df_yield[df_yield["Yield"] >= 10]),
            "High (7-10)": len(
                df_yield[(df_yield["Yield"] >= 7) & (df_yield["Yield"] < 10)]
            ),
            "Medium (5-7)": len(
                df_yield[(df_yield["Yield"] >= 5) & (df_yield["Yield"] < 7)]
            ),
            "Low (3-5)": len(
                df_yield[(df_yield["Yield"] >= 3) & (df_yield["Yield"] < 5)]
            ),
            "Very Low (<3)": len(df_yield[df_yield["Yield"] < 3]),
        }

        fig_pie = px.pie(
            values=list(category_counts.values()),
            names=list(category_counts.keys()),
            title="Distribution by Yield Category",
            color_discrete_sequence=px.colors.diverging.RdYlGn[::-1],
        )
        st.plotly_chart(fig_pie, use_container_width=True)

with tabs[5]:
    st.header("Yield Data Management")

    # Export options
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Export Current Data")

        # Filter data for export
        export_yield_data = {
            country: data
            for country, data in st.session_state.corn_yield_data.items()
            if country in ALLOWED_COUNTRIES
        }

        # Prepare export data
        export_data = {
            "corn_yield_data": export_yield_data,
            "metadata": st.session_state.corn_yield_metadata,
            "current_config": st.session_state.corn_yield_current_config,
            "export_timestamp": datetime.now().isoformat(),
            "data_source": (
                "database" if st.session_state.corn_yield_data_loaded else "local"
            ),
            "user": st.session_state.get("username", "unknown"),
        }

        # JSON export
        st.download_button(
            label="📥 Download Yield Data as JSON",
            data=json.dumps(export_data, indent=2),
            file_name=f"corn_yield_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
        )

        # CSV export
        df_export = pd.DataFrame(export_yield_data).T
        csv_data = df_export.to_csv()
        st.download_button(
            label="📥 Download Yield Data as CSV",
            data=csv_data,
            file_name=f"corn_yield_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
        )

    with col2:
        st.subheader("Import Data")

        uploaded_file = st.file_uploader("Upload JSON yield data file", type=["json"])

        if uploaded_file is not None:
            try:
                uploaded_data = json.load(uploaded_file)

                if st.button("Import Yield Data"):
                    if "corn_yield_data" in uploaded_data:
                        # Filter imported data to allowed countries
                        filtered_data = {
                            country: data
                            for country, data in uploaded_data[
                                "corn_yield_data"
                            ].items()
                            if country in ALLOWED_COUNTRIES
                        }
                        st.session_state.corn_yield_data = filtered_data

                    if "metadata" in uploaded_data:
                        st.session_state.corn_yield_metadata = uploaded_data["metadata"]

                    if "current_config" in uploaded_data:
                        st.session_state.corn_yield_current_config = uploaded_data[
                            "current_config"
                        ]

                    st.success("Yield data imported successfully!")
                    st.rerun()

            except json.JSONDecodeError:
                st.error("Invalid JSON file format")

# Footer
st.markdown("---")
status_text = (
    "🗄️ Database Connected"
    if st.session_state.corn_yield_data_loaded
    else "💾 Local Data Mode"
)
user_info = f"👤 {st.session_state.get('name', 'User')}"
st.markdown(
    f"""
    <div style='text-align: center; color: #666; font-size: 0.8em;'>
    🌱 Corn Yield Dashboard | {status_text} | {user_info} | PPF Europe Analysis Platform
    </div>
    """,
    unsafe_allow_html=True,
)
