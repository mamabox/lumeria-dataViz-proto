"""
Sidebar UI — file uploads, shared settings.
This is the only place users interact with data loading.
"""

import streamlit as st
import os
from modules.data_loader import get_game_data_dict, get_buildings_df, get_player_timeline_df
from modules.map_config import get_map_config, LEVELS

# Get the directory where sidebar.py lives (streamlit_app/components/)
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Default file paths (relative to streamlit_app/)
DEFAULTS = {
    "game_data": os.path.join(_BASE_DIR, "defaults", "example_game_data.json"),
    "buildings": os.path.join(_BASE_DIR, "defaults", "example_buildings.json"),
    "map_image": os.path.join(_BASE_DIR, "defaults", "example_map_level1.png"),
}

if os.path.exists(os.path.join(_BASE_DIR, "defaults", "example_gameplay.mp4")):
    DEFAULTS["video"] = os.path.join(_BASE_DIR, "defaults", "example_gameplay.mp4")

def render_sidebar():
    #st.sidebar.title("Settings")

    # --- Level selection ---
    # level_name = st.sidebar.selectbox(
    #     "Level",
    #     options=list(LEVELS.keys()),
    #     index=0,
    # )
    #level_name = "level_1"
    #map_config = get_map_config(**LEVELS[level_name])

    # --- File uploads ---
    #st.sidebar.markdown("---")
    st.sidebar.subheader("Data Files")

    game_file = st.sidebar.file_uploader(
        "Game data JSON", type=["json"], key="game_upload"
    )
    buildings_file = st.sidebar.file_uploader(
        "Buildings JSON", type=["json"], key="buildings_upload"
    )
    map_image_file = st.sidebar.file_uploader(
        "Map image", type=["png", "jpg"], key="map_upload"
    )
    video_file = st.sidebar.file_uploader(
        "Gameplay video", type=["mp4"], key="video_upload"
    )

    # --- Process uploads into session state ---
    if game_file:
        st.session_state["game_data_path"] = _save_upload(game_file, "game_data.json")
        # Clear cached data so it reloads
        st.session_state.pop("loaded_data", None)
        st.session_state.pop("snapshots", None)
        st.session_state.pop("animated_fig", None)

    if buildings_file:
        st.session_state["buildings_path"] = _save_upload(buildings_file, "buildings.json")
        st.session_state.pop("loaded_data", None)
        st.session_state.pop("snapshots", None)
        st.session_state.pop("animated_fig", None)

    if map_image_file:
        st.session_state["map_image_path"] = _save_upload(map_image_file, "map_image.png")
        st.session_state.pop("loaded_data", None)
        st.session_state.pop("snapshots", None)
        st.session_state.pop("animated_fig", None)

    if video_file:
        st.session_state["video_path"] = _save_upload(video_file, "video.mp4")
        st.session_state.pop("video_player", None)

    # --- Reset ---
    st.sidebar.markdown("---")
    if st.sidebar.button("Reset to example data"):
        st.session_state.pop("game_data_path", None)
        st.session_state.pop("buildings_path", None)
        st.session_state.pop("map_image_path", None)
        st.session_state.pop("video_path", None)
        st.session_state.pop("loaded_data", None)
        st.session_state.pop("snapshots", None)
        st.session_state.pop("animated_fig", None)
        st.session_state.pop("video_player", None)
        st.rerun()


    # --- Resolve paths (uploaded or defaults) ---
    game_data_path = st.session_state.get("game_data_path", DEFAULTS["game_data"])
    buildings_path = st.session_state.get("buildings_path", DEFAULTS["buildings"])
    map_image_path = st.session_state.get("map_image_path", DEFAULTS["map_image"])
    video_path = st.session_state.get("video_path", DEFAULTS.get("video"))

    # --- Load data (cached in session state) ---
    if "loaded_data" not in st.session_state:
        game_data = get_game_data_dict(game_data_path)
        map_config = get_map_config(**LEVELS[f"level_{game_data["level_number"]}"])
        buildings_df = get_buildings_df(buildings_path)
        timeline_df = get_player_timeline_df(
            game_data["player_movement_df"],
            game_data["challenge_df"],
        )
        target_building_id = game_data["challenge_df"].iloc[0]["target_building_id"]

        st.session_state["loaded_data"] = {
            "map_config": map_config,
            "map_image_path": map_image_path,
            "video_path": video_path,
            "game_data": game_data,
            "buildings_df": buildings_df,
            "timeline_df": timeline_df,
            "target_building_id": target_building_id,
        }

    # Update paths that might change without reloading data
    st.session_state["loaded_data"]["map_image_path"] = map_image_path
    st.session_state["loaded_data"]["video_path"] = video_path

    return st.session_state["loaded_data"]


def _save_upload(uploaded_file, filename: str) -> str:
    """
    Save an uploaded file to a temp location and return the path.
    Streamlit uploads are bytes — we need a file path for PIL and json.
    """
    temp_dir = "temp_uploads"
    os.makedirs(temp_dir, exist_ok=True)
    path = os.path.join(temp_dir, filename)
    with open(path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return path