# TeamSpeak 3 Python Interface 2

## About

This is a straightforward Python interface that can be used to interact with the TeamSpeak 3 Server Query.

It is extensible, meaning it can be used to quickly create plugins that can be run on the TeamSpeak 3 server.

## Installation

Check out the [quickstart guide](./docs/quickstart_guide.md) for instructions.

## Documentation

The `docs` directory contains documentation for this project.
It explains how to use the interface and provides detailed information on writing plugins.

## Plugins & Commands

The `plugins` directory contains plugins and commands that are ready to be used.
Writing plugins and commands is easy, and you can find more information in the
[documentation](./docs/plugins/plugins.md).

Currently, the following plugins and commands are available:

### Plugins

- [AFK Mover](./docs/plugins/afk_mover.md) - Moves users to a specified channel when they are inactive for a given amount of time.
- [Doodler](./docs/plugins/doodler.md) - Replaces the server banner on given dates with custom images, similar to Google Doodles.
- [Welcomer](./docs/plugins/welcomer.md) - Sends a welcome message to users when they join the server.

### Commands

- [Help](./docs/commands/help.md) - Displays a list of available commands.
- [Weather](./docs/commands/weather.md) - Displays the current weather for a given location.

### Planned Plugins

- Casino - A plugin that allows users to gamble with virtual currency.
- Poll - A plugin that allows users to create polls and surveys.
- Auto-Channel - A plugin that automatically creates channels when needed.

## Contributing

If you want to contribute to this project, simply fork it and open a pull request.
I'll be happy to review your changes and merge them into the main branch.

## Questions

If you have any questions about how to use this interface, feel free to open an issue, and I'll be happy to assist you.

## Suggestions

And ~~if~~ **when** you find ways to improve the code, please open a PR and let me know
about it; I'm eager to learn, and I know that my code has plenty of room for improvement.

## Previous Version

There is a belief among some programmers that in order to produce great code,
it should be rewritten at least three times.

I also believe that in order to create ever better code,
it's necessary to go through a few rounds of rewriting and refinement.

I made my [previous version](https://github.com/stefanluth/ts3python) of a pythonic TS3
query interface quite some time ago, when I knew a lot less about programming.
My hope is to improve my code and my understanding of Python with this new version.
