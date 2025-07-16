# utils/validators.py - Form validation utilities
import re
from datetime import datetime, timezone
from typing import Tuple, Optional, Dict, Any
import streamlit as st

def validate_required_field(value: Any, field_name: str) -> Tuple[bool, str]:
    """Validate that a field is not empty"""
    if not value or (isinstance(value, str) and not value.strip()):
        return False, f"{field_name} is required"
    return True, ""

def validate_string_length(value: str, field_name: str, min_length: int = 1, max_length: int = 255) -> Tuple[bool, str]:
    """Validate string length"""
    if len(value) < min_length:
        return False, f"{field_name} must be at least {min_length} characters long"
    if len(value) > max_length:
        return False, f"{field_name} must be less than {max_length} characters long"
    return True, ""

def validate_sensor_name(name: str) -> Tuple[bool, str]:
    """Validate sensor name"""
    if not name:
        return False, "Sensor name is required"
    
    # Check length
    if len(name) < 2:
        return False, "Sensor name must be at least 2 characters long"
    if len(name) > 100:
        return False, "Sensor name must be less than 100 characters long"
    
    # Check for valid characters (letters, numbers, spaces, hyphens, underscores)
    if not re.match(r'^[a-zA-Z0-9\s\-_]+$', name):
        return False, "Sensor name can only contain letters, numbers, spaces, hyphens, and underscores"
    
    return True, ""

def validate_mission_location(location: str) -> Tuple[bool, str]:
    """Validate mission location"""
    if not location:
        return False, "Mission location is required"
    
    # Check length
    if len(location) < 2:
        return False, "Location must be at least 2 characters long"
    if len(location) > 50:
        return False, "Location must be less than 50 characters long"
    
    # Allow letters, numbers, spaces, and common punctuation
    if not re.match(r'^[a-zA-Z0-9\s\-.,()]+$', location):
        return False, "Location can only contain letters, numbers, spaces, and common punctuation"
    
    return True, ""

def validate_depth(depth: float) -> Tuple[bool, str]:
    """Validate depth value"""
    if depth < 0:
        return False, "Depth must be positive"
    if depth > 1000:  # reasonable limit for underwater missions
        return False, "Depth must be less than 1000 meters"
    return True, ""

def validate_angle(angle: float, field_name: str) -> Tuple[bool, str]:
    """Validate angle value (0-360 degrees)"""
    if angle < 0 or angle > 360:
        return False, f"{field_name} must be between 0 and 360 degrees"
    return True, ""

def validate_datetime_range(start_time: datetime, end_time: Optional[datetime] = None) -> Tuple[bool, str]:
    """Validate datetime range"""
    if end_time and end_time <= start_time:
        return False, "End time must be after start time"
    
    # Check if start_time is in the future (with some tolerance)
    now = datetime.now(timezone.utc)
    if start_time > now:
        return False, "Start time cannot be in the future"
    
    return True, ""

def validate_json_field(json_data: Dict[str, Any], field_name: str) -> Tuple[bool, str]:
    """Validate JSON field"""
    if not isinstance(json_data, dict):
        return False, f"{field_name} must be a valid JSON object"
    
    # Check for reasonable size (to prevent extremely large JSON)
    import json
    json_str = json.dumps(json_data)
    if len(json_str) > 10000:  # 10KB limit
        return False, f"{field_name} is too large (max 10KB)"
    
    return True, ""

def validate_sensor_type(sensor_type: str) -> Tuple[bool, str]:
    """Validate sensor type"""
    valid_types = ['camera', 'compass', 'imu', 'pressure', 'sonar']
    if sensor_type not in valid_types:
        return False, f"Sensor type must be one of: {', '.join(valid_types)}"
    return True, ""

def validate_target_type(target_type: str) -> Tuple[bool, str]:
    """Validate mission target type"""
    valid_types = ['pillar', 'wall']
    if target_type not in valid_types:
        return False, f"Target type must be one of: {', '.join(valid_types)}"
    return True, ""

def validate_level_choice(level: str, field_name: str) -> Tuple[bool, str]:
    """Validate level choice (visibility, cloud_cover, tide_level)"""
    valid_levels = ['low', 'medium', 'high']
    if level not in valid_levels:
        return False, f"{field_name} must be one of: {', '.join(valid_levels)}"
    return True, ""

