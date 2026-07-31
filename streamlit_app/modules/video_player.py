"""
Video frame extraction and metadata.
Wraps OpenCV for frame-accurate seeking.
"""

import cv2
import numpy as np


class VideoPlayer:
    """
    Loads a video file and provides frame-by-frame access.
    
    Usage:
        player = VideoPlayer("path/to/video.mp4")
        frame = player.get_frame_at_time(15.0)
        player.release()
    """

    def __init__(self, video_path: str):
        self.cap = cv2.VideoCapture(video_path)
        if not self.cap.isOpened():
            raise FileNotFoundError(f"Could not open video: {video_path}")

        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.duration = self.total_frames / self.fps

    def get_frame_at_index(self, frame_index: int) -> np.ndarray | None:
        """Return RGB frame at a given index, or None if read fails."""
        frame_index = max(0, min(frame_index, self.total_frames - 1))
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
        ret, frame = self.cap.read()
        if not ret:
            return None
        return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    def get_frame_at_time(self, time_sec: float, offset: float = 0.0) -> np.ndarray | None:
        """
        Return RGB frame at a given time in seconds.
        Offset shifts the time (e.g. video starts 10s before game).
        """
        frame_index = int((time_sec + offset) * self.fps)
        return self.get_frame_at_index(frame_index)

    def get_metadata(self) -> dict:
        """Return video metadata."""
        return {
            "total_frames": self.total_frames,
            "fps": self.fps,
            "duration": self.duration,
        }

    def release(self):
        """Release the video file."""
        self.cap.release()