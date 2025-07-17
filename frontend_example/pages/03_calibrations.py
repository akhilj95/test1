# pages/03_📊_Calibrations.py - Calibration management page
import streamlit as st
import pandas as pd
import sys
from pathlib import Path
import json
from datetime import datetime, timezone

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from utils.api_client import APIClient
from utils.validators import validate_form_and_display_errors
from config.settings import API_BASE_URL

# Page configuration
st.set_page_config(page_title="📊 Calibrations", layout="wide")

# Initialize API client
if 'api_client' not in st.session_state:
    st.session_state.api_client = APIClient(API_BASE_URL)

def display_calibrations_table(calibrations):
    """Display calibrations in a table format"""
    if not calibrations:
        st.info("No calibrations found")
        return None
    
    # Convert to DataFrame for better display
    df = pd.DataFrame(calibrations)
    
    # Select and rename columns for display
    display_columns = {
        'id': 'ID',
        'sensor': 'Sensor ID',
        'effective_from': 'Effective From',
        'active': 'Active',
        'coefficients': 'Coefficients'
    }
    
    # Filter and rename columns
    available_columns = [col for col in display_columns.keys() if col in df.columns]
    df_display = df[available_columns].copy()
    df_display = df_display.rename(columns=display_columns)
    
    # Format datetime columns
    if 'Effective From' in df_display.columns:
        df_display['Effective From'] = pd.to_datetime(df_display['Effective From'], errors='coerce').dt.strftime('%Y-%m-%d %H:%M')
    
    # Format coefficients column
    if 'Coefficients' in df_display.columns:
        df_display['Coefficients'] = df_display['Coefficients'].apply(
            lambda x: f"{len(x)} coefficients" if isinstance(x, dict) and x else "No coefficients"
        )
    
    # Format active column
    if 'Active' in df_display.columns:
        df_display['Active'] = df_display['Active'].apply(lambda x: "✅ Yes" if x else "❌ No")
    
    # Add selection column
    df_display["Select"] = False
    
    # Display with selection using data_editor
    edited_df = st.data_editor(
        df_display,
        use_container_width=True,
        hide_index=True,
        key="calibrations_table",
        column_config={
            "Select": st.column_config.CheckboxColumn(
                "Select",
                help="Select a calibration",
                default=False,
            )
        }
    )
    
    # Check for selected calibration
    selected_rows = edited_df[edited_df["Select"] == True]
    if not selected_rows.empty:
        selected_idx = selected_rows.index[0]
        selected_calibration = calibrations[selected_idx]
        st.session_state.selected_calibration = selected_calibration
        return selected_calibration

    return None

def display_calibration_details(calibration):
    """Display detailed view of a selected calibration"""
    st.subheader(f"Calibration Details - ID {calibration.get('id', 'N/A')}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**ID:** {calibration.get('id', 'N/A')}")
        st.write(f"**Sensor ID:** {calibration.get('sensor', 'N/A')}")
        st.write(f"**Effective From:** {calibration.get('effective_from', 'N/A')}")
        st.write(f"**Active:** {'Yes' if calibration.get('active') else 'No'}")
    
    with col2:
        # Show coefficients
        coeffs = calibration.get('coefficients', {})
        if coeffs:
            st.write("**Coefficients:**")
            for key, value in coeffs.items():
                st.write(f"• {key}: {value}")
        else:
            st.write("**Coefficients:** No coefficients provided")
    
    # Show sensor details if available
    sensor_id = calibration.get('sensor')
    if sensor_id:
        try:
            sensor = st.session_state.api_client.get_sensor(sensor_id)
            if sensor:
                st.subheader("Associated Sensor")
                st.write(f"**Name:** {sensor.get('name', 'N/A')}")
                st.write(f"**Type:** {sensor.get('sensor_type', 'N/A').title()}")
        except Exception as e:
            st.warning(f"Could not load sensor details: {str(e)}")

