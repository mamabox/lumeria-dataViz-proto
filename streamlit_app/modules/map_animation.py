"""
Add animation frames and playback controls to a plotly figure.
Builds on top of map_builder's base figure.
Pure Python — no streamlit imports.
"""

import plotly.graph_objects as go
import pandas as pd
import numpy as np

from modules.map_styles import (
    TRAIL_COLOR, TRAIL_SIZE, TRAIL_OPACITY,
    PLAYER_COLOR, PLAYER_SIZE, PLAYER_OUTLINE_COLOR, PLAYER_OUTLINE_WIDTH,
    TRIANGLE_SIZE, TRIANGLE_FILL, TRIANGLE_OUTLINE_COLOR, TRIANGLE_OUTLINE_WIDTH, TRIANGLE_MODE,
    ATTEMPT_COLORS, ATTEMPT_MARKER_SIZE, ATTEMPT_LINE_WIDTH,
    EVENT_STYLES,
)
from modules.data_loader import get_player_pos_for_time


# ======================== TRIANGLE ======================== #

BASE_TRIANGLE = np.array([
    [0, TRIANGLE_SIZE / 2],
    [-TRIANGLE_SIZE / 2, -TRIANGLE_SIZE / 2],
    [TRIANGLE_SIZE / 2, -TRIANGLE_SIZE / 2],
])


def _get_rotated_triangle(x: float, z: float, rot_y: float) -> tuple[list, list]:
    """Rotate and translate triangle to a position. Returns (x_list, z_list)."""
    angle = -rot_y
    rad = np.radians(angle)
    cos_a, sin_a = np.cos(rad), np.sin(rad)
    rotated = np.array([
        [v[0] * cos_a - v[1] * sin_a, v[0] * sin_a + v[1] * cos_a]
        for v in BASE_TRIANGLE
    ])
    rotated[:, 0] += x
    rotated[:, 1] += z
    # Close the shape
    tri_x = list(rotated[:, 0]) + [rotated[0, 0]]
    tri_z = list(rotated[:, 1]) + [rotated[0, 1]]
    return tri_x, tri_z


# ======================== ANIMATED TRACES ======================== #

def add_animated_traces(
    fig: go.Figure,
    timeline_df: pd.DataFrame,
) -> dict:
    """
    Add empty animated traces to the figure.
    Returns a dict of trace indices for the frame builder.
    """
    attempts = sorted(timeline_df["attempt_number"].unique())
    attempts = [a for a in attempts if a != -1]

    # Track where each group of traces starts
    start_idx = len(fig.data)
    indices = {}

    # --- Trail (static, but added here to keep trace order clean) ---
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

    # --- Event traces (one per verb) ---
    event_start = len(fig.data)
    verb_list = list(EVENT_STYLES.keys())
    for verb in verb_list:
        style = EVENT_STYLES[verb]
        fig.add_trace(go.Scatter(
            x=[], y=[],
            mode="markers",
            marker=dict(
                color=style["color"], size=style["size"], symbol=style["symbol"],
                line=dict(color="black", width=1),
            ),
            hoverinfo="text",
            name=style["label"],
            opacity=style["opacity"],
        ))
    indices["events"] = list(range(event_start, event_start + len(verb_list)))

    # --- Attempt paths (one per attempt) ---
    attempt_start = len(fig.data)
    for j, attempt in enumerate(attempts):
        color = ATTEMPT_COLORS[j % len(ATTEMPT_COLORS)]
        fig.add_trace(go.Scatter(
            x=[], y=[],
            mode="lines+markers",
            marker=dict(color=color, size=ATTEMPT_MARKER_SIZE),
            line=dict(color=color, width=ATTEMPT_LINE_WIDTH),
            name=f"Attempt {attempt}",
        ))
    indices["attempts"] = list(range(attempt_start, attempt_start + len(attempts)))

    # --- Current position marker ---
    indices["current"] = len(fig.data)
    fig.add_trace(go.Scatter(
        x=[], y=[],
        mode="markers",
        marker=dict(
            color=PLAYER_COLOR, size=PLAYER_SIZE,
            line=dict(color=PLAYER_OUTLINE_COLOR, width=PLAYER_OUTLINE_WIDTH),
        ),
        showlegend=False,
    ))

    # --- Rotation triangle ---
    indices["triangle"] = len(fig.data)
    fig.add_trace(go.Scatter(
        x=[], y=[],
        fill="toself",
        fillcolor=TRIANGLE_FILL,
        line=dict(color=TRIANGLE_OUTLINE_COLOR, width=TRIANGLE_OUTLINE_WIDTH),
        mode=TRIANGLE_MODE,
        showlegend=False,
    ))

    # Store metadata for frame building
    indices["attempts_list"] = attempts
    indices["verb_list"] = verb_list

    return indices


# ======================== FRAMES ======================== #

