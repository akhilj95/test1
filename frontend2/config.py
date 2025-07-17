import os
from typing import Dict, Any

class Config:
    """Configuration settings for the Streamlit app"""
    
    # Django API settings
    API_BASE_URL = os.getenv('DJANGO_API_URL', 'http://localhost:8000/api')
    API_TIMEOUT = 30
    
    # Streamlit settings
    PAGE_TITLE = "Mission Management System"
    PAGE_ICON = "🚀"
    LAYOUT = "wide"
    
    # API endpoints
    ENDPOINTS = {
        'rovers': '/rovers/',
        'sensors': '/sensors/',
        'calibrations': '/calibrations/',
        'missions': '/missions/',
        'deployments': '/deployments/',
        'logfiles': '/logfiles/',
        'navsamples': '/navsamples/',
        'imusamples': '/imusamples/',
        'compasssamples': '/compasssamples/',
        'pressuresamples': '/pressuresamples/',
        'media_assets': '/media-assets/',
        'frame_indices': '/frame-indices/',
    }
    
    # Default pagination
    DEFAULT_PAGE_SIZE = 50
    
    # Chart colors
    CHART_COLORS = [
        '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', 
        '#9467bd', '#8c564b', '#e377c2', '#7f7f7f'
    ]

config = Config()
