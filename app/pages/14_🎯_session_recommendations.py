import streamlit as st
from streamlit import session_state as ss
import os
from pathlib import Path
import json
import pandas as pd
from dotenv import dotenv_values
import logging
from src.utils import print_stack
from src.maps import config as conf, init_session_num, reset_session_num
from src.session_recommendations import StreamlitSessionRecommendationService
from datetime import datetime
import time

# Read all Dataframe needed in this page
# where I am
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
path = Path(ROOT_DIR)
PROJECT_DIR = path.parent.absolute().as_posix()
logging.info(f"PROJECT DIR: {PROJECT_DIR}, this folder: {ROOT_DIR}")


def change_state_14(session, pp):
    """
    Change state after leaving the page
    Args:
        session: Streamlit session
        pp: Placeholder
    """
    reset_session_num(session, "14")
    pp.empty()
    del pp
    session.empty()
    session.cache_data.clear()
    session.stop()
    return


def format_visitor_for_display(visitor_data):
    """
    Format visitor data for display in selectbox
    """
    if not visitor_data:
        return "Unknown Visitor"
    
    badge_id = visitor_data.get("badge_id", "Unknown")
    job_role = visitor_data.get("job_role", "")
    job_title = visitor_data.get("job_title", "")
    what_type_does_your_practice_specialise_in = visitor_data.get("what_type_does_your_practice_specialise_in", "")
    
    # Create a display string
    display_parts = [badge_id]

    if job_title:
        display_parts.append(f"- {job_title}")
    if job_role :
        display_parts.append(f"({job_role})")
    if what_type_does_your_practice_specialise_in:
        display_parts.append(f"_ {what_type_does_your_practice_specialise_in}]")
    
    return " ".join(display_parts)


def display_session_recommendations(recommendations, title="Session Recommendations"):
    """
    Display session recommendations in a formatted table
    """
    if not recommendations:
        st.warning("No recommendations found.")
        return
    
    st.subheader(title)
    st.write(f"Found **{len(recommendations)}** recommendations")
    
    # Convert to DataFrame for better display
    df_recommendations = pd.DataFrame(recommendations)
    
    # Reorder columns for better display
    display_columns = [
        "session_id", "title", "stream", "theatre__name", 
        "date", "start_time", "end_time", "similarity"
    ]
    
    # Only include columns that exist
    available_columns = [col for col in display_columns if col in df_recommendations.columns]
    df_display = df_recommendations[available_columns].copy()
    
    # Format similarity as percentage if it exists
    if "similarity" in df_display.columns:
        df_display["similarity"] = df_display["similarity"].apply(lambda x: f"{x:.1%}" if pd.notnull(x) else "")
    
    # Display the dataframe
    st.dataframe(
        df_display,
        use_container_width=True,
        hide_index=True,
        column_config={
            "session_id": "Session ID",
            "title": "Title",
            "stream": "Stream",
            "theatre__name": "Theatre",
            "date": "Date",
            "start_time": "Start Time",
            "end_time": "End Time",
            "similarity": "Similarity",
        }
    )


def display_visitor_profile(visitor):
    """
    Display visitor profile information
    """
    if not visitor:
        st.warning("No visitor data available.")
        return
    
    st.subheader("Visitor Profile")
    
    # Create columns for better layout
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**Badge ID:** {visitor.get('BadgeId', 'N/A')}")
        st.write(f"**Email:** {visitor.get('Email', 'N/A')}")
        st.write(f"**Job Title:** {visitor.get('JobTitle', 'N/A')}")
        st.write(f"**Job Role:** {visitor.get('job_role', 'N/A')}")
        st.write(f"**Country:** {visitor.get('Country', 'N/A')}")
    
    with col2:
        st.write(f"**Organisation Type:** {visitor.get('organisation_type', 'N/A')}")
        st.write(f"**Practice Specialisation:** {visitor.get('what_type_does_your_practice_specialise_in', 'N/A')}")
        st.write(f"**Assisted Year Before:** {visitor.get('assist_year_before', 'N/A')}")
        st.write(f"**Days Since Registration:** {visitor.get('Days_since_registration', 'N/A')}")
        st.write(f"**Source:** {visitor.get('Source', 'N/A')}")


