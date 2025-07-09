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

# Define allowed countries
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
        if st.button("📦 Exports", use_container_width=True):
            st.switch_page("pages/2_wheat_exports.py")
        if st.button("🏢 Stocks", use_container_width=True):
            st.switch_page("pages/4_wheat_stocks.py")
        if st.button("🌾 Acreage", use_container_width=True):
            st.switch_page("pages/6_wheat_acreage.py")
    with col2:
        if st.button("📥 Imports", use_container_width=True):
            st.switch_page("pages/3_wheat_imports.py")
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


# Load data from database with filtering
@st.cache_data
def load_data_from_db():
    """Load data from database"""
    db = get_database()
    if not db:
        return None, None, None

    try:
        # Get all production data
        all_wheat_data = db.get_all_production_data()

        # Filter to keep only allowed countries
        wheat_data = {
            country: data
            for country, data in all_wheat_data.items()
            if country in ALLOWED_COUNTRIES
        }

        # Get metadata
        metadata = db.get_metadata()
        projection_metadata = {
            "last_updated": metadata.get("production_last_updated", "19 Sept'24"),
            "next_update": metadata.get("production_next_update", "17 Oct'24"),
        }

        # Get current year configuration
        current_config = {
            "display_years": metadata.get(
                "display_years", "2021/2022,2022/2023,2023/2024,2024/2025"
            ).split(","),
            "year_status": json.loads(
                metadata.get(
                    "year_status",
                    '{"2021/2022": "act", "2022/2023": "act", "2023/2024": "estimate", "2024/2025": "projection"}',
                )
            ),
        }

        return wheat_data, projection_metadata, current_config
    except Exception as e:
        st.error(f"❌ Error loading data from database: {e}")
        return None, None, None


