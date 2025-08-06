# utils/api_client.py - Django REST API client for Streamlit application
import requests
import json
import streamlit as st
from typing import Dict, List, Optional, Any
from pathlib import Path

class APIClient:
    """Client for communicating with Django REST API"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request with error handling"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json() if response.content else {}
        except requests.exceptions.ConnectionError:
            st.error("Cannot connect to Django backend. Please check if the server is running.")
            return {}
        except requests.exceptions.HTTPError as e:
            if response.status_code == 400:
                st.error(f"Validation error: {response.text}")
            elif response.status_code == 404:
                st.error("Resource not found")
            elif response.status_code == 500:
                st.error("Internal server error")
            else:
                st.error(f"HTTP error {response.status_code}: {response.text}")
            return {}
        except requests.exceptions.RequestException as e:
            st.error(f"Request failed: {str(e)}")
            return {}
    
    def health_check(self) -> bool:
        """Check if the Django backend is accessible"""
        try:
            response = self.session.get(f"{self.base_url}/missions/", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    # Mission methods
    def get_missions(self) -> List[Dict]:
        """Get all missions"""
        response = self._make_request('GET', '/missions/')
        return response.get('results', []) if 'results' in response else response if isinstance(response, list) else []
    
    def get_mission(self, mission_id: int) -> Dict:
        """Get a specific mission"""
        return self._make_request('GET', f'/missions/{mission_id}/')
    
    def create_mission(self, mission_data: Dict) -> Dict:
        """Create a new mission"""
        return self._make_request('POST', '/missions/', json=mission_data)
    
    def update_mission(self, mission_id: int, mission_data: Dict) -> Dict:
        """Update an existing mission"""
        return self._make_request('PUT', f'/missions/{mission_id}/', json=mission_data)
    
    def delete_mission(self, mission_id: int) -> bool:
        """Delete a mission"""
        response = self._make_request('DELETE', f'/missions/{mission_id}/')
        return response is not None
    
    # Sensor methods
    def get_sensors(self) -> List[Dict]:
        """Get all sensors"""
        response = self._make_request('GET', '/sensors/')
        return response.get('results', []) if 'results' in response else response if isinstance(response, list) else []
    
    def get_sensor(self, sensor_id: int) -> Dict:
        """Get a specific sensor"""
        return self._make_request('GET', f'/sensors/{sensor_id}/')
    
    def create_sensor(self, sensor_data: Dict) -> Dict:
        """Create a new sensor"""
        return self._make_request('POST', '/sensors/', json=sensor_data)
    
    def update_sensor(self, sensor_id: int, sensor_data: Dict) -> Dict:
        """Update an existing sensor"""
        return self._make_request('PUT', f'/sensors/{sensor_id}/', json=sensor_data)
    
    def delete_sensor(self, sensor_id: int) -> bool:
        """Delete a sensor"""
        response = self._make_request('DELETE', f'/sensors/{sensor_id}/')
        return response is not None
    
    # Calibration methods
    def get_calibrations(self) -> List[Dict]:
        """Get all calibrations"""
        response = self._make_request('GET', '/calibrations/')
        return response.get('results', []) if 'results' in response else response if isinstance(response, list) else []
    
    def get_calibration(self, calibration_id: int) -> Dict:
        """Get a specific calibration"""
        return self._make_request('GET', f'/calibrations/{calibration_id}/')
    
    def create_calibration(self, calibration_data: Dict) -> Dict:
        """Create a new calibration"""
        return self._make_request('POST', '/calibrations/', json=calibration_data)
    
    def update_calibration(self, calibration_id: int, calibration_data: Dict) -> Dict:
        """Update an existing calibration"""
        return self._make_request('PUT', f'/calibrations/{calibration_id}/', json=calibration_data)
    
    def delete_calibration(self, calibration_id: int) -> bool:
        """Delete a calibration"""
        response = self._make_request('DELETE', f'/calibrations/{calibration_id}/')
        return response is not None
    
    # Media Asset methods
    def get_media_assets(self, params: Optional[Dict] = None) -> List[Dict]:
        """Get media assets with optional filtering"""
        response = self._make_request('GET', '/media-assets/', params=params)
        return response.get('results', []) if 'results' in response else response if isinstance(response, list) else []
    
    def get_media_by_location(self, location: str, depth_min: Optional[float] = None, 
                             depth_max: Optional[float] = None, yaw_min: Optional[float] = None,
                             yaw_max: Optional[float] = None) -> List[Dict]:
        """Get media assets by location with nav sample filtering"""
        params = {'location': location}
        if depth_min is not None:
            params['depth_min'] = depth_min
        if depth_max is not None:
            params['depth_max'] = depth_max
        if yaw_min is not None:
            params['yaw_min'] = yaw_min
        if yaw_max is not None:
            params['yaw_max'] = yaw_max
        
        return self._make_request('GET', '/media-assets/by_location/', params=params)
    
    def get_media_asset(self, asset_id: int) -> Dict:
        """Get a specific media asset"""
        return self._make_request('GET', f'/media-assets/{asset_id}/')
    
    # NavSample methods
    def get_nav_samples(self, mission_id: Optional[int] = None) -> List[Dict]:
        """Get navigation samples, optionally filtered by mission"""
        params = {'mission': mission_id} if mission_id else {}
        response = self._make_request('GET', '/navsamples/', params=params)
        return response.get('results', []) if 'results' in response else response if isinstance(response, list) else []
    
    # Deployment methods
    def get_deployments(self, mission_id: Optional[int] = None) -> List[Dict]:
        """Get sensor deployments, optionally filtered by mission"""
        params = {'mission': mission_id} if mission_id else {}
        response = self._make_request('GET', '/deployments/', params=params)
        return response.get('results', []) if 'results' in response else response if isinstance(response, list) else []
    
    # Rover Hardware methods
    def get_rover_hardware(self) -> List[Dict]:
        """Get all rover hardware configurations"""
        response = self._make_request('GET', '/rovers/')
        return response.get('results', []) if 'results' in response else response if isinstance(response, list) else []
    
    def get_locations(self) -> List[str]:
        """Get unique locations from missions"""
        missions = self.get_missions()
        locations = list(set(mission.get('location', '') for mission in missions if mission.get('location')))
        return sorted(locations)

    # helping find frames
    def find_frames(self, location, depth, yaw, d_tol, y_tol):
        """
        Find frames at a location within a given depth and yaw tolerance.
        """
        return self.get_media_by_location(
            location=location,
            depth_min=depth - d_tol,
            depth_max=depth + d_tol,
            yaw_min=yaw - y_tol,
            yaw_max=yaw + y_tol
        )