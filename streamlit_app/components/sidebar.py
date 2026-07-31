"""
Sidebar UI — file uploads, level selection, shared settings.
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
    """
    Render the sidebar and return all loaded data.
    Uses session_state to persist data across reruns.
    """
    st.sidebar.title("Data Files")

    # --- Level selection ---
    level_name = st.sidebar.selectbox(
        "Level",
        options=list(LEVELS.keys()),
        index=0,
    )
    map_config = get_map_config(**LEVELS[level_name])

    # --- File uploads ---
    st.sidebar.markdown("---")
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

    # --- Load data (uploaded or defaults) ---
    game_data_path = _save_upload(game_file, "game_data.json") if game_file else DEFAULTS["game_data"]
    buildings_path = _save_upload(buildings_file, "buildings.json") if buildings_file else DEFAULTS["buildings"]
    map_image_path = _save_upload(map_image_file, "map_image.png") if map_image_file else DEFAULTS["map_image"]
    video_path = _save_upload(video_file, "video.mp4") if video_file else DEFAULTS.get("video")

    # --- Process data ---
    game_data = get_game_data_dict(game_data_path)
    buildings_df = get_buildings_df(buildings_path)
    timeline_df = get_player_timeline_df(
        game_data["player_movement_df"],
        game_data["challenge_df"],
    )
    target_building_id = game_data["challenge_df"].iloc[0]["target_building_id"]

    return {
        "map_config": map_config,
        "map_image_path": map_image_path,
        "video_path": video_path,
        "game_data": game_data,
        "buildings_df": buildings_df,
        "timeline_df": timeline_df,
        "target_building_id": target_building_id,
    }


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