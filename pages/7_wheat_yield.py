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
    page_title="Wheat Yield Dashboard",
    page_icon="🌱",
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

# Load yield data from database
@st.cache_data
def load_yield_data():
    """Load yield data from database"""
    db = get_database()
    if not db:
        return None, None
    
    try:
        # Get yield data
        yield_data = db.get_all_yield_data()
        
        # Get metadata
        metadata = db.get_metadata()
        projection_metadata = {
            "last_updated": metadata.get("yield_last_updated", "19 Sept'24"),
            "next_update": metadata.get("yield_next_update", "17 Oct'24")
        }
        
        return yield_data, projection_metadata
    except Exception as e:
        st.error(f"❌ Error loading yield data from database: {e}")
        return None, None

# Initialize session state
def initialize_session_state():
    """Initialize session state with database data"""
    if 'yield_data_loaded' not in st.session_state:
        yield_data, projection_metadata = load_yield_data()
        
        if yield_data and projection_metadata:
            st.session_state.yield_data = yield_data
            st.session_state.yield_projection_metadata = projection_metadata
            st.session_state.yield_data_loaded = True
        else:
            # Fallback to sample data if database is not available
            st.session_state.yield_data = {
                "WORLD": {
                    "2021/2022": 3.53, "2021/2022_change": None, "2021/2022_pct": None,
                    "2021/2022_category": "Medium", "2021/2022_weather": "Normal",
                    "2022/2023": 3.58, "2022/2023_change": 0.05, "2022/2023_pct": 1.3,
                    "2022/2023_category": "Medium", "2022/2023_weather": "Favorable",
                    "2023/2024": 3.48, "2023/2024_change": -0.10, "2023/2024_pct": -2.6,
                    "2023/2024_category": "Medium", "2023/2024_weather": "Mixed",
                    "2024/2025": 3.52, "2024/2025_change": 0.04, "2024/2025_pct": 1.1,
                    "2024/2025_category": "Medium", "2024/2025_weather": "Normal"
                }
            }
            st.session_state.yield_projection_metadata = {
                "last_updated": "19 Sept'24",
                "next_update": "17 Oct'24"
            }
            st.session_state.yield_data_loaded = False

# Initialize session state
initialize_session_state()

# Title and header
st.title("🌱 Wheat Yield Dashboard")
st.markdown("### Global Wheat Productivity Analysis")

# Database status indicator
if st.session_state.yield_data_loaded:
    st.sidebar.success("🗄️ Connected to Database")
else:
    st.sidebar.warning("⚠️ Using Local Data (No Database)")

# Sidebar for data management
create_projection_dates_sidebar(
    st.session_state.yield_projection_metadata,
    "yield_last_updated",
    "yield_next_update"
)

# Main content area
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📈 Data Overview", "✏️ Edit Projections", "📊 Visualizations", 
                                             "🌍 Regional Analysis", "🌤️ Weather Impact", "💾 Data Export"])

