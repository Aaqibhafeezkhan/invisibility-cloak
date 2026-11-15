"""Standalone desktop interface for the Invisibility Cloak effect."""

from __future__ import annotations

import time

import cv2
import numpy as np

from cloak_app.calibration import BackgroundCalibrator
from cloak_app.vision import apply_cloak, encode_png


def capture_background(cap: cv2.VideoCapture, frames: int = 45) -> np.ndarray | None:
    calibrator = BackgroundCalibrator(target_frames=frames)
    captured = 0
    while captured < frames:
        success, frame = cap.read()
        if not success:
            continue
        background = calibrator.add_frame(cv2.flip(frame, 1))
        captured += 1
        if background is not None:
            return background
    return None


def main() -> None:
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise RuntimeError("Could not open a camera. Check that a webcam is connected and available.")

    cv2.namedWindow("Controls", cv2.WINDOW_NORMAL)
    controls = (
        ("Hue min", 160, 179),
        ("Hue max", 10, 179),
        ("Saturation min", 70, 255),
        ("Brightness min", 45, 255),
    )
    for name, initial, maximum in controls:
        cv2.createTrackbar(name, "Controls", initial, maximum, lambda _: None)

    try:
        time.sleep(1)
        background = capture_background(cap)
        if background is None:
            raise RuntimeError("The camera did not provide enough frames for background calibration.")

        previous_mask = None
        while True:
            success, frame = cap.read()
            if not success:
                break
            frame = cv2.flip(frame, 1)
            settings = {
                "hue_min": cv2.getTrackbarPos("Hue min", "Controls"),
                "hue_max": cv2.getTrackbarPos("Hue max", "Controls"),
                "sat_min": cv2.getTrackbarPos("Saturation min", "Controls"),
                "sat_max": 255,
                "val_min": cv2.getTrackbarPos("Brightness min", "Controls"),
                "val_max": 255,
                "blur_size": 5,
                "cleanup_iterations": 2,
                "temporal_smoothing": 0.15,
            }
            if background.shape != frame.shape:
                background = cv2.resize(background, (frame.shape[1], frame.shape[0]))
                previous_mask = None

            output, previous_mask = apply_cloak(frame, background, settings, previous_mask)
            cv2.imshow("Invisibility Cloak", output)
            cv2.imshow("Detection mask", previous_mask)
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            if key == ord("b"):
                time.sleep(0.5)
                replacement = capture_background(cap)
                if replacement is not None:
                    background = replacement
                    previous_mask = None
            if key == ord("s"):
                filename = f"cloak_snapshot_{int(time.time())}.png"
                try:
                    with open(filename, "wb") as snapshot:
                        snapshot.write(encode_png(output))
                except OSError as error:
                    print(f"Could not save snapshot: {error}")
                else:
                    print(f"Saved {filename}")
    finally:
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
