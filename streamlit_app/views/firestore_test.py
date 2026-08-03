"""
Test page — load game data from Firestore.
"""
from modules.map_config import get_map_config, LEVELS
from modules.map_config import get_map_config, LEVELS
from modules.data_loader import get_buildings_df
from components.sidebar import DEFAULTS
from datetime import datetime as dt

import streamlit as st

from modules.data_loader import (
   get_game_data_dict_from_dict,
   get_player_timeline_df,
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
    else:
        game_data = get_game_data_dict_from_dict(raw_data)
        timeline_df = get_player_timeline_df(
            game_data["player_movement_df"],
            game_data["challenge_df"],
        )
        target_building_id = game_data["challenge_df"].iloc[0]["target_building_id"]

    existing = st.session_state.get("loaded_data", {})
    default_level = list(LEVELS.keys())[0]

    map_config = existing.get("map_config")
    if map_config is None:
        map_config = get_map_config(**LEVELS[default_level])

    buildings_df = existing.get("buildings_df")
    if buildings_df is None:
        buildings_df = get_buildings_df(DEFAULTS["buildings"])

    st.session_state["loaded_data"] = {
        "map_config": map_config,
        "map_image_path": existing.get("map_image_path") or DEFAULTS["map_image"],
        "video_path": existing.get("video_path"),
        "game_data": game_data,
        "buildings_df": buildings_df,
        "timeline_df": timeline_df,
        "target_building_id": target_building_id,
    }

    # Clear cached visuals so they rebuild with new data
    st.session_state.pop("snapshots", None)
    st.session_state.pop("animated_fig", None)

    st.success(f"Session loaded — switch to any page to visualize.")