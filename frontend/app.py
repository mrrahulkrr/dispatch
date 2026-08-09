import sys
import os
import requests
import streamlit as st
import streamlit.components.v1 as components

# Ensure project root is on sys.path for absolute imports (from frontend.styles import ...)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from frontend.styles import (
    REGION_META, get_region_options, get_region_code_from_label,
    detect_country_from_coords, get_main_css, GEOLOCATION_JS
)
from frontend.api_client import API_BASE_URL
from frontend.views import (
    render_my_feed, render_research_station, render_archive, render_agent_evals
)

st.set_page_config(
    page_title="Dispatch | AI Intelligence Briefing",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------------
# Session State Initialization
# ---------------------------------------------------------
if 'selected_region' not in st.session_state:
    st.session_state.selected_region = "US"
if 'run_active' not in st.session_state:
    st.session_state.run_active = False
    st.session_state.run_result = None
    st.session_state.run_cancelled = False
    st.session_state.run_start_time = None

# Handle geolocation detection via query params
params = st.query_params
if "detected_lat" in params and "detected_lng" in params:
    try:
        lat = float(params["detected_lat"])
        lng = float(params["detected_lng"])
        detected = detect_country_from_coords(lat, lng)
        st.session_state.selected_region = detected
        st.query_params.clear()
    except (ValueError, TypeError):
        pass

# Get accent color for current region
accent = REGION_META.get(st.session_state.selected_region, {}).get("accent", "#4facfe")
st.markdown(get_main_css(accent), unsafe_allow_html=True)


def main():
    # ---------------------------------------------------------
    # Sidebar Navigation
    # ---------------------------------------------------------
    with st.sidebar:
        st.markdown("## 🚀 DISPATCH")
        st.caption("AI Intelligence Briefing Platform")
        st.markdown("---")
        
        # Region Selector
        st.markdown("#### 🌍 Region")
        region_options = get_region_options()
        current_label = f"{REGION_META[st.session_state.selected_region]['flag']} {REGION_META[st.session_state.selected_region]['name']}"
        
        selected_label = st.selectbox(
            "Select your region",
            region_options,
            index=region_options.index(current_label) if current_label in region_options else 0,
            label_visibility="collapsed"
        )
        new_region = get_region_code_from_label(selected_label)
        if new_region != st.session_state.selected_region:
            st.session_state.selected_region = new_region
            st.cache_data.clear()
            st.rerun()
        
        # Detect Location button
        if st.button("📍 Detect my location", use_container_width=True):
            components.html(GEOLOCATION_JS, height=30)
        
        st.markdown("---")
        
        # Navigation
        page = st.radio(
            "Navigate",
            ["📬 My Feed", "🔬 Research Station", "📚 Archive", "📊 Agent Evaluations"],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        
        # Status
        region_info = REGION_META[st.session_state.selected_region]
        st.markdown(f"**Region:** {region_info['flag']} {region_info['name']}")
        
        try:
            health = requests.get(f"{API_BASE_URL}/regions", timeout=3)
            st.markdown("**Status:** 🟢 Connected")
        except Exception:
            st.markdown("**Status:** 🔴 Disconnected")
        
        st.caption(f"Backend: `{API_BASE_URL}`")

    # ---------------------------------------------------------
    # Page Routing
    # ---------------------------------------------------------
    if page == "📬 My Feed":
        render_my_feed()
    elif page == "🔬 Research Station":
        render_research_station()
    elif page == "📚 Archive":
        render_archive()
    elif page == "📊 Agent Evaluations":
        render_agent_evals()

if __name__ == "__main__":
    main()
