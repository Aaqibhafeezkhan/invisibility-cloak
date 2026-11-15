# Invisibility Cloak

A real-time browser-based invisibility cloak built with Streamlit, WebRTC, OpenCV, NumPy, and PyAV. Capture a clean background, hold up a solid-coloured cloth, and replace the detected cloth pixels with the background in the live video stream.

**Live app:** [Invisibility Cloak on Streamlit Community Cloud](https://invisibility-neon-cloak.streamlit.app/)

## What it does

- Streams a browser webcam through `streamlit-webrtc`.
- Captures a background over multiple frames and uses a per-pixel median to reduce transient movement.
- Detects cloak colours using HSV segmentation, including hue ranges that wrap from 179 back to 0.
- Provides Green, Blue, Red, Magenta, and Custom colour controls.
- Cleans and stabilizes the detection mask with lightweight OpenCV operations.
- Supports an optional live detection-mask view.
- Downloads a PNG of the latest processed frame.
- Uses short-lived Twilio TURN credentials from Streamlit Secrets when configured, with Google STUN fallback.

## Try the app

1. Open the live app over HTTPS.
2. Start the camera in the preview and allow browser camera access.
3. Step completely out of frame.
4. Select **Capture background** and wait for calibration to finish.
5. Enter the frame holding a solid-coloured cloth.
6. Choose a colour preset and adjust the detection thresholds if needed.
7. Download a snapshot of the processed output.

For the best result, keep the camera still after calibration, use a brightly coloured cloth, and avoid having similar colours elsewhere in the scene. Recalibrate after changing the camera position or lighting substantially.

## Run locally

The browser application requires Python 3.11 or newer and a working webcam in the browser.

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

python -m pip install -r requirements.txt
streamlit run streamlit_app.py
```

Open the local Streamlit URL. For remote access, camera capture requires HTTPS; a plain remote HTTP connection will not be able to request camera access in modern browsers.

### Optional TURN configuration

The application works with Google STUN when Twilio credentials are not configured. Some restrictive NATs, firewalls, and corporate networks require TURN relaying.

For Streamlit Community Cloud, add these values under **App settings → Secrets**:

```toml
[twilio]
account_sid = "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
auth_token = "your-twilio-auth-token"
```

The application requests temporary ICE credentials at runtime. Keep the account SID/auth token in Streamlit Secrets; do not commit them or place them in source code. The generated ICE configuration is cached for less than the requested credential lifetime. When credentials are missing or the provider request fails, the application falls back to Google STUN.

## Run the desktop version

`cloak.py` is a separate OpenCV desktop interface that uses OpenCV HighGUI windows. The Streamlit deployment intentionally uses `opencv-python-headless`; the desktop variant needs the GUI-enabled OpenCV wheel instead. In a separate virtual environment, install the GUI wheel in place of the headless package:

```bash
python -m pip uninstall opencv-python-headless
python -m pip install opencv-python==5.0.0.93
python cloak.py
```

Use the **Controls** window to tune the red hue range. Press `b` to recapture the background, `s` to save a snapshot, and `q` to quit.

## Architecture

```text
Browser camera
    │
    │ WebRTC media stream
    ▼
Streamlit application instance
    │
    ├── streamlit-webrtc processor
    │       ├── BackgroundCalibrator
    │       ├── HSV mask generation
    │       ├── Morphological cleanup and temporal smoothing
    │       └── Background/foreground compositing
    │
    └── Per-session CloakState
            ├── Current background (memory)
            ├── Processing settings
            └── Latest processed snapshot (memory)
```

The `cloak_app` package contains the independently testable computer-vision, calibration, configuration, session-state, and ICE helpers. `streamlit_app.py` is the Streamlit Community Cloud entry point. `cloak.py` is the standalone desktop entry point.

## Privacy and data handling

The browser requests camera permission and sends the video stream over WebRTC to the Streamlit application instance. Python and OpenCV process the frames on that application instance; this is **not** entirely browser-local processing. WebRTC may use STUN/TURN services to establish connectivity, and a TURN relay can transport media traffic through the configured networking provider.

The application keeps the current background, working mask, and latest processed snapshot in per-session memory. It does not write camera frames, backgrounds, or snapshots to persistent application storage, and it does not automatically upload snapshots to a separate storage service. A snapshot is encoded in memory when the user downloads it. Streamlit hosting and the configured WebRTC networking providers remain part of the data path.

## Tests

Install the development dependencies and run the regression suite:

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

The tests cover HSV segmentation (including hue wrap-around), image compositing, background calibration, per-session state transitions, snapshot encoding, and ICE configuration fallback. They do not require a physical webcam or live Twilio credentials.

## Deployment

See [STREAMLIT_DEPLOYMENT.md](STREAMLIT_DEPLOYMENT.md) for the Community Cloud deployment settings, secrets configuration, and troubleshooting steps.

## Known limitations

- A solid, saturated cloth that contrasts with the scene gives the best result. Similar colours in the background may also be replaced.
- This is colour-based chroma keying, not semantic person segmentation. Hair and transparent fabric may not be perfectly preserved.
- A stable camera and a clean background capture are important for a convincing effect.
- STUN alone may not establish a connection on restrictive networks; configure TURN for those environments.
- Automated tests validate core logic, but real browser camera permissions and network traversal still require manual checks on the target deployment.
