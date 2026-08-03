import streamlit as st

# --- Page config (must be first streamlit command) ---
st.set_page_config(
    page_title="Lumeria Data Visualization",
    page_icon="🎮",
    layout="wide"
)

# --- Define pages ---
home = st.Page("views/home.py", title="HOME", default=True)
static_map = st.Page("views/static_map.py", title="Static Map")
animated_map = st.Page("views/animated_map.py", title="Animated Map")
video_sync = st.Page("views/video_sync.py", title="Replay and Video")
about = st.Page("views/about.py", title="About")
firestore_test = st.Page("views/firestore_test.py", title="Firestore Test")

# --- Navigation ---
nav = st.navigation([home, static_map, animated_map, video_sync, about, firestore_test])
nav.run()