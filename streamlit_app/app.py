import streamlit as st

# --- Page config (must be first streamlit command) ---
st.set_page_config(
    page_title="Lumeria Data Visualization",
    page_icon="🎮",
    layout="wide"
)

# --- Define pages ---
home = st.Page("pages/home.py", title="HOME", default=True)
static_map = st.Page("pages/static_map.py", title="Static Map")
animated_map = st.Page("pages/animated_map.py", title="Animated Map")
video_sync = st.Page("pages/video_sync.py", title="Replay and Video")
about = st.Page("pages/about.py", title="About")

# --- Navigation ---
nav = st.navigation([home, static_map, animated_map, video_sync, about])
nav.run()