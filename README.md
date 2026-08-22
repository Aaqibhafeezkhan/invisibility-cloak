# NEON CLOAK AI

A browser-based invisibility cloak demo built with Streamlit, OpenCV, NumPy, and WebRTC.

The application captures a clean background and replaces pixels matching the selected cloak color with that background in real time.

## Features

- Live browser webcam processing with WebRTC
- Background calibration using multiple frames
- HSV color-range controls
- Correct handling of hue ranges that wrap around 0/179
- Mask smoothing and morphology controls
- Snapshot download as PNG
- Streamlit Community Cloud ready
- No camera recording or persistent image storage in the application

## Run locally

```bash
python -m venv .venv

# Windows
.venv\\Scripts\\activate

# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
streamlit run streamlit_app.py
```

Open the local Streamlit URL, start the camera, and allow browser camera access.

## Use the cloak

1. Start the camera.
2. Move completely out of frame.
3. Select **Capture background** and wait for calibration to finish.
4. Enter the frame holding a solid-colored cloth.
5. Adjust Hue, Saturation, and Brightness until the cloth is replaced by the background.
6. Use **Save snapshot** to download the result.

Good starting points:

| Cloth | Hue minimum | Hue maximum |
| --- | ---: | ---: |
| Green | 35 | 85 |
| Blue | 90 | 130 |
| Pink/Magenta | 140 | 179 |
| Red | 160 | 10 |

For red, the minimum is intentionally greater than the maximum; the application treats that as a hue range crossing 179 → 0.

## Streamlit Community Cloud

The repository already contains a root `requirements.txt` and `streamlit_app.py`, which are the important pieces Community Cloud needs to identify and install the app.

Deploy from [Streamlit Community Cloud](https://share.streamlit.io/) by selecting:

- Repository: `aaqib-hafeez-khan-in/invisibility-cloak`
- Branch: `main`
- Main file: `streamlit_app.py`

The live camera requires HTTPS. Streamlit Community Cloud provides HTTPS automatically. WebRTC uses the configured public STUN server; restrictive corporate or home networks may additionally require a TURN server.

For a TURN deployment, add the provider's ICE server configuration to `webrtc_streamer()` rather than committing credentials to the repository. Keep credentials in Streamlit secrets.

## Project files

- `streamlit_app.py` — deployed Streamlit application
- `cloak.py` — original desktop/OpenCV implementation
- `requirements.txt` — pinned deployment dependencies
- `.gitignore` — local development exclusions
