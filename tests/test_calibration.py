import numpy as np
import pytest

from cloak_app.calibration import BackgroundCalibrator


def test_calibrator_uses_median_to_reject_transient_frame():
    calibrator = BackgroundCalibrator(target_frames=5, max_samples=5)
    background = None
    for value in (20, 20, 255, 20, 20):
        background = calibrator.add_frame(np.full((2, 2, 3), value, dtype=np.uint8))
    assert calibrator.complete
    assert calibrator.progress == 1.0
    assert np.all(background == 20)


def test_calibrator_reports_progress_before_completion():
    calibrator = BackgroundCalibrator(target_frames=4, max_samples=4)
    calibrator.add_frame(np.zeros((2, 2, 3), dtype=np.uint8))
    calibrator.add_frame(np.zeros((2, 2, 3), dtype=np.uint8))
    assert calibrator.progress == 0.5
    assert not calibrator.complete


def test_calibrator_rejects_resolution_change():
    calibrator = BackgroundCalibrator(target_frames=3, max_samples=3)
    calibrator.add_frame(np.zeros((2, 2, 3), dtype=np.uint8))
    with pytest.raises(ValueError, match="resolution changed"):
        calibrator.add_frame(np.zeros((3, 2, 3), dtype=np.uint8))


def test_calibrator_rejects_invalid_frame():
    calibrator = BackgroundCalibrator(target_frames=1)
    with pytest.raises(ValueError, match="three-channel"):
        calibrator.add_frame(np.zeros((2, 2), dtype=np.uint8))
