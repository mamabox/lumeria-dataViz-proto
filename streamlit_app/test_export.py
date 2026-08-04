"""test_export.py — run from streamlit_app/ folder"""

from modules.map_config import get_map_config, LEVELS
from modules.data_loader import get_game_data_dict, get_buildings_df, get_player_timeline_df
from modules.map_builder import build_base_figure
from modules.map_animation import build_animated_figure
from modules.video_exporter import export_combined_video

# --- Load data ---
game_data = get_game_data_dict("defaults/example_game_data.json")
buildings_df = get_buildings_df("defaults/example_buildings.json")
timeline_df = get_player_timeline_df(
    game_data["player_movement_df"],
    game_data["challenge_df"],
)

map_config = get_map_config(**LEVELS["level_1"])
target_building_id = game_data["challenge_df"].iloc[0]["target_building_id"]

fig = build_base_figure(
    map_image_path="defaults/example_map_level1.png",
    map_config=map_config,
    buildings_df=buildings_df,
    target_building_id=target_building_id,
)

fig = build_animated_figure(
    fig=fig,
    timeline_df=timeline_df,
    game_events_df=game_data["game_events_df"],
)

def show_progress(current, total):
    if current % 10 == 0 or current == total:
        print(f"  {current}/{total}")

print("Exporting...")
export_combined_video(
    animated_fig=fig,
    video_path="../videos/video01.mp4",  # adjust path
    timeline_df=timeline_df,
    output_path="/tmp/test_combined.mp4",
    offset=0.0,
    speed=8,
    output_fps=10,
    on_progress=show_progress,
)

import os
if os.path.exists("/tmp/test_combined.mp4"):
    size = os.path.getsize("/tmp/test_combined.mp4")
    print(f"Success! File size: {size / 1024:.0f} KB")
else:
    print("FAILED — file not created")