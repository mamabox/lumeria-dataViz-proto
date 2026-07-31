"""
Home page — project overview with default data loaded.
"""

import streamlit as st
from components.sidebar import render_sidebar

# --- Load data via sidebar ---
data = render_sidebar()

# --- Page content ---
st.title("🏠 Lumeria Data Visualization")

st.markdown("""
This tool visualizes player movement and game events 
from the Lumeria educational game.

Use the sidebar to upload your own data files or explore 
with the default dataset.
""")

# --- Quick overview of loaded data ---
st.subheader("Loaded Data Overview")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.caption("Save Date")
    st.write(data["game_data"]["save_time"].strftime("%Y-%m-%d %H:%M"))

with col2:
   st.caption("Player ID")
   st.write(data["game_data"]["player_id"])

with col5:
    st.caption("Movement Points")
    st.write(len(data["timeline_df"]))

with col4:
   st.caption("Duration")
   st.write(f"{data['game_data']['challenge_duration']:.1f}s")

with col3:
   st.caption("Challenge")
   st.write(f"{data['game_data']['challenge_id']}")

# --- Preview dataframes ---

with st.expander("Buildings Data"):
    st.dataframe(data["buildings_df"])

with st.expander("Game Events"):
    st.dataframe(data["game_data"]["game_events_df"])

with st.expander("Player Movement Data (first 10 data points)"):
    st.dataframe(data["timeline_df"].head(10))