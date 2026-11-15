"""Streamlit entry point for the real-time Invisibility Cloak experience."""

from __future__ import annotations

import streamlit as st
import av
import cv2
from streamlit_webrtc import RTCConfiguration, VideoProcessorBase, webrtc_streamer

from cloak_app import COLOUR_PRESETS, DEFAULT_SETTINGS, CloakState
from cloak_app.config import normalize_settings
from cloak_app.webrpc import get_ice_servers

st.set_page_config(
    page_title="Invisibility Cloak",
    page_icon="🪄",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .stApp { background: radial-gradient(ellipse at 50% -20%, #13202d 0%, #080b11 48%, #07090e 100%); }
    .block-container { max-width: 1440px; padding-top: 1.5rem; padding-bottom: 2.5rem; }
    [data-testid="stSidebar"] { background: rgba(8, 13, 21, .96); border-right: 1px solid rgba(125, 211, 252, .12); }
    .cloak-hero { padding: .5rem 0 1.25rem; }
    .cloak-eyebrow { color: #67e8f9; text-transform: uppercase; letter-spacing: .22em; font-size: .7rem; font-weight: 700; }
    .cloak-title { color: #f8fafc; font-size: clamp(2.1rem, 5vw, 3.8rem); line-height: 1.05; font-weight: 850; letter-spacing: -.055em; margin: .35rem 0 .6rem; }
    .cloak-subtitle { max-width: 700px; color: #9ca3af; font-size: 1rem; line-height: 1.6; }
    .cloak-panel { background: rgba(15, 23, 42, .62); border: 1px solid rgba(148, 163, 184, .15); border-radius: 16px; padding: 1rem 1.1rem; }
    .cloak-panel-title { color: #e2e8f0; font-weight: 700; margin-bottom: .25rem; }
    .cloak-muted { color: #94a3b8; font-size: .88rem; }
    div[data-testid="stVerticalBlock"] > div:has(> div.stButton) button { border-radius: 10px; min-height: 2.7rem; }
    div[data-testid="stDownloadButton"] button { border-radius: 10px; min-height: 2.7rem; }
    @media (max-width: 760px) {
      .block-container { padding-left: 1rem; padding-right: 1rem; }
      .cloak-title { font-size: 2.35rem; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


class CloakProcessor(VideoProcessorBase):
    """Thin WebRTC adapter; all shared state and CV work live outside Streamlit UI."""

    def __init__(self, cloak_state: CloakState) -> None:
        self.cloak_state = cloak_state
        self.processor_token = cloak_state.register_processor()

    def on_ended(self) -> None:
        self.cloak_state.mark_disconnected(self.processor_token)

    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
        image = frame.to_ndarray(format="bgr24")
        image = cv2.flip(image, 1)
        processed, mask = self.cloak_state.process_frame(image, self.processor_token)
        settings = self.cloak_state.get_settings()

        if settings["debug_view"] and mask is not None:
            display = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
        else:
            display = processed
        return av.VideoFrame.from_ndarray(display, format="bgr24")


def read_twilio_credentials() -> tuple[str | None, str | None]:
    """Read secrets without exposing provider details in the UI or logs."""
    try:
        config = st.secrets["twilio"]
        account_sid = str(config["account_sid"]).strip()
        auth_token = str(config["auth_token"]).strip()
        if account_sid and auth_token:
            return account_sid, auth_token
    except Exception:
        pass
    return None, None


@st.cache_data(ttl=3000, show_spinner=False)
def cached_ice_servers(account_sid: str | None, auth_token: str | None) -> list[dict]:
    """Cache ephemeral TURN configuration for less than its requested lifetime."""
    return get_ice_servers(account_sid, auth_token, raise_on_error=True)


if "cloak_state" not in st.session_state:
    st.session_state.cloak_state = CloakState()

cloak_state: CloakState = st.session_state.cloak_state

st.markdown(
    """
    <div class="cloak-hero">
      <div class="cloak-eyebrow">Real-time computer vision</div>
      <div class="cloak-title">INVISIBILITY CLOAK</div>
      <div class="cloak-subtitle">Capture your surroundings, hold up a solid-coloured cloth, and watch it disappear into the background.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("### Cloak controls")
    preset_name = st.selectbox("Cloak colour", options=list(COLOUR_PRESETS), index=0)
    preset = COLOUR_PRESETS[preset_name]

    st.markdown("#### Colour detection")
    hue_min = st.slider("Hue minimum", 0, 179, int(preset["hue_min"]), key=f"hue_min_{preset_name}")
    hue_max = st.slider("Hue maximum", 0, 179, int(preset["hue_max"]), key=f"hue_max_{preset_name}")
    sat_min = st.slider("Saturation minimum", 0, 255, int(preset["sat_min"]), key=f"sat_min_{preset_name}")
    sat_max = st.slider("Saturation maximum", 0, 255, int(preset["sat_max"]), key=f"sat_max_{preset_name}")
    val_min = st.slider("Brightness minimum", 0, 255, int(preset["val_min"]), key=f"val_min_{preset_name}")
    val_max = st.slider("Brightness maximum", 0, 255, int(preset["val_max"]), key=f"val_max_{preset_name}")

    with st.expander("Advanced image controls"):
        blur_size = st.select_slider("Smoothing", options=[1, 3, 5, 7, 9], value=5, key="cloak_blur_size")
        cleanup_iterations = st.slider("Mask cleanup", 0, 4, 2, key="cloak_cleanup_iterations")
        temporal_smoothing = st.slider(
            "Temporal stability", 0.0, 0.5, 0.15, step=0.05,
            help="Blend a small amount of the previous mask to reduce frame-to-frame flicker.",
            key="cloak_temporal_smoothing",
        )
        debug_view = st.checkbox("Show detection mask", value=False, key="cloak_debug_view")

    settings = normalize_settings(
        {
            "hue_min": hue_min,
            "hue_max": hue_max,
            "sat_min": sat_min,
            "sat_max": sat_max,
            "val_min": val_min,
            "val_max": val_max,
            "blur_size": blur_size,
            "cleanup_iterations": cleanup_iterations,
            "temporal_smoothing": temporal_smoothing,
            "debug_view": debug_view,
        }
    )
    cloak_state.update_settings(settings)

    st.divider()
    st.caption("Tip: use a brightly coloured, evenly lit cloth. Keep that colour out of the background when possible.")

account_sid, auth_token = read_twilio_credentials()
try:
    ice_servers = cached_ice_servers(account_sid, auth_token)
except RuntimeError:
    # Exceptions are not cached, so a transient provider failure can be retried
    # after the next Streamlit rerun instead of caching STUN-only mode for 50 min.
    ice_servers = get_ice_servers()

with st.expander("How to use the cloak", expanded=False):
    st.markdown(
        """
        1. Start the camera in the preview and allow browser camera access.
        2. Step completely out of the camera view.
        3. Select **Capture background** and wait until calibration completes.
        4. Enter the frame holding a solid-coloured cloth.
        5. Choose a colour preset and fine-tune the controls if needed.
        6. Download a PNG snapshot of the processed frame.

        For the cleanest effect, keep the camera still after calibration and use a cloth that contrasts with the rest of the scene.
        """
    )

left, right = st.columns([4, 1], gap="large")

with left:
    st.markdown('<div class="cloak-panel-title">Live cloak preview</div>', unsafe_allow_html=True)
    webrtc_ctx = webrtc_streamer(
        key="neon-cloak",
        video_processor_factory=lambda: CloakProcessor(cloak_state),
        rtc_configuration=RTCConfiguration({"iceServers": ice_servers}),
        media_stream_constraints={
            "video": {
                "width": {"ideal": 640},
                "height": {"ideal": 480},
                "frameRate": {"ideal": 24, "max": 30},
            },
            "audio": False,
        },
        async_processing=True,
    )
    st.caption("Use the camera controls in the preview to start or stop your webcam.")

with right:
    st.markdown('<div class="cloak-panel-title">Session controls</div>', unsafe_allow_html=True)
    try:
        camera_is_playing = bool(webrtc_ctx.state.playing)
    except (AttributeError, TypeError):
        camera_is_playing = False

    if st.button("Capture background", type="primary", use_container_width=True, disabled=not camera_is_playing):
        cloak_state.request_background_capture()

    if st.button("Reset cloak", use_container_width=True):
        cloak_state.reset()

    st.markdown('<div class="cloak-muted">Step out of frame before capturing. The camera should remain still during calibration.</div>', unsafe_allow_html=True)

    @st.fragment(run_every="1s")
    def render_session_status() -> None:
        status = cloak_state.get_status()
        try:
            camera_playing = bool(webrtc_ctx.state.playing)
        except (AttributeError, TypeError):
            camera_playing = False

        st.markdown("#### Live status")
        if status["state"] == "error":
            st.error(status["error"] or "Calibration failed. Reset and try again.")
        elif status["state"] == "calibrating":
            st.info("Capturing a clean background…")
            st.progress(status["progress"], text=f"Calibration {status['progress']:.0%}")
        elif status["state"] == "active":
            st.success("Background ready · cloak active")
        elif status["state"] == "disconnected":
            st.warning("Camera disconnected. Reconnect the camera and capture the background again.")
        elif camera_playing:
            st.info("Camera connected » capture a clean background to begin")
        else:
            st.warning("Camera not connected. Start the preview and allow camera access.")

        snapshot_png = cloak_state.get_snapshot_png()
        if snapshot_png:
            st.download_button(
                "Download latest snapshot",
                data=snapshot_png,
                file_name="invisibility-cloak.png",
                mime="image/png",
                use_container_width=True,
                key="download-cloak-snapshot",
            )
        else:
            st.caption("A snapshot will be available after the cloak processes a frame.")

    render_session_status()

st.divider()
st.markdown("#### Privacy and camera processing")
st.caption(
    "Your browser camera stream is sent over WebRTC to this Streamlit app instance, where Python and OpenCV process the frames. "
    "The application keeps the current background and latest snapshot in session memory only; it does not write camera frames or "
    "snapshots to persistent application storage. WebRTC may use the configured STUN/TURN services to establish connectivity. "
    "A TURN relay can transport media traffic through the configured networking provider."
)
st.caption("The live camera requires HTTPS. Streamlit Community Cloud provides HTTPS automatically.")
