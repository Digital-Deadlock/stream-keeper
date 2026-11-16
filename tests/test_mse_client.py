import asyncio
import json
import logging

import websockets

from src.config import Config, StreamConfig
from src.mse_client import MSEKeeper


async def test_performs_mse_handshake_and_drains_media(unused_tcp_port):
    request_seen = asyncio.Event()

    async def handler(websocket):
        request = json.loads(await websocket.recv())
        assert request["type"] == "mse"
        assert "avc1" in request["value"]
        request_seen.set()
        await websocket.send(
            json.dumps({"type": "mse", "value": 'video/mp4; codecs="avc1.64001F"'})
        )
        await websocket.send(b"media-fragment")
        await asyncio.sleep(0.1)

    async with websockets.serve(handler, "127.0.0.1", unused_tcp_port):
        stream = StreamConfig("camera_1", f"ws://127.0.0.1:{unused_tcp_port}/api/ws?src=camera_1")
        config = Config(
            streams=(stream,),
            codecs="avc1.640029",
            reconnect_initial=0.01,
            reconnect_max=0.02,
            stats_interval=60,
            handshake_timeout=1,
            log_level="INFO",
            log_format="json",
        )
        keeper = MSEKeeper(stream, config, logging.getLogger("test"))
        stop = asyncio.Event()
        task = asyncio.create_task(keeper.run(stop))
        await asyncio.wait_for(request_seen.wait(), timeout=1)
        for _ in range(20):
            if keeper.stats.bytes_received:
                break
            await asyncio.sleep(0.01)
        stop.set()
        await asyncio.wait_for(task, timeout=1)

    assert keeper.stats.bytes_received == len(b"media-fragment")
    assert keeper.stats.messages_received == 1

