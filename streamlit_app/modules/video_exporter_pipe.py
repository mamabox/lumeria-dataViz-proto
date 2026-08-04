"""
Video exporter (pipe method) — combines animated map + gameplay video into a single mp4.

Streams raw frames directly to ffmpeg via stdin pipe.
No intermediate files, less disk I/O.

Usage:
    export_combined_video_pipe(
        animated_fig=fig,
        video_path="gameplay.mp4",
        timeline_df=timeline_df,
        output_path="/tmp/combined_pipe.mp4",
        offset=10.0,
        speed=1,
    )
"""

import bisect
import io

import cv2
import numpy as np
from PIL import Image
import subprocess

from modules.map_animation import get_frame_snapshot


def _render_map_to_array(fig, frame_index: int, width: int, height: int) -> np.ndarray:
    """Render a single animation frame to an RGB numpy array."""
    snapshot = get_frame_snapshot(fig, frame_index)
    img_bytes = snapshot.to_image(format="png", width=width, height=height)
    img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    return np.array(img)


def _find_frame_index(time_list: list[float], game_time: float) -> int:
    """Find the closest animation frame index for a given game time."""
    idx = bisect.bisect_right(time_list, game_time) - 1
    return max(0, min(idx, len(time_list) - 1))


def _make_even(n: int) -> int:
    """Round up to nearest even number (required by libx264)."""
    return n + (n % 2)


def _get_video_frame(cap: cv2.VideoCapture, game_time: float, offset: float, fps: float) -> np.ndarray | None:
    """Get an RGB frame from the video at a given game time."""
    frame_index = int((game_time + offset) * fps)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if frame_index < 0 or frame_index >= total:
        return None
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
    ret, frame = cap.read()
    if not ret:
        return None
    return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)


def export_combined_video_pipe(
    animated_fig,
    video_path: str,
    timeline_df,
    output_path: str,
    offset: float = 0.0,
    speed: int = 1,
    output_fps: int = 30,
    map_width: int = 800,
    map_height: int = 600,
    on_progress=None,
) -> None:
    """
    Export a combined video with gameplay footage on the left
    and the animated map on the right. Streams frames to ffmpeg via pipe.

    Parameters
    ----------
    animated_fig : plotly Figure with animation frames
    video_path : path to the gameplay .mp4
    timeline_df : DataFrame with a "time" column (game time in seconds)
    output_path : where to save the combined .mp4
    offset : seconds into the video where the game starts
    speed : playback speed multiplier (1, 4, 8)
    output_fps : frames per second in the output video
    map_width : pixel width for the rendered map
    map_height : pixel height for the rendered map
    on_progress : callable(current_frame, total_frames)
    """
    time_list = timeline_df["time"].tolist()
    max_game_time = time_list[-1]
    total_output_frames = int((max_game_time / speed) * output_fps)

    # --- Open gameplay video ---
    cap = cv2.VideoCapture(video_path)
    video_fps = cap.get(cv2.CAP_PROP_FPS)

    # --- Determine output dimensions ---
    map_sample = _render_map_to_array(animated_fig, 0, map_width, map_height)
    h_map, w_map = map_sample.shape[:2]

    video_sample = _get_video_frame(cap, time_list[0], offset, video_fps)
    if video_sample is not None:
        vid_aspect = video_sample.shape[1] / video_sample.shape[0]
        w_vid = int(h_map * vid_aspect)
    else:
        w_vid = int(h_map * 16 / 9)

    total_width = _make_even(w_map + w_vid)
    total_height = _make_even(h_map)

    # --- Start ffmpeg process ---
    cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{total_width}x{total_height}",
        "-pix_fmt", "rgb24",
        "-r", str(output_fps),
        "-i", "-",
        "-c:v", "libx264",
        "-crf", "28",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        output_path,
    ]

    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    # --- Stream frames ---
    last_map_idx = -1
    last_map_img = None
    black_video = np.zeros((total_height, w_vid, 3), dtype=np.uint8)

    for i in range(total_output_frames):
        game_time = (i / output_fps) * speed

        # Map frame — only re-render when the index changes
        map_idx = _find_frame_index(time_list, game_time)
        if map_idx != last_map_idx:
            last_map_img = _render_map_to_array(animated_fig, map_idx, map_width, map_height)
            if last_map_img.shape[0] != total_height or last_map_img.shape[1] != w_map:
                last_map_img = np.array(
                    Image.fromarray(last_map_img).resize((w_map, total_height))
                )
            last_map_idx = map_idx

        # Video frame
        video_frame = _get_video_frame(cap, game_time, offset, video_fps)
        if video_frame is not None:
            vid_resized = np.array(
                Image.fromarray(video_frame).resize((w_vid, total_height))
            )
        else:
            vid_resized = black_video

        # Combine: video on left, map on right
        combined = np.hstack([vid_resized, last_map_img])

        if combined.shape[1] < total_width:
            pad = np.zeros((total_height, total_width - combined.shape[1], 3), dtype=np.uint8)
            combined = np.hstack([combined, pad])
        elif combined.shape[1] > total_width:
            combined = combined[:, :total_width, :]

        proc.stdin.write(combined.tobytes())

        if on_progress:
            on_progress(i + 1, total_output_frames)

    # --- Finalize ---
    proc.stdin.close()
    proc.wait()
    cap.release()