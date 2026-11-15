import json

from cloak_app.webrtc import DEFAULT_ICE_SERVERS, get_ice_servers


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


def test_missing_credentials_return_stun_fallback():
    assert get_ice_servers() == DEFAULT_ICE_SERVERS


def test_valid_twilio_servers_keep_stun_fallback():
    payload = {"ice_servers": [{"urls": ["turn:relay.example.com"], "username": "temporary", "credential": "ephemeral"}]}
    result = get_ice_servers("AC123", "secret", opener=lambda request, timeout: FakeResponse(payload))
    assert len(result) == 2
    assert result[0]["urls"] == ["turn:relay.example.com"]
    assert result[1]["urls"][0].startswith("stun:")


def test_twilio_stun_server_avoids_duplicate_fallback():
    payload = {"ice_servers": [{"urls": ["stun:provider.example.com"]}]}
    result = get_ice_servers("AC123", "secret", opener=lambda request, timeout: FakeResponse(payload))
    assert result == payload["ice_servers"]


def test_malformed_or_failed_twilio_response_falls_back():
    result = get_ice_servers("AC123", "secret", opener=lambda request, timeout: FakeResponse({"unexpected": []}))
    assert result == DEFAULT_ICE_SERVERS

    def fail(request, timeout):
        raise TimeoutError("timeout")

    assert get_ice_servers("AC123", "secret", opener=fail) == DEFAULT_ICE_SERVERS
