"""Server-side ICE configuration and ephemeral TURN credential retrieval."""

from __future__ import annotations

import base64
import json
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from typing import Any

DEFAULT_ICE_SERVERS: list[dict[str, Any]] = [
    {"urls": ["stun:stun.l.google.com:19302"]},
]


def get_ice_servers(
    account_sid: str | None = None,
    auth_token: str | None = None,
    opener: Callable[..., Any] | None = None,
    raise_on_error: bool = False,
) -> list[dict[str, Any]]:
    """Return Twilio ephemeral ICE servers with a Google STUN fallback."""
    fallback = [dict(server) for server in DEFAULT_ICE_SERVERS]
    if not account_sid or not auth_token:
        return fallback

    account_sid = str(account_sid).strip()
    auth_token = str(auth_token).strip()
    if not account_sid or not auth_token:
        return fallback

    token_url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Tokens"
    payload = urllib.parse.urlencode({"Ttl": "3600"}).encode("utf-8")
    credentials = f"{account_sid}:{auth_token}".encode("utf-8")
    request = urllib.request.Request(token_url, data=payload, method="POST")
    request.add_header("Authorization", f"Basic {base64.b64encode(credentials).decode('ascii')}")
    request.add_header("Content-Type", "application/x-www-form-urlencoded")

    try:
        open_url = opener or urllib.request.urlopen
        with open_url(request, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
        ice_servers = data.get("ice_servers") if isinstance(data, dict) else None
        if not isinstance(ice_servers, list) or not ice_servers:
            if raise_on_error:
                raise RuntimeError("TURN provider returned no ICE servers.")
            return fallback
        valid_servers = [server for server in ice_servers if isinstance(server, dict) and server.get("urls")]
        if not valid_servers:
            if raise_on_error:
                raise RuntimeError("TURN provider returned an invalid ICE server configuration.")
            return fallback
        has_stun = any(
            "stun:" in " ".join(server.get("urls", []))
            if isinstance(server.get("urls"), list)
            else str(server.get("urls", ""))
            for server in valid_servers
        )
        return valid_servers if has_stun else valid_servers + fallback
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError, ValueError, TypeError, KeyError) as error:
        if raise_on_error:
            raise RuntimeError("Temporary TURN configuration could not be retrieved.") from error
        return fallback
