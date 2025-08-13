# utils/api_client.py - Django REST API client for Streamlit application
import requests
import json
import streamlit as st
from typing import Dict, List, Optional, Any

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
    
    # Rover methods
    def get_rovers(self) -> List[Dict]:
        """Get all rover hardware"""
        response = self._make_request('GET', '/rovers/')
        return response.get('results', []) if 'results' in response else response if isinstance(response, list) else []

    # Mission methods
    def get_missions(self) -> List[Dict]:
        """Get all missions"""
        response = self._make_request('GET', '/missions/')
        return response.get('results', []) if 'results' in response else response if isinstance(response, list) else []
    
    def get_mission(self, mission_id: int) -> Dict:
        """Get a specific mission"""
        return self._make_request('GET', f'/missions/{mission_id}/')


     # Sensor methods
    def get_sensors(self) -> List[Dict]:
        """Get all sensors"""
        response = self._make_request('GET', '/sensors/')
        return response.get('results', []) if 'results' in response else response if isinstance(response, list) else []
    
    def get_sensor(self, sensor_id: int) -> Dict:
        """Get a specific sensor"""
        return self._make_request('GET', f'/sensors/{sensor_id}/')
    
    # Deployment methods
    def get_deployments(self) -> List[Dict]:
        """Get all sensor deployments"""
        response = self._make_request('GET', '/deployments/')
        return response.get('results', []) if 'results' in response else response if isinstance(response, list) else []    

    # Calibration methods
    def get_calibrations(self) -> List[Dict]:
        """Get all calibrations"""
        response = self._make_request('GET', '/calibrations/')
        return response.get('results', []) if 'results' in response else response if isinstance(response, list) else []
    
    def get_calibration(self, calibration_id: int) -> Dict:
        """Get a specific calibration"""
        return self._make_request('GET', f'/calibrations/{calibration_id}/')
    

    # Media Asset methods
    def get_media_assets(self, filters=None, page=None, page_size=None):
        """
        Get media assets with optional filtering and pagination
        
        Args:
            filters (dict): Filter parameters matching MediaAssetFilter
            page (int): Page number for pagination
            page_size (int): Number of results per page
        
        Returns:
            dict: Paginated response with results, count, next, previous
        """
        params = {}

        # Add filters
        if filters:
            for key, value in filters.items():
                if value is not None and value != "":
                    params[key] = value
        
        # Add pagination
        if page:
            params['page'] = page
        if page_size:
            params['page_size'] = page_size
        
        return self._make_request("GET", "/media-assets/", params=params)

    def get_frame_indices(self, media_asset_id=None, filters=None):
        """
        Get frame indices with optional filtering
        
        Args:
            media_asset_id (int): Filter by specific media asset
            filters (dict): Additional filter parameters
        
        Returns:
            list: Frame indices data
        """
        params = {}
        
        if media_asset_id:
            params['media_asset'] = media_asset_id
        
        if filters:
            for key, value in filters.items():
                if value is not None and value != "":
                    params[key] = value
        
        response = self._make_request("GET", "/frame-indices/", params=params)
        
        # Handle paginated response
        if isinstance(response, dict) and 'results' in response:
            return response['results']
        return response if isinstance(response, list) else []
    
