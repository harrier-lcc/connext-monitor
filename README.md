# Connext Monitor

## Instruction
The configuration is done via `config.yaml`. Refer to the Configuration section of this document.

The system is packaged in docker compose environment.

To start the system, edit the configuration and use `docker compose up`.

As it is a python library packaged via `poetry`, you can also install the package via `pip install .` and run via `python -m connext_monitor`.

For support chains, the system currently only supports providers with `eth_subscribe` to `logs`, and with websocket connections. Most chain used by Connext can be added but an extensive test has not been done due to the scope.

Currently only Discord alerting is supported. You will have to go to [Discord Developers](https://discord.com/developers/applications) to setup the discord bot settings.

## Configuration
[config.toml](config.toml) is well documented for each configuration. Please refer to the file comments.

## Development
For development, this project uses [Poetry](https://python-poetry.org/) to manage the packaging and dependency. Refer to the documentation for dependency management, virtual environment and more.

Run `pytest` for running the unit tests.
