"""Bounded-memory, robust background calibration."""

from __future__ import annotations

import numpy as np


class BackgroundCalibrator:
    """Collect a bounded set of frames and use their per-pixel median."""

    def __init__(self, target_frames: int = 45, max_samples: int = 9) -> None:
        if target_frames < 1 or max_samples < 1:
            raise ValueError("Calibration frame counts must be positive.")
        self.target_frames = int(target_frames)
        self.max_samples = min(int(max_samples), self.target_frames)
        self._sample_interval = max(1, self.target_frames // self.max_samples)
        self._frames_seen = 0
        self._samples: list[np.ndarray] = []
        self._frame_shape: tuple[int, ...] | None = None
        self.background: np.ndarray | None = None

    @property
    def progress(self) -> float:
        return min(1.0, self._frames_seen / self.target_frames)

    @property
    def frames_seen(self) -> int:
        return self._frames_seen

    @property
    def complete(self) -> bool:
        return self.background is not None

    def add_frame(self, frame: np.ndarray) -> np.ndarray | None:
        if not isinstance(frame, np.ndarray) or frame.ndim != 3 or frame.shape[2] != 3:
            raise ValueError("A valid three-channel camera frame is required for calibration.")
        if frame.dtype != np.uint8:
            raise ValueError("Camera frames must use uint8 pixel values.")
        if self.background is not None:
            return self.background
        if self._frame_shape is None:
            self._frame_shape = frame.shape
        elif frame.shape != self._frame_shape:
            raise ValueError("Camera resolution changed during calibration. Please capture the background again.")

        if self._frames_seen % self._sample_interval == 0 and len(self._samples) < self.max_samples:
            self._samples.append(frame.copy())
        self._frames_seen += 1

        if self._frames_seen < self.target_frames:
            return None
        if not self._samples:
            raise ValueError("No valid camera frames were collected. Please try again.")

        stack = np.stack(self._samples, axis=0)
        self.background = np.median(stack, axis=0).astype(np.uint8)
        self._samples.clear()
        return self.background