def main(placeholder):
    """
    Main function for the session recommendations page
    Args:
        placeholder: Streamlit placeholder
    """
    with placeholder.container():
        
        if st.button("Exit", on_click=change_state_14, args=(st, placeholder)):
            logging.info("Exiting session recommendations page")

        st.title("🎯 Session Recommendations")
        st.markdown("Generate personalized session recommendations for visitors based on their profile and historical data.")

        # Initialize session states
        if "init_run_14" not in st.session_state:
            st.session_state["init_run_14"] = False
        if st.session_state["init_run_14"] == False:
            init_session_num(st, ss, "14", 50, 50, conf["14"]["config_14"], None)

        # Initialize recommendation service
        if "recommendation_service_14" not in st.session_state:
            try:
                # Load configuration for recommendations
                recommendation_config = {
                    "neo4j": {
                        "uri": os.environ.get("NEO4J_URI", "neo4j+s://c6cfaac8.databases.neo4j.io"),
                        "username": os.environ.get("NEO4J_USERNAME", "neo4j"),
                        "password": os.environ.get("NEO4J_PASSWORD", ""),
                    },
                    "recommendation": {
                        "rules_config": {
                            "equine_mixed_exclusions": ["exotics", "feline", "exotic animal", "farm", "small animal"],
                            "small_animal_exclusions": ["equine", "farm animal", "farm", "large animal"],
                            "vet_exclusions": ["nursing"],
                            "nurse_streams": ["nursing", "wellbeing", "welfare"],
                            "rule_priority": ["practice_type", "role"],
                        }
                    }
                }
                
                st.session_state["recommendation_service_14"] = StreamlitSessionRecommendationService(recommendation_config)
                st.success("✅ Recommendation service initialized successfully!")
            except Exception as e:
                st.error(f"❌ Failed to initialize recommendation service: {str(e)}")
                st.session_state["recommendation_service_14"] = None
                logging.error(f"Error initializing recommendation service: {e}")

        # Load visitor list
        if "visitor_list_14" not in st.session_state:
            if st.session_state["recommendation_service_14"] is not None:
                try:
                    with st.spinner("Loading visitor list from Neo4j..."):
                        st.session_state["visitor_list_14"] = st.session_state["recommendation_service_14"].get_all_visitors()
                    st.success(f"✅ Loaded {len(st.session_state['visitor_list_14'])} visitors")
                except Exception as e:
                    st.error(f"❌ Failed to load visitor list: {str(e)}")
                    st.session_state["visitor_list_14"] = []
                    logging.error(f"Error loading visitor list: {e}")
            else:
                st.session_state["visitor_list_14"] = []

        # Check if we have the service and visitor list
        if st.session_state["recommendation_service_14"] is None:
            st.error("❌ Recommendation service not available. Please check your configuration and Neo4j connection.")
            return

        if not st.session_state["visitor_list_14"]:
            st.warning("⚠️ No visitors found. Please ensure your Neo4j database is populated with visitor data.")
            return

        # Create the main interface
        col1, col2 = st.columns([1, 1])

        with col1:
            st.subheader("🔍 Select Visitor")
            
            # Create visitor selection options
            visitor_options = [format_visitor_for_display(visitor) for visitor in st.session_state["visitor_list_14"]]
            visitor_options.insert(0, "-- Select a visitor --")
            
            selected_visitor_display = st.selectbox(
                "Choose a visitor by Badge ID:",
                visitor_options,
                key="visitor_selector_14"
            )
            
            # Get the selected visitor data
            selected_visitor = None
            if selected_visitor_display != "-- Select a visitor --":
                # Extract badge_id from the display string
                badge_id = selected_visitor_display.split()[0]
                selected_visitor = next(
                    (v for v in st.session_state["visitor_list_14"] if v["badge_id"] == badge_id), 
                    None
                )

        with col2:
            st.subheader("⚙️ Recommendation Settings")
            
            # Recommendation parameters
            min_score = st.slider(
                "Minimum Similarity Score",
                min_value=0.0,
                max_value=1.0,
                value=0.3,
                step=0.1,
                help="Minimum similarity score for recommendations (0.0 to 1.0)"
            )
            
            max_recommendations = st.slider(
                "Maximum Recommendations",
                min_value=5,
                max_value=50,
                value=20,
                step=5,
                help="Maximum number of recommendations to return"
            )
            
            # Filtering method selection
            filtering_method = st.radio(
                "Filtering Method",
                ["Neo4j Rules", "LangChain (LLM)"],
                help="Choose the method for filtering recommendations"
            )
            
            use_langchain = filtering_method == "LangChain (LLM)"

        # Generate recommendations button
        if selected_visitor:
            st.divider()
            
            # Display visitor profile
            with st.expander("👤 View Visitor Profile", expanded=False):
                # Get full visitor data from Neo4j
                try:
                    full_visitor_data = st.session_state["recommendation_service_14"].get_visitor_by_badge_id(selected_visitor["badge_id"])
                    display_visitor_profile(full_visitor_data)
                except Exception as e:
                    st.error(f"Error loading visitor profile: {str(e)}")
            
            # Generate recommendations
            if st.button("🎯 Generate Recommendations", type="primary", use_container_width=True):
                try:
                    with st.spinner("Generating recommendations... This may take a few moments."):
                        start_time = time.time()
                        
                        # Get recommendations
                        result = st.session_state["recommendation_service_14"].get_recommendations_and_filter(
                            badge_id=selected_visitor["badge_id"],
                            min_score=min_score,
                            max_recommendations=max_recommendations,
                            use_langchain=use_langchain
                        )
                        
                        processing_time = time.time() - start_time
                        
                        # Store results in session state
                        st.session_state["last_recommendation_result_14"] = result
                        st.session_state["last_processing_time_14"] = processing_time
                        
                        # Display success message
                        st.success(f"✅ Recommendations generated in {processing_time:.2f} seconds!")
                        
                except Exception as e:
                    st.error(f"❌ Error generating recommendations: {str(e)}")
                    logging.error(f"Error generating recommendations: {e}")

        # Display results if available
        if "last_recommendation_result_14" in st.session_state:
            result = st.session_state["last_recommendation_result_14"]
            processing_time = st.session_state.get("last_processing_time_14", 0)
            
            if result.get("metadata", {}).get("error"):
                st.error(f"❌ Error: {result['metadata']['error']}")
            else:
                st.divider()
                
                # Display summary
                st.subheader("📊 Recommendation Summary")
                summary_col1, summary_col2, summary_col3 = st.columns(3)
                
                with summary_col1:
                    st.metric("Raw Recommendations", result["metadata"]["num_raw_recommendations"])
                
                with summary_col2:
                    st.metric("Filtered Recommendations", result["metadata"]["num_filtered_recommendations"])
                
                with summary_col3:
                    st.metric("Processing Time", f"{processing_time:.2f}s")
                
                # Display processing steps
                with st.expander("🔍 Processing Details", expanded=False):
                    st.write("**Processing Steps:**")
                    for step in result["metadata"]["processing_steps"]:
                        st.write(f"• {step}")
                
                # Display recommendations in tabs
                tab1, tab2 = st.tabs(["🎯 Filtered Recommendations", "📋 Raw Recommendations"])
                
                with tab1:
                    display_session_recommendations(
                        result["filtered_recommendations"], 
                        f"Filtered Recommendations ({filtering_method})"
                    )
                
                with tab2:
                    display_session_recommendations(
                        result["raw_recommendations"], 
                        "Raw Recommendations (Before Filtering)"
                    )
                
                # Export options
                if result["filtered_recommendations"]:
                    st.divider()
                    st.subheader("💾 Export Results")
                    
                    export_col1, export_col2 = st.columns(2)
                    
                    with export_col1:
                        # Export filtered recommendations as CSV
                        df_filtered = pd.DataFrame(result["filtered_recommendations"])
                        csv_filtered = df_filtered.to_csv(index=False)
                        st.download_button(
                            label="📄 Download Filtered Recommendations (CSV)",
                            data=csv_filtered,
                            file_name=f"filtered_recommendations_{selected_visitor['badge_id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv"
                        )
                    
                    with export_col2:
                        # Export full result as JSON
                        json_result = json.dumps(result, indent=2, default=str)
                        st.download_button(
                            label="📋 Download Full Result (JSON)",
                            data=json_result,
                            file_name=f"recommendations_full_{selected_visitor['badge_id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                            mime="application/json"
                        )


