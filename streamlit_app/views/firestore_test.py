"""
Test page — load game data from Firestore.
"""
from components.sidebar import DEFAULTS
from datetime import datetime as dt

import streamlit as st

from modules.data_loader import (
   get_game_data_dict_from_dict,
   get_loaded_data,
)

from modules.firestore_client import (
    get_firestore_client,
    get_all_sessions,
    get_session_game_data,
)


CREDS_PATH = "secrets/firestore-creds.json"


st.title("Firestore Test")

# --- Connect ---
db = get_firestore_client(CREDS_PATH)

# --- List sessions ---
sessions = get_all_sessions(db)

if not sessions:
    st.warning("No sessions found in Firestore.")
    st.stop()

st.write(f"Found {len(sessions)} session(s)")

# --- Build a readable label for each session ---
session_labels = {
    s["sessionId"]: f"{s['startTime']}  —  {s['playerId']}  —  {s['deviceName']}"
    for s in sessions
}

#st.subheader("Select a session")
selected_id = st.selectbox(
    "Select a session",
    options=session_labels.keys(),
    format_func=lambda x: session_labels[x],
)

# --- Preview selected session ---
raw_data = get_session_game_data(db, selected_id)

if not raw_data:
        st.error(f"No data found for {selected_id}")
        st.stop()

#st.subheader("Preview")

col_a, col_b, col_c = st.columns(3)

with col_a:
    st.caption("Start Time")
    st.write(dt.fromisoformat(raw_data["startTime"]).strftime("%Y-%m-%d %H:%M"))

with col_b:
    st.caption("Player ID")
    st.write(raw_data["playerId"])

with col_c:
    st.caption("Device Name")
    st.write(raw_data["deviceName"])

# --- Data preview ---
with st.expander("📊 Data Preview", expanded=True):
    game_data = get_game_data_dict_from_dict(raw_data)

    tab1, tab2, tab3 = st.tabs([
        "Challenges", "Game Events", "Validations"
    ])

    with tab1:
        st.dataframe(game_data["challenge_df"], width="stretch")

    with tab2:
        st.dataframe(game_data["game_events_df"], width="stretch")

    with tab3:
        st.dataframe(game_data["validations_df"], width="stretch")

# --- Load selected session ---
if st.button("Load session"):
    raw_data = get_session_game_data(db, selected_id)

    if not raw_data:
        st.error(f"No data found for {selected_id}")
        st.stop()

    game_data = get_game_data_dict_from_dict(raw_data)

    existing = st.session_state.get("loaded_data", {})
    # map_image_path=None — not uploadable, get_loaded_data() resolves the
    # level-appropriate default. Buildings are loaded internally there too.
    st.session_state["loaded_data"] = get_loaded_data(
        game_data,
        map_image_path=None,
        video_path=existing.get("video_path") or DEFAULTS.get("video"),
    )

    # Clear cached visuals so they rebuild with new data
    st.session_state.pop("snapshots", None)
    st.session_state.pop("animated_fig", None)

    st.success(f"Session loaded — switch to any page to visualize.")