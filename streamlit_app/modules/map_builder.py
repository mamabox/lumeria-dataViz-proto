"""
Build plotly figures for map visualization.
Shared base figure used by both static and animated pages.
Pure Python — no streamlit imports.
"""

import plotly.graph_objects as go
import pandas as pd
import numpy as np
from PIL import Image

from modules.map_styles import (
    TRAIL_COLOR, TRAIL_SIZE, TRAIL_OPACITY,
    POI_COLOR, POI_SIZE, POI_SYMBOL, POI_OUTLINE_COLOR, POI_OUTLINE_WIDTH,
    TARGET_COLOR, TARGET_SIZE, TARGET_SYMBOL, TARGET_OUTLINE_COLOR, TARGET_OUTLINE_WIDTH,
    CATHEDRAL_COLOR, CATHEDRAL_SIZE, CATHEDRAL_SYMBOL,
    CATHEDRAL_OUTLINE_COLOR, CATHEDRAL_OUTLINE_WIDTH, CATHEDRAL_POSITION,
    ATTEMPT_COLORS, ATTEMPT_MARKER_SIZE, ATTEMPT_LINE_WIDTH, ATTEMPT_OPACITY,
    EVENT_STYLES,
)

from modules.data_loader import get_player_pos_for_time


# ======================== BASE FIGURE ======================== #

def build_base_figure(
    map_image_path: str,
    map_config: dict,
    buildings_df: pd.DataFrame,
    target_building_id: str,
) -> go.Figure:
    """
    Create a figure with the map background and all static markers.
    Used as the starting point for both static and animated pages.
    """
    fig = go.Figure()
    map_img = Image.open(map_image_path)
    coord = map_config["coord"]
    axis_range = map_config["axis_range"]

    # --- Background image ---
    fig.add_layout_image(
        source=map_img,
        xref="x", yref="y",
        x=coord.x_min,
        y=coord.z_max,
        sizex=coord.x_max - coord.x_min,
        sizey=coord.z_max - coord.z_min,
        sizing="stretch",
        layer="below",
    )



    # --- POIs ---
    fig.add_trace(go.Scatter(
        x=buildings_df["world_pos_x"].tolist(),
        y=buildings_df["world_pos_z"].tolist(),
        mode="markers",
        marker=dict(
            color=POI_COLOR, size=POI_SIZE, symbol=POI_SYMBOL,
            line=dict(color=POI_OUTLINE_COLOR, width=POI_OUTLINE_WIDTH),
        ),
        hovertext=buildings_df["name"].tolist(),
        hoverinfo="text",
        name="POIs",
    ))

    # --- Target building ---
    fig.add_trace(go.Scatter(
        x=[buildings_df.loc[target_building_id, "world_pos_x"]],
        y=[buildings_df.loc[target_building_id, "world_pos_z"]],
        mode="markers",
        marker=dict(
            color=TARGET_COLOR, size=TARGET_SIZE, symbol=TARGET_SYMBOL,
            line=dict(color=TARGET_OUTLINE_COLOR, width=TARGET_OUTLINE_WIDTH),
        ),
        hoverinfo="skip",
        name="Target building",
    ))

    # --- Cathedral ---
    fig.add_trace(go.Scatter(
        x=[CATHEDRAL_POSITION[0]],
        y=[CATHEDRAL_POSITION[1]],
        mode="markers",
        marker=dict(
            color=CATHEDRAL_COLOR, size=CATHEDRAL_SIZE, symbol=CATHEDRAL_SYMBOL,
            line=dict(color=CATHEDRAL_OUTLINE_COLOR, width=CATHEDRAL_OUTLINE_WIDTH),
        ),
        hovertext="Cathedral",
        hoverinfo="text",
        name="Cathedral",
    ))

    # --- Layout ---
    fig.update_layout(
        width=800,
        height=700,
        xaxis=dict(
            range=[axis_range.x_min, axis_range.x_max],
            dtick=30,
            showgrid=True,
            fixedrange=True,
            constrain="domain",
        ),
        yaxis=dict(
            range=[axis_range.z_min, axis_range.z_max],
            dtick=30,
            showgrid=True,
            scaleanchor="x",
            fixedrange=True,
            constrain="domain",
        ),
    )

    # --- Grid coordinates ---
    add_grid_labels(fig, map_config)
  
    return fig


# ======================== STATIC TRACES ======================== #