def validate_calibration_coefficients(coefficients: Dict[str, Any]) -> Tuple[bool, str]:
    """Validate calibration coefficients"""
    if not isinstance(coefficients, dict):
        return False, "Calibration coefficients must be a dictionary"
    
    # Check for reasonable number of coefficients
    if len(coefficients) > 50:
        return False, "Too many calibration coefficients (max 50)"
    
    # Check that all values are numeric
    for key, value in coefficients.items():
        if not isinstance(value, (int, float)):
            return False, f"Calibration coefficient '{key}' must be numeric"
    
    return True, ""

def validate_file_path(file_path: str) -> Tuple[bool, str]:
    """Validate file path"""
    if not file_path:
        return False, "File path is required"
    
    # Check for reasonable length
    if len(file_path) > 500:
        return False, "File path is too long (max 500 characters)"
    
    # Check for valid characters (avoid path traversal)
    if '..' in file_path or file_path.startswith('/'):
        return False, "File path contains invalid characters"
    
    return True, ""

def validate_mission_form(form_data: Dict[str, Any]) -> Tuple[bool, Dict[str, str]]:
    """Validate complete mission form"""
    errors = {}
    
    # Validate required fields
    if not form_data.get('rover'):
        errors['rover'] = "Rover is required"
    
    # Validate location
    location = form_data.get('location', '')
    is_valid, error = validate_mission_location(location)
    if not is_valid:
        errors['location'] = error
    
    # Validate target type
    target_type = form_data.get('target_type', '')
    is_valid, error = validate_target_type(target_type)
    if not is_valid:
        errors['target_type'] = error
    
    # Validate depth if provided
    max_depth = form_data.get('max_depth')
    if max_depth is not None:
        is_valid, error = validate_depth(max_depth)
        if not is_valid:
            errors['max_depth'] = error
    
    # Validate level choices
    for field in ['visibility', 'cloud_cover', 'tide_level']:
        value = form_data.get(field)
        if value:
            is_valid, error = validate_level_choice(value, field)
            if not is_valid:
                errors[field] = error
    
    # Validate datetime range
    start_time = form_data.get('start_time')
    end_time = form_data.get('end_time')
    if start_time:
        is_valid, error = validate_datetime_range(start_time, end_time)
        if not is_valid:
            errors['datetime'] = error
    
    return len(errors) == 0, errors

def validate_sensor_form(form_data: Dict[str, Any]) -> Tuple[bool, Dict[str, str]]:
    """Validate complete sensor form"""
    errors = {}
    
    # Validate name
    name = form_data.get('name', '')
    is_valid, error = validate_sensor_name(name)
    if not is_valid:
        errors['name'] = error
    
    # Validate sensor type
    sensor_type = form_data.get('sensor_type', '')
    is_valid, error = validate_sensor_type(sensor_type)
    if not is_valid:
        errors['sensor_type'] = error
    
    # Validate specification JSON
    specification = form_data.get('specification', {})
    if specification:
        is_valid, error = validate_json_field(specification, 'specification')
        if not is_valid:
            errors['specification'] = error
    
    return len(errors) == 0, errors

def validate_calibration_form(form_data: Dict[str, Any]) -> Tuple[bool, Dict[str, str]]:
    """Validate complete calibration form"""
    errors = {}
    
    # Validate sensor
    if not form_data.get('sensor'):
        errors['sensor'] = "Sensor is required"
    
    # Validate coefficients
    coefficients = form_data.get('coefficients', {})
    if coefficients:
        is_valid, error = validate_calibration_coefficients(coefficients)
        if not is_valid:
            errors['coefficients'] = error
    
    return len(errors) == 0, errors

def display_validation_errors(errors: Dict[str, str]):
    """Display validation errors in Streamlit"""
    if errors:
        st.error("Please fix the following errors:")
        for field, error in errors.items():
            st.error(f"• {error}")

def validate_form_and_display_errors(form_data: Dict[str, Any], form_type: str) -> bool:
    """Validate form and display errors if any"""
    if form_type == 'mission':
        is_valid, errors = validate_mission_form(form_data)
    elif form_type == 'sensor':
        is_valid, errors = validate_sensor_form(form_data)
    elif form_type == 'calibration':
        is_valid, errors = validate_calibration_form(form_data)
    else:
        return False
    
    if not is_valid:
        display_validation_errors(errors)
    
    return is_valid