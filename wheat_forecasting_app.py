import streamlit as st
import pandas as pd
import json
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np
import sqlite3
import os

# Import database helper (make sure database_helper.py is in the same directory)
try:
    from database_helper import WheatProductionDB, init_database
    DB_AVAILABLE = True
except ImportError:
    st.error("❌ Database helper not found. Please ensure database_helper.py is in the same directory.")
    DB_AVAILABLE = False

# Page configuration
st.set_page_config(
    page_title="Wheat Production Forecasting",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database
@st.cache_resource
def get_database():
    """Initialize and return database instance"""
    if not DB_AVAILABLE:
        return None
    
    if not os.path.exists("wheat_production.db"):
        st.error("❌ Database not found. Please run 'python database_setup.py' first to create the database.")
        return None
    
    return WheatProductionDB()

# Load data from database
@st.cache_data
def load_data_from_db():
    """Load data from database"""
    db = get_database()
    if not db:
        return None, None
    
    try:
        # Get production data
        wheat_data = db.get_all_production_data()
        
        # Get metadata
        metadata = db.get_metadata()
        projection_metadata = {
            "last_updated": metadata.get("last_updated", "19 Sept'24"),
            "next_update": metadata.get("next_update", "17 Oct'24")
        }
        
        return wheat_data, projection_metadata
    except Exception as e:
        st.error(f"❌ Error loading data from database: {e}")
        return None, None

# Initialize session state with database data
def initialize_session_state():
    """Initialize session state with database data"""
    if 'data_loaded' not in st.session_state:
        wheat_data, projection_metadata = load_data_from_db()
        
        if wheat_data and projection_metadata:
            st.session_state.wheat_data = wheat_data
            st.session_state.projection_metadata = projection_metadata
            st.session_state.data_loaded = True
        else:
            # Fallback to hardcoded data if database is not available
            st.session_state.wheat_data = {
                "WORLD": {
                    "2021/2022": 779.7, "2021/2022_pct": None,
                    "2022/2023": 803.9, "2022/2023_change": 24.2,
                    "2023/2024": 795.0, "2023/2024_change": -8.9,
                    "2024/2025": 798.0, "2024/2025_change": 3.0
                }
                # ... other countries would be here in fallback mode
            }
            st.session_state.projection_metadata = {
                "last_updated": "19 Sept'24",
                "next_update": "17 Oct'24"
            }
            st.session_state.data_loaded = False

# Initialize session state
initialize_session_state()

# Status indicators
if 'status_info' not in st.session_state:
    st.session_state.status_info = {
        "2021/2022": "act",
        "2022/2023": "act", 
        "2023/2024": "estimate",
        "2024/2025": "projection"
    }

# Helper functions
def format_change(value):
    """Format change values"""
    if value is None or pd.isna(value):
        return ""
    if value >= 0:
        return f"+{value:.1f}"
    else:
        return f"({abs(value):.1f})"

def save_to_database(country, year, production, change):
    """Save data to database"""
    db = get_database()
    if db:
        return db.update_production_value(country, year, production, change)
    return False

def update_metadata_in_db(key, value):
    """Update metadata in database"""
    db = get_database()
    if db:
        return db.update_metadata(key, value)
    return False

# Title and header
st.title("🌾 Wheat Production Forecasting Dashboard")
st.markdown("### Global Wheat Production Data Management")

# Database status indicator
if DB_AVAILABLE and st.session_state.data_loaded:
    st.sidebar.success("🗄️ Connected to Database")
else:
    st.sidebar.warning("⚠️ Using Local Data (No Database)")

# Sidebar for data management
st.sidebar.header("📊 Data Management")
st.sidebar.markdown("**Projection Dates**")

# Date management
col1, col2 = st.sidebar.columns(2)
with col1:
    last_updated = st.text_input(
        "Last Updated",
        value=st.session_state.projection_metadata["last_updated"],
        help="Format: DD MMM'YY"
    )
with col2:
    next_update = st.text_input(
        "Next Update",
        value=st.session_state.projection_metadata["next_update"],
        help="Format: DD MMM'YY"
    )

# Update dates
if st.sidebar.button("Update Dates"):
    st.session_state.projection_metadata["last_updated"] = last_updated
    st.session_state.projection_metadata["next_update"] = next_update
    
    # Save to database
    if DB_AVAILABLE:
        update_metadata_in_db("last_updated", last_updated)
        update_metadata_in_db("next_update", next_update)
    
    st.sidebar.success("Dates updated successfully!")
    st.rerun()

# Database management section
if DB_AVAILABLE:
    st.sidebar.markdown("---")
    st.sidebar.header("🗄️ Database Management")
    
    if st.sidebar.button("🔄 Refresh Data from DB"):
        st.cache_data.clear()
        st.session_state.data_loaded = False
        st.rerun()
    
    if st.sidebar.button("📊 Show Database Stats"):
        db = get_database()
        if db:
            df_stats = db.get_production_dataframe()
            st.sidebar.info(f"Records: {len(df_stats)}")
            st.sidebar.info(f"Countries: {df_stats['country'].nunique()}")
            st.sidebar.info(f"Years: {df_stats['year'].nunique()}")

# Main content area
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📈 Data Overview", "✏️ Edit Projections", "📊 Visualizations", "💾 Data Export", "🗄️ Database"])

with tab1:
    st.header("Global Wheat Production")
    
    # Display status indicators
    st.markdown("### Status Information")
    status_cols = st.columns(4)
    with status_cols[0]:
        st.info(f"**2021/2022**: {st.session_state.status_info['2021/2022']}")
    with status_cols[1]:
        st.info(f"**2022/2023**: {st.session_state.status_info['2022/2023']}")
    with status_cols[2]:
        st.warning(f"**2023/2024**: {st.session_state.status_info['2023/2024']}")
    with status_cols[3]:
        st.success(f"**2024/2025**: {st.session_state.status_info['2024/2025']}")
    
    # Display projection dates
    st.markdown(f"**Projection Dates**: {st.session_state.projection_metadata['last_updated']} | {st.session_state.projection_metadata['next_update']}")
    
    st.markdown("---")
    
    # Create enhanced table
    st.markdown("### Production Data (Million Metric Tons)")
    
    # Create the data table with proper formatting
    table_data = []
    for country, data in st.session_state.wheat_data.items():
        row = {
            "Country/Region": country,
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
    
    # Enhanced styled dataframe
    def style_change_column(val):
        """Style function for change columns"""
        if pd.isna(val) or val == "-":
            return ''
        try:
            if '(' in str(val) and ')' in str(val):
                return 'color: red; font-weight: bold'
            elif '+' in str(val):
                return 'color: green; font-weight: bold'
            else:
                return ''
        except:
            return ''
    
    # Apply styling to the dataframe
    styled_df = df_display.style.map(
        style_change_column, 
        subset=['Change', 'Change ', 'Change  ']
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
    
    # Create a more detailed table with better formatting
    st.markdown("### Detailed Production Table")
    
    # Create columns for better layout
    col_headers = st.columns([3, 1, 1, 1, 1, 1, 1, 1, 1])
    
    with col_headers[0]:
        st.markdown("**Country/Region**")
    with col_headers[1]:
        st.markdown("**2021/2022**")
    with col_headers[2]:
        st.markdown("**% World**")
    with col_headers[3]:
        st.markdown("**2022/2023**")
    with col_headers[4]:
        st.markdown("**Change**")
    with col_headers[5]:
        st.markdown("**2023/2024**")
    with col_headers[6]:
        st.markdown("**Change**")
    with col_headers[7]:
        st.markdown("**2024/2025**")
    with col_headers[8]:
        st.markdown("**Change**")
    
    # Add status row
    st.markdown("---")
    status_cols = st.columns([3, 1, 1, 1, 1, 1, 1, 1, 1])
    with status_cols[0]:
        st.markdown("**Status:**")
    with status_cols[1]:
        st.markdown("*act*")
    with status_cols[2]:
        st.markdown("")
    with status_cols[3]:
        st.markdown("*act*")
    with status_cols[4]:
        st.markdown("")
    with status_cols[5]:
        st.markdown("*estimate*")
    with status_cols[6]:
        st.markdown("")
    with status_cols[7]:
        st.markdown("*projection*")
    with status_cols[8]:
        st.markdown("")
    
    # Add data rows
    st.markdown("---")
    for country, data in st.session_state.wheat_data.items():
        cols = st.columns([3, 1, 1, 1, 1, 1, 1, 1, 1])
        
        with cols[0]:
            st.markdown(f"**{country}**")
        with cols[1]:
            st.markdown(f"{data['2021/2022']:.1f}")
        with cols[2]:
            pct_text = f"{data.get('2021/2022_pct', 0):.1f}%" if data.get('2021/2022_pct') is not None else "-"
            st.markdown(pct_text)
        with cols[3]:
            st.markdown(f"{data['2022/2023']:.1f}")
        with cols[4]:
            change_val = data.get('2022/2023_change', 0)
            if change_val >= 0:
                st.markdown(f"<span style='color: green; font-weight: bold'>+{change_val:.1f}</span>", unsafe_allow_html=True)
            else:
                st.markdown(f"<span style='color: red; font-weight: bold'>({abs(change_val):.1f})</span>", unsafe_allow_html=True)
        with cols[5]:
            st.markdown(f"{data['2023/2024']:.1f}")
        with cols[6]:
            change_val = data.get('2023/2024_change', 0)
            if change_val >= 0:
                st.markdown(f"<span style='color: green; font-weight: bold'>+{change_val:.1f}</span>", unsafe_allow_html=True)
            else:
                st.markdown(f"<span style='color: red; font-weight: bold'>({abs(change_val):.1f})</span>", unsafe_allow_html=True)
        with cols[7]:
            st.markdown(f"{data['2024/2025']:.1f}")
        with cols[8]:
            change_val = data.get('2024/2025_change', 0)
            if change_val >= 0:
                st.markdown(f"<span style='color: green; font-weight: bold'>+{change_val:.1f}</span>", unsafe_allow_html=True)
            else:
                st.markdown(f"<span style='color: red; font-weight: bold'>({abs(change_val):.1f})</span>", unsafe_allow_html=True)
    
    # Summary statistics
    st.markdown("### Summary Statistics")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        world_2024 = st.session_state.wheat_data['WORLD']['2024/2025']
        st.metric("Global Production 2024/2025", f"{world_2024:.1f} Mt")
    
    with col2:
        world_change = st.session_state.wheat_data['WORLD'].get('2024/2025_change', 0)
        st.metric("Change from 2023/2024", f"{world_change:+.1f} Mt")
    
    with col3:
        # Find top producer (excluding WORLD)
        countries_only = {k: v for k, v in st.session_state.wheat_data.items() if k != "WORLD"}
        if countries_only:
            top_producer = max(countries_only.items(), key=lambda x: x[1]['2024/2025'])
            st.metric("Top Producer 2024/2025", f"{top_producer[0][:15]}...")
    
    with col4:
        if countries_only:
            top_production = top_producer[1]['2024/2025']
            st.metric("Top Production", f"{top_production:.1f} Mt")

with tab2:
    st.header("Edit 2024/2025 Projections")
    st.markdown("**Note:** Historical data (2021/2022 - 2023/2024) is static and cannot be modified.")
    
    if not DB_AVAILABLE:
        st.warning("⚠️ Database not available. Changes will only be saved locally for this session.")
    
    # Create form for editing projections
    with st.form("projection_form"):
        st.markdown("### Update Production Projections and Changes")
        
        # Create input fields for each country
        updated_values = {}
        updated_changes = {}
        
        for country in st.session_state.wheat_data.keys():
            current_value = st.session_state.wheat_data[country]["2024/2025"]
            current_change = st.session_state.wheat_data[country].get("2024/2025_change", 0)
            
            # Show historical trend
            historical_values = [
                st.session_state.wheat_data[country]["2021/2022"],
                st.session_state.wheat_data[country]["2022/2023"],
                st.session_state.wheat_data[country]["2023/2024"]
            ]
            
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
                    help=f"Historical: {historical_values[0]:.1f} → {historical_values[1]:.1f} → {historical_values[2]:.1f}"
                )
            
            with col2:
                updated_changes[country] = st.number_input(
                    f"Change from 2023/2024",
                    value=float(current_change),
                    step=0.1,
                    format="%.1f",
                    key=f"change_{country}",
                    help="Positive for increase, negative for decrease"
                )
            
            with col3:
                # Calculate and display automatic change
                auto_change = updated_values[country] - st.session_state.wheat_data[country]["2023/2024"]
                if auto_change > 0:
                    st.success(f"Auto: +{auto_change:.1f}")
                elif auto_change < 0:
                    st.error(f"Auto: {auto_change:.1f}")
                else:
                    st.info("Auto: 0.0")
        
        # Submit button
        if st.form_submit_button("Update Projections", type="primary"):
            # Update the data
            for country, value in updated_values.items():
                st.session_state.wheat_data[country]["2024/2025"] = value
                st.session_state.wheat_data[country]["2024/2025_change"] = updated_changes[country]
                
                # Save to database
                if DB_AVAILABLE:
                    save_to_database(country, "2024/2025", value, updated_changes[country])
            
            st.success("✅ Projections updated successfully!")
            if DB_AVAILABLE:
                st.info("💾 Changes saved to database")
            st.rerun()

with tab3:
    st.header("Production Visualizations")
    
    # Prepare data for visualization
    df_viz = pd.DataFrame({
        country: {
            "2021/2022": data["2021/2022"],
            "2022/2023": data["2022/2023"],
            "2023/2024": data["2023/2024"],
            "2024/2025": data["2024/2025"]
        }
        for country, data in st.session_state.wheat_data.items()
    }).T
    
    # Time series plot
    st.subheader("Production Trends Over Time")
    
    # Select countries to display
    countries_to_plot = st.multiselect(
        "Select countries/regions to display:",
        options=list(st.session_state.wheat_data.keys()),
        default=["WORLD", "China", "European Union (FR, DE)", "India", "Russia", "United States"]
    )
    
    if countries_to_plot:
        # Create time series plot
        fig = go.Figure()
        
        years = ["2021/2022", "2022/2023", "2023/2024", "2024/2025"]
        
        for country in countries_to_plot:
            values = [st.session_state.wheat_data[country][year] for year in years]
            
            fig.add_trace(go.Scatter(
                x=years,
                y=values,
                mode='lines+markers',
                name=country,
                hovertemplate=f'<b>{country}</b><br>' +
                             'Year: %{x}<br>' +
                             'Production: %{y:.1f} Mt<extra></extra>'
            ))
        
        fig.update_layout(
            title="Wheat Production Trends",
            xaxis_title="Year",
            yaxis_title="Production (Million Metric Tons)",
            hovermode='x unified',
            height=500
        )
        
        # Add vertical line to separate historical from projection
        fig.add_vline(x=2.5, line_dash="dot", line_color="gray", 
                     annotation_text="Historical | Projection", 
                     annotation_position="top")
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Change analysis
    st.subheader("Production Changes Analysis")
    
    # Create change visualization
    countries_only = {k: v for k, v in st.session_state.wheat_data.items() if k != "WORLD"}
    
    change_data = []
    for country, data in countries_only.items():
        change_data.append({
            "Country": country,
            "2022/2023 Change": data.get("2022/2023_change", 0),
            "2023/2024 Change": data.get("2023/2024_change", 0),
            "2024/2025 Change": data.get("2024/2025_change", 0)
        })
    
    df_changes = pd.DataFrame(change_data)
    
    # Create grouped bar chart for changes
    fig_changes = go.Figure()
    
    years = ["2022/2023 Change", "2023/2024 Change", "2024/2025 Change"]
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c']
    
    for i, year in enumerate(years):
        fig_changes.add_trace(go.Bar(
            name=year,
            x=df_changes['Country'],
            y=df_changes[year],
            marker_color=colors[i],
            hovertemplate=f'<b>%{{x}}</b><br>{year}: %{{y:.1f}} Mt<extra></extra>'
        ))
    
    fig_changes.update_layout(
        title="Production Changes by Country",
        xaxis_title="Country/Region",
        yaxis_title="Change (Million Metric Tons)",
        barmode='group',
        height=400
    )
    
    # Add horizontal line at y=0
    fig_changes.add_hline(y=0, line_dash="dash", line_color="gray")
    
    st.plotly_chart(fig_changes, use_container_width=True)

with tab4:
    st.header("Data Export & Import")
    
    # Export options
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Export Current Data")
        
        # Export data
        export_data = {
            "wheat_production_data": st.session_state.wheat_data,
            "metadata": st.session_state.projection_metadata,
            "status_info": st.session_state.status_info,
            "export_timestamp": datetime.now().isoformat(),
            "data_source": "database" if DB_AVAILABLE and st.session_state.data_loaded else "local"
        }
        
        # JSON export
        st.download_button(
            label="📥 Download as JSON",
            data=json.dumps(export_data, indent=2),
            file_name=f"wheat_production_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )
        
        # CSV export
        df_export = pd.DataFrame(st.session_state.wheat_data).T
        csv_data = df_export.to_csv()
        st.download_button(
            label="📥 Download as CSV",
            data=csv_data,
            file_name=f"wheat_production_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
        
        # Database CSV export
        if DB_AVAILABLE:
            db = get_database()
            if st.button("📥 Export Database to CSV"):
                try:
                    filename = db.export_to_csv()
                    st.success(f"✅ Database exported to {filename}")
                except Exception as e:
                    st.error(f"❌ Export failed: {e}")
    
    with col2:
        st.subheader("Import Data")
        
        uploaded_file = st.file_uploader("Upload JSON data file", type=['json'])
        
        if uploaded_file is not None:
            try:
                uploaded_data = json.load(uploaded_file)
                
                if st.button("Import Data"):
                    if "wheat_production_data" in uploaded_data:
                        st.session_state.wheat_data = uploaded_data["wheat_production_data"]
                    
                    if "metadata" in uploaded_data:
                        st.session_state.projection_metadata = uploaded_data["metadata"]
                    
                    if "status_info" in uploaded_data:
                        st.session_state.status_info = uploaded_data["status_info"]
                    
                    st.success("Data imported successfully!")
                    st.rerun()
                    
            except json.JSONDecodeError:
                st.error("Invalid JSON file format")

with tab5:
    st.header("Database Management")
    
    if not DB_AVAILABLE:
        st.error("❌ Database functionality not available")
        st.markdown("""
        To enable database functionality:
        1. Ensure `database_helper.py` is in the same directory
        2. Run `python database_setup.py` to create the database
        3. Restart the Streamlit app
        """)
    else:
        db = get_database()
        if not db:
            st.error("❌ Database not found or not accessible")
        else:
            # Database statistics
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Database Statistics")
                try:
                    df_stats = db.get_production_dataframe()
                    
                    st.metric("Total Records", len(df_stats))
                    st.metric("Countries", df_stats['country'].nunique())
                    st.metric("Years", df_stats['year'].nunique())
                    
                    # Show recent updates
                    st.markdown("### Recent Records")
                    recent_data = df_stats.head(10)
                    st.dataframe(recent_data, use_container_width=True)
                    
                except Exception as e:
                    st.error(f"Error loading database stats: {e}")
            
            with col2:
                st.subheader("Database Operations")
                
                # Backup and restore
                if st.button("📦 Create Backup"):
                    try:
                        backup_data = db.backup_data()
                        backup_json = json.dumps(backup_data, indent=2)
                        st.download_button(
                            label="💾 Download Backup",
                            data=backup_json,
                            file_name=f"wheat_db_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                            mime="application/json"
                        )
                        st.success("✅ Backup created successfully!")
                    except Exception as e:
                        st.error(f"❌ Backup failed: {e}")
                
                # Show audit log
                if st.button("📋 Show Audit Log"):
                    try:
                        audit_data = db.get_audit_log(20)
                        if audit_data:
                            audit_df = pd.DataFrame(audit_data, columns=[
                                'Table', 'Record ID', 'Action', 'Old Values', 'New Values', 'Changed By', 'Changed At'
                            ])
                            st.dataframe(audit_df, use_container_width=True)
                        else:
                            st.info("No audit records found")
                    except Exception as e:
                        st.error(f"Error loading audit log: {e}")

# Footer
st.markdown("---")
status_text = "🗄️ Database Connected" if (DB_AVAILABLE and st.session_state.data_loaded) else "💾 Local Data Mode"
st.markdown(
    f"""
    <div style='text-align: center; color: #666; font-size: 0.8em;'>
    🌾 Wheat Production Forecasting Dashboard | {status_text}
    </div>
    """,
    unsafe_allow_html=True
)