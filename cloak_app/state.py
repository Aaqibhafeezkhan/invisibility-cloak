"""Thread-safe per-session state shared by Streamlit and the WebRTC worker."""

from __future__ import annotations

import threading
import time
from collections.abc import Mapping
from typing import Any

import cv2
import numpy as np

from .calibration import BackgroundCalibrator
from .config import DEFAULT_SETTINGS, normalize_settings
from .vision import apply_cloak, encode_png


class CloakState:
    """Own camera-session state without calling Streamlit from worker threads."""

    def __init__(self, calibration_frames: int = 45) -> None:
        self._lock = threading.RLock()
        self._calibration_frames = calibration_frames
        self._generation = 0
        self._settings = dict(DEFAULT_SETTINGS)
        self._background: np.ndarray | None = None
        self._background_for_shape: tuple[int, ...] | None = None
        self._background_cache: np.ndarray | None = None
        self._calibrator: BackgroundCalibrator | None = None
        self._calibrating = False
        self._calibration_progress = 0.0
        self._calibration_error: str | None = None
        self._previous_mask: np.ndarray | None = None
        self._snapshot: np.ndarray | None = None
        self._last_frame_at: float | None = None
        self._frames_processed = 0
        self._processor_sequence = 0
        self._active_processor_token = 0
        self._camera_disconnected = False

    def register_processor(self) -> int:
        """Register a newly created WebRTC processor and invalidate stale frames."""
        with self._lock:
            self._processor_sequence += 1
            self._active_processor_token = self._processor_sequence
            self._generation += 1
            self._background = None
            self._background_for_shape = None
            self._background_cache = None
            self._calibrator = None
            self._calibrating = False
            self._calibration_progress = 0.0
            self._calibration_error = None
            self._previous_mask = None
            self._snapshot = None
            self._camera_disconnected = False
            return self._active_processor_token

    def mark_disconnected(self, processor_token: int) -> None:
        """Invalidate this processor's output when its input track ends."""
        with self._lock:
            if processor_token != self._active_processor_token:
                return
            self._generation += 1
            self._background = None
            self._background_for_shape = None
            self._background_cache = None
            self._calibrator = None
            self._calibrating = False
            self._calibration_progress = 0.0
            self._calibration_error = None
            self._previous_mask = None
            self._snapshot = None
            self._camera_disconnected = True

    def update_settings(self, settings: Mapping[str, Any]) -> None:
        values = normalize_settings(settings)
        with self._lock:
            self._settings = values

    def get_settings(self) -> dict[str, Any]:
        with self._lock:
            return dict(self._settings)

    def request_background_capture(self) -> None:
        with self._lock:
            self._generation += 1
            self._background = None
            self._background_for_shape = None
            self._background_cache = None
            self._calibrator = BackgroundCalibrator(self._calibration_frames)
            self._calibrating = True
            self._calibration_progress = 0.0
            self._calibration_error = None
            self._previous_mask = None
            self._snapshot = None

    def reset(self) -> None:
        with self._lock:
            self._generation += 1
            self._background = None
            self._background_for_shape = None
            self._background_cache = None
            self._calibrator = None
            self._calibrating = False
            self._calibration_progress = 0.0
            self._calibration_error = None
            self._previous_mask = None
            self._snapshot = None

    def process_frame(self, frame: np.ndarray) -> tuple[np.ndarray, np.ndarray | None]:
        """Process a frame and return (display frame, detection mask)."""
        if not isinstance(frame, np.ndarray) or frame.ndim != 3 or frame.shape[2] != 3:
            raise ValueError("A three-channel BGR camera frame is required.")

        with self._lock:
            self._last_frame_at = time.monotonic()
            self._frames_processed += 1
            self._camera_disconnected = False
            generation = self._generation
            calibrating = self._calibrating
            calibrator = self._calibrator
            background = self._background
            settings = dict(self._settings)
            previous_mask = self._previous_mask

        if calibrating and calibrator is not None:
            try:
                completed_background = calibrator.add_frame(frame)
                progress = calibrator.progress
            except ValueError as error:
                with self._lock:
                    if generation == self._generation:
                        self._calibrating = False
                        self._calibrator = None
                        self._calibration_error = str(error)
                return frame, None

            with self._lock:
                if generation == self._generation and self._calibrating:
                    self._calibration_progress = progress
                    if completed_background is not None:
                        self._background = completed_background
                        self._background_for_shape = completed_background.shape
                        self._background_cache = completed_background
                        self._calibrating = False
                        self._calibrator = None
                        self._calibration_progress = 1.0
                        self._previous_mask = None
            return frame, None

        if background is None:
            return frame, None

        if background.shape != frame.shape:
            with self._lock:
                cached = self._background_cache
                cached_shape = self._background_for_shape
            if cached is None or cached_shape != frame.shape:
                resized = cv2.resize(background, (frame.shape[1], frame.shape[0]), interpolation=cv2.INTER_LINEAR)
                with self._lock:
                    if generation != self._generation or self._background is None:
                        return frame, None
                    self._background_cache = resized
                    self._background_for_shape = frame.shape
                    background = resized
            else:
                background = cached

        output, mask = apply_cloak(frame, background, settings, previous_mask)
        with self._lock:
            if generation == self._generation and self._background is not None:
                self._snapshot = output.copy()
                self._previous_mask = mask
        return output, mask

    def get_snapshot(self) -> np.ndarray | None:
        with self._lock:
            return None if self._snapshot is None else self._snapshot.copy()

    def get_snapshot_png(self) -> bytes | None:
        snapshot = self.get_snapshot()
        return None if snapshot is None else encode_png(snapshot)

    def get_status(self) -> dict[str, Any]:
        with self._lock:
            if self._calibration_error:
                state = "error"
            elif self._calibrating:
                state = "calibrating"
            elif self._background is not None:
                state = "active"
            elif self._camera_disconnected:
                state = "disconnected"
            else:
                state = "waiting"
            return {
                "state": state,
                "progress": self._calibration_progress,
                "error": self._calibration_error,
                "has_background": self._background is not None,
                "has_snapshot": self._snapshot is not None,
                "frames_processed": self._frames_processed,
                "last_frame_at": self._last_frame_at,
            }
