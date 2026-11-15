# Streamlit Community Cloud deployment

## Application configuration

Deploy the repository using:

- **Repository:** `Aaqibhafeezkhan/invisibility-cloak`
- **Branch:** `main`
- **Main file:** `streamlit_app.py`
- **Python runtime:** Python 3.14 (select it in Advanced settings when creating the app)

The pinned dependencies in the root `requirements.txt` include Streamlit, `streamlit-webrtc`, headless OpenCV, NumPy, PyArrow, and PyAV. Keep those versions pinned and verify wheel availability for the selected Python runtime before changing them.

## Webcam and HTTPS

The browser camera requires a secure context. Streamlit Community Cloud provides HTTPS automatically. The browser sends camera frames to the Streamlit application instance over WebRTC, where the Python video processor applies the cloak effect.

The app requests a 640×480 ideal video resolution and a frame rate of up to 30 FPS to keep normal webcam processing responsive. Browsers may negotiate a different resolution depending on the selected camera and device capabilities.

## STUN and TURN

The application keeps Google's public STUN server as a fallback. STUN-only connectivity may not work on restrictive NATs, firewalls, or corporate networks. Configure TURN credentials to support relayed connections in those environments.

Add the following to **App settings → Secrets**:

```toml
[twilio]
account_sid = "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
auth_token = "your-twilio-auth-token"
```

The application requests temporary ICE credentials from Twilio at runtime using a server-side authenticated request. The account token is never passed to the browser. The returned ICE configuration is cached for 3,000 seconds, below the 3,600-second lifetime requested from the provider. Google STUN remains in the configuration as a fallback.

When credentials are absent or the provider request fails, the app continues with STUN-only connectivity and does not expose the provider's internal error details in the UI.

For local development, the same structure can be placed in `.streamlit/secrets.toml`. That file is ignored by Git and must never be committed.

## Troubleshooting

### The camera does not start

- Open the app over HTTPS.
- Allow camera access in the browser permission prompt.
- Check that another application is not exclusively using the camera.
- Use the camera selector in the WebRTC preview if more than one camera is available.
- Reload the page and retry after changing browser permissions.

### The WebRTC preview does not connect

- Confirm that outbound WebRTC traffic is allowed by the network.
- Try a different network to distinguish a browser/device issue from a restrictive NAT or firewall.
- Configure Twilio TURN credentials in Streamlit Secrets when STUN-only connectivity is insufficient.
- Confirm that the Streamlit Secrets section names and keys match the example above.

### The cloak looks noisy or incomplete

- Capture the background again with nobody in the frame.
- Keep the camera still during calibration.
- Choose the closest colour preset.
- Adjust hue, saturation, and brightness thresholds.
- Reduce mask cleanup if narrow details such as fingers are disappearing.
- Avoid clothing or objects in the background that share the cloak colour.

### The camera disconnects

The current calibration and snapshot are invalidated when the video track ends. Restart the camera and capture a fresh background before using the cloak again.

## Redeploying

After changing dependencies or deployment configuration, use **Reboot app** or redeploy from the Streamlit Community Cloud workspace. Confirm the package installer completes and manually verify the camera stream and TURN configuration on the deployed URL.
