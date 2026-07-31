import streamlit as st

# --- Page config (must be first streamlit command) ---
st.set_page_config(
    page_title="Lumeria Data Visualization",
    page_icon="🎮",
    layout="wide"
)

# --- Define pages ---
home = st.Page("pages/home.py", title="Home", icon="🏠", default=True)
static_map = st.Page("pages/static_map.py", title="Static Map", icon="🗺️")
animated_map = st.Page("pages/animated_map.py", title="Animated Map", icon="▶️")
video_sync = st.Page("pages/video_sync.py", title="Video + Animation", icon="🎬")
about = st.Page("pages/about.py", title="About", icon="ℹ️")

# --- Navigation ---
nav = st.navigation([home, static_map, animated_map, video_sync, about])
nav.run()