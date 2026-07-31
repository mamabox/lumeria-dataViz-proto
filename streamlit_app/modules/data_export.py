"""
Export dataframes to downloadable formats.
Pure Python — no streamlit imports.
"""

import os
import pandas as pd
import cv2
import numpy as np
import plotly.graph_objects as go


def dataframe_to_csv_bytes(df: pd.DataFrame) -> bytes:
    """Convert a dataframe to CSV bytes for download."""
    return df.to_csv(index=False).encode("utf-8")


def export_all_to_csv(game_data: dict, output_dir: str) -> list[str]:
    """
    Export all dataframes from game_data to CSV files on disk.
    Returns list of file paths created.
    """
    os.makedirs(output_dir, exist_ok=True)

    exports = {
        "player_movement.csv": game_data["player_movement_df"],
        "challenges.csv": game_data["challenge_df"],
        "game_events.csv": game_data["game_events_df"],
        "validations.csv": game_data["validations_df"],
    }

    paths = []
    for filename, df in exports.items():
        path = os.path.join(output_dir, filename)
        df.to_csv(path, index=False)
        paths.append(path)

    return paths

def export_animation_to_mp4(
    fig: go.Figure,
    output_path: str = "temp_animation.mp4",
    fps: int = 10,
    width: int = 800,
    height: int = 700,
    every_n: int = 1,
) -> bytes:
    """
    Render the animated figure's frames to MP4.
    Pulls frame data directly from the figure.
    """
    import cv2
    import numpy as np
    import plotly.graph_objects as go

    if not fig.frames:
        raise ValueError("Figure has no animation frames")

    base_data = list(fig.data)
    layout = fig.layout

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    for i, frame in enumerate(fig.frames):
        if i % every_n != 0:
            continue

        # Start with base traces, swap in this frame's data
        frame_data = list(base_data)
        for trace_data, trace_idx in zip(frame.data, frame.traces):
            frame_data[trace_idx] = trace_data

        # Fresh figure with correct data
        frame_fig = go.Figure(data=frame_data, layout=layout)
        frame_fig.update_layout(title=f"Game Time: {frame.name}")

        # Render to image
        img_bytes = frame_fig.to_image(format="png", width=width, height=height)
        img_array = np.frombuffer(img_bytes, dtype=np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        writer.write(img)

    writer.release()

    with open(output_path, "rb") as f:
        return f.read()