with tab1:
    st.header("Global Wheat Yields")
    
    # Display status indicators
    create_status_indicators()
    
    # Display projection dates
    st.markdown(f"**Projection Dates**: {st.session_state.yield_projection_metadata['last_updated']} | {st.session_state.yield_projection_metadata['next_update']}")
    
    st.markdown("---")
    
    # Key insights
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.info("""
        **Yield** (tonnes per hectare) measures wheat productivity and farming efficiency.
        
        Key factors affecting yield:
        - Weather conditions (rainfall, temperature)
        - Soil quality and management
        - Seed varieties and technology
        - Fertilizer and input use
        - Irrigation availability
        """)
    
    with col2:
        st.markdown("### Yield Categories")
        st.markdown("""
        - 🟣 **Very High**: ≥7.0 t/ha
        - 🟢 **High**: 5.0-7.0 t/ha
        - 🔵 **Medium**: 3.0-5.0 t/ha
        - 🟡 **Low**: 2.0-3.0 t/ha
        - 🔴 **Very Low**: <2.0 t/ha
        """)
    
    # Create enhanced table
    st.markdown("### Yield Data (tonnes per hectare)")
    
    # Create the data table with proper formatting
    table_data = []
    for country, data in st.session_state.yield_data.items():
        # Get current category
        current_category = data.get('2024/2025_category', 'Unknown')
        
        # Emoji based on category
        category_emoji = {
            "Very High": "🟣",
            "High": "🟢",
            "Medium": "🔵",
            "Low": "🟡",
            "Very Low": "🔴"
        }.get(current_category, "⚪")
        
        # Weather impact for current year
        weather_2024 = data.get('2024/2025_weather', '')
        weather_emoji = ""
        if weather_2024:
            if "Excellent" in weather_2024 or "Favorable" in weather_2024:
                weather_emoji = "☀️"
            elif "Drought" in weather_2024 or "Dry" in weather_2024:
                weather_emoji = "🌵"
            elif "Wet" in weather_2024:
                weather_emoji = "🌧️"
            elif "Challenging" in weather_2024:
                weather_emoji = "⚠️"
        
        row = {
            "Country/Region": f"{category_emoji} {country}",
            "2021/2022": f"{data['2021/2022']:.2f}",
            "2022/2023": f"{data['2022/2023']:.2f}",
            "Change": f"{data.get('2022/2023_change', 0):+.2f}" if data.get('2022/2023_change') else "-",
            "2023/2024": f"{data['2023/2024']:.2f}",
            "Change ": f"{data.get('2023/2024_change', 0):+.2f}" if data.get('2023/2024_change') else "-",
            "2024/2025": f"{data['2024/2025']:.2f}",
            "Change  ": f"{data.get('2024/2025_change', 0):+.2f}" if data.get('2024/2025_change') else "-",
            "Weather": f"{weather_emoji} {weather_2024}"
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
    }, subset=['Country/Region', 'Weather'])
    
    st.dataframe(
        styled_df,
        use_container_width=True,
        hide_index=True
    )
    
    # Summary statistics
    st.markdown("### Summary Statistics")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        world_yield = st.session_state.yield_data.get('WORLD', {}).get('2024/2025', 0)
        st.metric("Global Avg Yield", f"{world_yield:.2f} t/ha")
    
    with col2:
        # Find highest yield country
        countries_only = {k: v for k, v in st.session_state.yield_data.items() if k != "WORLD"}
        if countries_only:
            max_country = max(countries_only.items(), key=lambda x: x[1]['2024/2025'])
            st.metric("Highest Yield", f"{max_country[0]}: {max_country[1]['2024/2025']:.2f}")
    
    with col3:
        # Find lowest yield country
        if countries_only:
            min_country = min(countries_only.items(), key=lambda x: x[1]['2024/2025'])
            st.metric("Lowest Yield", f"{min_country[0]}: {min_country[1]['2024/2025']:.2f}")
    
    with col4:
        # Count improving countries
        improving = sum(1 for country, data in countries_only.items() 
                       if data.get('2024/2025_change', 0) > 0)
        st.metric("Countries Improving", improving)