def create_calibration_form():
    """Create form for adding/editing calibrations"""
    st.subheader("Add New Calibration")
    
    # Get available sensors
    try:
        sensors = st.session_state.api_client.get_sensors()
        if not sensors:
            st.warning("No sensors available. Please add a sensor first.")
            return
    except Exception as e:
        st.error(f"Error loading sensors: {str(e)}")
        return
    
    with st.form("calibration_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            # Sensor selection
            sensor_options = {sensor['id']: f"{sensor['name']} ({sensor['sensor_type']})" for sensor in sensors}
            selected_sensor = st.selectbox(
                "Select Sensor",
                options=list(sensor_options.keys()),
                format_func=lambda x: sensor_options[x]
            )
            
            # Effective from date/time
            effective_date = st.date_input("Effective From Date", value=datetime.now().date())
            effective_time = st.time_input("Effective From Time", value=datetime.now().time())
        
        with col2:
            # Coefficients (JSON)
            st.write("**Calibration Coefficients (JSON format):**")
            coeffs_text = st.text_area(
                "Coefficients",
                placeholder='{"offset_x": 0.1, "offset_y": 0.2, "scale": 1.0}',
                height=150,
                label_visibility="collapsed"
            )
        
        # Submit button
        submitted = st.form_submit_button("Create Calibration")
        
        if submitted:
            # Parse coefficients JSON
            coefficients = {}
            if coeffs_text.strip():
                try:
                    coefficients = json.loads(coeffs_text)
                except json.JSONDecodeError:
                    st.error("Invalid JSON format in coefficients")
                    return
            
            # Combine date and time
            effective_datetime = datetime.combine(effective_date, effective_time)
            effective_datetime = effective_datetime.replace(tzinfo=timezone.utc)
            
            # Prepare calibration data
            calibration_data = {
                'sensor': selected_sensor,
                'effective_from': effective_datetime.isoformat(),
                'coefficients': coefficients,
                'active': True  # New calibrations are active by default
            }
            
            # Validate form
            if validate_form_and_display_errors(calibration_data, 'calibration'):
                try:
                    # Create calibration
                    result = st.session_state.api_client.create_calibration(calibration_data)
                    if result:
                        st.success("Calibration created successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to create calibration")
                except Exception as e:
                    st.error(f"Error creating calibration: {str(e)}")

def edit_calibration_form(calibration):
    """Create form for editing an existing calibration"""
    st.subheader(f"Edit Calibration - ID {calibration.get('id', 'Unknown')}")
    
    # Get available sensors
    try:
        sensors = st.session_state.api_client.get_sensors()
        if not sensors:
            st.warning("No sensors available.")
            return
    except Exception as e:
        st.error(f"Error loading sensors: {str(e)}")
        return
    
    with st.form("edit_calibration_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            # Sensor selection
            sensor_options = {sensor['id']: f"{sensor['name']} ({sensor['sensor_type']})" for sensor in sensors}
            current_sensor = calibration.get('sensor')
            sensor_index = list(sensor_options.keys()).index(current_sensor) if current_sensor in sensor_options else 0
            
            selected_sensor = st.selectbox(
                "Select Sensor",
                options=list(sensor_options.keys()),
                format_func=lambda x: sensor_options[x],
                index=sensor_index
            )
            
            # Effective from date/time
            current_effective = calibration.get('effective_from')
            if current_effective:
                try:
                    effective_dt = datetime.fromisoformat(current_effective.replace('Z', '+00:00'))
                    effective_date = st.date_input("Effective From Date", value=effective_dt.date())
                    effective_time = st.time_input("Effective From Time", value=effective_dt.time())
                except:
                    effective_date = st.date_input("Effective From Date", value=datetime.now().date())
                    effective_time = st.time_input("Effective From Time", value=datetime.now().time())
            else:
                effective_date = st.date_input("Effective From Date", value=datetime.now().date())
                effective_time = st.time_input("Effective From Time", value=datetime.now().time())
            
            # Active status
            active = st.checkbox("Active", value=calibration.get('active', True))
        
        with col2:
            # Coefficients (JSON)
            st.write("**Calibration Coefficients (JSON format):**")
            current_coeffs = calibration.get('coefficients', {})
            coeffs_text = st.text_area(
                "Coefficients",
                value=json.dumps(current_coeffs, indent=2) if current_coeffs else "",
                height=150,
                label_visibility="collapsed"
            )
        
        # Submit button
        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button("Update Calibration")
        with col2:
            delete_clicked = st.form_submit_button("Delete Calibration", type="secondary")
        
        if submitted:
            # Parse coefficients JSON
            coefficients = {}
            if coeffs_text.strip():
                try:
                    coefficients = json.loads(coeffs_text)
                except json.JSONDecodeError:
                    st.error("Invalid JSON format in coefficients")
                    return
            
            # Combine date and time
            effective_datetime = datetime.combine(effective_date, effective_time)
            effective_datetime = effective_datetime.replace(tzinfo=timezone.utc)
            
            # Prepare calibration data
            calibration_data = {
                'sensor': selected_sensor,
                'effective_from': effective_datetime.isoformat(),
                'coefficients': coefficients,
                'active': active
            }
            
            # Validate form
            if validate_form_and_display_errors(calibration_data, 'calibration'):
                try:
                    # Update calibration
                    result = st.session_state.api_client.update_calibration(calibration['id'], calibration_data)
                    if result:
                        st.success("Calibration updated successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to update calibration")
                except Exception as e:
                    st.error(f"Error updating calibration: {str(e)}")
        
        if delete_clicked:
            # Use session state for confirmation instead of inline buttons
            if 'confirm_delete_calibration' not in st.session_state:
                st.session_state.confirm_delete_calibration = False
            
            if not st.session_state.confirm_delete_calibration:
                st.warning("Are you sure you want to delete this calibration?")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Yes, Delete", key="confirm_delete_btn"):
                        st.session_state.confirm_delete_calibration = True
                        st.rerun()
                with col2:
                    if st.button("Cancel", key="cancel_delete_btn"):
                        st.session_state.confirm_delete_calibration = False
                        st.rerun()
            else:
                try:
                    success = st.session_state.api_client.delete_calibration(calibration['id'])
                    if success:
                        st.success("Calibration deleted successfully!")
                        st.session_state.selected_calibration = None
                        st.session_state.confirm_delete_calibration = False
                        st.rerun()
                    else:
                        st.error("Failed to delete calibration")
                        st.session_state.confirm_delete_calibration = False
                except Exception as e:
                    st.error(f"Error deleting calibration: {str(e)}")
                    st.session_state.confirm_delete_calibration = False

def main():
    """Main function for the calibrations page"""
    st.title("📊 Calibration Management")
    st.markdown("---")
    
    # Create tabs
    tab1, tab2 = st.tabs(["📋 View Calibrations", "➕ Add Calibration"])
    
    with tab1:
        st.header("All Calibrations")
        
        # Load calibrations
        try:
            calibrations = st.session_state.api_client.get_calibrations()
            
            if calibrations:
                # Display calibrations table
                selected_calibration = display_calibrations_table(calibrations)
                
                # Display calibration details if selected
                if selected_calibration or st.session_state.get('selected_calibration'):
                    calibration_to_show = selected_calibration or st.session_state.get('selected_calibration')
                    st.markdown("---")
                    display_calibration_details(calibration_to_show)
                    
                    # Show edit form
                    st.markdown("---")
                    edit_calibration_form(calibration_to_show)
                
                # Show summary statistics
                st.sidebar.header("Calibration Statistics")
                
                # Count active vs inactive
                active_count = sum(1 for cal in calibrations if cal.get('active'))
                inactive_count = len(calibrations) - active_count
                
                st.sidebar.metric("Active Calibrations", active_count)
                st.sidebar.metric("Inactive Calibrations", inactive_count)
                st.sidebar.metric("Total Calibrations", len(calibrations))
                
                # Show sensor distribution
                sensor_counts = {}
                for calibration in calibrations:
                    sensor_id = calibration.get('sensor', 'Unknown')
                    sensor_counts[sensor_id] = sensor_counts.get(sensor_id, 0) + 1
                
                if sensor_counts:
                    st.sidebar.write("**Calibrations by Sensor:**")
                    for sensor_id, count in sorted(sensor_counts.items()):
                        st.sidebar.write(f"• Sensor {sensor_id}: {count}")
                
            else:
                st.info("No calibrations found. Add your first calibration using the 'Add Calibration' tab.")
                
        except Exception as e:
            st.error(f"Error loading calibrations: {str(e)}")
    
    with tab2:
        create_calibration_form()
    
    # Refresh button
    if st.button("🔄 Refresh Data"):
        st.rerun()

if __name__ == "__main__":
    main()
