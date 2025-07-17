# pages/04_🎥_Media_Explorer.py - Media asset exploration page
import streamlit as st
import pandas as pd
import sys
from pathlib import Path
from typing import List, Dict, Optional

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from utils.api_client import APIClient
from utils.file_utils import display_media_file, create_media_grid, display_media_with_nav_data, get_file_info
from config.settings import API_BASE_URL, PROJECT_DIR, DEFAULT_DEPTH_RANGE, DEFAULT_YAW_RANGE, MEDIA_TYPES

# Page configuration
st.set_page_config(page_title="🎥 Media Explorer", layout="wide")

# Initialize API client
if 'api_client' not in st.session_state:
    st.session_state.api_client = APIClient(API_BASE_URL)

def get_location_options():
    """Get available locations from missions"""
    try:
        locations = st.session_state.api_client.get_locations()
        return locations if isinstance(locations, list) else []
    except Exception as e:
        st.error(f"Error loading locations: {str(e)}")
        return []

def create_filter_sidebar():
    """Create sidebar with filtering options"""
    with st.sidebar:
        st.header("🔍 Media Filters")
        
        # Location filter
        locations = get_location_options()
        if not locations:
            st.warning("No locations available")
            return None
        
        selected_location = st.selectbox("Select Location", locations)
        
        # Media type filter
        media_types = [choice[0] for choice in MEDIA_TYPES]
        selected_media_types = st.multiselect(
            "Media Types",
            options=media_types,
            default=media_types,
            format_func=lambda x: x.title()
        )
        
        # Navigation data filters
        st.subheader("Navigation Filters")
        
        # Depth range filter - Fix the type mismatch
        depth_range = st.slider(
            "Depth Range (m)",
            min_value=0.0,
            max_value=200.0,
            value=(float(DEFAULT_DEPTH_RANGE[0]), float(DEFAULT_DEPTH_RANGE[1])),
            step=0.1,
            help="Filter by depth in meters"
        )
        
        # Yaw range filter - Fix the type mismatch
        yaw_range = st.slider(
            "Yaw Range (°)",
            min_value=0.0,
            max_value=360.0,
            value=(float(DEFAULT_YAW_RANGE[0]), float(DEFAULT_YAW_RANGE[1])),
            step=1.0,
            help="Filter by yaw angle in degrees"
        )
        
        # Advanced filters
        with st.expander("Advanced Filters"):
            # Time range filter
            use_time_filter = st.checkbox("Filter by Time Range")
            start_time = None
            end_time = None
            
            if use_time_filter:
                start_date = st.date_input("Start Date")
                end_date = st.date_input("End Date")
                start_time = st.time_input("Start Time")
                end_time = st.time_input("End Time")
        
        # Apply filters button
        apply_filters = st.button("🔍 Apply Filters", type="primary")
        
        return {
            'location': selected_location,
            'media_types': selected_media_types,
            'depth_range': depth_range,
            'yaw_range': yaw_range,
            'apply_filters': apply_filters
        }

def get_filtered_media(filters: Dict) -> List[Dict]:
    """Get media assets based on filters"""
    try:
        # Get media by location with nav sample filtering
        media_assets = st.session_state.api_client.get_media_by_location(
            location=filters['location'],
            depth_min=filters['depth_range'][0],
            depth_max=filters['depth_range'][1],
            yaw_min=filters['yaw_range'][0],
            yaw_max=filters['yaw_range'][1]
        )
        
        # Guard against bad API response
        if not isinstance(media_assets, list):
            st.error("Unexpected response from API. Please adjust your filters.")
            return []
        
        # Filter by media type if specified
        if filters['media_types']:
            media_assets = [
                asset for asset in media_assets 
                if asset.get('media_type') in filters['media_types']
            ]
        
        return media_assets
    except Exception as e:
        st.error(f"Error loading media assets: {str(e)}")
        return []

def display_media_stats(media_assets: List[Dict]):
    """Display statistics about the media assets"""
    if not media_assets:
        return
    
    # Count by media type
    type_counts = {}
    for asset in media_assets:
        media_type = asset.get('media_type', 'Unknown')
        type_counts[media_type] = type_counts.get(media_type, 0) + 1
    
    # Display metrics
    cols = st.columns(len(type_counts) + 1)
    
    with cols[0]:
        st.metric("Total Media", len(media_assets))
    
    for i, (media_type, count) in enumerate(type_counts.items()):
        with cols[i + 1]:
            st.metric(f"{media_type.title()}s", count)