with tab2:
    st.header("Edit 2024/2025 Yield Projections")
    st.markdown("**Note:** Historical data (2021/2022 - 2023/2024) is static and cannot be modified.")
    
    # Create form for editing projections
    with st.form("yield_projection_form"):
        st.markdown("### Update Yield Projections and Weather Impact")
        
        # Create input fields for each country
        updated_values = {}
        updated_changes = {}
        updated_weather = {}
        
        for country in st.session_state.yield_data.keys():
            current_value = st.session_state.yield_data[country]["2024/2025"]
            current_change = st.session_state.yield_data[country].get("2024/2025_change", 0)
            current_weather = st.session_state.yield_data[country].get("2024/2025_weather", "Normal")
            
            # Show historical trend
            historical_values = [
                st.session_state.yield_data[country]["2021/2022"],
                st.session_state.yield_data[country]["2022/2023"],
                st.session_state.yield_data[country]["2023/2024"]
            ]
            
            st.subheader(f"{country}")
            col1, col2, col3, col4 = st.columns([2, 1, 1.5, 1])
            
            with col1:
                updated_values[country] = st.number_input(
                    f"Yield (t/ha)",
                    value=float(current_value),
                    min_value=0.0,
                    max_value=10.0,
                    step=0.01,
                    format="%.2f",
                    key=f"yield_{country}",
                    help=f"Historical: {historical_values[0]:.2f} → {historical_values[1]:.2f} → {historical_values[2]:.2f}"
                )
            
            with col2:
                # Calculate automatic change
                auto_change = updated_values[country] - st.session_state.yield_data[country]["2023/2024"]
                updated_changes[country] = auto_change
                
                if auto_change > 0:
                    st.success(f"Change: +{auto_change:.2f}")
                elif auto_change < 0:
                    st.error(f"Change: {auto_change:.2f}")
                else:
                    st.info("Change: 0.00")
            
            with col3:
                weather_options = ["Excellent", "Favorable", "Normal", "Mixed", 
                                 "Challenging", "Dry", "Drought", "Wet", "Recovery"]
                updated_weather[country] = st.selectbox(
                    "Weather Impact",
                    options=weather_options,
                    index=weather_options.index(current_weather) if current_weather in weather_options else 2,
                    key=f"weather_{country}"
                )
            
            with col4:
                # Show yield category
                yield_val = updated_values[country]
                if yield_val >= 7.0:
                    category = "Very High"
                    st.markdown("🟣 **Very High**")
                elif yield_val >= 5.0:
                    category = "High"
                    st.markdown("🟢 **High**")
                elif yield_val >= 3.0:
                    category = "Medium"
                    st.markdown("🔵 **Medium**")
                elif yield_val >= 2.0:
                    category = "Low"
                    st.markdown("🟡 **Low**")
                else:
                    category = "Very Low"
                    st.markdown("🔴 **Very Low**")
        
        # Submit button
        if st.form_submit_button("Update Yield Projections", type="primary"):
            # Update the data
            db = get_database()
            
            for country, value in updated_values.items():
                # Calculate percentage change
                prev_value = st.session_state.yield_data[country]["2023/2024"]
                pct_change = (updated_changes[country] / prev_value * 100) if prev_value > 0 else 0
                
                # Update session state
                st.session_state.yield_data[country]["2024/2025"] = value
                st.session_state.yield_data[country]["2024/2025_change"] = updated_changes[country]
                st.session_state.yield_data[country]["2024/2025_pct"] = pct_change
                st.session_state.yield_data[country]["2024/2025_weather"] = updated_weather[country]
                
                # Determine category
                if value >= 7.0:
                    category = "Very High"
                elif value >= 5.0:
                    category = "High"
                elif value >= 3.0:
                    category = "Medium"
                elif value >= 2.0:
                    category = "Low"
                else:
                    category = "Very Low"
                
                st.session_state.yield_data[country]["2024/2025_category"] = category
                
                # Save to database
                if db:
                    db.update_yield_value(country, "2024/2025", value, updated_changes[country], 
                                        pct_change, updated_weather[country])
            
            st.success("✅ Yield projections updated successfully!")
            if db:
                st.info("💾 Changes saved to database")
            st.rerun()

with tab3:
    st.header("Yield Visualizations")
    
    # Time series plot
    st.subheader("Yield Trends Over Time")
    
    # Select countries to display
    countries_to_plot = st.multiselect(
        "Select countries/regions to display:",
        options=list(st.session_state.yield_data.keys()),
        default=["WORLD", "China", "European Union 27 (FR, DE)", "India", 
                "United States", "Russia", "Australia"]
    )
    
    if countries_to_plot:
        # Create time series plot
        fig = go.Figure()
        
        years = ["2021/2022", "2022/2023", "2023/2024", "2024/2025"]
        
        for country in countries_to_plot:
            values = [st.session_state.yield_data[country][year] for year in years]
            
            fig.add_trace(go.Scatter(
                x=years,
                y=values,
                mode='lines+markers',
                name=country,
                hovertemplate=f'<b>{country}</b><br>' +
                             'Year: %{x}<br>' +
                             'Yield: %{y:.2f} t/ha<extra></extra>'
            ))
        
        # Add world average line if not already included
        if "WORLD" not in countries_to_plot:
            world_values = [st.session_state.yield_data["WORLD"][year] for year in years]
            fig.add_trace(go.Scatter(
                x=years,
                y=world_values,
                mode='lines',
                name="World Average",
                line=dict(dash='dash', color='gray'),
                hovertemplate='<b>World Average</b><br>' +
                             'Year: %{x}<br>' +
                             'Yield: %{y:.2f} t/ha<extra></extra>'
            ))
        
        fig.update_layout(
            title="Wheat Yield Trends",
            xaxis_title="Year",
            yaxis_title="Yield (tonnes per hectare)",
            hovermode='x unified',
            height=500
        )
        
        # Add vertical line to separate historical from projection
        fig.add_vline(x=2.5, line_dash="dot", line_color="gray", 
                     annotation_text="Historical | Projection", 
                     annotation_position="top")
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Yield distribution by category
    st.subheader("Yield Distribution by Category (2024/2025)")
    
    # Count countries by category
    category_counts = {}
    for country, data in st.session_state.yield_data.items():
        if country != "WORLD":
            category = data.get('2024/2025_category', 'Unknown')
            category_counts[category] = category_counts.get(category, 0) + 1
    
    # Order categories
    ordered_categories = ["Very High", "High", "Medium", "Low", "Very Low"]
    ordered_counts = [category_counts.get(cat, 0) for cat in ordered_categories]
    
    # Create bar chart
    fig_bar = go.Figure(data=[
        go.Bar(
            x=ordered_categories,
            y=ordered_counts,
            marker_color=['#9370DB', '#90EE90', '#87CEEB', '#F0E68C', '#FFB6C1'],
            text=ordered_counts,
            textposition='auto'
        )
    ])
    
    fig_bar.update_layout(
        title="Distribution of Countries by Yield Category",
        xaxis_title="Yield Category",
        yaxis_title="Number of Countries",
        height=400
    )
    
    st.plotly_chart(fig_bar, use_container_width=True)

