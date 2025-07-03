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

from helpers.database_helper import WheatProductionDB
from helpers.common_functions import (
    format_change, 
    create_status_indicators,
    create_projection_dates_sidebar,
    style_change_column
)

# Page configuration
st.set_page_config(
    page_title="Stock-to-Use Ratio Dashboard",
    page_icon="📊",
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

# Load S/U ratio data from database
@st.cache_data
def load_su_ratio_data():
    """Load stock-to-use ratio data from database"""
    db = get_database()
    if not db:
        return None, None
    
    try:
        # Get S/U ratio data
        su_data = db.get_all_su_ratio_data()
        
        # Get metadata
        metadata = db.get_metadata()
        projection_metadata = {
            "last_updated": metadata.get("su_ratio_last_updated", "19 Sept'24"),
            "next_update": metadata.get("su_ratio_next_update", "17 Oct'24")
        }
        
        return su_data, projection_metadata
    except Exception as e:
        st.error(f"❌ Error loading S/U ratio data from database: {e}")
        return None, None

# Initialize session state
def initialize_session_state():
    """Initialize session state with database data"""
    if 'su_ratio_data_loaded' not in st.session_state:
        su_data, projection_metadata = load_su_ratio_data()
        
        if su_data and projection_metadata:
            st.session_state.su_ratio_data = su_data
            st.session_state.su_ratio_projection_metadata = projection_metadata
            st.session_state.su_ratio_data_loaded = True
        else:
            # Fallback to sample data if database is not available
            st.session_state.su_ratio_data = {
                "WORLD": {
                    "2021/2022": 35.0, "2021/2022_category": "Comfortable",
                    "2022/2023": 35.7, "2022/2023_change": 0.7, "2022/2023_category": "Comfortable",
                    "2023/2024": 33.7, "2023/2024_change": -2.0, "2023/2024_category": "Comfortable",
                    "2024/2025": 33.2, "2024/2025_change": -0.5, "2024/2025_category": "Comfortable"
                },
                "China": {
                    "2021/2022": 93.7, "2021/2022_category": "Strategic Reserve",
                    "2022/2023": 98.2, "2022/2023_change": 4.5, "2022/2023_category": "Strategic Reserve",
                    "2023/2024": 93.5, "2023/2024_change": -4.7, "2023/2024_category": "Strategic Reserve",
                    "2024/2025": 97.3, "2024/2025_change": 3.8, "2024/2025_category": "Strategic Reserve"
                }
            }
            st.session_state.su_ratio_projection_metadata = {
                "last_updated": "19 Sept'24",
                "next_update": "17 Oct'24"
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

# Sidebar for data management
create_projection_dates_sidebar(
    st.session_state.su_ratio_projection_metadata,
    "su_ratio_last_updated",
    "su_ratio_next_update"
)

# Main content area
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📈 Overview", "✏️ Edit Projections", "📊 Analysis", "🌍 Regional Insights", "💾 Data Export"])

with tab1:
    st.header("Global Stock-to-Use Ratios")
    
    # Display status indicators
    create_status_indicators()
    
    # Display projection dates
    st.markdown(f"**Projection Dates**: {st.session_state.su_ratio_projection_metadata['last_updated']} | {st.session_state.su_ratio_projection_metadata['next_update']}")
    
    st.markdown("---")
    
    # Key insights and explanation
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.info("""
        **Stock-to-Use (S/U) Ratio** measures ending stocks as a percentage of total consumption.
        It's a critical indicator of market supply security and price volatility risk.
        
        The ratio helps assess whether markets are:
        - **Well-supplied** (high ratio) → Lower price volatility
        - **Tight** (low ratio) → Higher price volatility risk
        """)
    
    with col2:
        st.markdown("### Category Thresholds")
        st.markdown("""
        - 🟢 **Strategic Reserve**: ≥50%
        - 🔵 **Comfortable**: 30-50%
        - 🟡 **Adequate**: 20-30%
        - 🟠 **Tight**: 10-20%
        - 🔴 **Critical**: <10%
        """)
    
    # Create enhanced table
    st.markdown("### Stock-to-Use Ratio Data (%)")
    
    # Create the data table with proper formatting
    table_data = []
    for country, data in st.session_state.su_ratio_data.items():
        # Get current category
        current_category = data.get('2024/2025_category', 'Unknown')
        
        # Emoji based on category
        category_emoji = {
            "Strategic Reserve": "🟢",
            "Comfortable": "🔵",
            "Adequate": "🟡",
            "Tight": "🟠",
            "Critical": "🔴"
        }.get(current_category, "⚪")
        
        row = {
            "Country/Region": f"{category_emoji} {country}",
            "2021/2022": f"{data['2021/2022']:.1f}%",
            "2022/2023": f"{data['2022/2023']:.1f}%",
            "Change": format_change(data.get('2022/2023_change')),
            "2023/2024": f"{data['2023/2024']:.1f}%",
            "Change ": format_change(data.get('2023/2024_change')),
            "2024/2025": f"{data['2024/2025']:.1f}%",
            "Change  ": format_change(data.get('2024/2025_change')),
            "Category": current_category
        }
        table_data.append(row)
    
    df_display = pd.DataFrame(table_data)
    
    # Apply styling to the dataframe
    def style_category(val):
        """Style function for category column"""
        if val == "Strategic Reserve":
            return 'background-color: #90EE90'
        elif val == "Comfortable":
            return 'background-color: #87CEEB'
        elif val == "Adequate":
            return 'background-color: #F0E68C'
        elif val == "Tight":
            return 'background-color: #FFB366'
        elif val == "Critical":
            return 'background-color: #FFB6C1'
        return ''
    
    styled_df = df_display.style.map(
        style_change_column, 
        subset=['Change', 'Change ', 'Change  ']
    ).map(
        style_category,
        subset=['Category']
    ).set_properties(**{
        'text-align': 'center'
    }).set_properties(**{
        'text-align': 'left'
    }, subset=['Country/Region'])
    
    st.dataframe(
        styled_df,
        use_container_width=True,
        hide_index=True
    )
    
    # Summary statistics
    st.markdown("### Key Metrics")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        world_su = st.session_state.su_ratio_data.get('WORLD', {}).get('2024/2025', 0)
        world_change = st.session_state.su_ratio_data.get('WORLD', {}).get('2024/2025_change', 0)
        st.metric("Global S/U Ratio", f"{world_su:.1f}%", f"{world_change:+.1f}%")
    
    with col2:
        # Count critical countries
        critical_count = sum(1 for country, data in st.session_state.su_ratio_data.items() 
                           if data.get('2024/2025_category') == 'Critical')
        st.metric("Critical Countries", critical_count,
                 help="Countries with S/U ratio below 10%")
    
    with col3:
        # Highest S/U ratio
        max_country = max(st.session_state.su_ratio_data.items(), 
                         key=lambda x: x[1].get('2024/2025', 0))
        st.metric("Highest S/U Ratio", 
                 f"{max_country[0]}: {max_country[1]['2024/2025']:.1f}%")
    
    with col4:
        # Lowest S/U ratio (excluding WORLD)
        countries_only = {k: v for k, v in st.session_state.su_ratio_data.items() if k != "WORLD"}
        min_country = min(countries_only.items(), 
                         key=lambda x: x[1].get('2024/2025', 100))
        st.metric("Lowest S/U Ratio", 
                 f"{min_country[0]}: {min_country[1]['2024/2025']:.1f}%")

with tab2:
    st.header("Edit 2024/2025 S/U Ratio Projections")
    st.markdown("**Note:** Historical data (2021/2022 - 2023/2024) is static and cannot be modified.")
    
    # Create form for editing projections
    with st.form("su_ratio_projection_form"):
        st.markdown("### Update S/U Ratio Projections")
        
        # Create input fields for each country
        updated_values = {}
        updated_changes = {}
        
        for country in st.session_state.su_ratio_data.keys():
            current_value = st.session_state.su_ratio_data[country]["2024/2025"]
            current_change = st.session_state.su_ratio_data[country].get("2024/2025_change", 0)
            
            # Show historical trend
            historical_values = [
                st.session_state.su_ratio_data[country]["2021/2022"],
                st.session_state.su_ratio_data[country]["2022/2023"],
                st.session_state.su_ratio_data[country]["2023/2024"]
            ]
            
            # Determine new category based on input
            def get_category(ratio):
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
            
            st.subheader(f"{country}")
            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
            
            with col1:
                updated_values[country] = st.number_input(
                    f"S/U Ratio (%)",
                    value=float(current_value),
                    min_value=0.0,
                    max_value=200.0,
                    step=0.1,
                    format="%.1f",
                    key=f"su_{country}",
                    help=f"Historical: {historical_values[0]:.1f}% → {historical_values[1]:.1f}% → {historical_values[2]:.1f}%"
                )
            
            with col2:
                updated_changes[country] = st.number_input(
                    f"Change from 2023/2024",
                    value=float(current_change),
                    step=0.1,
                    format="%.1f",
                    key=f"su_change_{country}",
                    help="Positive for increase, negative for decrease"
                )
            
            with col3:
                # Show new category
                new_category = get_category(updated_values[country])
                category_color = {
                    "Strategic Reserve": "🟢",
                    "Comfortable": "🔵",
                    "Adequate": "🟡",
                    "Tight": "🟠",
                    "Critical": "🔴"
                }.get(new_category, "⚪")
                st.markdown(f"**Category**: {category_color} {new_category}")
            
            with col4:
                # Calculate and display automatic change
                auto_change = updated_values[country] - st.session_state.su_ratio_data[country]["2023/2024"]
                if auto_change > 0:
                    st.success(f"Auto: +{auto_change:.1f}")
                elif auto_change < 0:
                    st.error(f"Auto: {auto_change:.1f}")
                else:
                    st.info("Auto: 0.0")
        
        # Submit button
        if st.form_submit_button("Update S/U Ratio Projections", type="primary"):
            # Update the data
            db = get_database()
            
            for country, value in updated_values.items():
                st.session_state.su_ratio_data[country]["2024/2025"] = value
                st.session_state.su_ratio_data[country]["2024/2025_change"] = updated_changes[country]
                st.session_state.su_ratio_data[country]["2024/2025_category"] = get_category(value)
                
                # Save to database
                if db:
                    db.update_su_ratio_value(country, "2024/2025", value, updated_changes[country])
            
            st.success("✅ S/U ratio projections updated successfully!")
            if db:
                st.info("💾 Changes saved to database")
            st.rerun()

with tab3:
    st.header("S/U Ratio Analysis")
    
    # Time series plot
    st.subheader("S/U Ratio Trends Over Time")
    
    # Select countries to display
    countries_to_plot = st.multiselect(
        "Select countries/regions to display:",
        options=list(st.session_state.su_ratio_data.keys()),
        default=["WORLD", "China", "United States", "European Union 27 (FR, DE)", "India", "Russia"]
    )
    
    if countries_to_plot:
        # Create time series plot
        fig = go.Figure()
        
        years = ["2021/2022", "2022/2023", "2023/2024", "2024/2025"]
        
        for country in countries_to_plot:
            values = [st.session_state.su_ratio_data[country][year] for year in years]
            
            fig.add_trace(go.Scatter(
                x=years,
                y=values,
                mode='lines+markers',
                name=country,
                hovertemplate=f'<b>{country}</b><br>' +
                             'Year: %{x}<br>' +
                             'S/U Ratio: %{y:.1f}%<extra></extra>'
            ))
        
        # Add reference lines for categories
        fig.add_hline(y=50, line_dash="dash", line_color="green", 
                     annotation_text="Strategic Reserve (≥50%)", annotation_position="right")
        fig.add_hline(y=30, line_dash="dash", line_color="blue", 
                     annotation_text="Comfortable (30%)", annotation_position="right")
        fig.add_hline(y=20, line_dash="dash", line_color="orange", 
                     annotation_text="Adequate (20%)", annotation_position="right")
        fig.add_hline(y=10, line_dash="dash", line_color="red", 
                     annotation_text="Tight (10%)", annotation_position="right")
        
        fig.update_layout(
            title="Stock-to-Use Ratio Trends",
            xaxis_title="Year",
            yaxis_title="Stock-to-Use Ratio (%)",
            hovermode='x unified',
            height=500
        )
        
        # Add vertical line to separate historical from projection
        fig.add_vline(x=2.5, line_dash="dot", line_color="gray", 
                     annotation_text="Historical | Projection", 
                     annotation_position="top")
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Category distribution
    st.subheader("S/U Ratio Category Distribution (2024/2025)")
    
    # Count countries by category
    category_counts = {}
    for country, data in st.session_state.su_ratio_data.items():
        if country != "WORLD":
            category = data.get('2024/2025_category', 'Unknown')
            category_counts[category] = category_counts.get(category, 0) + 1
    
    # Create pie chart
    fig_pie = go.Figure(data=[go.Pie(
        labels=list(category_counts.keys()),
        values=list(category_counts.values()),
        marker_colors=['#90EE90', '#87CEEB', '#F0E68C', '#FFB366', '#FFB6C1'],
        hovertemplate='<b>%{label}</b><br>' +
                     'Countries: %{value}<br>' +
                     'Share: %{percent}<extra></extra>'
    )])
    
    fig_pie.update_layout(
        title="Distribution of Countries by S/U Ratio Category",
        height=400
    )
    
    st.plotly_chart(fig_pie, use_container_width=True)
    
    # Scatter plot: S/U Ratio vs Change
    st.subheader("S/U Ratio vs Year-over-Year Change")
    
    scatter_data = []
    for country, data in st.session_state.su_ratio_data.items():
        if country != "WORLD":
            scatter_data.append({
                "Country": country,
                "S/U Ratio": data['2024/2025'],
                "Change": data.get('2024/2025_change', 0),
                "Category": data.get('2024/2025_category', 'Unknown')
            })
    
    df_scatter = pd.DataFrame(scatter_data)
    
    fig_scatter = px.scatter(df_scatter, 
                            x="S/U Ratio", 
                            y="Change",
                            color="Category",
                            size=[10]*len(df_scatter),
                            hover_data=["Country"],
                            color_discrete_map={
                                "Strategic Reserve": "#90EE90",
                                "Comfortable": "#87CEEB",
                                "Adequate": "#F0E68C",
                                "Tight": "#FFB366",
                                "Critical": "#FFB6C1"
                            })
    
    fig_scatter.update_layout(
        title="S/U Ratio vs Change (2024/2025)",
        xaxis_title="Stock-to-Use Ratio (%)",
        yaxis_title="Year-over-Year Change (%)",
        height=400
    )
    
    # Add quadrant lines
    fig_scatter.add_hline(y=0, line_dash="dash", line_color="gray")
    fig_scatter.add_vline(x=30, line_dash="dash", line_color="gray")
    
    st.plotly_chart(fig_scatter, use_container_width=True)

with tab4:
    st.header("Regional S/U Ratio Insights")
    
    # Regional groupings
    regions = {
        "Major Exporters": ["United States", "Canada", "Australia", "Argentina", "Russia", "Ukraine"],
        "Major Importers": ["China", "India", "European Union 27 (FR, DE)", "Turkey", "Pakistan"],
        "Self-Sufficient": ["Iran", "Kazakhstan"]
    }
    
    # Display regional analysis
    for region_name, countries in regions.items():
        st.subheader(f"{region_name}")
        
        # Calculate regional metrics
        region_data = []
        for country in countries:
            if country in st.session_state.su_ratio_data:
                data = st.session_state.su_ratio_data[country]
                region_data.append({
                    "Country": country,
                    "2024/2025 S/U Ratio": data['2024/2025'],
                    "Change": data.get('2024/2025_change', 0),
                    "Category": data.get('2024/2025_category', 'Unknown')
                })
        
        if region_data:
            df_region = pd.DataFrame(region_data)
            
            # Create bar chart
            fig_region = px.bar(df_region, 
                              x="Country", 
                              y="2024/2025 S/U Ratio",
                              color="Category",
                              color_discrete_map={
                                  "Strategic Reserve": "#90EE90",
                                  "Comfortable": "#87CEEB",
                                  "Adequate": "#F0E68C",
                                  "Tight": "#FFB366",
                                  "Critical": "#FFB6C1"
                              },
                              title=f"{region_name} - S/U Ratios 2024/2025")
            
            fig_region.update_layout(
                xaxis_title="Country",
                yaxis_title="Stock-to-Use Ratio (%)",
                height=300
            )
            
            # Add reference line at 30%
            fig_region.add_hline(y=30, line_dash="dash", line_color="gray", 
                               annotation_text="Comfortable threshold")
            
            st.plotly_chart(fig_region, use_container_width=True)
            
            # Summary metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                avg_su = df_region["2024/2025 S/U Ratio"].mean()
                st.metric(f"Average S/U Ratio", f"{avg_su:.1f}%")
            with col2:
                max_su = df_region["2024/2025 S/U Ratio"].max()
                max_country = df_region[df_region["2024/2025 S/U Ratio"] == max_su]["Country"].values[0]
                st.metric("Highest", f"{max_country}: {max_su:.1f}%")
            with col3:
                min_su = df_region["2024/2025 S/U Ratio"].min()
                min_country = df_region[df_region["2024/2025 S/U Ratio"] == min_su]["Country"].values[0]
                st.metric("Lowest", f"{min_country}: {min_su:.1f}%")
        
        st.markdown("---")

with tab5:
    st.header("S/U Ratio Data Management")
    
    # Export options
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Export Current Data")
        
        # Prepare export data
        export_data = {
            "wheat_su_ratio_data": st.session_state.su_ratio_data,
            "metadata": st.session_state.su_ratio_projection_metadata,
            "export_timestamp": datetime.now().isoformat(),
            "data_source": "database" if st.session_state.su_ratio_data_loaded else "local"
        }
        
        # JSON export
        st.download_button(
            label="📥 Download S/U Ratio Data as JSON",
            data=json.dumps(export_data, indent=2),
            file_name=f"wheat_su_ratio_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )
        
        # CSV export
        df_export = pd.DataFrame(st.session_state.su_ratio_data).T
        csv_data = df_export.to_csv()
        st.download_button(
            label="📥 Download S/U Ratio Data as CSV",
            data=csv_data,
            file_name=f"wheat_su_ratio_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    
    with col2:
        st.subheader("Import Data")
        
        uploaded_file = st.file_uploader("Upload JSON S/U ratio data file", type=['json'])
        
        if uploaded_file is not None:
            try:
                uploaded_data = json.load(uploaded_file)
                
                if st.button("Import S/U Ratio Data"):
                    if "wheat_su_ratio_data" in uploaded_data:
                        st.session_state.su_ratio_data = uploaded_data["wheat_su_ratio_data"]
                    
                    if "metadata" in uploaded_data:
                        st.session_state.su_ratio_projection_metadata = uploaded_data["metadata"]
                    
                    st.success("S/U ratio data imported successfully!")
                    st.rerun()
                    
            except json.JSONDecodeError:
                st.error("Invalid JSON file format")

# Footer
st.markdown("---")
status_text = "🗄️ Database Connected" if st.session_state.su_ratio_data_loaded else "💾 Local Data Mode"
st.markdown(
    f"""
    <div style='text-align: center; color: #666; font-size: 0.8em;'>
    📊 Stock-to-Use Ratio Dashboard | {status_text} | Market Tightness Analysis
    </div>
    """,
    unsafe_allow_html=True
)