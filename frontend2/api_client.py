import requests
import streamlit as st
from typing import Dict, List, Optional, Any
from config import config
import json

class APIClient:
    """Client for interacting with Django REST API"""
    
    def __init__(self):
        self.base_url = config.API_BASE_URL
        self.timeout = config.API_TIMEOUT
        self.session = requests.Session()
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make HTTP request with error handling"""
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.request(method, url, timeout=self.timeout, **kwargs)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            st.error(f"API Error: {str(e)}")
            raise
    
    def get(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """GET request"""
        response = self._make_request('GET', endpoint, params=params)
        return response.json()
    
    def post(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """POST request"""
        response = self._make_request('POST', endpoint, json=data)
        return response.json()
    
    def put(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """PUT request"""
        response = self._make_request('PUT', endpoint, json=data)
        return response.json()
    
    def patch(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """PATCH request"""
        response = self._make_request('PATCH', endpoint, json=data)
        return response.json()
    
    def delete(self, endpoint: str) -> bool:
        """DELETE request"""
        try:
            self._make_request('DELETE', endpoint)
            return True
        except:
            return False
    
    # Specific API methods
    def get_rovers(self, **params) -> Dict[str, Any]:
        return self.get(config.ENDPOINTS['rovers'], params)
    
    def get_sensors(self, **params) -> Dict[str, Any]:
        return self.get(config.ENDPOINTS['sensors'], params)
    
    def get_missions(self, **params) -> Dict[str, Any]:
        return self.get(config.ENDPOINTS['missions'], params)
    
    def get_deployments(self, **params) -> Dict[str, Any]:
        return self.get(config.ENDPOINTS['deployments'], params)
    
    def get_media_assets(self, **params) -> Dict[str, Any]:
        return self.get(config.ENDPOINTS['media_assets'], params)
    
    def get_media_by_location(self, location: str, **params) -> Dict[str, Any]:
        endpoint = f"{config.ENDPOINTS['media_assets']}by_location/"
        params['location'] = location
        return self.get(endpoint, params)
    
    def get_nav_samples(self, **params) -> Dict[str, Any]:
        return self.get(config.ENDPOINTS['navsamples'], params)
    
    def get_sensor_samples(self, sensor_type: str, **params) -> Dict[str, Any]:
        endpoint_key = f"{sensor_type}samples"
        return self.get(config.ENDPOINTS[endpoint_key], params)

# Global API client instance
api_client = APIClient()
