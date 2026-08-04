"""
Video + Animation page.
Set video offset, scrub to compare animation with video frame.
"""



import streamlit as st
from components.sidebar import render_sidebar
from modules.video_player import VideoPlayer
from modules.map_builder import build_base_figure
from modules.map_animation import build_animated_figure, get_frame_snapshot
from modules.map_builder import build_event_timeline
from modules.video_exporter import export_combined_video
from modules.video_exporter_pipe import export_combined_video_pipe
from modules.data_loader import get_nearest_index_for_time

import tempfile
import os


# --- Load data via sidebar ---
data = render_sidebar()

# --- Check for video ---
if not data.video_path:
    st.info("No gameplay video available. Upload one in the sidebar.")
    st.stop()

# --- Page content ---
st.title("Replay and video")

# --- Challenge info ---
st.caption(
    f"Challenge {data.game_data['challenge_id']} — "
    f"Duration: {data.game_data['challenge_duration']:.2f}s — "
    f"Player: {data.game_data['player_id']}"
)

# --- Video player (persist across reruns) ---
if "video_player" not in st.session_state:
    st.session_state["video_player"] = VideoPlayer(data.video_path)

player = st.session_state["video_player"]

# --- 1. Set video offset ---
with st.expander("🎥 Set Video Offset", expanded=True):
    col_vid, col_offset = st.columns([3, 1])
    with col_vid:
        st.video(data.video_path, start_time=0)
    with col_offset:
        offset = st.number_input(
            "Game starts at (seconds)",
            value=0.0,
            step=0.5,
        )
        st.session_state["video_offset"] = offset

offset = st.session_state.get("video_offset", 0.0)

# --- Build snapshots once (no play controls) ---
if "snapshots" not in st.session_state:
    with st.spinner("Preparing frames..."):
        fig = build_base_figure(
            map_image_path=data.map_image_path,
            map_config=data.map_config,
            buildings_df=data.buildings_df,
            target_building_id=data.target_building_id,
        )
        fig = build_animated_figure(
            fig=fig,
            timeline_df=data.timeline_df,
            game_events_df=data.game_data["game_events_df"],
        )

        fig.update_layout(
            width=500,
            height=400,
            margin=dict(l=20, r=20, t=40, b=20),
        )

        st.session_state["animated_fig"] = fig
        st.session_state["snapshots"] = [
            get_frame_snapshot(fig, i)
            for i in range(len(data.timeline_df))
        ]


# --- Event timeline strip ---
event_timeline = build_event_timeline(
    timeline_df=data.timeline_df,
    game_events_df=data.game_data["game_events_df"],
    player_movement_df=data.timeline_df,
)
st.plotly_chart(
    event_timeline,
    width="stretch",
    config={
        "staticPlot": False,
        #"scrollZoom": False,
        #"displayModeBar": False,
        })


# --- 2. Synced scrubbing ---
st.markdown("---")

time_list = data.timeline_df["time"].tolist()
total_frames = len(time_list)

if "frame_slider" not in st.session_state:
    st.session_state["frame_slider"] = float(time_list[0])

def on_time_jump():
    """When user types a time, move the slider to that time."""
    st.session_state["frame_slider"] = st.session_state["time_jump"]


col_slider, col_input = st.columns([4, 1])

with col_input:
    st.number_input(
        "Go to time (s)",
        min_value=float(time_list[0]),
        max_value=float(time_list[-1]),
        value=float(time_list[0]),
        step=2.0,
        key="time_jump",
        on_change=on_time_jump,
    )

with col_slider:
    game_time_slider = st.slider(
        "Game Time",
        min_value=float(time_list[0]),
        max_value=float(time_list[-1]),
        key="frame_slider",
        label_visibility="collapsed",
        format="%.1fs",
    )
    # Last recorded frame strictly before the selected time; clamp -1
    # (before the first sample) to the first frame.
    frame_index = get_nearest_index_for_time(data.timeline_df, game_time_slider)
    if frame_index == -1:
        frame_index = 0

game_time = time_list[frame_index]
st.caption(f"Game Time: {game_time:.2f}s | Video Time: {game_time + offset:.2f}s")

