"""
Home page — project overview with default data loaded.
"""

import streamlit as st
from components.sidebar import render_sidebar

# --- Load data via sidebar ---
data = render_sidebar()

# --- Page content ---
st.title("Luméria Data Visualization")

st.markdown("""
Replay and explore a Luméria game session. See the player's journey 
through the virtual city — their movement, decisions, and the events 
they encounter — reconstructed from the game's raw data.
""")

# --- How to use ---
st.markdown("""
**Get started:** the app loads with example data so everything works 
right away. Upload your own game files in the sidebar to analyze a 
different session.
""")

# --- Page overview ---
st.markdown("---")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.page_link("views/static_map.py", label="Static Map")
    st.caption("Full session at a glance — every position, event, and attempt on one map. Export as PNG.")

with col2:
    st.page_link("views/animated_map.py", label="Animated Map")
    st.caption("Watch the session unfold in real time. Scrub, play at different speeds, export as MP4.")

with col3:
    st.page_link("views/video_sync.py", label="Replay and Video")
    st.caption("Compare the game replay side by side with gameplay video footage.")

with col4:
    st.page_link("views/about.py", label="About")
    st.caption("Project context, credits, and links.")

# --- Session summary ---
st.markdown("---")
st.subheader("Current Session")

col_a, col_b, col_c, col_d, col_e = st.columns(5)

with col_a:
    st.caption("Player")
    st.write(data["game_data"]["player_id"])

with col_b:
    st.caption("Challenge")
    st.write(data["game_data"]["challenge_id"])

with col_c:
    st.caption("Duration")
    st.write(f"{data['game_data']['challenge_duration']:.1f}s")

with col_d:
    st.caption("Data Points")
    st.write(len(data["timeline_df"]))

with col_e:
    st.caption("Recorded")
    st.write(data["game_data"]["save_time"].strftime("%Y-%m-%d %H:%M"))

# --- Data preview ---
with st.expander("📊 Data Preview"):
    tab1, tab2, tab3, tab4 = st.tabs([
        "Player Movement", "Challenges", "Game Events", "Validations"
    ])

    with tab1:
        st.dataframe(data["timeline_df"].head(10), width="stretch")

    with tab2:
        st.dataframe(data["game_data"]["challenge_df"], width="stretch")

    with tab3:
        st.dataframe(data["game_data"]["game_events_df"], width="stretch")

    with tab4:
        st.dataframe(data["game_data"]["validations_df"], width="stretch")