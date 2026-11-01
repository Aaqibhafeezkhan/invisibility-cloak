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

The live webcam requires HTTPS. Streamlit Community Cloud provides HTTPS automatically. WebRTC connectivity on restrictive networks can require TURN configuration.

## TURN configuration

The application reads Twilio Network Traversal credentials from Streamlit secrets and requests short-lived ICE server credentials at runtime. Google STUN remains available as a fallback when Twilio secrets are missing or the token request fails.

Configure the following values in the Streamlit Community Cloud **Secrets** setting:

```toml
[twilio]
account_sid = "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
auth_token = "your-twilio-auth-token"
```

Do not commit `.streamlit/secrets.toml` or place Twilio credentials in application code. Streamlit recommends storing secrets outside the repository and exposes deployed-app secrets through its Secrets management interface. Twilio's Network Traversal Service issues ephemeral TURN credentials for WebRTC clients, with a configurable lifetime.

Local development can use `.streamlit/secrets.toml` with the same structure. Keep that file out of version control.
