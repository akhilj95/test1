# app.py - Main Streamlit Application for Underwater Rover Mission Management
import streamlit as st
import sys
from pathlib import Path

# Add utils directory to path
sys.path.append(str(Path(__file__).parent))

from config.settings import API_BASE_URL, PROJECT_DIR
from utils.api_client import APIClient

# Configure page
st.set_page_config(
    page_title="🌊 Underwater Rover Mission Control",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize API client
if 'api_client' not in st.session_state:
    st.session_state.api_client = APIClient(API_BASE_URL)

# Initialize session state
if 'current_mission' not in st.session_state:
    st.session_state.current_mission = None

def main():
    """Main application function"""
    
    # Main header
    st.title("🌊 Underwater Inspection Database Viewer")
    st.markdown("---")
    
    # Welcome message
    st.markdown("""
    ## Welcome to the Underwater Inspection Database Viewer
    
    This application allows you to manage underwater rover missions, sensors, calibrations, and media assets.
    Use the navigation sidebar to access different sections:
    
    - 🚀 **Missions**: View and manage rover missions
    - 🔧 **Sensors**: Configure sensors and add new ones
    - 📊 **Calibrations**: Manage sensor calibrations
    - 🎥 **Media Explorer**: Browse and filter media assets by location
    """)
    
    # Quick stats
    try:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            missions = st.session_state.api_client.get_missions()
            st.metric("📋 Total Missions", len(missions) if missions else 0)
        
        with col2:
            sensors = st.session_state.api_client.get_sensors()
            st.metric("🔧 Total Sensors", len(sensors) if sensors else 0)
        
        with col3:
            calibrations = st.session_state.api_client.get_calibrations()
            st.metric("📊 Calibrations", len(calibrations) if calibrations else 0)
        
        with col4:
            media_assets = st.session_state.api_client.get_media_assets()
            st.metric("🎥 Media Assets", len(media_assets) if media_assets else 0)
            
    except Exception as e:
        st.error(f"Error loading dashboard stats: {str(e)}")
    
    # Instructions
    st.markdown("""    
    ### Features:
    - **Mission Management**: Create, view, and update mission details
    - **Sensor Configuration**: Add new sensors and manage existing ones
    - **Calibration Management**: Update and track sensor calibrations
    - **Media Asset Browser**: Filter and view media assets by location and navigation data
    """)
    
    # System status
    st.markdown("---")
    st.markdown("### System Status")
    
    # Check API connection
    try:
        health_check = st.session_state.api_client.health_check()
        if health_check:
            st.success("✅ Connected to Django Backend")
        else:
            st.error("❌ Cannot connect to Django Backend")
    except Exception as e:
        st.error(f"❌ Django Backend Error: {str(e)}")
    
    # Show current configuration
    with st.expander("🔧 Configuration"):
        st.code(f"""
API Base URL: {API_BASE_URL}
Project Directory: {PROJECT_DIR}
Media Files Path: {PROJECT_DIR}/data/
        """)

if __name__ == "__main__":
    main()