import streamlit as st
import requests
import pandas as pd
from datetime import datetime
from typing import Optional

# ==== CONFIG ====

API_BASE_URL = st.secrets.get("DJANGO_API_URL", "http://localhost:8000/api")

HEADERS = {"Content-Type": "application/json"}

# Helper function for paginated GET requests
def api_get(endpoint: str, params: Optional[dict] = None):
    url = f"{API_BASE_URL}{endpoint}"
    try:
        resp = requests.get(url, params=params, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        st.error(f"API GET error {url}: {str(e)}")
        return None

# Helper function for POST
def api_post(endpoint: str, data: dict):
    url = f"{API_BASE_URL}{endpoint}"
    try:
        resp = requests.post(url, json=data, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        st.error(f"API POST error {url}: {str(e)}")
        return None

# Helper function PATCH
def api_patch(endpoint: str, data: dict):
    url = f"{API_BASE_URL}{endpoint}"
    try:
        resp = requests.patch(url, json=data, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        st.error(f"API PATCH error {url}: {str(e)}")
        return None

# Helper function DELETE
def api_delete(endpoint: str):
    url = f"{API_BASE_URL}{endpoint}"
    try:
        resp = requests.delete(url, headers=HEADERS, timeout=15)
        if resp.status_code in (204, 200):
            return True
        else:
            st.error(f"Delete failed with status {resp.status_code}: {resp.text}")
            return False
    except requests.RequestException as e:
        st.error(f"API DELETE error {url}: {str(e)}")
        return False

# ==== UTILITIES ====

def format_datetime(dt_str):
    if not dt_str:
        return ""
    try:
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return dt_str

def display_paginated_table(endpoint, params=None):
    """Display multiple pages of results, allowing user to load more"""
    if params is None:
        params = {}
    page_size = 50
    params["limit"] = page_size
    offset = 0
    all_rows = []
    more = True
    while more:
        params["offset"] = offset
        data = api_get(endpoint, params)
        if not data or "results" not in data:
            st.warning(f"No data from {endpoint}.")
            return
        df = pd.DataFrame(data["results"])
        if df.empty:
            st.info("No data to show.")
            return
        st.dataframe(df)
        # Pagination UI
        if data.get("next"):
            if st.button("Load More", key=f"load_more_{endpoint}_{offset}"):
                offset += page_size
                continue
        more = False

# ==== APP ====

st.set_page_config(page_title="Mission Management Streamlit Client", layout="wide")

st.title("🚀 Mission Management System - Streamlit Frontend")

menu = ["Dashboard", "Rovers", "Sensors", "Calibrations", "Missions", "Deployments", "Media Assets"]
choice = st.sidebar.selectbox("Navigation Menu", menu)

def dashboard():
    st.header("📊 Overview Dashboard")
    rovers = api_get("/rovers/")
    sensors = api_get("/sensors/")
    missions = api_get("/missions/")
    media = api_get("/media-assets/")

    if rovers and sensors and missions and media:
        st.metric("Rovers", rovers.get("count", 0))
        st.metric("Sensors", sensors.get("count", 0))
        st.metric("Missions", missions.get("count", 0))
        st.metric("Media Assets", media.get("count", 0))

def list_rovers():
    st.header("🛸 Rovers")
    data = api_get("/rovers/")
    if not data:
        return
    df = pd.DataFrame(data["results"])
    if df.empty:
        st.info("No rovers found")
        return
    st.dataframe(df[["id","name","effective_from_display","active"]])

    st.markdown("### Add New Rover")
    with st.form("add_rover"):
        name = st.text_input("Name", max_chars=100)
        hardware_config = st.text_area("Hardware Config (JSON)", "{}")
        submitted = st.form_submit_button("Submit")
        if submitted:
            import json
            try:
                config_json = json.loads(hardware_config)
                payload = {"name":name, "hardware_config": config_json}
                result = api_post("/rovers/", payload)
                if result:
                    st.success(f"Rover '{name}' added.")
                    st.experimental_rerun()
            except json.JSONDecodeError:
                st.error("Invalid JSON in Hardware Config.")

def list_sensors():
    st.header("🔧 Sensors")
    data = api_get("/sensors/")
    if not data:
        return
    df = pd.DataFrame(data["results"])
    if df.empty:
        st.info("No sensors found")
        return
    st.dataframe(df[["id", "name", "sensor_type"]])

    st.markdown("### Add New Sensor")
    with st.form("add_sensor"):
        name = st.text_input("Sensor Name", max_chars=100)
        sensor_type = st.selectbox("Sensor Type", ["camera", "compass", "imu", "pressure", "sonar"])
        specification = st.text_area("Specification (JSON)", "{}")
        submitted = st.form_submit_button("Submit")
        if submitted:
            import json
            try:
                spec_json = json.loads(specification)
                payload = {"name":name, "sensor_type": sensor_type, "specification": spec_json}
                result = api_post("/sensors/", payload)
                if result:
                    st.success(f"Sensor '{name}' added.")
                    st.experimental_rerun()
            except json.JSONDecodeError:
                st.error("Invalid JSON in Specification.")

def list_calibrations():
    st.header("⚙️ Calibrations")
    data = api_get("/calibrations/")
    if not data:
        return
    df = pd.DataFrame(data["results"])
    if df.empty:
        st.info("No calibrations found")
        return
    st.dataframe(df[["id", "sensor", "effective_from", "active"]])

def list_missions():
    st.header("🚀 Missions")
    with st.expander("Filters"):
        rover_name = st.text_input("Rover name (partial)")
        target_type = st.selectbox("Target Type", options=["", "pillar", "wall"])
        location = st.text_input("Location (exact)")
        start_after = st.date_input("Start After")
        start_before = st.date_input("Start Before")

    params = {}
    if rover_name:
        params["rover__name"] = rover_name
    if target_type:
        params["target_type"] = target_type
    if location:
        params["location"] = location
    if start_after:
        params["start_after"] = start_after.isoformat()
    if start_before:
        params["start_before"] = start_before.isoformat()

    data = api_get("/missions/", params)
    if not data:
        return
    df = pd.DataFrame(data["results"])
    if df.empty:
        st.info("No missions found")
        return
    df["start_time"] = df["start_time"].apply(format_datetime)
    df["end_time"] = df["end_time"].apply(format_datetime)
    st.dataframe(df[["id","rover","location","target_type","start_time","end_time","max_depth"]])

    # Add mission form
    st.markdown("### Add New Mission")
    with st.form("add_mission"):
        rovers_data = api_get("/rovers/")
        rover_choices = {r["name"]: r["id"] for r in rovers_data.get("results", [])} if rovers_data else {}
        rover_sel = st.selectbox("Rover", options=list(rover_choices.keys()))
        location = st.text_input("Location", "")
        target_type = st.selectbox("Target Type", options=["pillar","wall"])
        max_depth = st.number_input("Max Depth (m)", min_value=0.0, step=0.1)
        start_time = st.text_input("Start Time (ISO, e.g. 2025-07-17T10:46:00Z)")
        end_time = st.text_input("End Time (ISO or blank)")
        visibility = st.selectbox("Visibility", options=["low","medium","high"])
        cloud_cover = st.selectbox("Cloud Cover", options=["low","medium","high"])
        tide_level = st.selectbox("Tide Level", options=["low","medium","high"])
        notes = st.text_area("Notes","")
        submitted = st.form_submit_button("Submit")
        if submitted:
            try:
                payload = {
                    "rover": rover_choices[rover_sel],
                    "location": location,
                    "target_type": target_type,
                    "max_depth": max_depth,
                    "start_time": start_time,
                    "end_time": end_time if end_time else None,
                    "visibility": visibility,
                    "cloud_cover": cloud_cover,
                    "tide_level": tide_level,
                    "notes": notes
                }
                result = api_post("/missions/", payload)
                if result:
                    st.success("Mission added.")
                    st.experimental_rerun()
            except Exception as e:
                st.error(f"Error adding mission: {str(e)}")

def list_deployments():
    st.header("📡 Deployments")
    data = api_get("/deployments/")
    if not data:
        return
    df = pd.DataFrame(data["results"])
    if df.empty:
        st.info("No deployments found")
        return
    st.dataframe(df[["id","sensor_name","position","instance","mission"]])

    st.markdown("### Add New Deployment")
    with st.form("add_deployment"):
        missions_data = api_get("/missions/")
        mission_choices = {f"{m['id']} - {m['location']}": m['id'] for m in missions_data.get("results", [])} if missions_data else {}
        sensors_data = api_get("/sensors/")
        sensor_choices = {s['name']: s['id'] for s in sensors_data.get("results", [])} if sensors_data else {}
        mission_sel = st.selectbox("Mission", options=list(mission_choices.keys()))
        sensor_sel = st.selectbox("Sensor", options=list(sensor_choices.keys()))
        position = st.text_input("Position")
        instance = st.selectbox("Instance", options=[0,1])
        submitted = st.form_submit_button("Submit")
        if submitted:
            try:
                payload = {
                    "mission": mission_choices[mission_sel],
                    "sensor": sensor_choices[sensor_sel],
                    "position": position,
                    "instance": instance,
                }
                result = api_post("/deployments/", payload)
                if result:
                    st.success("Deployment added.")
                    st.experimental_rerun()
            except Exception as e:
                st.error(f"Error adding deployment: {str(e)}")

def list_media_assets():
    st.header("📸 Media Assets")

    with st.expander("Filter Parameters"):
        media_type = st.selectbox("Media Type", options=["","image","video"])
        location = st.text_input("Location (exact)")
        depth_min = st.number_input("Depth Min", value=0.0, step=0.1)
        depth_max = st.number_input("Depth Max", value=1000.0, step=0.1)
        yaw_min = st.number_input("Yaw Min", value=0.0, step=0.1)
        yaw_max = st.number_input("Yaw Max", value=360.0, step=0.1)

    params = {}
    if media_type:
        params["media_type"] = media_type
    if location:
        params["location"] = location
    if depth_min is not None:
        params["depth_min"] = depth_min
    if depth_max is not None:
        params["depth_max"] = depth_max
    if yaw_min is not None:
        params["yaw_min"] = yaw_min
    if yaw_max is not None:
        params["yaw_max"] = yaw_max

    # Use your custom action endpoint by sending to /media-assets/by_location/
    try:
        url = f"{API_BASE_URL}/media-assets/by_location/"
        resp = requests.get(url, params=params, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        st.error(f"API GET error: {e}")
        return

    results = data.get("results", [])
    if not results:
        st.info("No media assets found for given filters.")
        return
    df = pd.DataFrame(results)
    if df.empty:
        st.info("No media assets found.")
        return
    df["start_time"] = df["start_time"].apply(format_datetime)
    st.dataframe(df[["id","media_type","file_path","start_time","deployment_details"]])

def main():
    if choice == "Dashboard":
        dashboard()
    elif choice == "Rovers":
        list_rovers()
    elif choice == "Sensors":
        list_sensors()
    elif choice == "Calibrations":
        list_calibrations()
    elif choice == "Missions":
        list_missions()
    elif choice == "Deployments":
        list_deployments()
    elif choice == "Media Assets":
        list_media_assets()

if __name__ == "__main__":
    main()
