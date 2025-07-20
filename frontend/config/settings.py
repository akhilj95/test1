# config/settings.py - Configuration settings for the Streamlit application
import streamlit as st
from pathlib import Path

# Django REST API Configuration
API_BASE_URL = st.secrets.get("DJANGO_API_URL", "http://localhost:8000/api")

# Django Project Directory (matches settings.py PROJECT_DIR)
# This should match the PROJECT_DIR in your Django settings.py
PROJECT_DIR = Path(__file__).resolve().parent.parent.parent

# Media files configuration
MEDIA_ROOT = PROJECT_DIR / 'data'

# Sensor type choices (matching Django model)
SENSOR_TYPES = [
    ('camera', 'Camera'),
    ('compass', 'Compass'),
    ('imu', 'IMU'),
    ('pressure', 'Pressure'),
    ('sonar', 'Sonar'),
]

# Mission target types (matching Django model)
TARGET_TYPES = [
    ('pillar', 'Pillar'),
    ('wall', 'Wall'),
]

# Level choices (matching Django model)
LEVEL_CHOICES = [
    ('low', 'Low'),
    ('medium', 'Medium'),
    ('high', 'High'),
]

# Media types (matching Django model)
MEDIA_TYPES = [
    ('image', 'Image'),
    ('video', 'Video'),
]
