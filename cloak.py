import cv2
import numpy as np
import time

def nothing(x):
    pass

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    exit()

cv2.namedWindow("Controls", cv2.WINDOW_NORMAL)
cv2.createTrackbar("H_low", "Controls", 140, 179, nothing)
cv2.createTrackbar("S_low", "Controls", 60, 255, nothing)
cv2.createTrackbar("V_low", "Controls", 40, 255, nothing)
cv2.createTrackbar("H_high", "Controls", 179, 179, nothing)
cv2.createTrackbar("S_high", "Controls", 255, 255, nothing)
cv2.createTrackbar("V_high", "Controls", 255, 255, nothing)

def capture_background(frames=60, delay=0.05):
    buf = None
    for i in range(frames):
        ret, frame = cap.read()
        if not ret:
            continue
        frame = cv2.flip(frame, 1)
        frame = cv2.GaussianBlur(frame, (5, 5), 0)
        if buf is None:
            buf = np.float32(frame)
        else:
            cv2.accumulate(frame, buf)
        time.sleep(delay)
    if buf is None:
        return None
    avg = (buf / frames).astype(np.uint8)
    return avg

time.sleep(2)
background = capture_background()

if background is None:
    cap.release()
    cv2.destroyAllWindows()
    exit()

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    blurred = cv2.GaussianBlur(frame, (5, 5), 0)
    hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

    h_low = cv2.getTrackbarPos("H_low", "Controls")
    s_low = cv2.getTrackbarPos("S_low", "Controls")
    v_low = cv2.getTrackbarPos("V_low", "Controls")
    h_high = cv2.getTrackbarPos("H_high", "Controls")
    s_high = cv2.getTrackbarPos("S_high", "Controls")
    v_high = cv2.getTrackbarPos("V_high", "Controls")

    lower1 = np.array([h_low, s_low, v_low])
    upper1 = np.array([h_high, s_high, v_high])

    mask1 = cv2.inRange(hsv, lower1, upper1)

    lower2 = np.array([0, s_low, v_low])
    upper2 = np.array([10, s_high, v_high])
    mask2 = cv2.inRange(hsv, lower2, upper2)

    mask = cv2.bitwise_or(mask1, mask2)

    kernel = np.ones((3, 3), np.uint8)
    mask = cv2.medianBlur(mask, 5)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=2)
    mask = cv2.dilate(mask, kernel, iterations=2)

    mask_inv = cv2.bitwise_not(mask)

    part1 = cv2.bitwise_and(background, background, mask=mask)
    part2 = cv2.bitwise_and(frame, frame, mask=mask_inv)
    final = cv2.addWeighted(part1, 1, part2, 1, 0)

    cv2.imshow("Pink Cloak Effect", final)
    cv2.imshow("Mask", mask)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key == ord('b'):
        time.sleep(1)
        background = capture_background()
    elif key == ord('s'):
        timestamp = int(time.time())
        filename = f"cloak_snapshot_{timestamp}.png"
        cv2.imwrite(filename, final)

cap.release()
cv2.destroyAllWindows()

