"""
Animation exporter — renders an animated map figure's own frames to MP4.
No gameplay video involved (see video_exporter.py for the combined export).
Pure Python — no streamlit imports.
"""

import cv2
import numpy as np
import plotly.graph_objects as go


def export_animation_to_mp4(
    fig: go.Figure,
    output_path: str = "temp_animation.mp4",
    fps: int = 1,
    width: int = 800,
    height: int = 700,
) -> bytes:
    """
    Render the animated figure's frames to MP4.
    Pulls frame data directly from the figure.
    """

    if not fig.frames:
        raise ValueError("Figure has no animation frames")

    base_data = list(fig.data)
    layout = fig.layout

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    for i, frame in enumerate(fig.frames):

        # Copy base traces as dicts (preserves all styling)
        frame_data = [trace.to_plotly_json() for trace in base_data]

        # Merge frame data into base (keeps styles, updates x/y/text)
        for trace_data, trace_idx in zip(frame.data, frame.traces):
            frame_data[trace_idx].update(trace_data.to_plotly_json())

        frame_fig = go.Figure(data=frame_data, layout=layout)
        frame_fig.update_layout(title=f"Game Time: {frame.name}")

        # Render
        img_bytes = frame_fig.to_image(format="png", width=width, height=height)
        img_array = np.frombuffer(img_bytes, dtype=np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        writer.write(img)

    writer.release()

    with open(output_path, "rb") as f:
        return f.read()
