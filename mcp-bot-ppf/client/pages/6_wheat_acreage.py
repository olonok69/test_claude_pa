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

# Add return to main button in sidebar
with st.sidebar:
    if st.button(
        "🏠 Return to Main Dashboard", use_container_width=True, type="primary"
    ):
        st.switch_page("app.py")

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


# Load acreage data from database
@st.cache_data
def load_acreage_data():
    """Load acreage data from database"""
    db = get_database()
    if not db:
        return None, None

    try:
        # Get acreage data
        acreage_data = db.get_all_acreage_data()

        # Get metadata
        metadata = db.get_metadata()
        projection_metadata = {
            "last_updated": metadata.get("acreage_last_updated", "19 Sept'24"),
            "next_update": metadata.get("acreage_next_update", "17 Oct'24"),
        }

        return acreage_data, projection_metadata
    except Exception as e:
        st.error(f"❌ Error loading acreage data from database: {e}")
        return None, None


# Initialize session state
def initialize_session_state():
    """Initialize session state with database data"""
    if "acreage_data_loaded" not in st.session_state:
        acreage_data, projection_metadata = load_acreage_data()

        if acreage_data and projection_metadata:
            st.session_state.acreage_data = acreage_data
            st.session_state.acreage_projection_metadata = projection_metadata
            st.session_state.acreage_data_loaded = True
        else:
            # Fallback to sample data if database is not available
            st.session_state.acreage_data = {
                "WORLD": {
                    "2021/2022": 220.8,
                    "2021/2022_pct": None,
                    "2021/2022_yield": 3.53,
                    "2022/2023": 224.79,
                    "2022/2023_change": 3.99,
                    "2022/2023_yield": 3.58,
                    "2023/2024": 228.18,
                    "2023/2024_change": 3.39,
                    "2023/2024_yield": 3.48,
                    "2024/2025": 226.5,
                    "2024/2025_change": -1.68,
                    "2024/2025_yield": 3.52,
                }
            }
            st.session_state.acreage_projection_metadata = {
                "last_updated": "19 Sept'24",
                "next_update": "17 Oct'24",
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

# Sidebar for data management
create_projection_dates_sidebar(
    st.session_state.acreage_projection_metadata,
    "acreage_last_updated",
    "acreage_next_update",
)

# Main content area
tab1, tab2, tab3, tab4, tab5 = st.tabs(
    [
        "📈 Data Overview",
        "✏️ Edit Projections",
        "📊 Visualizations",
        "🌱 Yield Analysis",
        "💾 Data Export",
    ]
)

with tab1:
    st.header("Global Wheat Acreage (Area Harvested)")

    # Display status indicators
    create_status_indicators()

    # Display projection dates
    st.markdown(
        f"**Projection Dates**: {st.session_state.acreage_projection_metadata['last_updated']} | {st.session_state.acreage_projection_metadata['next_update']}"
    )

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

    # Create the data table with proper formatting
    table_data = []
    for country, data in st.session_state.acreage_data.items():
        # Get yield for 2024/2025
        yield_2024 = data.get("2024/2025_yield", 0)

        row = {
            "Country/Region": country,
            "2021/2022": f"{data['2021/2022']:.2f}",
            "% World": (
                f"{data['2021/2022_pct']:.1f}%"
                if data.get("2021/2022_pct") is not None
                else "-"
            ),
            "2022/2023": f"{data['2022/2023']:.2f}",
            "Change": format_change(data.get("2022/2023_change")),
            "2023/2024": f"{data['2023/2024']:.2f}",
            "Change ": format_change(data.get("2023/2024_change")),
            "2024/2025": f"{data['2024/2025']:.2f}",
            "Change  ": format_change(data.get("2024/2025_change")),
            "Yield (t/ha)": f"{yield_2024:.2f}" if yield_2024 > 0 else "-",
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
        world_acreage = st.session_state.acreage_data.get("WORLD", {}).get(
            "2024/2025", 0
        )
        st.metric("Global Acreage 2024/2025", f"{world_acreage:.1f} Mha")

    with col2:
        world_change = st.session_state.acreage_data.get("WORLD", {}).get(
            "2024/2025_change", 0
        )
        st.metric("Change from 2023/2024", f"{world_change:+.1f} Mha")

    with col3:
        # Average yield
        world_yield = st.session_state.acreage_data.get("WORLD", {}).get(
            "2024/2025_yield", 0
        )
        st.metric("Global Avg Yield", f"{world_yield:.2f} t/ha")

    with col4:
        # Top country by acreage (excluding WORLD and Others)
        countries_only = {
            k: v
            for k, v in st.session_state.acreage_data.items()
            if k not in ["WORLD", "Others"]
        }
        if countries_only:
            top_country = max(countries_only.items(), key=lambda x: x[1]["2024/2025"])
            st.metric(
                "Largest Area",
                f"{top_country[0]}: {top_country[1]['2024/2025']:.1f} Mha",
            )

with tab2:
    st.header("Edit 2024/2025 Acreage Projections")
    st.markdown(
        "**Note:** Historical data (2021/2022 - 2023/2024) is static and cannot be modified."
    )

    # Create form for editing projections
    with st.form("acreage_projection_form"):
        st.markdown("### Update Acreage Projections and Yields")

        # Create input fields for each country
        updated_values = {}
        updated_changes = {}
        updated_yields = {}

        for country in st.session_state.acreage_data.keys():
            if country == "Others":
                continue  # Skip others as it should be calculated

            current_value = st.session_state.acreage_data[country]["2024/2025"]
            current_change = st.session_state.acreage_data[country].get(
                "2024/2025_change", 0
            )
            current_yield = st.session_state.acreage_data[country].get(
                "2024/2025_yield", 0
            )

            # Show historical trend
            historical_values = [
                st.session_state.acreage_data[country]["2021/2022"],
                st.session_state.acreage_data[country]["2022/2023"],
                st.session_state.acreage_data[country]["2023/2024"],
            ]

            st.subheader(f"{country}")
            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

            with col1:
                updated_values[country] = st.number_input(
                    f"Acreage (Mha)",
                    value=float(current_value),
                    min_value=0.0,
                    step=0.1,
                    format="%.2f",
                    key=f"acreage_{country}",
                    help=f"Historical: {historical_values[0]:.2f} → {historical_values[1]:.2f} → {historical_values[2]:.2f}",
                )

            with col2:
                updated_changes[country] = st.number_input(
                    f"Change from 2023/2024",
                    value=float(current_change),
                    step=0.1,
                    format="%.2f",
                    key=f"acreage_change_{country}",
                    help="Positive for increase, negative for decrease",
                )

            with col3:
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

            with col4:
                # Calculate and display automatic change
                auto_change = (
                    updated_values[country]
                    - st.session_state.acreage_data[country]["2023/2024"]
                )
                if auto_change > 0:
                    st.success(f"Auto: +{auto_change:.2f}")
                elif auto_change < 0:
                    st.error(f"Auto: {auto_change:.2f}")
                else:
                    st.info("Auto: 0.00")

        # Submit button
        if st.form_submit_button("Update Acreage Projections", type="primary"):
            # Update the data
            db = get_database()

            for country, value in updated_values.items():
                st.session_state.acreage_data[country]["2024/2025"] = value
                st.session_state.acreage_data[country]["2024/2025_change"] = (
                    updated_changes[country]
                )
                st.session_state.acreage_data[country]["2024/2025_yield"] = (
                    updated_yields[country]
                )

                # Save to database
                if db:
                    db.update_acreage_value(
                        country,
                        "2024/2025",
                        value,
                        updated_changes[country],
                        updated_yields[country],
                    )

            st.success("✅ Acreage projections updated successfully!")
            if db:
                st.info("💾 Changes saved to database")
            st.rerun()

with tab3:
    st.header("Acreage Visualizations")

    # Time series plot
    st.subheader("Acreage Trends Over Time")

    # Select countries to display
    countries_to_plot = st.multiselect(
        "Select countries/regions to display:",
        options=[
            c for c in st.session_state.acreage_data.keys() if c not in ["Others"]
        ],
        default=[
            "WORLD",
            "India",
            "Russia",
            "China",
            "European Union 27 (FR, DE)",
            "United States",
        ],
    )

    if countries_to_plot:
        # Create time series plot
        fig = go.Figure()

        years = ["2021/2022", "2022/2023", "2023/2024", "2024/2025"]

        for country in countries_to_plot:
            values = [st.session_state.acreage_data[country][year] for year in years]

            fig.add_trace(
                go.Scatter(
                    x=years,
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
        fig.add_vline(
            x=2.5,
            line_dash="dot",
            line_color="gray",
            annotation_text="Historical | Projection",
            annotation_position="top",
        )

        st.plotly_chart(fig, use_container_width=True)

    # Top countries by acreage
    st.subheader("Top 10 Countries by Wheat Acreage (2024/2025)")

    # Get top 10 countries
    countries_only = {
        k: v
        for k, v in st.session_state.acreage_data.items()
        if k not in ["WORLD", "Others"]
    }
    top_countries = sorted(
        countries_only.items(), key=lambda x: x[1]["2024/2025"], reverse=True
    )[:10]

    fig_bar = go.Figure(
        data=[
            go.Bar(
                x=[country for country, _ in top_countries],
                y=[data["2024/2025"] for _, data in top_countries],
                text=[f"{data['2024/2025']:.1f}" for _, data in top_countries],
                textposition="auto",
                marker_color="darkgreen",
                hovertemplate="<b>%{x}</b><br>"
                + "Acreage: %{y:.2f} Mha<br>"
                + "Share: %{text}<extra></extra>",
            )
        ]
    )

    fig_bar.update_layout(
        title="Top 10 Wheat Growing Countries by Area - 2024/2025",
        xaxis_title="Country",
        yaxis_title="Area Harvested (Million Hectares)",
        height=400,
    )

    st.plotly_chart(fig_bar, use_container_width=True)

    # Change analysis
    create_change_visualization(
        st.session_state.acreage_data, "Acreage", exclude=["WORLD", "Others"]
    )

with tab4:
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

    # Yield comparison chart
    st.subheader("Yield Comparison by Country (2024/2025)")

    # Get yield data
    yield_data = []
    for country, data in st.session_state.acreage_data.items():
        if country not in ["WORLD", "Others"] and data.get("2024/2025_yield"):
            yield_data.append(
                {
                    "Country": country,
                    "Yield": data["2024/2025_yield"],
                    "Acreage": data["2024/2025"],
                }
            )

    df_yield = pd.DataFrame(yield_data)
    df_yield = df_yield.sort_values("Yield", ascending=False)

    # Create yield bar chart
    fig_yield = px.bar(
        df_yield,
        x="Country",
        y="Yield",
        title="Wheat Yields by Country - 2024/2025",
        color="Yield",
        color_continuous_scale="Greens",
    )

    fig_yield.update_layout(
        xaxis_title="Country", yaxis_title="Yield (tonnes per hectare)", height=400
    )

    # Add world average line
    world_yield = st.session_state.acreage_data.get("WORLD", {}).get(
        "2024/2025_yield", 3.52
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
        title="Wheat Acreage vs Yield (2024/2025)",
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

with tab5:
    st.header("Acreage Data Management")

    # Export options
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Export Current Data")

        # Prepare export data
        export_data = {
            "wheat_acreage_data": st.session_state.acreage_data,
            "metadata": st.session_state.acreage_projection_metadata,
            "export_timestamp": datetime.now().isoformat(),
            "data_source": (
                "database" if st.session_state.acreage_data_loaded else "local"
            ),
        }

        # JSON export
        st.download_button(
            label="📥 Download Acreage Data as JSON",
            data=json.dumps(export_data, indent=2),
            file_name=f"wheat_acreage_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
        )

        # CSV export
        df_export = pd.DataFrame(st.session_state.acreage_data).T
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
                        st.session_state.acreage_data = uploaded_data[
                            "wheat_acreage_data"
                        ]

                    if "metadata" in uploaded_data:
                        st.session_state.acreage_projection_metadata = uploaded_data[
                            "metadata"
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
st.markdown(
    f"""
    <div style='text-align: center; color: #666; font-size: 0.8em;'>
    🌾 Wheat Acreage Dashboard | {status_text} | Area Harvested & Yield Analysis
    </div>
    """,
    unsafe_allow_html=True,
)
