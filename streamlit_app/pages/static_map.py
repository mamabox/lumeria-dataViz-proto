"""
Static map page — full map with all traces, export to PNG.
"""

import streamlit as st
from components.sidebar import render_sidebar
from components.export import image_download_button, csv_download_button
from modules.map_builder import build_static_figure


# --- Load data via sidebar ---
data = render_sidebar()

# --- Page content ---
st.title("🗺️ Static Map")

# --- Build figure ---
fig = build_static_figure(
    map_image_path=data["map_image_path"],
    map_config=data["map_config"],
    buildings_df=data["buildings_df"],
    target_building_id=data["target_building_id"],
    timeline_df=data["timeline_df"],
    game_events_df=data["game_data"]["game_events_df"],
    title=f"Player {data['game_data']['player_id']} — Challenge {data['game_data']['challenge_id']}",
)

# --- Display ---
st.plotly_chart(fig, use_container_width=True)

# --- Exports ---
st.subheader("Downloads")

col1, col2, col3 = st.columns(3)

with col1:
    image_download_button(fig, filename="static_map.png", label="📷 Map PNG")

with col2:
    csv_download_button(
        data["timeline_df"],
        filename="player_movement.csv",
        label="📄 Movements CSV",
    )

with col3:
    csv_download_button(
        data["game_data"]["game_events_df"],
        filename="game_events.csv",
        label="📄 Events CSV",
    )