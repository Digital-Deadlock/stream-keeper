"""A real go2rtc MSE WebSocket consumer."""

from __future__ import annotations

import asyncio
import json
import logging
import random
import time
from dataclasses import dataclass

import websockets
from websockets.asyncio.client import connect

from .config import Config, StreamConfig
from .logging_config import log_event


@dataclass
class ConnectionStats:
    bytes_received: int = 0
    messages_received: int = 0
    connected_at: float | None = None
    last_media_at: float | None = None


class MSEKeeper:
    def __init__(self, stream: StreamConfig, config: Config, logger: logging.Logger):
        self.stream = stream
        self.config = config
        self.logger = logger
        self.stats = ConnectionStats()

    async def run(self, stop: asyncio.Event) -> None:
        delay = self.config.reconnect_initial
        attempt = 0
        while not stop.is_set():
            attempt += 1
            try:
                await self._consume(stop, attempt)
                delay = self.config.reconnect_initial
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # connection errors are expected operational events
                error_message = str(exc).replace(self.stream.url, "<redacted-url>")
                log_event(
                    self.logger,
                    logging.WARNING,
                    "MSE connection ended",
                    event="disconnected",
                    stream=self.stream.identifier,
                    attempt=attempt,
                    error_type=type(exc).__name__,
                    error=error_message,
                )

            if stop.is_set():
                break
            wait_seconds = min(delay, self.config.reconnect_max)
            jittered = wait_seconds * random.uniform(0.8, 1.2)
            log_event(
                self.logger,
                logging.INFO,
                "Waiting before reconnect",
                event="reconnect_wait",
                stream=self.stream.identifier,
                retry_in_seconds=round(jittered, 2),
            )
            try:
                await asyncio.wait_for(stop.wait(), timeout=jittered)
            except TimeoutError:
                pass
            delay = min(delay * 2, self.config.reconnect_max)

    async def _consume(self, stop: asyncio.Event, attempt: int) -> None:
        log_event(
            self.logger,
            logging.INFO,
            "Connecting to go2rtc MSE feed",
            event="connecting",
            stream=self.stream.identifier,
            attempt=attempt,
        )
        async with connect(
            self.stream.url,
            open_timeout=self.config.handshake_timeout,
            ping_interval=20,
            ping_timeout=20,
            max_size=None,
            compression=None,
        ) as websocket:
            await websocket.send(json.dumps({"type": "mse", "value": self.config.codecs}))
            response = await asyncio.wait_for(
                websocket.recv(), timeout=self.config.handshake_timeout
            )
            if not isinstance(response, str):
                raise RuntimeError("go2rtc sent media before the MSE acknowledgement")
            try:
                acknowledgement = json.loads(response)
            except json.JSONDecodeError as exc:
                raise RuntimeError("invalid MSE acknowledgement from go2rtc") from exc
            if acknowledgement.get("type") != "mse":
                raise RuntimeError("go2rtc did not acknowledge the MSE request")

            now = time.monotonic()
            self.stats = ConnectionStats(connected_at=now)
            log_event(
                self.logger,
                logging.INFO,
                "MSE consumer established",
                event="negotiated",
                stream=self.stream.identifier,
                content_type=acknowledgement.get("value", "unknown"),
            )

            stats_task = asyncio.create_task(self._report_stats(stop))
            try:
                while not stop.is_set():
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=1)
                    except TimeoutError:
                        continue
                    if isinstance(message, bytes):
                        self.stats.bytes_received += len(message)
                        self.stats.messages_received += 1
                        self.stats.last_media_at = time.monotonic()
                    else:
                        self._log_control_message(message)
            except websockets.ConnectionClosed:
                raise
            finally:
                stats_task.cancel()
                await asyncio.gather(stats_task, return_exceptions=True)

    def _log_control_message(self, message: str) -> None:
        try:
            payload = json.loads(message)
            message_type = payload.get("type", "unknown")
        except (json.JSONDecodeError, AttributeError):
            message_type = "invalid"
        log_event(
            self.logger,
            logging.DEBUG,
            "Received go2rtc control message",
            event="control_message",
            stream=self.stream.identifier,
            message_type=message_type,
        )

    async def _report_stats(self, stop: asyncio.Event) -> None:
        while not stop.is_set():
            try:
                await asyncio.wait_for(stop.wait(), timeout=self.config.stats_interval)
                return
            except TimeoutError:
                pass
            now = time.monotonic()
            last_media_age = (
                round(now - self.stats.last_media_at, 1)
                if self.stats.last_media_at is not None
                else None
            )
            log_event(
                self.logger,
                logging.INFO,
                "MSE consumer statistics",
                event="media_stats",
                stream=self.stream.identifier,
                connection_age_seconds=round(now - (self.stats.connected_at or now), 1),
                bytes_received=self.stats.bytes_received,
                messages_received=self.stats.messages_received,
                last_media_age_seconds=last_media_age,
            )

