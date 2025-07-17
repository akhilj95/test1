import streamlit as st
import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime

def format_datetime(dt_str: str) -> str:
    """Format datetime string for display"""
    if not dt_str:
        return ""
    try:
        dt = pd.to_datetime(dt_str)
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except:
        return dt_str

def safe_float(value: Any) -> float:
    """Safely convert value to float"""
    try:
        return float(value) if value is not None else 0.0
    except:
        return 0.0

def paginate_results(data: Dict[str, Any], page_size: int = 50) -> pd.DataFrame:
    """Handle paginated API results"""
    results = data.get('results', [])
    if results:
        df = pd.DataFrame(results)
        return df
    return pd.DataFrame()

def create_filter_params(filters: Dict[str, Any]) -> Dict[str, Any]:
    """Create API filter parameters from form inputs"""
    params = {}
    for key, value in filters.items():
        if value is not None and value != "" and value != "All":
            params[key] = value
    return params

@st.cache_data
def load_cached_data(endpoint: str, params: Dict[str, Any] = None):
    """Cache API responses for better performance"""
    from api_client import api_client
    return api_client.get(endpoint, params)
