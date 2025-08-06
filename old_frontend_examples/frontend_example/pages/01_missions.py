# pages/01_🚀_Missions.py - Missions management page
import streamlit as st
import pandas as pd
import sys
from pathlib import Path
from datetime import datetime, timezone
import json

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from utils.api_client import APIClient
from utils.validators import validate_form_and_display_errors
from config.settings import API_BASE_URL, TARGET_TYPES, LEVEL_CHOICES

# Page configuration
st.set_page_config(page_title="🚀 Missions", layout="wide")

# Initialize API client
if 'api_client' not in st.session_state:
    st.session_state.api_client = APIClient(API_BASE_URL)

def display_missions_table(missions):
    """Display missions in a table format"""
    if not missions:
        st.info("No missions found")
        return
    
    # Convert to DataFrame for better display
    df = pd.DataFrame(missions)
    
    # Select and rename columns for display
    display_columns = {
        'id': 'ID',
        'location': 'Location',
        'target_type': 'Target Type',
        'start_time': 'Start Time',
        'end_time': 'End Time',
        'max_depth': 'Max Depth (m)',
        'visibility': 'Visibility',
        'cloud_cover': 'Cloud Cover',
        'tide_level': 'Tide Level'
    }
    
    # Filter and rename columns
    available_columns = [col for col in display_columns.keys() if col in df.columns]
    df_display = df[available_columns].copy()
    df_display = df_display.rename(columns=display_columns)
    
    # Format datetime columns
    for col in ['Start Time', 'End Time']:
        if col in df_display.columns:
            df_display[col] = pd.to_datetime(df_display[col], errors='coerce').dt.strftime('%Y-%m-%d %H:%M')
    
    # Add a manual selection column
    df_display["Select"] = False
    edited_df = st.data_editor(df_display, use_container_width=True, key="mission_table")

    # Check for selected mission via checkbox
    selected_rows = edited_df[edited_df["Select"] == True]
    
    if not selected_rows.empty:
        selected_index = selected_rows.index[0]
        selected_mission = missions[selected_index]
        st.session_state.selected_mission = selected_mission
        return selected_mission

    return None

def display_mission_details(mission):
    """Display detailed view of a selected mission"""
    st.subheader(f"Mission Details - {mission.get('location', 'Unknown Location')}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**ID:** {mission.get('id', 'N/A')}")
        st.write(f"**Location:** {mission.get('location', 'N/A')}")
        st.write(f"**Target Type:** {mission.get('target_type', 'N/A').title()}")
        st.write(f"**Start Time:** {mission.get('start_time', 'N/A')}")
        st.write(f"**End Time:** {mission.get('end_time', 'N/A') or 'Ongoing'}")
    
    with col2:
        st.write(f"**Max Depth:** {mission.get('max_depth', 'N/A')} m")
        st.write(f"**Visibility:** {mission.get('visibility', 'N/A').title()}")
        st.write(f"**Cloud Cover:** {mission.get('cloud_cover', 'N/A').title()}")
        st.write(f"**Tide Level:** {mission.get('tide_level', 'N/A').title()}")
    
    if mission.get('notes'):
        st.write(f"**Notes:** {mission.get('notes')}")
    
    # Show rover information
    rover_info = mission.get('rover')
    if rover_info:
        st.subheader("Rover Information")
        if isinstance(rover_info, dict):
            st.write(f"**Rover:** {rover_info.get('name', 'N/A')}")
            st.write(f"**Hardware Config:** {rover_info.get('hardware_config', 'N/A')}")
        else:
            st.write(f"**Rover ID:** {rover_info}")