with tab4:
    st.header("Regional Yield Analysis")
    
    # Create yield comparison by region
    st.subheader("Yield Comparison by Country (2024/2025)")
    
    # Get yield data for all countries except WORLD
    countries_only = {k: v for k, v in st.session_state.yield_data.items() if k != "WORLD"}
    
    # Create dataframe for plotting
    yield_comparison = []
    for country, data in countries_only.items():
        yield_comparison.append({
            "Country": country,
            "Yield": data['2024/2025'],
            "Category": data.get('2024/2025_category', 'Unknown'),
            "Change": data.get('2024/2025_change', 0)
        })
    
    df_yield = pd.DataFrame(yield_comparison)
    df_yield = df_yield.sort_values("Yield", ascending=False)
    
    # Create bar chart with color coding
    fig_comparison = px.bar(df_yield, x="Country", y="Yield", color="Category",
                           color_discrete_map={
                               "Very High": "#9370DB",
                               "High": "#90EE90",
                               "Medium": "#87CEEB",
                               "Low": "#F0E68C",
                               "Very Low": "#FFB6C1"
                           },
                           title="Wheat Yields by Country - 2024/2025")
    
    # Add world average line
    world_yield = st.session_state.yield_data.get('WORLD', {}).get('2024/2025', 3.52)
    fig_comparison.add_hline(y=world_yield, line_dash="dash", line_color="red", 
                           annotation_text=f"World Average: {world_yield:.2f} t/ha")
    
    fig_comparison.update_layout(
        xaxis_title="Country",
        yaxis_title="Yield (t/ha)",
        height=500,
        xaxis_tickangle=-45
    )
    
    st.plotly_chart(fig_comparison, use_container_width=True)
    
    # Yield gap analysis
    st.subheader("Yield Gap Analysis")
    
    # Calculate yield gaps relative to best performer
    max_yield = df_yield['Yield'].max()
    df_yield['Yield_Gap'] = max_yield - df_yield['Yield']
    df_yield['Potential_Increase_Pct'] = (df_yield['Yield_Gap'] / df_yield['Yield'] * 100).round(1)
    
    # Show top 10 countries with largest yield gaps
    top_gaps = df_yield.nlargest(10, 'Yield_Gap')
    
    fig_gap = go.Figure()
    
    # Add current yield bars
    fig_gap.add_trace(go.Bar(
        name='Current Yield',
        x=top_gaps['Country'],
        y=top_gaps['Yield'],
        marker_color='lightblue'
    ))
    
    # Add potential yield bars
    fig_gap.add_trace(go.Bar(
        name='Yield Gap',
        x=top_gaps['Country'],
        y=top_gaps['Yield_Gap'],
        marker_color='lightcoral'
    ))
    
    fig_gap.update_layout(
        title="Top 10 Countries with Largest Yield Improvement Potential",
        xaxis_title="Country",
        yaxis_title="Yield (t/ha)",
        barmode='stack',
        height=400
    )
    
    st.plotly_chart(fig_gap, use_container_width=True)
    
    # Summary metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        avg_gap = df_yield['Yield_Gap'].mean()
        st.metric("Average Yield Gap", f"{avg_gap:.2f} t/ha")
    
    with col2:
        total_potential = (df_yield['Yield_Gap'] * 100).sum()  # Simplified calculation
        st.metric("Production Potential", f"{total_potential:.0f} Mt",
                 help="Rough estimate if all countries achieved highest yield")
    
    with col3:
        countries_below_avg = len(df_yield[df_yield['Yield'] < world_yield])
        st.metric("Countries Below Average", countries_below_avg)

