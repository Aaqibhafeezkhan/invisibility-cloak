"""Pure OpenCV operations used by the desktop and WebRTC applications."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import cv2
import numpy as np

from .config import normalize_settings


def build_mask(
    hsv: np.ndarray,
    hue_min: int,
    hue_max: int,
    sat_min: int,
    sat_max: int,
    val_min: int,
    val_max: int,
) -> np.ndarray:
    """Create an 8-bit cloak mask, supporting hue ranges that cross 179 -> 0."""
    if not isinstance(hsv, np.ndarray) or hsv.ndim != 3 or hsv.shape[2] != 3:
        raise ValueError("HSV input must be a three-channel image.")
    if hsv.dtype != np.uint8:
        raise ValueError("HSV input must use uint8 values.")

    h_min, h_max = int(hue_min), int(hue_max)
    s_min, s_max = sorted((int(sat_min), int(sat_max)))
    v_min, v_max = sorted((int(val_min), int(val_max)))
    if not 0 <= h_min <= 179 or not 0 <= h_max <= 179:
        raise ValueError("Hue thresholds must be between 0 and 179.")
    if not 0 <= s_min <= s_max <= 255 or not 0 <= v_min <= v_max <= 255:
        raise ValueError("Saturation and brightness thresholds must be between 0 and 255.")

    if h_min <= h_max:
        lower = np.array([h_min, s_min, v_min], dtype=np.uint8)
        upper = np.array([h_max, s_max, v_max], dtype=np.uint8)
        return cv2.inRange(hsv, lower, upper)

    first = cv2.inRange(
        hsv,
        np.array([h_min, s_min, v_min], dtype=np.uint8),
        np.array([179, s_max, v_max], dtype=np.uint8),
    )
    second = cv2.inRange(
        hsv,
        np.array([0, s_min, v_min], dtype=np.uint8),
        np.array([h_max, s_max, v_max], dtype=np.uint8),
    )
    return cv2.bitwise_or(first, second)


def apply_cloak(
    frame: np.ndarray,
    background: np.ndarray,
    settings: Mapping[str, Any] | None = None,
    previous_mask: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Replace detected cloak-colour pixels with the calibrated background."""
    if not isinstance(frame, np.ndarray) or frame.ndim != 3 or frame.shape[2] != 3:
        raise ValueError("Frame must be a three-channel BGR image.")
    if frame.dtype != np.uint8:
        raise ValueError("Frame must use uint8 pixel values.")
    if not isinstance(background, np.ndarray) or background.shape != frame.shape:
        raise ValueError("Background and camera frame must have identical dimensions.")
    if background.dtype != np.uint8:
        raise ValueError("Background must use uint8 pixel values.")

    values = normalize_settings(settings)
    blur_size = values["blur_size"]
    blurred = cv2.GaussianBlur(frame, (blur_size, blur_size), 0) if blur_size > 1 else frame
    hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)
    mask = build_mask(
        hsv,
        values["hue_min"],
        values["hue_max"],
        values["sat_min"],
        values["sat_max"],
        values["val_min"],
        values["val_max"],
    )

    if blur_size > 1:
        mask = cv2.medianBlur(mask, 3)

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    iterations = values["cleanup_iterations"]
    if iterations:
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=iterations)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=1)

    smoothing = values["temporal_smoothing"]
    if (
        smoothing > 0
        and isinstance(previous_mask, np.ndarray)
        and previous_mask.shape == mask.shape
        and previous_mask.dtype == np.uint8
    ):
        mask = cv2.addWeighted(mask, 1.0 - smoothing, previous_mask, smoothing, 0)

    alpha = mask.astype(np.float32)[..., np.newaxis] / 255.0
    output = np.rint(
        frame.astype(np.float32) * (1.0 - alpha)
        + background.astype(np.float32) * alpha
    ).astype(np.uint8)
    return output, mask


def encode_png(image: np.ndarray) -> bytes:
    """Encode a processed frame as PNG bytes, raising a useful error on failure."""
    if not isinstance(image, np.ndarray) or image.ndim != 3 or image.shape[2] != 3:
        raise ValueError("Snapshot must be a three-channel image.")
    success, encoded = cv2.imencode(".png", image)
    if not success:
        raise RuntimeError("OpenCV could not encode the snapshot as PNG.")
    return encoded.tobytes()
