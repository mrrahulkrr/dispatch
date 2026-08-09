import streamlit as st
import requests
import os

def _get_api_url():
    """Resolve the backend API URL from Streamlit secrets, env var, or default."""
    try:
        return st.secrets["API_BASE_URL"]
    except (KeyError, FileNotFoundError):
        return os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

API_BASE_URL = _get_api_url()

@st.cache_data(ttl=60)
def fetch_regions():
    try:
        response = requests.get(f"{API_BASE_URL}/regions", timeout=10)
        if response.status_code == 200:
            return response.json()
        return []
    except Exception:
        return []

@st.cache_data(ttl=60)
def fetch_sections_for_region(region_code):
    try:
        response = requests.get(f"{API_BASE_URL}/regions/{region_code}/sections", timeout=10)
        if response.status_code == 200:
            return response.json()
        return []
    except Exception:
        return []

@st.cache_data(ttl=60)
def fetch_all_sections():
    try:
        response = requests.get(f"{API_BASE_URL}/sections", timeout=10)
        if response.status_code == 200:
            return response.json()
        return []
    except Exception:
        return []

def run_research(region, slug, topic):
    try:
        response = requests.post(
            f"{API_BASE_URL}/regions/{region}/sections/{slug}/runs",
            json={"watch_topic": topic},
            timeout=180
        )
        if response.status_code == 200:
            return response.json()
        else:
            return {"_error": f"Server error ({response.status_code}): {response.text}"}
    except requests.exceptions.Timeout:
        return {"_error": "Request timed out after 3 minutes. The backend may still be processing — check your terminal."}
    except Exception as e:
        return {"_error": f"Failed to run research: {e}"}

def fetch_digests(region, slug):
    try:
        response = requests.get(f"{API_BASE_URL}/regions/{region}/sections/{slug}/digests", timeout=10)
        if response.status_code == 200:
            return response.json()
        return []
    except Exception:
        return []

def fetch_run(slug, run_id):
    try:
        response = requests.get(f"{API_BASE_URL}/sections/{slug}/runs/{run_id}", timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception:
        return None

@st.cache_data(ttl=60)
def fetch_evals(region, slug):
    try:
        response = requests.get(f"{API_BASE_URL}/regions/{region}/evals/{slug}", timeout=10)
        if response.status_code == 200:
            return response.json()
        return {}
    except Exception:
        return {}
