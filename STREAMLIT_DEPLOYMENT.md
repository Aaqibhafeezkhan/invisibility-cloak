# Streamlit Community Cloud deployment

## Runtime

The application is compatible with the current Streamlit Community Cloud Python 3.14 runtime using the pinned dependencies in `requirements.txt`.

## Deploy

Use:

- Repository: `aaqib-hafeez-khan-in/invisibility-cloak`
- Branch: `main`
- Main file: `streamlit_app.py`

After merging a dependency change, use **Reboot app** or redeploy from the Streamlit workspace so the new environment is rebuilt.

## Python version

Community Cloud lets you select the Python version from **Advanced settings** when deploying. Python version cannot be changed on an already-deployed app without deleting and redeploying the app. This repository is configured to work with Python 3.14, so changing the runtime should not be necessary for this release.

## Webcam

The live webcam requires HTTPS. Streamlit Community Cloud provides HTTPS automatically. WebRTC connectivity on restrictive networks may additionally require TURN configuration through Streamlit secrets.
