import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from helpers.database_helper import WheatProductionDB
from helpers.common_functions import (
    format_change, 
    create_status_indicators,
    create_projection_dates_sidebar,
    create_change_visualization,
    style_change_column
)

# Page configuration
st.set_page_config(
    page_title="Wheat Exports Dashboard",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database
@st.cache_resource
def get_database():
    """Initialize and return database instance"""
    if not os.path.exists("wheat_production.db"):
        st.error("❌ Database not found. Please run 'python database_setup.py' first to create the database.")
        return None
    return WheatProductionDB()

# Load export data from database
@st.cache_data
def load_export_data():
    """Load export data from database"""
    db = get_database()
    if not db:
        return None, None
    
    try:
        # Get export data
        export_data = db.get_all_export_data()
        
        # Get metadata
        metadata = db.get_metadata()
        projection_metadata = {
            "last_updated": metadata.get("export_last_updated", "19 Sept'24"),
            "next_update": metadata.get("export_next_update", "17 Oct'24")
        }
        
        return export_data, projection_metadata
    except Exception as e:
        st.error(f"❌ Error loading export data from database: {e}")
        return None, None

# Initialize session state
def initialize_session_state():
    """Initialize session state with database data"""
    if 'export_data_loaded' not in st.session_state:
        export_data, projection_metadata = load_export_data()
        
        if export_data and projection_metadata:
            st.session_state.export_data = export_data
            st.session_state.export_projection_metadata = projection_metadata
            st.session_state.export_data_loaded = True
        else:
            # Fallback to sample data if database is not available
            st.session_state.export_data = {
                "Argentina": {
                    "2021/2022": 14.5, "2021/2022_pct": 7.3,
                    "2022/2023": 5.5, "2022/2023_change": -9.0,
                    "2023/2024": 12.5, "2023/2024_change": 7.0,
                    "2024/2025": 12.5, "2024/2025_change": 0.0
                },
                "Australia": {
                    "2021/2022": 27.5, "2021/2022_pct": 13.9,
                    "2022/2023": 31.9, "2022/2023_change": 4.4,
                    "2023/2024": 18.0, "2023/2024_change": -13.9,
                    "2024/2025": 24.0, "2024/2025_change": 6.0
                },
                "Canada": {
                    "2021/2022": 15.4, "2021/2022_pct": 7.8,
                    "2022/2023": 25.1, "2022/2023_change": 9.7,
                    "2023/2024": 24.0, "2023/2024_change": -1.1,
                    "2024/2025": 24.5, "2024/2025_change": 0.5
                },
                "European Union": {
                    "2021/2022": 37.5, "2021/2022_pct": 18.9,
                    "2022/2023": 34.6, "2022/2023_change": -2.9,
                    "2023/2024": 35.0, "2023/2024_change": 0.4,
                    "2024/2025": 30.0, "2024/2025_change": -5.0
                },
                "Russia": {
                    "2021/2022": 32.1, "2021/2022_pct": 16.2,
                    "2022/2023": 45.5, "2022/2023_change": 13.4,
                    "2023/2024": 51.0, "2023/2024_change": 5.5,
                    "2024/2025": 48.0, "2024/2025_change": -3.0
                },
                "Ukraine": {
                    "2021/2022": 19.0, "2021/2022_pct": 9.6,
                    "2022/2023": 10.0, "2022/2023_change": -9.0,
                    "2023/2024": 16.5, "2023/2024_change": 6.5,
                    "2024/2025": 16.0, "2024/2025_change": -0.5
                },
                "United States": {
                    "2021/2022": 21.8, "2021/2022_pct": 11.0,
                    "2022/2023": 21.5, "2022/2023_change": -0.3,
                    "2023/2024": 21.1, "2023/2024_change": -0.4,
                    "2024/2025": 21.8, "2024/2025_change": 0.7
                },
                "TOTAL MAJOR EXPORTERS": {
                    "2021/2022": 167.8, "2021/2022_pct": 84.6,
                    "2022/2023": 184.1, "2022/2023_change": 16.3,
                    "2023/2024": 182.1, "2023/2024_change": -2.0,
                    "2024/2025": 176.8, "2024/2025_change": -5.3
                }
            }
            st.session_state.export_projection_metadata = {
                "last_updated": "19 Sept'24",
                "next_update": "17 Oct'24"
            }
            st.session_state.export_data_loaded = False

# Initialize session state
initialize_session_state()

# Title and header
st.title("📦 Wheat Exports Dashboard")
st.markdown("### Major Wheat Exporters Data Management")

# Database status indicator
if st.session_state.export_data_loaded:
    st.sidebar.success("🗄️ Connected to Database")
else:
    st.sidebar.warning("⚠️ Using Local Data (No Database)")

# Sidebar for data management
create_projection_dates_sidebar(
    st.session_state.export_projection_metadata,
    "export_last_updated",
    "export_next_update"
)

# Main content area
tab1, tab2, tab3, tab4 = st.tabs(["📈 Data Overview", "✏️ Edit Projections", "📊 Visualizations", "💾 Data Export"])

with tab1:
    st.header("Global Wheat Exports")
    
    # Display status indicators
    create_status_indicators()
    
    # Display projection dates
    st.markdown(f"**Projection Dates**: {st.session_state.export_projection_metadata['last_updated']} | {st.session_state.export_projection_metadata['next_update']}")
    
    st.markdown("---")
    
    # Create enhanced table
    st.markdown("### Export Data (Million Metric Tons)")
    
    # Create the data table with proper formatting
    table_data = []
    for country, data in st.session_state.export_data.items():
        row = {
            "Country": country,
            "2021/2022": f"{data['2021/2022']:.1f}",
            "% World": f"{data['2021/2022_pct']:.1f}%" if data.get('2021/2022_pct') is not None else "-",
            "2022/2023": f"{data['2022/2023']:.1f}",
            "Change": format_change(data.get('2022/2023_change')),
            "2023/2024": f"{data['2023/2024']:.1f}",
            "Change ": format_change(data.get('2023/2024_change')),
            "2024/2025": f"{data['2024/2025']:.1f}",
            "Change  ": format_change(data.get('2024/2025_change'))
        }
        table_data.append(row)
    
    df_display = pd.DataFrame(table_data)
    
    # Apply styling to the dataframe
    styled_df = df_display.style.map(
        style_change_column, 
        subset=['Change', 'Change ', 'Change  ']
    ).set_properties(**{
        'text-align': 'center'
    }).set_properties(**{
        'text-align': 'left'
    }, subset=['Country'])
    
    st.dataframe(
        styled_df,
        use_container_width=True,
        hide_index=True
    )
    
    # Summary statistics
    st.markdown("### Summary Statistics")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_exports = st.session_state.export_data.get('TOTAL MAJOR EXPORTERS', {}).get('2024/2025', 0)
        st.metric("Total Major Exports 2024/2025", f"{total_exports:.1f} Mt")
    
    with col2:
        total_change = st.session_state.export_data.get('TOTAL MAJOR EXPORTERS', {}).get('2024/2025_change', 0)
        st.metric("Change from 2023/2024", f"{total_change:+.1f} Mt")
    
    with col3:
        # Find top exporter (excluding TOTAL)
        countries_only = {k: v for k, v in st.session_state.export_data.items() if k != "TOTAL MAJOR EXPORTERS"}
        if countries_only:
            top_exporter = max(countries_only.items(), key=lambda x: x[1]['2024/2025'])
            st.metric("Top Exporter 2024/2025", top_exporter[0])
    
    with col4:
        if countries_only:
            top_export = top_exporter[1]['2024/2025']
            st.metric("Top Export Volume", f"{top_export:.1f} Mt")

with tab2:
    st.header("Edit 2024/2025 Export Projections")
    st.markdown("**Note:** Historical data (2021/2022 - 2023/2024) is static and cannot be modified.")
    
    # Create form for editing projections
    with st.form("export_projection_form"):
        st.markdown("### Update Export Projections and Changes")
        
        # Create input fields for each country
        updated_values = {}
        updated_changes = {}
        
        for country in st.session_state.export_data.keys():
            if country == "TOTAL MAJOR EXPORTERS":
                continue  # Skip total as it should be calculated
                
            current_value = st.session_state.export_data[country]["2024/2025"]
            current_change = st.session_state.export_data[country].get("2024/2025_change", 0)
            
            # Show historical trend
            historical_values = [
                st.session_state.export_data[country]["2021/2022"],
                st.session_state.export_data[country]["2022/2023"],
                st.session_state.export_data[country]["2023/2024"]
            ]
            
            st.subheader(f"{country}")
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                updated_values[country] = st.number_input(
                    f"Exports (Mt)",
                    value=float(current_value),
                    min_value=0.0,
                    step=0.1,
                    format="%.1f",
                    key=f"export_{country}",
                    help=f"Historical: {historical_values[0]:.1f} → {historical_values[1]:.1f} → {historical_values[2]:.1f}"
                )
            
            with col2:
                updated_changes[country] = st.number_input(
                    f"Change from 2023/2024",
                    value=float(current_change),
                    step=0.1,
                    format="%.1f",
                    key=f"export_change_{country}",
                    help="Positive for increase, negative for decrease"
                )
            
            with col3:
                # Calculate and display automatic change
                auto_change = updated_values[country] - st.session_state.export_data[country]["2023/2024"]
                if auto_change > 0:
                    st.success(f"Auto: +{auto_change:.1f}")
                elif auto_change < 0:
                    st.error(f"Auto: {auto_change:.1f}")
                else:
                    st.info("Auto: 0.0")
        
        # Submit button
        if st.form_submit_button("Update Export Projections", type="primary"):
            # Update the data
            db = get_database()
            
            # Update individual countries
            for country, value in updated_values.items():
                st.session_state.export_data[country]["2024/2025"] = value
                st.session_state.export_data[country]["2024/2025_change"] = updated_changes[country]
                
                # Save to database
                if db:
                    db.update_export_value(country, "2024/2025", value, updated_changes[country])
            
            # Calculate and update total
            total_exports = sum(updated_values.values())
            total_change = sum(updated_changes.values())
            
            st.session_state.export_data["TOTAL MAJOR EXPORTERS"]["2024/2025"] = total_exports
            st.session_state.export_data["TOTAL MAJOR EXPORTERS"]["2024/2025_change"] = total_change
            
            if db:
                db.update_export_value("TOTAL MAJOR EXPORTERS", "2024/2025", total_exports, total_change)
            
            st.success("✅ Export projections updated successfully!")
            if db:
                st.info("💾 Changes saved to database")
            st.rerun()

with tab3:
    st.header("Export Visualizations")
    
    # Time series plot
    st.subheader("Export Trends Over Time")
    
    # Select countries to display
    countries_to_plot = st.multiselect(
        "Select countries to display:",
        options=[c for c in st.session_state.export_data.keys() if c != "TOTAL MAJOR EXPORTERS"],
        default=["Russia", "European Union", "Australia", "Canada", "United States"]
    )
    
    if countries_to_plot:
        # Create time series plot
        fig = go.Figure()
        
        years = ["2021/2022", "2022/2023", "2023/2024", "2024/2025"]
        
        for country in countries_to_plot:
            values = [st.session_state.export_data[country][year] for year in years]
            
            fig.add_trace(go.Scatter(
                x=years,
                y=values,
                mode='lines+markers',
                name=country,
                hovertemplate=f'<b>{country}</b><br>' +
                             'Year: %{x}<br>' +
                             'Exports: %{y:.1f} Mt<extra></extra>'
            ))
        
        # Add total line if requested
        if st.checkbox("Show Total Major Exporters"):
            total_values = [st.session_state.export_data["TOTAL MAJOR EXPORTERS"][year] for year in years]
            fig.add_trace(go.Scatter(
                x=years,
                y=total_values,
                mode='lines+markers',
                name="TOTAL MAJOR EXPORTERS",
                line=dict(dash='dash', width=3),
                hovertemplate='<b>TOTAL</b><br>' +
                             'Year: %{x}<br>' +
                             'Exports: %{y:.1f} Mt<extra></extra>'
            ))
        
        fig.update_layout(
            title="Wheat Export Trends by Major Exporters",
            xaxis_title="Year",
            yaxis_title="Exports (Million Metric Tons)",
            hovermode='x unified',
            height=500
        )
        
        # Add vertical line to separate historical from projection
        fig.add_vline(x=2.5, line_dash="dot", line_color="gray", 
                     annotation_text="Historical | Projection", 
                     annotation_position="top")
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Market share visualization
    st.subheader("Export Market Share (2024/2025)")
    
    # Prepare data for pie chart
    countries_only = {k: v for k, v in st.session_state.export_data.items() if k != "TOTAL MAJOR EXPORTERS"}
    
    fig_pie = go.Figure(data=[go.Pie(
        labels=list(countries_only.keys()),
        values=[data["2024/2025"] for data in countries_only.values()],
        hovertemplate='<b>%{label}</b><br>' +
                     'Exports: %{value:.1f} Mt<br>' +
                     'Share: %{percent}<extra></extra>'
    )])
    
    fig_pie.update_layout(
        title="Export Market Share - 2024/2025 Projection",
        height=500
    )
    
    st.plotly_chart(fig_pie, use_container_width=True)
    
    # Change analysis
    create_change_visualization(st.session_state.export_data, "Exports", exclude=["TOTAL MAJOR EXPORTERS"])

with tab4:
    st.header("Export Data Management")
    
    # Export options
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Export Current Data")
        
        # Prepare export data
        export_data = {
            "wheat_export_data": st.session_state.export_data,
            "metadata": st.session_state.export_projection_metadata,
            "export_timestamp": datetime.now().isoformat(),
            "data_source": "database" if st.session_state.export_data_loaded else "local"
        }
        
        # JSON export
        import json
        st.download_button(
            label="📥 Download Export Data as JSON",
            data=json.dumps(export_data, indent=2),
            file_name=f"wheat_export_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )
        
        # CSV export
        df_export = pd.DataFrame(st.session_state.export_data).T
        csv_data = df_export.to_csv()
        st.download_button(
            label="📥 Download Export Data as CSV",
            data=csv_data,
            file_name=f"wheat_export_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    
    with col2:
        st.subheader("Import Data")
        
        uploaded_file = st.file_uploader("Upload JSON export data file", type=['json'])
        
        if uploaded_file is not None:
            try:
                uploaded_data = json.load(uploaded_file)
                
                if st.button("Import Export Data"):
                    if "wheat_export_data" in uploaded_data:
                        st.session_state.export_data = uploaded_data["wheat_export_data"]
                    
                    if "metadata" in uploaded_data:
                        st.session_state.export_projection_metadata = uploaded_data["metadata"]
                    
                    st.success("Export data imported successfully!")
                    st.rerun()
                    
            except json.JSONDecodeError:
                st.error("Invalid JSON file format")

# Footer
st.markdown("---")
status_text = "🗄️ Database Connected" if st.session_state.export_data_loaded else "💾 Local Data Mode"
st.markdown(
    f"""
    <div style='text-align: center; color: #666; font-size: 0.8em;'>
    📦 Wheat Exports Dashboard | {status_text} | Major Exporters Analysis
    </div>
    """,
    unsafe_allow_html=True
)