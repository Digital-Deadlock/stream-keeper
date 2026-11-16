"""Environment configuration for Stream Keeper."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from urllib.parse import parse_qs, urlsplit

DEFAULT_CODECS = (
    "avc1.640029,avc1.64002A,avc1.640033,hvc1.1.6.L153.B0,"
    "mp4a.40.2,mp4a.40.5,flac,opus"
)


@dataclass(frozen=True)
class StreamConfig:
    identifier: str
    url: str


@dataclass(frozen=True)
class Config:
    streams: tuple[StreamConfig, ...]
    codecs: str
    reconnect_initial: float
    reconnect_max: float
    stats_interval: float
    handshake_timeout: float
    log_level: str
    log_format: str


def _positive_float(name: str, default: float) -> float:
    raw = os.getenv(name, str(default))
    try:
        value = float(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be a number") from exc
    if value <= 0:
        raise ValueError(f"{name} must be greater than zero")
    return value


def _stream_identifier(url: str, index: int) -> str:
    query = parse_qs(urlsplit(url).query)
    source = query.get("src", [""])[0].strip()
    return source or f"stream_{index}"


def load_config() -> Config:
    raw_urls = os.getenv("MSE_URLS")
    if not raw_urls:
        raise ValueError("MSE_URLS is required and must be a JSON array")
    try:
        urls = json.loads(raw_urls)
    except json.JSONDecodeError as exc:
        raise ValueError("MSE_URLS must be a valid JSON array") from exc
    if not isinstance(urls, list) or not urls:
        raise ValueError("MSE_URLS must be a non-empty JSON array")

    streams: list[StreamConfig] = []
    for index, url in enumerate(urls, start=1):
        if not isinstance(url, str) or not url.strip():
            raise ValueError(f"MSE_URLS item {index} must be a non-empty string")
        parsed = urlsplit(url)
        if parsed.scheme not in {"ws", "wss"} or not parsed.netloc:
            raise ValueError(f"MSE_URLS item {index} must be a ws:// or wss:// URL")
        streams.append(StreamConfig(_stream_identifier(url, index), url))

    reconnect_initial = _positive_float("RECONNECT_INITIAL_SECONDS", 2)
    reconnect_max = _positive_float("RECONNECT_MAX_SECONDS", 60)
    if reconnect_max < reconnect_initial:
        raise ValueError(
            "RECONNECT_MAX_SECONDS must be greater than or equal to "
            "RECONNECT_INITIAL_SECONDS"
        )

    log_format = os.getenv("LOG_FORMAT", "json").lower()
    if log_format not in {"json", "text"}:
        raise ValueError("LOG_FORMAT must be json or text")

    return Config(
        streams=tuple(streams),
        codecs=os.getenv("MSE_CODECS", DEFAULT_CODECS),
        reconnect_initial=reconnect_initial,
        reconnect_max=reconnect_max,
        stats_interval=_positive_float("STATS_INTERVAL_SECONDS", 30),
        handshake_timeout=_positive_float("HANDSHAKE_TIMEOUT_SECONDS", 10),
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
        log_format=log_format,
    )

