import json
import logging

from src.logging_config import EventFormatter


def test_json_event_formatter():
    record = logging.LogRecord("test", logging.INFO, "", 0, "connected", (), None)
    record.event_fields = {"event": "negotiated", "stream": "camera_1"}
    payload = json.loads(EventFormatter(True).format(record))
    assert payload["event"] == "negotiated"
    assert payload["stream"] == "camera_1"
    assert payload["message"] == "connected"