def add_trail(fig: go.Figure, timeline_df: pd.DataFrame) -> None:
    """Add faded trail showing all positions."""
    fig.add_trace(go.Scatter(
        x=timeline_df["pos_x"].tolist(),
        y=timeline_df["pos_z"].tolist(),
        mode="markers",
        marker=dict(color=TRAIL_COLOR, size=TRAIL_SIZE, opacity=TRAIL_OPACITY),
        hovertext=[f"{t:.2f}s" for t in timeline_df["time"].tolist()],
        hoverinfo="text",
        name="Trail",
        showlegend=False,
    ))


def add_attempt_paths(fig: go.Figure, timeline_df: pd.DataFrame) -> None:
    """Add one colored path per attempt. All data shown at once."""
    attempts = sorted(timeline_df["attempt_number"].unique())
    attempts = [a for a in attempts if a != -1]

    for j, attempt in enumerate(attempts):
        mask = timeline_df[timeline_df["attempt_number"] == attempt]
        color = ATTEMPT_COLORS[j % len(ATTEMPT_COLORS)]

        fig.add_trace(go.Scatter(
            x=mask["pos_x"].tolist(),
            y=mask["pos_z"].tolist(),
            mode="lines+markers",
            marker=dict(color=color, size=ATTEMPT_MARKER_SIZE),
            line=dict(color=color, width=ATTEMPT_LINE_WIDTH),
            opacity=ATTEMPT_OPACITY,
            name=f"Attempt {attempt}",
            hovertext=[f"{t:.2f}s" for t in mask["time"].tolist()],
            hoverinfo="text",
        ))


def add_game_events(
    fig: go.Figure,
    game_events_df: pd.DataFrame,
    player_movement_df: pd.DataFrame,
) -> None:
    """Add all game events at their player positions."""
    for verb, style in EVENT_STYLES.items():
        verb_df = game_events_df[game_events_df["verb"] == verb]
        positions = [
            get_player_pos_for_time(player_movement_df, t)
            for t in verb_df["time"]
        ]
        valid = [
            (pos, row)
            for pos, (_, row) in zip(positions, verb_df.iterrows())
            if pos is not None
        ]

        if valid:
            fig.add_trace(go.Scatter(
                x=[pos[0] for pos, _ in valid],
                y=[pos[1] for pos, _ in valid],
                mode="markers",
                marker=dict(
                    color=style["color"], size=style["size"], symbol=style["symbol"],
                    line=dict(color="black", width=1),
                ),
                hovertext=[
                    f"{row['actor']} {row['verb']} {row['object']}"
                    for _, row in valid
                ],
                hoverinfo="text",
                opacity=style["opacity"],
                name=style["label"],
            ))

def add_grid_labels(fig: go.Figure, map_config: dict) -> None:
    """Add grid position labels (0,0), (0,1), etc. Hidden by default via legend toggle."""
    block = map_config["block_size"]
    cols = map_config["grid_cols"]
    rows = map_config["grid_rows"]
    half = block / 2

    x_coords = []
    z_coords = []
    labels = []

    # One fewer cell than grid points in each direction
    for col in range(cols):
        for row in range(rows):
            x_coords.append(col * block + half)
            z_coords.append(row * block + half)
            labels.append(f"({col + 1},{row + 1})")

    fig.add_trace(go.Scatter(
        x=x_coords,
        y=z_coords,
        mode="markers+text",
        text=labels,
        textfont=dict(size=9, color="white"),
        textposition="middle center",
        marker=dict(size=9, color="black", opacity=0, symbol="cross"),
        name="Grid coord (x,z)",
        visible="legendonly",  # hidden by default, click legend to show
        hoverinfo="skip"
    ))

# ======================== COMPOSITE ======================== #

def build_static_figure(
    map_image_path: str,
    map_config: dict,
    buildings_df: pd.DataFrame,
    target_building_id: str,
    timeline_df: pd.DataFrame,
    game_events_df: pd.DataFrame,
    title: str = "Player Position",
) -> go.Figure:
    """
    Build a complete static map with all traces.
    One call for the static page.
    """
    fig = build_base_figure(
        map_image_path, map_config, buildings_df, target_building_id
    )

    add_trail(fig, timeline_df)
    add_attempt_paths(fig, timeline_df)
    add_game_events(fig, game_events_df, timeline_df)

    fig.update_layout(title=title)

    return fig