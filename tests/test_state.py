import cv2
import numpy as np

from cloak_app.state import CloakState


def test_state_transitions_from_waiting_to_active_and_reset():
    state = CloakState(calibration_frames=3)
    frame = np.full((4, 4, 3), 40, dtype=np.uint8)
    assert state.get_status()["state"] == "waiting"
    state.request_background_capture()
    assert state.get_status()["state"] == "calibrating"
    for _ in range(3):
        state.process_frame(frame)
    assert state.get_status()["state"] == "active"
    state.process_frame(frame)
    assert state.get_snapshot() is not None
    state.reset()
    status = state.get_status()
    assert status["state"] == "waiting"
    assert not status["has_background"]
    assert not status["has_snapshot"]


def test_state_invalidates_partial_calibration_when_resolution_changes():
    state = CloakState(calibration_frames=3)
    state.request_background_capture()
    state.process_frame(np.zeros((2, 2, 3), dtype=np.uint8))
    state.process_frame(np.zeros((3, 2, 3), dtype=np.uint8))
    status = state.get_status()
    assert status["state"] == "error"
    assert "resolution changed" in status["error"]
    assert not status["has_background"]


def test_settings_updates_reach_active_state():
    state = CloakState()
    state.update_settings({"hue_min": 160, "hue_max": 10, "debug_view": True})
    settings = state.get_settings()
    assert settings["hue_min"] == 160
    assert settings["hue_max"] == 10
    assert settings["debug_view"] is True


def test_snapshot_png_is_available_only_after_processed_frame():
    state = CloakState(calibration_frames=1)
    assert state.get_snapshot_png() is None
    background = np.zeros((8, 8, 3), dtype=np.uint8)
    state.request_background_capture()
    state.process_frame(background)
    current = background.copy()
    current[2:6, 2:6] = (0, 255, 0)
    state.update_settings({"cleanup_iterations": 0, "blur_size": 1, "temporal_smoothing": 0})
    state.process_frame(current)
    png = state.get_snapshot_png()
    assert png and png.startswith(b"\x89PNG\r\n\x1a\n")
    decoded = cv2.imdecode(np.frombuffer(png, dtype=np.uint8), cv2.IMREAD_COLOR)
    assert decoded.shape == current.shape


def test_disconnect_clears_background_and_ignores_old_processor_callback():
    state = CloakState(calibration_frames=1)
    old_token = state.register_processor()
    state.request_background_capture()
    frame = np.zeros((3, 3, 3), dtype=np.uint8)
    state.process_frame(frame)
    assert state.get_status()["state"] == "active"

    new_token = state.register_processor()
    state.mark_disconnected(old_token)
    assert state.get_status()["state"] == "waiting"
    state.mark_disconnected(new_token)
    status = state.get_status()
    assert status["state"] == "disconnected"
    assert not status["has_background"]
    assert not status["has_snapshot"]
