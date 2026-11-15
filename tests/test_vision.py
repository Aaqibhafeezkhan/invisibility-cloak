import cv2
import numpy as np
import pytest

from cloak_app.config import normalize_settings
from cloak_app.vision import apply_cloak, build_mask, encode_png


def test_build_mask_supports_normal_hue_range():
    hsv = np.array([[[50, 200, 200], [100, 200, 200]]], dtype=np.uint8)
    mask = build_mask(hsv, 35, 85, 70, 255, 45, 255)
    assert mask.tolist() == [[255, 0]]


def test_build_mask_supports_hue_wraparound_for_red():
    hsv = np.array([[[0, 220, 220], [179, 220, 220], [80, 220, 220]]], dtype=np.uint8)
    mask = build_mask(hsv, 160, 10, 70, 255, 45, 255)
    assert mask.tolist() == [[255, 255, 0]]


def test_build_mask_rejects_invalid_shape_and_hue():
    with pytest.raises(ValueError):
        build_mask(np.zeros((2, 2), dtype=np.uint8), 0, 10, 0, 255, 0, 255)
    with pytest.raises(ValueError):
        build_mask(np.zeros((2, 2, 3), dtype=np.uint8), -1, 10, 0, 255, 0, 255)


def test_normalize_settings_makes_blur_odd_and_orders_thresholds():
    values = normalize_settings({"blur_size": 4, "sat_min": 240, "sat_max": 20, "val_min": 230, "val_max": 10})
    assert values["blur_size"] == 5
    assert (values["sat_min"], values["sat_max"]) == (20, 240)
    assert (values["val_min"], values["val_max"]) == (10, 230)


def test_apply_cloak_replaces_only_detected_pixels():
    frame = np.zeros((5, 5, 3), dtype=np.uint8)
    frame[:, :2] = (0, 255, 0)
    background = np.full_like(frame, 120)
    settings = {
        "hue_min": 35,
        "hue_max": 85,
        "sat_min": 70,
        "sat_max": 255,
        "val_min": 45,
        "val_max": 255,
        "blur_size": 1,
        "cleanup_iterations": 0,
        "temporal_smoothing": 0,
    }
    output, mask = apply_cloak(frame, background, settings)
    assert np.all(output[:, :2] == 120)
    assert np.all(output[:, 2:] == 0)
    assert mask.dtype == np.uint8
    assert mask.shape == frame.shape[:2]


def test_apply_cloak_rejects_different_background_dimensions():
    with pytest.raises(ValueError):
        apply_cloak(np.zeros((4, 4, 3), dtype=np.uint8), np.zeros((3, 4, 3), dtype=np.uint8))


def test_encode_png_returns_png_bytes():
    encoded = encode_png(np.zeros((4, 4, 3), dtype=np.uint8))
    assert encoded.startswith(b"\x89PNG\r\n\x1a\n")
    decoded = cv2.imdecode(np.frombuffer(encoded, dtype=np.uint8), cv2.IMREAD_COLOR)
    assert decoded.shape == (4, 4, 3)
