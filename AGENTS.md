# Contributor guidance for coding agents

This repository contains an intentionally small diagnostic sidecar. Automated
coding agents and human contributors should preserve these boundaries:

- Never add camera names, internal hostnames, credentials, source URLs from
  private deployments, or captured media to the repository or test fixtures.
- Keep the sidecar independent of Frigate. Do not require the Docker socket,
  privileged mode, Frigate configuration changes, or camera-provider tokens.
- A WebSocket connection alone is not an MSE consumer. Send the go2rtc MSE
  request, validate its acknowledgement, and drain binary media messages.
- Do not claim that keeper media activity proves Frigate recovery. Those are
  separate observations.
- Prefer small, testable changes and retain clean SIGTERM/SIGINT behavior,
  bounded retries, URL-redacted logs, and non-root container operation.
- Add or update tests for protocol, configuration, reconnect, and lifecycle
  changes. Run `pytest` before submitting a pull request.
- Keep documentation and examples generic and safe to publish.

The current MVP supports MSE only. RTSP consumers, go2rtc API diagnostics, and
active remediation are future scope and should be proposed before being added.