def build_frames(
    timeline_df: pd.DataFrame,
    game_events_df: pd.DataFrame,
    indices: dict,
) -> list[go.Frame]:
    """
    Build all animation frames.
    Each frame updates: events, attempt paths, current marker, triangle.
    """
    x_list = timeline_df["pos_x"].tolist()
    z_list = timeline_df["pos_z"].tolist()
    time_list = timeline_df["time"].tolist()
    rot_y_list = timeline_df["rot_y"].tolist()
    attempt_list = timeline_df["attempt_number"].tolist()
    attempt_duration_list = timeline_df["attempt_duration"].tolist()

    attempts = indices["attempts_list"]
    verb_list = indices["verb_list"]

    # Precompute event positions
    event_positions = {
        i: get_player_pos_for_time(timeline_df, t)
        for i, t in game_events_df["time"].items()
    }

    # All animated trace indices in order
    animated_indices = (
        indices["events"]
        + indices["attempts"]
        + [indices["current"], indices["triangle"]]
    )

    frames = []
    for i in range(len(x_list)):
        # --- Events ---
        event_traces = []
        for verb in verb_list:
            style = EVENT_STYLES[verb]
            mask = game_events_df[
                (game_events_df["verb"] == verb)
                & (game_events_df["time"] <= time_list[i])
            ].index
            event_traces.append(go.Scatter(
                x=[event_positions[j][0] for j in mask if event_positions[j] is not None],
                y=[event_positions[j][1] for j in mask if event_positions[j] is not None],
                hovertext=[
                    f"{game_events_df.loc[j, 'actor']} {verb} {game_events_df.loc[j, 'object']}"
                    for j in mask if event_positions[j] is not None
                ],
                hoverinfo="text",
                name=style["label"],
                showlegend=True,
            ))

        # --- Attempt paths ---
        attempt_traces = []
        for attempt in attempts:
            mask = [j for j in range(i + 1) if attempt_list[j] == attempt]
            attempt_traces.append(go.Scatter(
                x=[x_list[j] for j in mask],
                y=[z_list[j] for j in mask],
                hovertext=[
                    f"Duration: {attempt_duration_list[j]:.1f}s"
                    if not np.isnan(attempt_duration_list[j])
                    else "In progress"
                    for j in mask
                ],
                hoverinfo="text",
                name=f"Attempt {attempt}",
                showlegend=True,
            ))

        # --- Current marker ---
        current_trace = go.Scatter(
            x=[x_list[i]], y=[z_list[i]],
        )

        # --- Triangle ---
        next_frame = min(i + 1, len(x_list) - 1)
        tri_x, tri_z = _get_rotated_triangle(
            x_list[next_frame], z_list[next_frame], rot_y_list[i]
        )
        tri_trace = go.Scatter(x=tri_x, y=tri_z)

        frames.append(go.Frame(
            data=event_traces + attempt_traces + [current_trace, tri_trace],
            traces=animated_indices,
            name=str(i),
        ))

    return frames


# ======================== PLAYBACK CONTROLS ======================== #

def add_playback_controls(
    fig: go.Figure,
    time_list: list[float],
    speeds: dict = None,
) -> None:
    """
    Add play/pause buttons and time slider to the figure.
    """
   # Real time between samples in ms
    realtime_ms = int((time_list[-1] - time_list[0]) / len(time_list) * 1000)

    speeds = {
        "1x": realtime_ms,
        "8x": realtime_ms // 8,
        "16x": realtime_ms // 16,
    }

    # --- Speed buttons ---
    play_buttons = [
        dict(
            label=f"▶ {label}",
            method="animate",
            args=[None, dict(
                frame=dict(duration=ms, redraw=True),
                transition=dict(duration=0),
                fromcurrent=True,
            )],
        )
        for label, ms in speeds.items()
    ]

    play_buttons.append(
        dict(
            label="⏸",
            method="animate",
            args=[[None], dict(
                frame=dict(duration=0, redraw=True),
                mode="immediate",
            )],
        )
    )

    # --- Slider steps ---

    steps = [
        dict(
            args=[[str(i)], dict(
                frame=dict(duration=0, redraw=True),
                mode="immediate",
            )],
            method="animate",
            label=f"{time_list[i]:.0f}s" if i % 2 == 0 else "", # show every other label
        )
        for i in range(len(time_list))
    ]

    fig.update_layout(
         updatemenus=[dict(
            type="buttons",
            showactive=True,
            x=1.0, y=1.1, xanchor="right",
            direction="left",
            buttons=play_buttons,
        )],
        sliders=[dict(
            active=0,
            x=0.05, len=0.9,
            minorticklen=0,
            currentvalue=dict(prefix="Game Time: "),
            steps=steps,
        )],
    )


# ======================== FULL BUILD ======================== #

def build_animated_figure(
    fig: go.Figure,
    timeline_df: pd.DataFrame,
    game_events_df: pd.DataFrame,
    challenge_id: int = None,
    challenge_duration: float = None,
) -> go.Figure:
    """
    Add animation to an existing base figure.
    Call with the result of build_base_figure().
    """
    indices = add_animated_traces(fig, timeline_df)
    frames = build_frames(timeline_df, game_events_df, indices)
    fig.frames = frames

    time_list = timeline_df["time"].tolist()
    add_playback_controls(fig, time_list)

    # Challenge annotation
    if challenge_id is not None and challenge_duration is not None:
        fig.add_annotation(
            text=f"Challenge {challenge_id} - {challenge_duration:.2f}s",
            x=0, y=1.15,
            xref="paper", yref="paper",
            showarrow=False,
            font=dict(size=14),
        )

    return fig