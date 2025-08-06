import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
import plotly.express as px
import plotly.graph_objects as go

def process_sensor_data(samples: List[Dict[str, Any]], sensor_type: str) -> pd.DataFrame:
    """Process sensor samples into DataFrame"""
    if not samples:
        return pd.DataFrame()
    
    df = pd.DataFrame(samples)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Sensor-specific processing
    if sensor_type == 'imu':
        df = process_imu_data(df)
    elif sensor_type == 'compass':
        df = process_compass_data(df)
    elif sensor_type == 'pressure':
        df = process_pressure_data(df)
    
    return df

def process_imu_data(df: pd.DataFrame) -> pd.DataFrame:
    """Process IMU data with calculated fields"""
    if df.empty:
        return df
    
    # Calculate magnitude of angular velocity
    df['angular_velocity_mag'] = np.sqrt(
        df['gx_rad_s']**2 + df['gy_rad_s']**2 + df['gz_rad_s']**2
    )
    
    # Calculate magnitude of acceleration
    df['acceleration_mag'] = np.sqrt(
        df['ax_m_s2']**2 + df['ay_m_s2']**2 + df['az_m_s2']**2
    )
    
    return df

def process_compass_data(df: pd.DataFrame) -> pd.DataFrame:
    """Process compass data with calculated fields"""
    if df.empty:
        return df
    
    # Calculate magnetic field magnitude
    df['magnetic_field_mag'] = np.sqrt(
        df['mx_uT']**2 + df['my_uT']**2 + df['mz_uT']**2
    )
    
    # Calculate heading (simplified)
    df['heading_deg'] = np.arctan2(df['my_uT'], df['mx_uT']) * 180 / np.pi
    
    return df

def process_pressure_data(df: pd.DataFrame) -> pd.DataFrame:
    """Process pressure data with calculated depth"""
    if df.empty:
        return df
    
    # Convert pressure to depth (rough approximation)
    # 1 bar = 10 meters of water depth
    atmospheric_pressure = 101325  # Pa
    df['depth_m'] = (df['pressure_pa'] - atmospheric_pressure) / 10000
    
    return df

def create_time_series_chart(df: pd.DataFrame, y_column: str, title: str) -> go.Figure:
    """Create time series chart"""
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df[y_column],
        mode='lines',
        name=y_column,
        line=dict(width=2)
    ))
    
    fig.update_layout(
        title=title,
        xaxis_title="Time",
        yaxis_title=y_column,
        hovermode='x unified'
    )
    
    return fig

def create_depth_profile(nav_samples: List[Dict[str, Any]]) -> go.Figure:
    """Create depth profile chart"""
    if not nav_samples:
        return go.Figure()
    
    df = pd.DataFrame(nav_samples)
    df = df.dropna(subset=['depth_m'])
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df['depth_m'],
        mode='lines+markers',
        name='Depth',
        line=dict(width=2, color='blue'),
        marker=dict(size=4)
    ))
    
    fig.update_layout(
        title="Depth Profile Over Time",
        xaxis_title="Time",
        yaxis_title="Depth (m)",
        yaxis=dict(autorange='reversed'),  # Invert y-axis for depth
        hovermode='x unified'
    )
    
    return fig

def create_mission_summary_stats(missions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate mission summary statistics"""
    if not missions:
        return {}
    
    df = pd.DataFrame(missions)
    
    stats = {
        'total_missions': len(df),
        'locations': df['location'].nunique(),
        'avg_depth': df['max_depth'].mean() if 'max_depth' in df else 0,
        'target_types': df['target_type'].value_counts().to_dict(),
        'recent_missions': len(df[pd.to_datetime(df['start_time']) > pd.Timestamp.now() - pd.Timedelta(days=30)])
    }
    
    return stats