with tab5:
    st.header("Weather Impact Analysis")
    
    st.markdown("""
    Weather conditions are the primary driver of year-to-year yield variability. 
    This analysis shows how different weather patterns affect wheat yields.
    """)
    
    # Weather impact by country
    st.subheader("Weather Conditions by Country (2024/2025)")
    
    # Create weather impact summary
    weather_data = []
    for country, data in st.session_state.yield_data.items():
        if country != "WORLD":
            weather_data.append({
                "Country": country,
                "Yield": data['2024/2025'],
                "Weather": data.get('2024/2025_weather', 'Unknown'),
                "Change": data.get('2024/2025_change', 0),
                "Category": data.get('2024/2025_category', 'Unknown')
            })
    
    df_weather = pd.DataFrame(weather_data)
    
    # Group by weather condition
    weather_summary = df_weather.groupby('Weather').agg({
        'Country': 'count',
        'Yield': 'mean',
        'Change': 'mean'
    }).round(2)
    weather_summary.columns = ['Countries', 'Avg Yield', 'Avg Change']
    weather_summary = weather_summary.sort_values('Avg Yield', ascending=False)
    
    # Display weather impact summary
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("### Weather Impact Summary")
        st.dataframe(weather_summary)
    
    with col2:
        # Create scatter plot of weather vs yield
        fig_weather = px.scatter(df_weather, x="Yield", y="Change", 
                               color="Weather", size=[10]*len(df_weather),
                               hover_data=['Country'],
                               title="Weather Impact on Yield Changes")
        
        fig_weather.update_layout(
            xaxis_title="Yield (t/ha)",
            yaxis_title="Year-over-Year Change (t/ha)",
            height=400
        )
        
        # Add reference lines
        fig_weather.add_hline(y=0, line_dash="dash", line_color="gray")
        
        st.plotly_chart(fig_weather, use_container_width=True)
    
    # Historical weather patterns
    st.subheader("Historical Weather Patterns")
    
    # Count weather conditions over time
    weather_counts = {}
    years = ["2021/2022", "2022/2023", "2023/2024", "2024/2025"]
    
    for year in years:
        weather_counts[year] = {}
        for country, data in st.session_state.yield_data.items():
            if country != "WORLD":
                weather = data.get(f'{year}_weather', 'Unknown')
                weather_counts[year][weather] = weather_counts[year].get(weather, 0) + 1
    
    # Create stacked bar chart
    fig_weather_trend = go.Figure()
    
    weather_types = set()
    for year_data in weather_counts.values():
        weather_types.update(year_data.keys())
    
    for weather in weather_types:
        values = [weather_counts[year].get(weather, 0) for year in years]
        fig_weather_trend.add_trace(go.Bar(name=weather, x=years, y=values))
    
    fig_weather_trend.update_layout(
        title="Weather Conditions Distribution Over Time",
        xaxis_title="Year",
        yaxis_title="Number of Countries",
        barmode='stack',
        height=400
    )
    
    st.plotly_chart(fig_weather_trend, use_container_width=True)

with tab6:
    st.header("Yield Data Management")
    
    # Export options
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Export Current Data")
        
        # Prepare export data
        export_data = {
            "wheat_yield_data": st.session_state.yield_data,
            "metadata": st.session_state.yield_projection_metadata,
            "export_timestamp": datetime.now().isoformat(),
            "data_source": "database" if st.session_state.yield_data_loaded else "local"
        }
        
        # JSON export
        st.download_button(
            label="📥 Download Yield Data as JSON",
            data=json.dumps(export_data, indent=2),
            file_name=f"wheat_yield_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )
        
        # CSV export
        df_export = pd.DataFrame(st.session_state.yield_data).T
        csv_data = df_export.to_csv()
        st.download_button(
            label="📥 Download Yield Data as CSV",
            data=csv_data,
            file_name=f"wheat_yield_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    
    with col2:
        st.subheader("Import Data")
        
        uploaded_file = st.file_uploader("Upload JSON yield data file", type=['json'])
        
        if uploaded_file is not None:
            try:
                uploaded_data = json.load(uploaded_file)
                
                if st.button("Import Yield Data"):
                    if "wheat_yield_data" in uploaded_data:
                        st.session_state.yield_data = uploaded_data["wheat_yield_data"]
                    
                    if "metadata" in uploaded_data:
                        st.session_state.yield_projection_metadata = uploaded_data["metadata"]
                    
                    st.success("Yield data imported successfully!")
                    st.rerun()
                    
            except json.JSONDecodeError:
                st.error("Invalid JSON file format")

# Footer
st.markdown("---")
status_text = "🗄️ Database Connected" if st.session_state.yield_data_loaded else "💾 Local Data Mode"
st.markdown(
    f"""
    <div style='text-align: center; color: #666; font-size: 0.8em;'>
    🌱 Wheat Yield Dashboard | {status_text} | Productivity & Weather Analysis
    </div>
    """,
    unsafe_allow_html=True
)