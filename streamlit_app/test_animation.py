"""Test animated map — run from streamlit_app/ folder."""

from modules.map_config import get_map_config, LEVELS
from modules.data_loader import get_game_data_dict, get_buildings_df, get_player_timeline_df
from modules.map_builder import build_base_figure
from modules.map_animation import build_animated_figure

# --- Load data ---
game_data = get_game_data_dict("defaults/example_game_data.json")
buildings_df = get_buildings_df("defaults/example_buildings.json")
timeline_df = get_player_timeline_df(
    game_data["player_movement_df"],
    game_data["challenge_df"],
)

# --- Map config ---
map_config = get_map_config(**LEVELS["level_1"])
target_building_id: str = game_data["challenge_df"].iloc[0]["target_building_id"]

# --- Build base then animate ---
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
    challenge_id=game_data["challenge_id"],
    challenge_duration=game_data["challenge_duration"],
)

fig.show()