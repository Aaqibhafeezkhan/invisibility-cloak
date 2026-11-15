"""Application defaults and validated cloak settings."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

DEFAULT_SETTINGS: dict[str, Any] = {
    "hue_min": 35,
    "hue_max": 85,
    "sat_min": 70,
    "sat_max": 255,
    "val_min": 45,
    "val_max": 255,
    "blur_size": 5,
    "cleanup_iterations": 2,
    "temporal_smoothing": 0.15,
    "debug_view": False,
}

COLOUR_PRESETS: dict[str, dict[str, int]] = {
    "Green": {"hue_min": 35, "hue_max": 85, "sat_min": 70, "sat_max": 255, "val_min": 45, "val_max": 255},
    "Blue": {"hue_min": 90, "hue_max": 130, "sat_min": 65, "sat_max": 255, "val_min": 40, "val_max": 255},
    "Red": {"hue_min": 160, "hue_max": 10, "sat_min": 70, "sat_max": 255, "val_min": 45, "val_max": 255},
    "Magenta": {"hue_min": 140, "hue_max": 179, "sat_min": 60, "sat_max": 255, "val_min": 40, "val_max": 255},
    "Custom": DEFAULT_SETTINGS,
}


def normalize_settings(settings: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Merge user values with defaults and constrain them to valid OpenCV ranges."""
    values = dict(DEFAULT_SETTINGS)
    if settings:
        values.update(settings)

    for key in ("hue_min", "hue_max"):
        values[key] = int(max(0, min(179, int(values[key]))))

    for low_key, high_key in (("sat_min", "sat_max"), ("val_min", "val_max")):
        low = int(max(0, min(255, int(values[low_key]))))
        high = int(max(0, min(255, int(values[high_key]))))
        values[low_key], values[high_key] = min(low, high), max(low, high)

    blur_size = int(values["blur_size"])
    blur_size = max(1, min(15, blur_size))
    if blur_size > 1 and blur_size % 2 == 0:
        blur_size += 1
    values["blur_size"] = blur_size
    values["cleanup_iterations"] = max(0, min(4, int(values["cleanup_iterations"])))
    values["temporal_smoothing"] = max(0.0, min(0.5, float(values["temporal_smoothing"])))
    values["debug_view"] = bool(values["debug_view"])
    return values
