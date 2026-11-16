"""Application entry point."""

from __future__ import annotations

import asyncio
import logging
import signal

from .config import load_config
from .logging_config import configure_logging, log_event
from .mse_client import MSEKeeper


async def run() -> None:
    config = load_config()
    logger = configure_logging(config.log_level, config.log_format)
    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop.set)

    log_event(
        logger,
        logging.INFO,
        "Frigate Stream Keeper starting",
        event="startup",
        configured_streams=len(config.streams),
    )
    tasks = [
        asyncio.create_task(MSEKeeper(stream, config, logger).run(stop))
        for stream in config.streams
    ]
    await stop.wait()
    log_event(logger, logging.INFO, "Shutdown requested", event="shutdown")
    for task in tasks:
        task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)


def main() -> None:
    try:
        asyncio.run(run())
    except ValueError as exc:
        logger = configure_logging("INFO", "text")
        log_event(
            logger,
            logging.ERROR,
            "Invalid configuration",
            event="configuration_error",
            error=str(exc),
        )
        raise SystemExit(2) from exc


if __name__ == "__main__":
    main()

