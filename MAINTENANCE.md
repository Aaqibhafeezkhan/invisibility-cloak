# Maintenance Notes

## Local development

- Keep `streamlit_app.py` as the Streamlit Community Cloud entry point.
- Keep the reusable computer-vision, calibration, session-state, and ICE configuration logic in `cloak_app/`.
- Add regression tests for behavior changes under `tests/`.
- Run `python -m pytest -q` after changing core processing or state logic.
- Install development dependencies with `python -m pip install -r requirements-dev.txt`.

## Runtime and deployment

- Keep deployment dependencies pinned in `requirements.txt`.
- Verify wheel availability and Python-version compatibility before changing pinned versions.
- The documented Streamlit Community Cloud runtime is Python 3.14.
- Keep the root `streamlit_app.py` entry point and deploy manually through Streamlit Community Cloud.
- After dependency changes, reboot the app and confirm the dependency installer resolves without unexpected source builds.

## WebRTC and secrets

- Keep STUN fallback behavior in `cloak_app/webrtc.py`.
- Generate short-lived TURN credentials server-side; never pass the Twilio account token to the browser.
- Configure `[twilio] account_sid` and `auth_token` through Streamlit Secrets.
- Keep `.streamlit/secrets.toml` out of version control.
- Do not log ICE credentials, raw camera frames, or snapshot contents.

## Privacy

- The browser camera stream is transported over WebRTC to the Streamlit application instance for Python/OpenCV processing.
- Current background, masks, and the latest snapshot are held in per-session memory only.
- Do not introduce persistent camera-frame or snapshot storage without an explicit product and privacy review.
- Keep the UI and README privacy statements aligned with the actual media and processing path.