if __name__ == "__main__":
    # Set page layout
    st.set_page_config(layout="wide", initial_sidebar_state="collapsed")
    
    # Go to login page if not authenticated
    if (
        st.session_state.get("authentication_status") is None
        or st.session_state.get("authentication_status") is False
    ):
        st.session_state.runpage = "main.py"
        st.switch_page("main.py")

    # Initialize session state for exit handling
    if "salir_14" not in st.session_state:
        st.session_state["salir_14"] = False

    if st.session_state["salir_14"] == False:
        placeholder_recommendations = st.empty()
        
        try:
            # Load environment configuration
            config = dotenv_values(os.path.join(PROJECT_DIR, "keys", ".env"))
            
            # Set environment variables for Neo4j connection
            if "NEO4J_URI" not in os.environ:
                os.environ["NEO4J_URI"] = config.get("NEO4J_URI", "")
            if "NEO4J_USERNAME" not in os.environ:
                os.environ["NEO4J_USERNAME"] = config.get("NEO4J_USERNAME", "neo4j")
            if "NEO4J_PASSWORD" not in os.environ:
                os.environ["NEO4J_PASSWORD"] = config.get("NEO4J_PASSWORD", "")
            
            # Set Azure OpenAI environment variables if available
            if "AZURE_ENDPOINT" not in os.environ:
                os.environ["AZURE_ENDPOINT"] = config.get("AZURE_ENDPOINT", "")
            if "AZURE_API_KEY" not in os.environ:
                os.environ["AZURE_API_KEY"] = config.get("AZURE_API_KEY", "")
            if "AZURE_DEPLOYMENT" not in os.environ:
                os.environ["AZURE_DEPLOYMENT"] = config.get("AZURE_DEPLOYMENT", "")
            if "AZURE_API_VERSION" not in os.environ:
                os.environ["AZURE_API_VERSION"] = config.get("AZURE_API_VERSION", "")
            
            main(placeholder=placeholder_recommendations)
            
        except Exception as e:
            st.session_state["salir_14"] = True
            placeholder_recommendations.empty()
            text = print_stack()
            text = "Session Recommendations Page Error: " + text
            logging.error(text)
            st.error(f"An error occurred: {str(e)}")