# --- Display ---
st.subheader("Game Map")
st.plotly_chart(
    st.session_state["snapshots"][frame_index],
    config={"staticPlot": False, "responsive": False},
)

st.subheader("Video Frame")
game_time = time_list[frame_index]
st.caption(f"Game Time: {game_time:.2f}s | Video Time: {game_time + offset:.2f}s")
frame_rgb = player.get_frame_at_time(game_time, offset=offset)
if frame_rgb is not None:
    st.image(frame_rgb, width=600)
else:
    st.warning("No frame available at this time")

# --- Export Videos ---
speed = st.selectbox("Export speed", [1, 4, 8, 16, 32])

OUTPUT_PATH = "/tmp/lumeria_combined.mp4"


if st.button("Export video"):
    progress = st.progress(0, text="Exporting...")
    
    def update_progress(current, total):
        progress.progress(current / total, text=f"Frame {current}/{total}")
    
    try:
        export_combined_video(
            animated_fig=st.session_state["animated_fig"],
            video_path=data.video_path,
            timeline_df=data.timeline_df,
            output_path=OUTPUT_PATH,
            offset=offset,
            speed=speed,
            on_progress=update_progress,
        )
        st.session_state["export_done"] = True
    except Exception as e:
        st.error(f"Export failed: {e}")

if st.session_state.get("export_done") and os.path.exists(OUTPUT_PATH):
    st.success("Export complete!")
    st.video(OUTPUT_PATH)
    with open(OUTPUT_PATH, "rb") as f:
        st.download_button("Download combined video", f.read(), "combined.mp4")


OUTPUT_PATH_PNG = "/tmp/lumeria_combined.mp4"
OUTPUT_PATH_PIPE = "/tmp/lumeria_combined_pipe.mp4"

col_png, col_pipe = st.columns(2)

with col_png:
    if st.button("Export (PNG method)"):
        progress = st.progress(0, text="Exporting (PNG)...")
        def update_png(current, total):
            progress.progress(current / total, text=f"PNG: {current}/{total}")
        try:
            import time
            start = time.time()
            export_combined_video(
                animated_fig=st.session_state["animated_fig"],
                video_path=data.video_path,
                timeline_df=data.timeline_df,
                output_path=OUTPUT_PATH_PNG,
                offset=offset,
                speed=speed,
                on_progress=update_png,
            )
            st.session_state["export_png_time"] = time.time() - start
            st.session_state["export_png_done"] = True
        except Exception as e:
            st.error(f"PNG export failed: {e}")

with col_pipe:
    if st.button("Export (Pipe method)"):
        progress = st.progress(0, text="Exporting (Pipe)...")
        def update_pipe(current, total):
            progress.progress(current / total, text=f"Pipe: {current}/{total}")
        try:
            import time
            start = time.time()
            export_combined_video_pipe(
                animated_fig=st.session_state["animated_fig"],
                video_path=data.video_path,
                timeline_df=data.timeline_df,
                output_path=OUTPUT_PATH_PIPE,
                offset=offset,
                speed=speed,
                on_progress=update_pipe,
            )
            st.session_state["export_pipe_time"] = time.time() - start
            st.session_state["export_pipe_done"] = True
        except Exception as e:
            st.error(f"Pipe export failed: {e}")

# Results — persist across reruns
if st.session_state.get("export_png_done") and os.path.exists(OUTPUT_PATH_PNG):
    size = os.path.getsize(OUTPUT_PATH_PNG) / (1024 * 1024)
    st.success(f"PNG method: {st.session_state['export_png_time']:.1f}s | {size:.1f} MB")
    st.video(OUTPUT_PATH_PNG)

if st.session_state.get("export_pipe_done") and os.path.exists(OUTPUT_PATH_PIPE):
    size = os.path.getsize(OUTPUT_PATH_PIPE) / (1024 * 1024)
    st.success(f"Pipe method: {st.session_state['export_pipe_time']:.1f}s | {size:.1f} MB")
    st.video(OUTPUT_PATH_PIPE)