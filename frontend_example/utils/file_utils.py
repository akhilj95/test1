# utils/file_utils.py - File handling utilities for media assets
import os
import streamlit as st
from pathlib import Path
from PIL import Image
from typing import Optional, Tuple, Union
import mimetypes

def get_media_file_path(file_path: str, project_dir: Path) -> Path:
    """
    Convert relative media file path to absolute path using PROJECT_DIR
    
    Args:
        file_path: Relative path from Django MediaAsset.file_path
        project_dir: PROJECT_DIR from Django settings
    
    Returns:
        Absolute path to the media file
    """
    # Remove leading slash if present
    if file_path.startswith('/'):
        file_path = file_path[1:]
    
    # Combine with project directory
    full_path = project_dir / file_path
    return full_path

def display_media_file(file_path: str, project_dir: Path, caption: str = None) -> bool:
    """
    Display media file in Streamlit
    
    Args:
        file_path: Relative path from Django MediaAsset.file_path
        project_dir: PROJECT_DIR from Django settings
        caption: Optional caption for the media
    
    Returns:
        True if successfully displayed, False otherwise
    """
    try:
        full_path = get_media_file_path(file_path, project_dir)
        
        if not full_path.exists():
            st.error(f"Media file not found: {file_path}")
            return False
        
        # Get file type
        mime_type, _ = mimetypes.guess_type(str(full_path))
        
        if mime_type and mime_type.startswith('image/'):
            # Display image
            try:
                image = Image.open(full_path)
                st.image(image, caption=caption, use_column_width=True)
                return True
            except Exception as e:
                st.error(f"Error loading image: {str(e)}")
                return False
        
        elif mime_type and mime_type.startswith('video/'):
            # Display video
            try:
                with open(full_path, 'rb') as video_file:
                    video_bytes = video_file.read()
                st.video(video_bytes)
                if caption:
                    st.caption(caption)
                return True
            except Exception as e:
                st.error(f"Error loading video: {str(e)}")
                return False
        
        else:
            st.warning(f"Unsupported media type: {mime_type}")
            return False
            
    except Exception as e:
        st.error(f"Error displaying media file: {str(e)}")
        return False

def get_file_info(file_path: str, project_dir: Path) -> Optional[dict]:
    """
    Get information about a media file
    
    Args:
        file_path: Relative path from Django MediaAsset.file_path
        project_dir: PROJECT_DIR from Django settings
    
    Returns:
        Dictionary with file information or None if file not found
    """
    try:
        full_path = get_media_file_path(file_path, project_dir)
        
        if not full_path.exists():
            return None
        
        stat = full_path.stat()
        mime_type, _ = mimetypes.guess_type(str(full_path))
        
        info = {
            'name': full_path.name,
            'size': stat.st_size,
            'size_mb': round(stat.st_size / (1024 * 1024), 2),
            'modified': stat.st_mtime,
            'mime_type': mime_type,
            'exists': True
        }
        
        # Add image-specific info
        if mime_type and mime_type.startswith('image/'):
            try:
                with Image.open(full_path) as img:
                    info['width'] = img.width
                    info['height'] = img.height
                    info['format'] = img.format
            except:
                pass
        
        return info
        
    except Exception as e:
        st.error(f"Error getting file info: {str(e)}")
        return None

