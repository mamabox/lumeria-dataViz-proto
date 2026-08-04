"""
Sidebar UI — file uploads, shared settings.
This is the only place users interact with data loading.
"""

import streamlit as st
import os
from modules.data_loader import get_game_data_dict, get_loaded_data, GameDataError, LoadedData

# Get the directory where sidebar.py lives (streamlit_app/components/)
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMP_DIR:str = os.path.join(_BASE_DIR, "temp_uploads")

# Default file paths (relative to streamlit_app/)
# Note: buildings and map image aren't uploadable — buildings.json is one
# canonical file covering every level, and the map image is resolved per
# level. Both are handled entirely inside data_loader.get_loaded_data().
DEFAULTS = {
    "game_data": os.path.join(_BASE_DIR, "defaults", "example_game_data.json"),
}

if os.path.exists(os.path.join(_BASE_DIR, "defaults", "example_gameplay.mp4")):
    DEFAULTS["video"] = os.path.join(_BASE_DIR, "defaults", "example_gameplay.mp4")

def render_sidebar() -> LoadedData:
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

    if video_file:
        st.session_state["video_path"] = _save_upload(video_file, "video.mp4")
        st.session_state.pop("loaded_data", None)
        st.session_state.pop("video_player", None)

    # --- Reset ---
    st.sidebar.markdown("---")
    if st.sidebar.button("Reset to example data"):
        st.session_state.pop("game_data_path", None)
        st.session_state.pop("video_path", None)
        st.session_state.pop("loaded_data", None)
        st.session_state.pop("snapshots", None)
        st.session_state.pop("animated_fig", None)
        st.session_state.pop("video_player", None)
        st.rerun()


    # --- Resolve paths (uploaded or defaults) ---
    game_data_path = st.session_state.get("game_data_path", DEFAULTS["game_data"])
    video_path = st.session_state.get("video_path", DEFAULTS.get("video"))

    # --- Load data (cached in session state) ---
    if "loaded_data" not in st.session_state:
        try:
            game_data = get_game_data_dict(game_data_path)
        except GameDataError as e:
            st.sidebar.error(str(e))
            st.stop()
        # map_image_path=None — not uploadable, get_loaded_data() resolves
        # the level-appropriate default.
        st.session_state["loaded_data"] = get_loaded_data(
            game_data, map_image_path=None, video_path=video_path
        )

    return st.session_state["loaded_data"]


def _save_upload(uploaded_file, filename: str) -> str:
    """
    Save an uploaded file to a temp location and return the path.
    Streamlit uploads are bytes — we need a file path for json and cv2.
    """

    os.makedirs(TEMP_DIR, exist_ok=True)
    path = os.path.join(TEMP_DIR, filename)
    with open(path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return path