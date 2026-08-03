"""
Test page — load game data from Firestore.
"""

import streamlit as st
from modules.data_loader import get_game_data_dict_from_dict
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

selected_id = st.selectbox(
    "Select a session",
    options=session_labels.keys(),
    format_func=lambda x: session_labels[x],
)

# --- Load selected session ---
if st.button("Load session"):
    raw_data = get_session_game_data(db, selected_id)

    if raw_data:
        st.json(raw_data.keys())
        st.json(list(raw_data.get("challengesSaveObject", {}).keys()))
        st.json(raw_data["challengesSaveObject"])
        game_data = get_game_data_dict_from_dict(raw_data)
        st.success(f"Loaded: {selected_id}")
        st.metric("Player ID", game_data["player_id"])
        st.metric("Data Points", len(game_data["player_movement_df"]))
        st.dataframe(game_data["player_movement_df"].head(10))
    else:
        st.error(f"No data found for {selected_id}")