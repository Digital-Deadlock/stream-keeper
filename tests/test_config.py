import pytest

from src.config import load_config


def test_loads_multiple_urls(monkeypatch):
    monkeypatch.setenv(
        "MSE_URLS",
        '["ws://frigate:1984/api/ws?src=camera_1",'
        '"wss://video.example/api/ws?src=camera_2"]',
    )
    config = load_config()
    assert [stream.identifier for stream in config.streams] == ["camera_1", "camera_2"]
    assert config.reconnect_initial == 2


@pytest.mark.parametrize(
    "value",
    ["", "not-json", "[]", '"ws://frigate:1984/api/ws?src=camera_1"', '["http://bad"]'],
)
def test_rejects_invalid_urls(monkeypatch, value):
    monkeypatch.setenv("MSE_URLS", value)
    with pytest.raises(ValueError):
        load_config()


def test_rejects_inverted_backoff(monkeypatch):
    monkeypatch.setenv("MSE_URLS", '["ws://frigate:1984/api/ws?src=camera_1"]')
    monkeypatch.setenv("RECONNECT_INITIAL_SECONDS", "10")
    monkeypatch.setenv("RECONNECT_MAX_SECONDS", "2")
    with pytest.raises(ValueError, match="RECONNECT_MAX_SECONDS"):
        load_config()