# Function to initialize new year
def initialize_new_year():
    """Initialize a new year by shifting the year window"""
    db = get_database()
    if not db:
        return False

    try:
        conn = db.get_connection()
        cursor = conn.cursor()

        # Get current configuration from metadata
        metadata = db.get_metadata()
        current_display_years = metadata.get(
            "display_years", "2021/2022,2022/2023,2023/2024,2024/2025"
        ).split(",")

        # Check what years actually exist in the database
        cursor.execute("SELECT DISTINCT year FROM wheat_production ORDER BY year")
        all_years = [row[0] for row in cursor.fetchall()]

        print(f"Current display years: {current_display_years}")
        print(f"All years in database: {all_years}")

        # Determine the new display years by shifting forward
        if "2025/2026" in all_years:
            # If 2025/2026 exists, shift to show it
            new_display_years = ["2022/2023", "2023/2024", "2024/2025", "2025/2026"]
            new_year_status = {
                "2022/2023": "act",
                "2023/2024": "act",
                "2024/2025": "estimate",
                "2025/2026": "projection",
            }
        else:
            # If 2025/2026 doesn't exist, create it first
            print("Creating 2025/2026 data...")

            # Insert data for 2025/2026 by copying from 2024/2025
            cursor.execute(
                """
                INSERT INTO wheat_production (country, year, production_value, percentage_world, change_value, status)
                SELECT country, '2025/2026', production_value, percentage_world, 0, 'projection'
                FROM wheat_production
                WHERE year = '2024/2025' AND country IN ({})
            """.format(
                    ",".join(["?"] * len(ALLOWED_COUNTRIES))
                ),
                ALLOWED_COUNTRIES,
            )

            new_display_years = ["2022/2023", "2023/2024", "2024/2025", "2025/2026"]
            new_year_status = {
                "2022/2023": "act",
                "2023/2024": "act",
                "2024/2025": "estimate",
                "2025/2026": "projection",
            }

        # Update statuses for all years
        for year, status in new_year_status.items():
            cursor.execute(
                """
                UPDATE wheat_production 
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
            ("display_years", ",".join(new_display_years), datetime.now().isoformat()),
        )

        cursor.execute(
            """
            INSERT OR REPLACE INTO metadata (key, value, updated_at)
            VALUES (?, ?, ?)
        """,
            ("year_status", json.dumps(new_year_status), datetime.now().isoformat()),
        )

        cursor.execute(
            """
            INSERT OR REPLACE INTO metadata (key, value, updated_at)
            VALUES (?, ?, ?)
        """,
            (
                "year_initialized_at",
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

        # Clear session state to force reload
        if "production_data_loaded" in st.session_state:
            del st.session_state["production_data_loaded"]

        return True

    except Exception as e:
        if conn:
            conn.rollback()
            conn.close()
        st.error(f"❌ Error initializing new year: {e}")
        import traceback

        traceback.print_exc()
        return False


# Initialize session state
def initialize_session_state():
    """Initialize session state with database data"""
    if "production_data_loaded" not in st.session_state:
        wheat_data, projection_metadata, current_config = load_data_from_db()

        if wheat_data and projection_metadata:
            st.session_state.wheat_data = wheat_data
            st.session_state.production_projection_metadata = projection_metadata
            st.session_state.current_config = current_config
            st.session_state.production_data_loaded = True
        else:
            # Fallback to hardcoded data if database is not available
            st.session_state.wheat_data = {
                "WORLD": {
                    "2021/2022": 779.7,
                    "2022/2023": 803.9,
                    "2023/2024": 795.0,
                    "2024/2025": 798.0,
                }
            }
            st.session_state.production_projection_metadata = {
                "last_updated": "19 Sept'24",
                "next_update": "17 Oct'24",
            }
            st.session_state.current_config = {
                "display_years": ["2021/2022", "2022/2023", "2023/2024", "2024/2025"],
                "year_status": {
                    "2021/2022": "act",
                    "2022/2023": "act",
                    "2023/2024": "estimate",
                    "2024/2025": "projection",
                },
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

    # Year initialization button
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.info("📅 Current Year Configuration")
    with col2:
        if st.button(
            "🔄 Initialize New Year", type="primary", help="Shift year window forward"
        ):
            if initialize_new_year():
                st.success("✅ Year initialized successfully!")
                st.rerun()
            else:
                st.error("❌ Failed to initialize new year")
    with col3:
        if st.button("🔄 Refresh Data"):
            st.cache_data.clear()
            st.rerun()

    # Display dynamic status indicators based on current configuration
    if "current_config" in st.session_state:
        st.markdown("### Status Information")
        status_cols = st.columns(4)

        display_years = st.session_state.current_config["display_years"]
        year_status = st.session_state.current_config["year_status"]

        for i, year in enumerate(display_years[-4:]):  # Show last 4 years
            if i < len(status_cols):
                with status_cols[i]:
                    status = year_status.get(year, "unknown")
                    if status == "act":
                        st.info(f"**{year}**: actual")
                    elif status == "estimate":
                        st.warning(f"**{year}**: estimate")
                    elif status == "projection":
                        st.success(f"**{year}**: projection")

    # Display projection dates
    st.markdown(
        f"**Projection Dates**: {st.session_state.production_projection_metadata['last_updated']} | {st.session_state.production_projection_metadata['next_update']}"
    )

    st.markdown("---")

    # Create enhanced table - filter to display years only
    st.markdown("### Production Data (Million Metric Tons)")

    # Get display years from configuration
    display_years = st.session_state.current_config.get(
        "display_years", ["2021/2022", "2022/2023", "2023/2024", "2024/2025"]
    )

    # Create the data table with proper formatting
    table_data = []
    for country, data in st.session_state.wheat_data.items():
        if country not in ALLOWED_COUNTRIES:
            continue

        row = {"Country/Region": country}

        # Add data for display years only
        for i, year in enumerate(display_years):
            if year in data:
                row[year] = f"{data[year]:.1f}"

                # Add percentage for first year if available
                if i == 0 and f"{year}_pct" in data and data[f"{year}_pct"] is not None:
                    row["% World"] = f"{data[f'{year}_pct']:.1f}%"
                elif i == 0:
                    row["% World"] = "-"

                # Add change column
                if f"{year}_change" in data:
                    row[f"Change{' ' * i}"] = format_change(data.get(f"{year}_change"))
                else:
                    row[f"Change{' ' * i}"] = "-"

        table_data.append(row)

    df_display = pd.DataFrame(table_data)

    # Apply styling to the dataframe
    change_columns = [
        col for col in df_display.columns if col.strip().startswith("Change")
    ]
    styled_df = (
        df_display.style.map(style_change_column, subset=change_columns)
        .set_properties(**{"text-align": "center"})
        .set_properties(**{"text-align": "left"}, subset=["Country/Region"])
    )

    st.dataframe(styled_df, use_container_width=True, hide_index=True)

    # Summary statistics
    st.markdown("### Summary Statistics")
    col1, col2, col3, col4 = st.columns(4)

    # Get the latest projection year
    latest_year = display_years[-1]

    with col1:
        if (
            "WORLD" in st.session_state.wheat_data
            and latest_year in st.session_state.wheat_data["WORLD"]
        ):
            world_latest = st.session_state.wheat_data["WORLD"][latest_year]
            st.metric(f"Global Production {latest_year}", f"{world_latest:.1f} Mt")

    with col2:
        if (
            "WORLD" in st.session_state.wheat_data
            and f"{latest_year}_change" in st.session_state.wheat_data["WORLD"]
        ):
            world_change = st.session_state.wheat_data["WORLD"].get(
                f"{latest_year}_change", 0
            )
            st.metric("Change from Previous Year", f"{world_change:+.1f} Mt")

    with col3:
        # Find top producer (excluding WORLD)
        countries_only = {
            k: v
            for k, v in st.session_state.wheat_data.items()
            if k != "WORLD" and k in ALLOWED_COUNTRIES
        }
        if countries_only and latest_year in next(iter(countries_only.values())):
            top_producer = max(
                countries_only.items(), key=lambda x: x[1].get(latest_year, 0)
            )
            st.metric(f"Top Producer {latest_year}", f"{top_producer[0][:15]}...")

    with col4:
        if countries_only and latest_year in top_producer[1]:
            top_production = top_producer[1][latest_year]
            st.metric("Top Production", f"{top_production:.1f} Mt")

with tab2:
    st.header(f"Edit {display_years[-1]} Projections")
    st.markdown(
        f"**Note:** Historical data ({', '.join(display_years[:-1])}) is static and cannot be modified."
    )

    # Create form for editing projections
    with st.form("projection_form"):
        st.markdown(
            f"### Update Production Projections and Changes for {display_years[-1]}"
        )

        # Create input fields for each country
        updated_values = {}
        updated_changes = {}

        # Filter countries
        filtered_countries = [
            c for c in st.session_state.wheat_data.keys() if c in ALLOWED_COUNTRIES
        ]

        for country in filtered_countries:
            if latest_year not in st.session_state.wheat_data[country]:
                continue

            current_value = st.session_state.wheat_data[country][latest_year]
            current_change = st.session_state.wheat_data[country].get(
                f"{latest_year}_change", 0
            )

            # Show historical trend
            historical_values = []
            for year in display_years[:-1]:
                if year in st.session_state.wheat_data[country]:
                    historical_values.append(st.session_state.wheat_data[country][year])

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
                    help=(
                        f"Historical: {' → '.join([f'{v:.1f}' for v in historical_values])}"
                        if historical_values
                        else "No historical data"
                    ),
                )

            with col2:
                updated_changes[country] = st.number_input(
                    f"Change from {display_years[-2]}",
                    value=float(current_change),
                    step=0.1,
                    format="%.1f",
                    key=f"change_{country}",
                    help="Positive for increase, negative for decrease",
                )

            with col3:
                # Calculate and display automatic change
                if display_years[-2] in st.session_state.wheat_data[country]:
                    auto_change = (
                        updated_values[country]
                        - st.session_state.wheat_data[country][display_years[-2]]
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
                st.session_state.wheat_data[country][latest_year] = value
                st.session_state.wheat_data[country][f"{latest_year}_change"] = (
                    updated_changes[country]
                )

                # Save to database
                if db:
                    db.update_production_value(
                        country, latest_year, value, updated_changes[country]
                    )

            st.success("✅ Projections updated successfully!")
            if db:
                st.info("💾 Changes saved to database")
            st.rerun()

with tab3:
    st.header("Production Visualizations")

    # Time series plot
    st.subheader("Production Trends Over Time")

    # Select countries to display - filtered to allowed countries
    available_countries = [
        c for c in st.session_state.wheat_data.keys() if c in ALLOWED_COUNTRIES
    ]

    countries_to_plot = st.multiselect(
        "Select countries/regions to display:",
        options=available_countries,
        default=[
            c
            for c in [
                "WORLD",
                "China",
                "European Union",
                "India",
                "Russia",
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
                if year in st.session_state.wheat_data[country]:
                    values.append(st.session_state.wheat_data[country][year])
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
        if len(display_years) > 1:
            fig.add_vline(
                x=len(display_years) - 1.5,
                line_dash="dot",
                line_color="gray",
                annotation_text="Historical | Projection",
                annotation_position="top",
            )

        st.plotly_chart(fig, use_container_width=True)

    # Change analysis - filtered to allowed countries
    filtered_data = {
        k: v for k, v in st.session_state.wheat_data.items() if k in ALLOWED_COUNTRIES
    }
    create_change_visualization(filtered_data, "Production", exclude=["WORLD"])

with tab4:
    st.header("Data Export & Import")

    # Export options
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Export Current Data")

        # Filter data for export
        export_wheat_data = {
            country: data
            for country, data in st.session_state.wheat_data.items()
            if country in ALLOWED_COUNTRIES
        }

        # Export data
        export_data = {
            "wheat_production_data": export_wheat_data,
            "metadata": st.session_state.production_projection_metadata,
            "current_config": st.session_state.current_config,
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
        df_export = pd.DataFrame(export_wheat_data).T
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
                        # Filter imported data to allowed countries
                        filtered_data = {
                            country: data
                            for country, data in uploaded_data[
                                "wheat_production_data"
                            ].items()
                            if country in ALLOWED_COUNTRIES
                        }
                        st.session_state.wheat_data = filtered_data

                    if "metadata" in uploaded_data:
                        st.session_state.production_projection_metadata = uploaded_data[
                            "metadata"
                        ]

                    if "current_config" in uploaded_data:
                        st.session_state.current_config = uploaded_data[
                            "current_config"
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
