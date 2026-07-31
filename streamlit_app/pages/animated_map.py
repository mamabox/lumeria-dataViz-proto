"""
Animated map page — playback with slider and speed controls.
"""

import streamlit as st
from components.sidebar import render_sidebar
from components.export import csv_download_button
from modules.map_builder import build_base_figure
from modules.map_animation import build_animated_figure
from modules.data_export import export_animation_to_mp4


# --- Load data via sidebar ---
data = render_sidebar()

# --- Page content ---
st.title("Animated Map")

# --- Build figure ---
fig = build_base_figure(
    map_image_path=data["map_image_path"],
    map_config=data["map_config"],
    buildings_df=data["buildings_df"],
    target_building_id=data["target_building_id"],
)

fig = build_animated_figure(
    fig=fig,
    timeline_df=data["timeline_df"],
    game_events_df=data["game_data"]["game_events_df"],
    challenge_id=data["game_data"]["challenge_id"],
    challenge_duration=data["game_data"]["challenge_duration"],
)

# --- Display ---
st.plotly_chart(fig)

# --- Exports ---
st.subheader("Downloads")
st.write("'Export MP4' may take a few minutes. It renders a video at 10fps.")

col1, col2, col3 = st.columns(3)

with col1:
    speed = st.selectbox("Export speed", ["1x", "8x", "16x"], index=1)
    export_fps = int(speed.replace("x", ""))

    if st.button("🎬 Export MP4"):
      st.warning("⚠️ Don't navigate away — export will be cancelled.")
      with st.spinner('Rendering frames... "Patience Iago, patience."'):
         video_bytes = export_animation_to_mp4(fig, fps=export_fps)
         st.session_state["exported_video"] = video_bytes

    if "exported_video" in st.session_state:
         st.download_button(
               label="💾 Download MP4",
               data=video_bytes,
               file_name="animation.mp4",
               mime="video/mp4",
         )

with col2:
    csv_download_button(
        data["timeline_df"],
        filename="player_movement.csv",
        label="📄 Movement CSV",
    )

with col3:
    csv_download_button(
        data["game_data"]["game_events_df"],
        filename="game_events.csv",
        label="📄 Events CSV",
    )