def display_detailed_media_list(media_assets: List[Dict]):
    """Display detailed list of media assets"""
    if not media_assets:
        st.info("No media assets found with the current filters")
        return
    
    st.subheader(f"Media Assets ({len(media_assets)} items)")
    
    # Create DataFrame for filtering and sorting
    df_data = []
    for asset in media_assets:
        # Get navigation data from first frame if available
        frames = asset.get('frames', [])
        nav_data = {}
        if frames:
            nav_sample = frames[0].get('closest_nav_sample', {})
            nav_data = {
                'depth_m': nav_sample.get('depth_m'),
                'yaw_deg': nav_sample.get('yaw_deg'),
                'pitch_deg': nav_sample.get('pitch_deg'),
                'roll_deg': nav_sample.get('roll_deg')
            }
        
        df_data.append({
            'id': asset.get('id'),
            'file_path': asset.get('file_path', ''),
            'media_type': asset.get('media_type', 'Unknown'),
            'start_time': asset.get('start_time', ''),
            'sensor': asset.get('deployment_details', {}).get('sensor_name', 'Unknown'),
            'depth_m': nav_data.get('depth_m'),
            'yaw_deg': nav_data.get('yaw_deg'),
            'pitch_deg': nav_data.get('pitch_deg'),
            'roll_deg': nav_data.get('roll_deg'),
            'original_asset': asset
        })
    
    df = pd.DataFrame(df_data)
    
    # Display sorting options
    col1, col2 = st.columns(2)
    with col1:
        # Fixed selectbox - added missing closing parenthesis
        sort_by = st.selectbox(
            "Sort by",
            options=['start_time', 'depth_m', 'yaw_deg', 'media_type'],
            format_func=lambda x: {
                'start_time': 'Start Time',
                'depth_m': 'Depth',
                'yaw_deg': 'Yaw',
                'media_type': 'Media Type'
            }.get(x, x)
        )
    
    with col2:
        sort_order = st.selectbox("Sort order", ['Ascending', 'Descending'])
    
    # Sort DataFrame
    if sort_by in df.columns:
        df_sorted = df.sort_values(
            by=sort_by, 
            ascending=(sort_order == 'Ascending'),
            na_position='last'
        )
    else:
        df_sorted = df
    
    # Display options
    display_mode = st.radio(
        "Display Mode",
        options=['Grid View', 'List View', 'Detailed View'],
        horizontal=True
    )
    
    if display_mode == 'Grid View':
        # Grid display
        items_per_row = st.slider("Items per row", 1, 4, 3)
        create_media_grid(df_sorted['original_asset'].tolist(), PROJECT_DIR, items_per_row)
    
    elif display_mode == 'List View':
        # List display with basic info
        for _, row in df_sorted.iterrows():
            with st.container():
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.write(f"**{Path(row['file_path']).name}**")
                    st.write(f"Type: {row['media_type'].title()}")
                    st.write(f"Sensor: {row['sensor']}")
                
                with col2:
                    st.write(f"**Navigation Data**")
                    if row['depth_m'] is not None:
                        st.write(f"Depth: {row['depth_m']:.1f}m")
                    if row['yaw_deg'] is not None:
                        st.write(f"Yaw: {row['yaw_deg']:.1f}°")
                
                with col3:
                    if st.button(f"View Details", key=f"view_{row['id']}"):
                        st.session_state.selected_media = row['original_asset']
                        st.rerun()
                
                st.divider()
    
    elif display_mode == 'Detailed View':
        # Detailed display with media preview
        for _, row in df_sorted.iterrows():
            with st.expander(f"{Path(row['file_path']).name} - {row['media_type'].title()}"):
                display_media_with_nav_data(row['original_asset'], PROJECT_DIR)

