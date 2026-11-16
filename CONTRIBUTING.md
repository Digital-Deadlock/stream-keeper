# Contributing

Issues and pull requests are welcome, especially reports that clearly separate
keeper connection state, keeper media activity, and observed Frigate behavior.

Before opening a pull request:

1. Remove private camera names, hostnames, credentials, and source URLs from
   logs and fixtures.
2. Install `requirements-dev.txt` and run `pytest`.
3. Build the container if Docker is available.
4. Explain what was tested against mocks and what was tested against a live
   go2rtc/Frigate deployment.

Do not submit recorded media or unredacted go2rtc configuration.

