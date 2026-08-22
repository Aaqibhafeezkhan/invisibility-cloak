import streamlit as st
import streamlit_webrtc
import streamlit_webrtc.shutdown
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase, RTCConfiguration
import cv2
import numpy as np
import av
import threading

if hasattr(streamlit_webrtc.shutdown, "SessionShutdownObserver"):
    _original_stop = getattr(streamlit_webrtc.shutdown.SessionShutdownObserver, "stop", None)
    if _original_stop:
        def _patched_stop(self, *args, **kwargs):
            if not hasattr(self, "_polling_thread"):
                return
            return _original_stop(self, *args, **kwargs)
        streamlit_webrtc.shutdown.SessionShutdownObserver.stop = _patched_stop

st.set_page_config(page_title="NEON CLOAK AI", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;900&display=swap');
    
    * { font-family: 'Outfit', sans-serif; }
    
    .stApp {
        background: radial-gradient(circle at top right, #12122b, #050507);
    }
    
    [data-testid="stSidebar"] {
        background: rgba(10, 10, 15, 0.8) !important;
        backdrop-filter: blur(20px);
        border-right: 1px solid rgba(255, 255, 255, 0.05);
        min-width: 300px !important;
    }
    
    .stButton>button {
        background: linear-gradient(90deg, #6366f1, #a855f7);
        color: white;
        border: none;
        border-radius: 12px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
        padding: 12px;
        transition: all 0.3s;
        margin-top: 0.5rem;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(99, 102, 241, 0.4);
        color: white;
    }
    
    h1 {
        background: linear-gradient(to right, #6366f1, #a855f7, #ec4899);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 900;
        font-size: 4.5rem !important;
        text-align: center;
        margin-bottom: 0 !important;
    }
    
    .subtitle {
        color: #94a3b8;
        text-align: center;
        letter-spacing: 8px;
        font-size: 0.9rem;
        margin-bottom: 3rem;
        font-weight: 300;
    }
    
    .stSlider label {
        color: #a855f7 !important;
        font-weight: 600 !important;
        letter-spacing: 1px;
        font-size: 0.8rem !important;
    }
    
    .instruction-card {
        background: rgba(255, 255, 255, 0.03);
        padding: 1.5rem;
        border-radius: 16px;
        border: 1px solid rgba(255, 255, 255, 0.05);
        margin-bottom: 2rem;
    }
    
    .instruction-card h4 {
        color: #6366f1;
        margin-bottom: 1rem;
        font-size: 0.9rem;
        letter-spacing: 2px;
    }
    
    .instruction-card p {
        font-size: 0.85rem;
        color: #94a3b8;
        margin-bottom: 0.5rem;
    }
    
    section[data-testid="stSidebar"] h2 {
        font-size: 1.5rem !important;
        color: white !important;
        font-weight: 900 !important;
        letter-spacing: 1px !important;
        margin-top: -2rem !important;
        margin-bottom: 2rem !important;
    }

    .css-1v0mb7p.e115fcil1 {
        background-color: transparent !important;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1>NEON CLOAK AI</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>PYTHON STREAMLIT CORE</p>", unsafe_allow_html=True)

with st.expander("📖 **HOW TO USE INVISIBILITY CLOAK (Setup Guide)**", expanded=False):
    st.markdown("""
        **1. Initialize the Camera**: Click **START** below and allow browser camera permissions.
        **2. Calibrate Background**: Step completely out of the camera view. Click **CAPTURE BASE** on the right side. Wait until status says **CLOAK ACTIVE**.
        **3. Deploy Cloak**: Step back into the frame holding a solid-colored cloth (e.g., Green or Red).
        **4. Tune Frequencies**: Use the sliders in the left sidebar to dial in your cloth's exact Hue, Saturation, and Brightness until it vanishes!
        **5. Save Proof**: Once you achieve maximum invisibility, click **SAVE SNAPSHOT** to download your masterpiece.
    """)

class SharedState:
    def __init__(self):
        self.lock = threading.Lock()
        self.bg_frame = None
        self.capture_requested = False
        self.capture_count = 0
        self.bg_accumulator = None
        self.snapshot = None

if "state" not in st.session_state:
    st.session_state.state = SharedState()

state = st.session_state.state

st.sidebar.markdown("## SYSTEM CONFIG")

with st.sidebar:
    st.markdown("""
        <div class="instruction-card">
            <h4>HOW TO USE</h4>
            <p>1. Start the camera below.</p>
            <p>2. Move out of the frame.</p>
            <p>3. Click <b>CAPTURE BASE</b>.</p>
            <p>4. Enter the frame and adjust sliders to vanish.</p>
        </div>
    """, unsafe_allow_html=True)

h_low = st.sidebar.slider("HUE MIN", 0, 179, 140)
h_high = st.sidebar.slider("HUE MAX", 0, 179, 179)
s_low = st.sidebar.slider("SAT MIN", 0, 255, 60)
s_high = st.sidebar.slider("SAT MAX", 0, 255, 255)
v_low = st.sidebar.slider("VAL MIN", 0, 255, 40)
v_high = st.sidebar.slider("VAL MAX", 0, 255, 255)

class CloakProcessor(VideoProcessorBase):
    def __init__(self):
        self._state = state
        self.h_low = h_low
        self.h_high = h_high
        self.s_low = s_low
        self.s_high = s_high
        self.v_low = v_low
        self.v_high = v_high

    def recv(self, frame):
        img = frame.to_ndarray(format="bgr24")
        img = cv2.flip(img, 1)

        with self._state.lock:
            if self._state.capture_requested:
                if self._state.capture_count == 0:
                    self._state.bg_accumulator = np.float32(img)
                else:
                    cv2.accumulate(img, self._state.bg_accumulator)
                
                self._state.capture_count += 1
                if self._state.capture_count >= 30:
                    self._state.bg_frame = (self._state.bg_accumulator / 30).astype(np.uint8)
                    self._state.capture_requested = False
                    self._state.capture_count = 0
                
                return av.VideoFrame.from_ndarray(img, format="bgr24")

            if self._state.bg_frame is None:
                return av.VideoFrame.from_ndarray(img, format="bgr24")

            bg = self._state.bg_frame
            if bg.shape != img.shape:
                bg = cv2.resize(bg, (img.shape[1], img.shape[0]))

            blurred = cv2.GaussianBlur(img, (5, 5), 0)
            hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

            lower1 = np.array([self.h_low, self.s_low, self.v_low])
            upper1 = np.array([self.h_high, self.s_high, self.v_high])
            mask1 = cv2.inRange(hsv, lower1, upper1)

            lower2 = np.array([0, self.s_low, self.v_low])
            upper2 = np.array([10, self.s_high, self.v_high])
            mask2 = cv2.inRange(hsv, lower2, upper2)
            
            mask = cv2.bitwise_or(mask1, mask2)
            kernel = np.ones((3, 3), np.uint8)
            mask = cv2.medianBlur(mask, 5)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=2)
            mask = cv2.dilate(mask, kernel, iterations=2)

            mask_inv = cv2.bitwise_not(mask)
            part1 = cv2.bitwise_and(bg, bg, mask=mask)
            part2 = cv2.bitwise_and(img, img, mask=mask_inv)
            final = cv2.addWeighted(part1, 1, part2, 1, 0)
            
            self._state.snapshot = final.copy()

            return av.VideoFrame.from_ndarray(final, format="bgr24")

col_main, col_ctrl = st.columns([3, 1])

with col_ctrl:
    st.markdown("<h3 style='font-size: 1rem; color: #94a3b8; letter-spacing: 2px; margin-bottom: 2rem;'>OPERATIONS</h3>", unsafe_allow_html=True)
    if st.button("CAPTURE BASE"):
        with state.lock:
            state.capture_requested = True
            state.capture_count = 0
            state.bg_frame = None
            
    if st.button("RESET SYSTEM"):
        with state.lock:
            state.bg_frame = None
            state.capture_requested = False
            state.snapshot = None

    if st.button("SAVE SNAPSHOT"):
        if state.snapshot is not None:
            ret, buffer = cv2.imencode('.png', cv2.cvtColor(state.snapshot, cv2.COLOR_BGR2RGB))
            st.download_button(label="DOWNLOAD IMAGE", data=buffer.tobytes(), file_name="neon_cloak_capture.png", mime="image/png")
        else:
            st.error("NO ACTIVE CLOAK")

with col_main:
    ctx = webrtc_streamer(
        key="neon-cloak",
        video_processor_factory=CloakProcessor,
        rtc_configuration=RTCConfiguration({
            "iceServers": [{"urls": ["stun:stun.l.google.com:19302", "stun:global.stun.twilio.com:3478", "stun:stun.services.mozilla.com"]}]
        }),
        media_stream_constraints={"video": True, "audio": False}
    )
    
    if ctx.video_processor:
        ctx.video_processor.h_low = h_low
        ctx.video_processor.h_high = h_high
        ctx.video_processor.s_low = s_low
        ctx.video_processor.s_high = s_high
        ctx.video_processor.v_low = v_low
        ctx.video_processor.v_high = v_high
    
    if state.bg_frame is not None:
        st.success("CLOAK ACTIVE")
    elif state.capture_requested:
        st.info(f"CALIBRATING SENSORS... {int((state.capture_count/30)*100)}%")
    else:
        st.warning("SYSTEM READY - CAPTURE BACKGROUND")