def display_selected_media_details():
    """Display details of the selected media asset"""
    if 'selected_media' not in st.session_state:
        return
    
    media_asset = st.session_state.selected_media
    
    st.subheader(f"Media Details - {Path(media_asset.get('file_path', '')).name}")
    
    # Back button
    if st.button("← Back to Media List"):
        del st.session_state.selected_media
        st.rerun()
    
    # Display media with navigation data
    display_media_with_nav_data(media_asset, PROJECT_DIR)
    
    # Additional metadata
    st.subheader("Additional Metadata")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**ID:** {media_asset.get('id', 'N/A')}")
        st.write(f"**Start Time:** {media_asset.get('start_time', 'N/A')}")
        if media_asset.get('end_time'):
            st.write(f"**End Time:** {media_asset.get('end_time')}")
        if media_asset.get('fps'):
            st.write(f"**FPS:** {media_asset.get('fps')}")
    
    with col2:
        # File information
        file_info = get_file_info(media_asset.get('file_path', ''), PROJECT_DIR)
        if file_info:
            st.write(f"**File Size:** {file_info.get('size_mb', 'N/A')} MB")
            if 'width' in file_info and 'height' in file_info:
                st.write(f"**Dimensions:** {file_info['width']}x{file_info['height']}")
            st.write(f"**Format:** {file_info.get('format', 'N/A')}")
    
    # File metadata
    file_metadata = media_asset.get('file_metadata', {})
    if file_metadata:
        st.subheader("File Metadata")
        for key, value in file_metadata.items():
            st.write(f"**{key}:** {value}")
    
    # Notes
    if media_asset.get('notes'):
        st.subheader("Notes")
        st.write(media_asset.get('notes'))

def main():
    """Main function for the media explorer page"""
    st.title("🎥 Media Asset Explorer")
    st.markdown("---")
    
    # Check if a specific media asset is selected
    if 'selected_media' in st.session_state:
        display_selected_media_details()
        return
    
    # Create filter sidebar
    filters = create_filter_sidebar()
    
    if not filters:
        st.warning("Cannot load media explorer - no locations available")
        return
    
    # Main content area
    st.header(f"Media Assets from {filters['location']}")
    
    # Load and display media
    if filters['apply_filters'] or 'last_filters' not in st.session_state:
        # Store filters for comparison
        st.session_state.last_filters = filters
        
        # Get filtered media
        with st.spinner("Loading media assets..."):
            media_assets = get_filtered_media(filters)
        
        st.session_state.current_media = media_assets
    else:
        # Use cached media
        media_assets = st.session_state.get('current_media', [])
    
    # Display statistics
    display_media_stats(media_assets)
    
    # Display filter summary
    if media_assets:
        st.success(f"Found {len(media_assets)} media assets matching your filters")
        
        # Show current filters
        with st.expander("Current Filters"):
            st.write(f"**Location:** {filters['location']}")
            st.write(f"**Media Types:** {', '.join(filters['media_types'])}")
            st.write(f"**Depth Range:** {filters['depth_range'][0]}m - {filters['depth_range'][1]}m")
            st.write(f"**Yaw Range:** {filters['yaw_range'][0]}° - {filters['yaw_range'][1]}°")
    
    # Display media
    display_detailed_media_list(media_assets)
    
    # Export functionality
    if media_assets:
        st.markdown("---")
        st.subheader("Export Options")
        
        # Export metadata as CSV
        if st.button("📊 Export Metadata as CSV"):
            # Prepare data for export
            export_data = []
            for asset in media_assets:
                frames = asset.get('frames', [])
                nav_data = {}
                if frames:
                    nav_sample = frames[0].get('closest_nav_sample', {})
                    nav_data = {
                        'depth_m': nav_sample.get('depth_m'),
                        'yaw_deg': nav_sample.get('yaw_deg'),
                        'pitch_deg': nav_sample.get('pitch_deg'),
                        'roll_deg': nav_sample.get('roll_deg')
                    }
                
                export_data.append({
                    'id': asset.get('id'),
                    'file_path': asset.get('file_path'),
                    'media_type': asset.get('media_type'),
                    'start_time': asset.get('start_time'),
                    'sensor': asset.get('deployment_details', {}).get('sensor_name'),
                    'mission_location': asset.get('deployment_details', {}).get('mission_location'),
                    'depth_m': nav_data.get('depth_m'),
                    'yaw_deg': nav_data.get('yaw_deg'),
                    'pitch_deg': nav_data.get('pitch_deg'),
                    'roll_deg': nav_data.get('roll_deg')
                })
            
            df_export = pd.DataFrame(export_data)
            csv = df_export.to_csv(index=False)
            
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"media_assets_{filters['location']}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )

if __name__ == "__main__":
    main()
