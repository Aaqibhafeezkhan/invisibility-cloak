"""Standalone desktop version of the Invisibility Cloak effect."""

from __future__ import annotations

import time

import cv2
import numpy as np

from cloak_app.vision import apply_cloak


def capture_background(cap: cv2.VideoCapture, frames: int = 45, delay: float = 0.05) -> np.ndarray | None:
    """Capture a clean background, averaging only successfully read frames."""
    accumulator = None
    captured = 0
    while captured < frames:
        success, image = cap.read()
        if not success:
            time.sleep(delay)
            continue
        image = cv2.flip(image, 1)
        image = cv2.GaussianBlur(image, (5, 5), 0)
        if accumulator is None:
            accumulator = np.float32(image)
        else:
            cv2.accumulate(image, accumulator)
        captured += 1
        time.sleep(delay)

    if accumulator is None or captured == 0:
        return None
    return (accumulator / captured).astype(np.uint8)


def main() -> None:
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise RuntimeError("Could not open a camera. Check that a webcam is connected and available.")

    window = "Invisibility Cloak"
    cv2.namedWindow("Controls", cv2.WINDOW_NORMAL)
    cv2.createTrackbar("Hue min", "Controls", 160, 179, lambda _: None)
    cv2.createTrackbar("Hue max", "Controls", 10, 179, lambda _: None)
    cv2.createTrackbar("Saturation min", "Controls", 70, 255, lambda _: None)
    cv2.createTrackbar("Brightness min", "Controls", 45, 255, lambda _: None)

    try:
        time.sleep(1)
        background = capture_background(cap)
        if background is None:
            raise RuntimeError("The camera did not provide frames for background calibration.")

        previous_mask = None
        while True:
            success, frame = cap.read()
            if not success:
                break
            frame = cv2.flip(image, 1)
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

            output, mask = apply_cloak(frame, background, settings, previous_mask)
            previous_mask = mask
            cv2.imshow(window, output)
            cv2.imshow("Detection mask", mask)

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            if key == ord("b"):
                time.sleep(0.5)
                updated_background = capture_background(cap)
                if updated_background is not None:
                    background = updated_background
                    previous_mask = None
            if key == ord("s"):
                filename = f"cloak_snapshot_{int(time.time())}.png"
                if not cv2.imwrite(filename, output):
                    print(f"Could not save snapshot: {filename}")
                else:
                    print(f"Saved {filename}")
    finally:
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
