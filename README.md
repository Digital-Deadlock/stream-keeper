# Frigate Stream Keeper

Frigate Stream Keeper is an experimental, lightweight sidecar that maintains
real MSE consumers against the go2rtc instance bundled with Frigate. It is
intended to test a workaround for a go2rtc/Nest WebRTC receiver-selection bug
where a consumer can attach to an H.264 receiver that never receives packets.

This MVP is deliberately narrow. It opens configured MSE WebSockets, performs
the go2rtc MSE negotiation, drains and discards incoming fMP4 media, and
reconnects when a connection closes. It does not record, decode, transcode, or
inspect video.

> [!IMPORTANT]
> This is an experimental mitigation and diagnostic tool, not an upstream fix.
> A keeper receiving media does not prove that Frigate is receiving media.

## Related upstream work

- [go2rtc issue #2386](https://github.com/AlexxIT/go2rtc/issues/2386)
- [go2rtc issue #2389](https://github.com/AlexxIT/go2rtc/issues/2389)
- [go2rtc issue #2599](https://github.com/AlexxIT/go2rtc/issues/2599)
- [go2rtc PR #2480](https://github.com/AlexxIT/go2rtc/pull/2480)

## Quick start

The container needs network access to Frigate's go2rtc HTTP port, normally
`1984`. The included Compose example assumes both containers share an external
Docker network named `frigate`, and that the Frigate container is reachable by
the DNS name `frigate`.

```sh
cp .env.example .env
docker network inspect frigate
docker compose up -d
docker compose logs -f stream-keeper
```

Edit `MSE_URLS` in `.env` before startup. It is a JSON array, even for one
stream:

```env
MSE_URLS=["ws://frigate:1984/api/ws?src=camera_1"]
```

Multiple streams are independent keeper connections:

```env
MSE_URLS=["ws://frigate:1984/api/ws?src=camera_1","ws://frigate:1984/api/ws?src=camera_2"]
```

Stream identifiers come from the `src` query parameter. Full URLs are never
written to logs. Do not put camera credentials in keeper URLs.

If your Frigate deployment uses a different network name or container DNS
name, change `compose.yaml` and the URLs accordingly. `127.0.0.1` in an
independent sidecar refers to the sidecar itself, not Frigate.

## Configuration

| Variable | Required | Default | Description |
| --- | --- | --- | --- |
| `MSE_URLS` | yes | none | JSON array of `ws://` or `wss://` go2rtc MSE URLs |
| `MSE_CODECS` | no | common go2rtc browser codecs | Codecs offered in the MSE request |
| `RECONNECT_INITIAL_SECONDS` | no | `2` | Initial reconnect delay |
| `RECONNECT_MAX_SECONDS` | no | `60` | Maximum reconnect delay |
| `HANDSHAKE_TIMEOUT_SECONDS` | no | `10` | WebSocket and MSE acknowledgement timeout |
| `STATS_INTERVAL_SECONDS` | no | `30` | Media-counter log interval |
| `LOG_LEVEL` | no | `INFO` | Python log level |
| `LOG_FORMAT` | no | `json` | `json` or `text` |

Reconnect delays use bounded exponential backoff with jitter. Zero incoming
bytes are reported but do not cause a deliberate bootstrap consumer to close.

## Logging

Logs use stable event names and contain connection state, negotiation result,
media byte/message counters, disconnect errors, and reconnect timing.

```json
{"event":"negotiated","level":"INFO","stream":"camera_1","content_type":"video/mp4; codecs=..."}
{"event":"media_stats","level":"INFO","stream":"camera_1","bytes_received":1048576,"messages_received":120}
```

The `stream` value is the runtime `src` value. Avoid using sensitive or
person-identifying stream names if logs may be shared publicly.

## Proving the concept

1. Reproduce the Frigate video failure without manually opening another viewer.
2. Record the current Frigate and go2rtc logs.
3. Start Stream Keeper with only the affected stream configured.
4. Confirm the keeper logs `negotiated` and increasing `bytes_received`.
5. Verify independently whether Frigate begins receiving and processing video.
6. Stop and start only Stream Keeper and repeat the observation.

Keeper media activity and Frigate recovery are separate results. Please report
both when filing an issue.

## Development

```sh
python -m venv .venv
. .venv/bin/activate
pip install -r requirements-dev.txt
pytest
docker build -t frigate-stream-keeper:dev .
```

## Rollback

Stop and remove only the sidecar:

```sh
docker compose down
```

This does not edit Frigate configuration, stop Frigate, or remove the shared
external Docker network.

## Upstream fix migration

After Frigate bundles a go2rtc release with a verified receiver-selection fix,
stop Stream Keeper and validate the affected feeds without it. Remove the
sidecar from Compose only after that validation succeeds across restarts.

## Security

The sample container runs without Linux capabilities, with no new privileges,
as an unprivileged user, and with a read-only root filesystem. It exposes no
ports and does not mount the Docker socket. See [SECURITY.md](SECURITY.md) for
reporting instructions.

## License

[MIT](LICENSE)

