# Maintenance Notes

## Streamlit deployment

- Keep `streamlit_app.py` as the Streamlit Community Cloud entrypoint.
- Keep deployment dependencies pinned in `requirements.txt` and verify Python-version compatibility before changing them.
- After dependency changes, reboot the Streamlit app and confirm the dependency installer resolves without source builds.
- Keep WebRTC/TURN credentials out of source control; use Streamlit secrets for private configuration.
