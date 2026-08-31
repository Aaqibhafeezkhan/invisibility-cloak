import base64
import json
import threading
import time
import urllib.parse
import urllib.request
import urllib.error

import av
import cv2
import numpy as np
import streamlit as st
from streamlit_webrtc import RTCConfiguration, VideoProcessorBase, webrtc_streamer

st.set_page_config(page_title="Neon Cloak AI", page_icon="🪄", layout="wide")

st.markdown(
    """
    <style>
    .stApp { background: #07070a; }
    .block-container { max-width: 1400px; padding-top: 2rem; }
    .hero { text-align: center; padding: 0.5rem 0 1.5rem; }
    .hero h1 { font-size: clamp(2.5rem, 6vw, 4.5rem); margin: 0; font-weight: 800; letter-spacing: -0.04em; }
    .hero p { color: #9ca3af; letter-spacing: 0.25em; margin: 0.4rem 0 0; font-size: 0.78rem; }
    .card { background: rgba(255,255,255,.035); border: 1px solid rgba(255,255,255,.08); border-radius: 14px; padding: 1rem 1.1rem; }
    .muted { color: #9ca3af; font-size: .9rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="hero"><h1>NEON CLOAK AI</h1><p>REAL-TIME COMPUTER VISION</p></div>',
    unsafe_allow_html=True,
)

with st.expander("How to use", expanded=False):
    st.markdown(
        """
        1. Start the camera and allow browser camera access.
        2. Step completely out of frame and click **Capture background**.
        3. Wait for calibration to finish, then enter the frame with a solid-colored cloth.
        4. Tune the HSV sliders until the cloth is replaced by the captured background.
        5. Click **Save snapshot** to download the current effect.

        The app runs the vision processing in the browser's live WebRTC stream; no camera recording is uploaded or stored by the application.
        """
    )


class CloakState:
    def __init__(self):
        self.lock = threading.Lock()
        self.background = None
        self.capture_requested = False
        self.capture_count = 0
        self.capture_target = 45
        self.accumulator = None
        self.snapshot = None
        self.last_frame_at = 0.0


if "cloak_state" not in st.session_state:
    st.session_state.cloak_state = CloakState()

state = st.session_state.cloak_state


def get_turn_ice_servers():
    fallback = [{"urls": ["stun:stun.l.google.com:19302"]}]

    try:
        config = st.secrets["twilio"]
        account_sid = config["account_sid"]
        auth_token = config["auth_token"]
    except (KeyError, TypeError):
        return fallback

    if not account_sid or not auth_token:
        return fallback

    token_url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Tokens"
    payload = urllib.parse.urlencode({"Ttl": "3600"}).encode("utf-8")
    credentials = f"{account_sid}:{auth_token}".encode("utf-8")
    request = urllib.request.Request(token_url, data=payload, method="POST")
    request.add_header("Authorization", f"Basic {base64.b64encode(credentials).decode('ascii')}")
    request.add_header("Content-Type", "application/x-www-form-urlencoded")

    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
        ice_servers = data.get("ice_servers")
        if isinstance(ice_servers, list) and ice_servers:
            return ice_servers + fallback
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, ValueError, json.JSONDecodeError):
        return fallback

    return fallback


@st.cache_data(ttl=3000, show_spinner=False)
def cached_turn_ice_servers():
    return get_turn_ice_servers()


ice_servers = cached_turn_ice_servers()

st.sidebar.header("Cloak settings")

hue_min = st.sidebar.slider("Hue minimum", 0, 179, 35)
hue_max = st.sidebar.slider("Hue maximum", 0, 179, 85)
sat_min = st.sidebar.slider("Saturation minimum", 0, 255, 70)
sat_max = st.sidebar.slider("Saturation maximum", 0, 255, 255)
val_min = st.sidebar.slider("Brightness minimum", 0, 255, 45)
val_max = st.sidebar.slider("Brightness maximum", 0, 255, 255)

blur_size = st.sidebar.select_slider("Smoothing", options=[3, 5, 7, 9], value=5)
open_iterations = st.sidebar.slider("Mask cleanup", 0, 4, 2)


def build_mask(hsv, h_min, h_max, s_min, s_max, v_min, v_max):
    lower = np.array([s_min, v_min], dtype=np.uint8)
    upper = np.array([s_max, v_max], dtype=np.uint8)

    if h_min <= h_max:
        return cv2.inRange(hsv, np.array([h_min, s_min, v_min]), np.array([h_max, s_max, v_max]))

    first = cv2.inRange(hsv, np.array([h_min, s_min, v_min]), np.array([179, s_max, v_max]))
    second = cv2.inRange(hsv, np.array([0, s_min, v_min]), np.array([h_max, s_max, v_max]))
    return cv2.bitwise_or(first, second)


class CloakProcessor(VideoProcessorBase):
    def __init__(self):
        self.state = state
        self.hue_min = hue_min
        self.hue_max = hue_max
        self.sat_min = sat_min
        self.sat_max = sat_max
        self.val_min = val_min
        self.val_max = val_max
        self.blur_size = blur_size
        self.open_iterations = open_iterations

    def recv(self, frame):
        image = frame.to_ndarray(format="bgr24")
        image = cv2.flip(image, 1)

        with self.state.lock:
            self.state.last_frame_at = time.time()
            if self.state.capture_requested:
                if self.state.capture_count == 0:
                    self.state.accumulator = np.float32(image)
                else:
                    cv2.accumulate(image, self.state.accumulator)

                self.state.capture_count += 1
                if self.state.capture_count >= self.state.capture_target:
                    self.state.background = (
                        self.state.accumulator / self.state.capture_target
                    ).astype(np.uint8)
                    self.state.accumulator = None
                    self.state.capture_requested = False
                    self.state.capture_count = 0
                return av.VideoFrame.from_ndarray(image, format="bgr24")

            background = self.state.background
            if background is None:
                return av.VideoFrame.from_ndarray(image, format="bgr24")

            if background.shape != image.shape:
                background = cv2.resize(background, (image.shape[1], image.shape[0]))

            blurred = cv2.GaussianBlur(image, (self.blur_size, self.blur_size), 0)
            hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)
            mask = build_mask(
                hsv,
                self.hue_min,
                self.hue_max,
                self.sat_min,
                self.sat_max,
                self.val_min,
                self.val_max,
            )

            kernel = np.ones((3, 3), np.uint8)
            mask = cv2.medianBlur(mask, 5)
            if self.open_iterations:
                mask = cv2.morphologyEx(
                    mask, cv2.MORPH_OPEN, kernel, iterations=self.open_iterations
                )
            mask = cv2.dilate(mask, kernel, iterations=1)

            inverse = cv2.bitwise_not(mask)
            background_part = cv2.bitwise_and(background, background, mask=mask)
            foreground_part = cv2.bitwise_and(image, image, mask=inverse)
            result = cv2.add(background_part, foreground_part)
            self.state.snapshot = result.copy()

        return av.VideoFrame.from_ndarray(result, format="bgr24")


def request_background_capture():
    with state.lock:
        state.background = None
        state.accumulator = None
        state.capture_count = 0
        state.capture_requested = True
        state.snapshot = None


def reset_system():
    with state.lock:
        state.background = None
        state.accumulator = None
        state.capture_count = 0
        state.capture_requested = False
        state.snapshot = None


left, right = st.columns([4, 1], gap="large")

with right:
    st.subheader("Operations")
    if st.button("Capture background", use_container_width=True):
        request_background_capture()
        st.rerun()

    if st.button("Reset system", use_container_width=True):
        reset_system()
        st.rerun()

    with state.lock:
        active = state.background is not None
        calibrating = state.capture_requested
        progress = state.capture_count / state.capture_target
        snapshot = None if state.snapshot is None else state.snapshot.copy()

    if active:
        st.success("Cloak active")
    elif calibrating:
        st.info(f"Calibrating: {progress:.0%}")
    else:
        st.warning("Capture a clean background first")

    if st.button("Save snapshot", use_container_width=True):
        if snapshot is None:
            st.error("Start the camera and activate the cloak first.")
        else:
            ok, encoded = cv2.imencode(".png", snapshot)
            if ok:
                st.download_button(
                    "Download PNG",
                    data=encoded.tobytes(),
                    file_name="neon_cloak_capture.png",
                    mime="image/png",
                    use_container_width=True,
                )

    st.markdown(
        '<div class="card"><div class="muted">Tip</div><div>Use a brightly colored, solid cloth and avoid similar colors in the background.</div></div>',
        unsafe_allow_html=True,
    )

with left:
    webrtc_streamer(
        key="neon-cloak",
        video_processor_factory=CloakProcessor,
        rtc_configuration=RTCConfiguration({"iceServers": ice_servers}),
        media_stream_constraints={"video": True, "audio": False},
        async_processing=True,
    )

st.caption("Camera processing happens in the live WebRTC stream. HTTPS is required. The app uses Twilio TURN credentials from Streamlit secrets when configured, with Google STUN retained as a fallback.")