def create_mission_form():
    """Create form for adding/editing missions"""
    st.subheader("Add New Mission")
    
    # Get available rovers
    try:
        rovers = st.session_state.api_client.get_rover_hardware()
        if not rovers:
            st.warning("No rovers available. Please add a rover first.")
            return
    except Exception as e:
        st.error(f"Error loading rovers: {str(e)}")
        return
    
    with st.form("mission_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            # Rover selection
            rover_options = {rover['id']: rover['name'] for rover in rovers}
            selected_rover = st.selectbox(
                "Select Rover",
                options=list(rover_options.keys()),
                format_func=lambda x: rover_options[x]
            )
            
            # Location
            location = st.text_input("Location", placeholder="e.g., Great Barrier Reef")
            
            # Target type
            target_type = st.selectbox(
                "Target Type",
                options=[choice[0] for choice in TARGET_TYPES],
                format_func=lambda x: next(choice[1] for choice in TARGET_TYPES if choice[0] == x)
            )
            
            # Start time
            start_date = st.date_input("Start Date", value=datetime.now().date())
            start_time = st.time_input("Start Time", value=datetime.now().time())
            
        with col2:
            # End time (optional)
            end_date = st.date_input("End Date (Optional)", value=None)
            end_time = st.time_input("End Time (Optional)", value=None)
            
            # Max depth
            max_depth = st.number_input("Max Depth (m)", min_value=0.0, value=10.0, step=0.1)
            
            # Environmental conditions
            visibility = st.selectbox(
                "Visibility",
                options=[choice[0] for choice in LEVEL_CHOICES],
                format_func=lambda x: next(choice[1] for choice in LEVEL_CHOICES if choice[0] == x),
                index=1  # Default to medium
            )
            
            cloud_cover = st.selectbox(
                "Cloud Cover",
                options=[choice[0] for choice in LEVEL_CHOICES],
                format_func=lambda x: next(choice[1] for choice in LEVEL_CHOICES if choice[0] == x),
                index=1  # Default to medium
            )
            
            tide_level = st.selectbox(
                "Tide Level",
                options=[choice[0] for choice in LEVEL_CHOICES],
                format_func=lambda x: next(choice[1] for choice in LEVEL_CHOICES if choice[0] == x),
                index=1  # Default to medium
            )
        
        # Notes
        notes = st.text_area("Notes", placeholder="Additional mission details...")
        
        # Submit button
        submitted = st.form_submit_button("Create Mission")
        
        if submitted:
            # Combine date and time
            start_datetime = datetime.combine(start_date, start_time)
            start_datetime = start_datetime.replace(tzinfo=timezone.utc)
            
            end_datetime = None
            if end_date and end_time:
                end_datetime = datetime.combine(end_date, end_time)
                end_datetime = end_datetime.replace(tzinfo=timezone.utc)
            
            # Prepare mission data
            mission_data = {
                'rover': selected_rover,
                'location': location,
                'target_type': target_type,
                'start_time': start_datetime.isoformat(),
                'end_time': end_datetime.isoformat() if end_datetime else None,
                'max_depth': max_depth,
                'visibility': visibility,
                'cloud_cover': cloud_cover,
                'tide_level': tide_level,
                'notes': notes
            }
            
            # Validate form
            if validate_form_and_display_errors(mission_data, 'mission'):
                try:
                    # Create mission
                    result = st.session_state.api_client.create_mission(mission_data)
                    if result:
                        st.success("Mission created successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to create mission")
                except Exception as e:
                    st.error(f"Error creating mission: {str(e)}")

def main():
    """Main function for the missions page"""
    st.title("🚀 Mission Management")
    st.markdown("---")
    
    # Create tabs
    tab1, tab2 = st.tabs(["📋 View Missions", "➕ Add Mission"])
    
    with tab1:
        st.header("All Missions")
        
        # Load missions
        try:
            missions = st.session_state.api_client.get_missions()
            
            if missions:
                # Display missions table
                selected_mission = display_missions_table(missions)
                
                # Display mission details if selected
                if selected_mission or st.session_state.get('selected_mission'):
                    mission_to_show = selected_mission or st.session_state.get('selected_mission')
                    st.markdown("---")
                    display_mission_details(mission_to_show)
                
                # Show summary statistics
                st.sidebar.header("Mission Statistics")
                
                # Count by target type
                target_counts = {}
                for mission in missions:
                    target_type = mission.get('target_type', 'Unknown')
                    target_counts[target_type] = target_counts.get(target_type, 0) + 1
                
                for target_type, count in target_counts.items():
                    st.sidebar.metric(f"{target_type.title()} Missions", count)
                
                # Show locations
                locations = list(set(mission.get('location', 'Unknown') for mission in missions))
                st.sidebar.write(f"**Locations:** {len(locations)}")
                for location in sorted(locations):
                    st.sidebar.write(f"• {location}")
                
            else:
                st.info("No missions found. Add your first mission using the 'Add Mission' tab.")
                
        except Exception as e:
            st.error(f"Error loading missions: {str(e)}")
    
    with tab2:
        create_mission_form()
    
    # Refresh button
    if st.button("🔄 Refresh Data"):
        st.rerun()

if __name__ == "__main__":
    main()