def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format"""
    if size_bytes == 0:
        return "0 B"
    
    units = ['B', 'KB', 'MB', 'GB']
    size = size_bytes
    unit_index = 0
    
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
    
    return f"{size:.1f} {units[unit_index]}"

def is_image_file(file_path: str) -> bool:
    """Check if file is an image based on extension"""
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'}
    return Path(file_path).suffix.lower() in image_extensions

def is_video_file(file_path: str) -> bool:
    """Check if file is a video based on extension"""
    video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm'}
    return Path(file_path).suffix.lower() in video_extensions

def create_media_grid(media_items: list, project_dir: Path, cols: int = 3):
    """
    Create a grid layout for displaying media items
    
    Args:
        media_items: List of media asset dictionaries
        project_dir: PROJECT_DIR from Django settings
        cols: Number of columns in the grid
    """
    if not media_items:
        st.info("No media items to display")
        return
    
    # Create columns
    columns = st.columns(cols)
    
    for i, item in enumerate(media_items):
        col_index = i % cols
        
        with columns[col_index]:
            # Display media file
            file_path = item.get('file_path', '')
            caption = f"{item.get('media_type', 'Unknown').title()} - {item.get('start_time', 'Unknown time')}"
            
            if display_media_file(file_path, project_dir, caption):
                # Add additional info
                with st.expander(f"Details - {Path(file_path).name}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Type:** {item.get('media_type', 'Unknown')}")
                        st.write(f"**Start Time:** {item.get('start_time', 'Unknown')}")
                        if item.get('end_time'):
                            st.write(f"**End Time:** {item.get('end_time')}")
                    
                    with col2:
                        file_info = get_file_info(file_path, project_dir)
                        if file_info:
                            st.write(f"**Size:** {format_file_size(file_info['size'])}")
                            if 'width' in file_info and 'height' in file_info:
                                st.write(f"**Dimensions:** {file_info['width']}x{file_info['height']}")
                    
                    # Show deployment info if available
                    if 'deployment_details' in item:
                        deploy_info = item['deployment_details']
                        st.write(f"**Sensor:** {deploy_info.get('sensor_name', 'Unknown')}")
                        st.write(f"**Mission:** {deploy_info.get('mission_location', 'Unknown')}")

def display_media_with_nav_data(media_item: dict, project_dir: Path):
    """
    Display media item with associated navigation data
    
    Args:
        media_item: Media asset dictionary
        project_dir: PROJECT_DIR from Django settings
    """
    file_path = media_item.get('file_path', '')
    
    # Create two columns - media and nav data
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Display media
        caption = f"{media_item.get('media_type', 'Unknown').title()} - {media_item.get('start_time', 'Unknown time')}"
        display_media_file(file_path, project_dir, caption)
    
    with col2:
        # Display navigation data
        st.subheader("Navigation Data")
        
        # Get frame index data if available
        frames = media_item.get('frames', [])
        if frames:
            frame = frames[0]  # Use first frame as example
            nav_sample = frame.get('closest_nav_sample')
            
            if nav_sample:
                st.metric("Depth (m)", f"{nav_sample.get('depth_m', 'N/A'):.1f}" if nav_sample.get('depth_m') else "N/A")
                st.metric("Yaw (°)", f"{nav_sample.get('yaw_deg', 'N/A'):.1f}" if nav_sample.get('yaw_deg') else "N/A")
                st.metric("Pitch (°)", f"{nav_sample.get('pitch_deg', 'N/A'):.1f}" if nav_sample.get('pitch_deg') else "N/A")
                st.metric("Roll (°)", f"{nav_sample.get('roll_deg', 'N/A'):.1f}" if nav_sample.get('roll_deg') else "N/A")
                
                # Show time difference
                time_diff = frame.get('nav_match_time_diff_ms')
                if time_diff is not None:
                    st.metric("Time Diff (ms)", time_diff)
        
        # Show deployment details
        if 'deployment_details' in media_item:
            st.subheader("Deployment Info")
            deploy_info = media_item['deployment_details']
            st.write(f"**Sensor:** {deploy_info.get('sensor_name', 'Unknown')}")
            st.write(f"**Mission:** {deploy_info.get('mission_location', 'Unknown')}")
        
        # Show file info
        file_info = get_file_info(file_path, project_dir)
        if file_info:
            st.subheader("File Info")
            st.write(f"**Size:** {format_file_size(file_info['size'])}")
            if 'width' in file_info and 'height' in file_info:
                st.write(f"**Dimensions:** {file_info['width']}x{file_info['height']}")
            st.write(f"**Format:** {file_info.get('format', 'Unknown')}")