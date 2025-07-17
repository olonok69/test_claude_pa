import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from .database_helper import CornProductionDB
import json


def format_change(value):
    """Format change values with appropriate sign and parentheses"""
    if value is None or pd.isna(value):
        return ""
    if value >= 0:
        return f"+{value:.1f}"
    else:
        return f"({abs(value):.1f})"


def style_change_column(val):
    """Style function for change columns in dataframes"""
    if pd.isna(val) or val == "-" or val == "":
        return ""
    try:
        if "(" in str(val) and ")" in str(val):
            return "color: red; font-weight: bold"
        elif "+" in str(val):
            return "color: green; font-weight: bold"
        else:
            return ""
    except:
        return ""


def create_status_indicators():
    """Create status indicators for years"""
    st.markdown("### Status Information")
    status_cols = st.columns(4)
    with status_cols[0]:
        st.info("**2022/2023**: actual")
    with status_cols[1]:
        st.info("**2023/2024**: actual")
    with status_cols[2]:
        st.warning("**2024/2025**: estimate")
    with status_cols[3]:
        st.success("**2025/2026**: projection")


def create_projection_dates_sidebar(
    projection_metadata, last_updated_key, next_update_key
):
    """Create sidebar section for projection dates management"""
    st.sidebar.header("📊 Data Management")
    st.sidebar.markdown("**Projection Dates**")

    col1, col2 = st.sidebar.columns(2)
    with col1:
        last_updated = st.text_input(
            "Last Updated",
            value=projection_metadata["last_updated"],
            help="Format: DD MMM'YY",
        )
    with col2:
        next_update = st.text_input(
            "Next Update",
            value=projection_metadata["next_update"],
            help="Format: DD MMM'YY",
        )

    # Update dates
    if st.sidebar.button("Update Dates"):
        projection_metadata["last_updated"] = last_updated
        projection_metadata["next_update"] = next_update

        # Save to database
        db = CornProductionDB()
        db.update_metadata(last_updated_key, last_updated)
        db.update_metadata(next_update_key, next_update)

        st.sidebar.success("Dates updated successfully!")
        st.rerun()

    # Database management section
    st.sidebar.markdown("---")
    st.sidebar.header("🗄️ Database Management")

    if st.sidebar.button("🔄 Refresh Data from DB"):
        st.cache_data.clear()
        st.rerun()


def create_change_visualization(data, data_type="Production", exclude=None):
    """Create change visualization for production or export data"""
    st.subheader(f"{data_type} Changes Analysis")

    # Filter out excluded items
    if exclude:
        filtered_data = {k: v for k, v in data.items() if k not in exclude}
    else:
        filtered_data = data

    change_data = []
    for country, values in filtered_data.items():
        change_data.append(
            {
                "Country": country,
                "2023/2024 Change": values.get("2023/2024_change", 0),
                "2024/2025 Change": values.get("2024/2025_change", 0),
                "2025/2026 Change": values.get("2025/2026_change", 0),
            }
        )

    df_changes = pd.DataFrame(change_data)

    # Create grouped bar chart for changes
    fig_changes = go.Figure()

    years = ["2023/2024 Change", "2024/2025 Change", "2025/2026 Change"]
    colors = ["#1f77b4", "#ff7f0e", "#2ca02c"]

    for i, year in enumerate(years):
        fig_changes.add_trace(
            go.Bar(
                name=year,
                x=df_changes["Country"],
                y=df_changes[year],
                marker_color=colors[i],
                hovertemplate=f"<b>%{{x}}</b><br>{year}: %{{y:.1f}} Mt<extra></extra>",
            )
        )

    fig_changes.update_layout(
        title=f"{data_type} Changes by Country",
        xaxis_title="Country/Region",
        yaxis_title="Change (Million Metric Tons)",
        barmode="group",
        height=400,
    )

    # Add horizontal line at y=0
    fig_changes.add_hline(y=0, line_dash="dash", line_color="gray")

    st.plotly_chart(fig_changes, use_container_width=True)


def export_data_to_json(data, metadata, data_type):
    """Export data to JSON format"""
    from datetime import datetime

    export_data = {
        f"{data_type}_data": data,
        "metadata": metadata,
        "export_timestamp": datetime.now().isoformat(),
    }

    return json.dumps(export_data, indent=2)


def import_data_from_json(uploaded_file, data_key, metadata_key=None):
    """Import data from JSON file"""
    try:
        uploaded_data = json.load(uploaded_file)

        data = uploaded_data.get(data_key, None)
        metadata = uploaded_data.get(metadata_key, None) if metadata_key else None

        return data, metadata
    except json.JSONDecodeError:
        return None, None


def calculate_percentage_of_world(country_value, world_total):
    """Calculate percentage of world total"""
    if world_total > 0:
        return (country_value / world_total) * 100
    return 0


def validate_projection_data(value, historical_data):
    """Validate projection data against historical trends"""
    if not historical_data:
        return True, "No historical data available"

    avg_historical = sum(historical_data) / len(historical_data)
    deviation = abs(value - avg_historical) / avg_historical

    if deviation > 0.5:  # More than 50% deviation
        return (
            False,
            f"Value deviates significantly from historical average ({avg_historical:.1f})",
        )

    return True, "Valid"


def create_summary_statistics_card(title, value, change=None, icon=None):
    """Create a styled summary statistics card"""
    if icon:
        title = f"{icon} {title}"

    if change is not None:
        change_color = "green" if change >= 0 else "red"
        change_icon = "↑" if change >= 0 else "↓"

        st.markdown(
            f"""
            <div style='background-color: #f0f2f6; padding: 20px; border-radius: 10px; text-align: center;'>
                <h4 style='margin: 0; color: #333;'>{title}</h4>
                <h2 style='margin: 10px 0; color: #1f77b4;'>{value}</h2>
                <p style='margin: 0; color: {change_color};'>{change_icon} {abs(change):.1f} Mt</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"""
            <div style='background-color: #f0f2f6; padding: 20px; border-radius: 10px; text-align: center;'>
                <h4 style='margin: 0; color: #333;'>{title}</h4>
                <h2 style='margin: 10px 0; color: #1f77b4;'>{value}</h2>
            </div>
            """,
            unsafe_allow_html=True,
        )


def format_number_with_commas(number):
    """Format number with thousand separators"""
    return f"{number:,.1f}"


def get_trend_indicator(current, previous):
    """Get trend indicator based on current and previous values"""
    if current > previous:
        return "📈", "increasing"
    elif current < previous:
        return "📉", "decreasing"
    else:
        return "➡️", "stable"
