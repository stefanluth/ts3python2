# Quickstart Guide

## Introduction

This guide will walk you through the process of setting up the TS3Client, connecting to your TeamSpeak 3 server and
activating the `AFK Mover` and `Welcomer` plugins.

## Prerequisites

Before you begin, you should have the following installed on your computer:

- Python 3.10 or higher
- Git

It should be noted that the TS3Client has only been tested on Linux. It may work on Windows and MacOS, but this is not
guaranteed. If you want to run the TS3Client on Windows, you should use the Windows Subsystem for Linux (WSL).

## Installation

### Quickstart Script

The quickest way to get started is to run the quickstart script. This script will clone the TS3Client repository,
ask for your server credentials and save them in a `.env` file and run the TS3Client with the `AFK Mover` and `Welcomer` plugins.

To run the quickstart script, open a terminal and run the following command:

```bash
bash <(curl -s https://raw.githubusercontent.com/stefanluth/ts3python2/main/quickstart.sh)
```

### Manual Installation

If you prefer to install the TS3Client manually, you can follow the steps below.

#### Clone the Repository

To clone the TS3Client repository, open a terminal and run the following command:

```bash
git clone https://github.com/stefanluth/ts3python2
```

#### Create a `.env` File

Create a `.env` file in the root directory of the TS3Client repository and add the following lines:

```bash
TS3_SERVER_IP="12.34.56.78"
TS3_SERVER_PORT=1337
TS3_TELNET_LOGIN="bot_login"
TS3_TELNET_PASSWORD="bot_password"
TS3_TELNET_PORT=1337
```

Replace the values with your server's IP address, port, telnet login, telnet password and telnet port.

You can generate a telnet login and password by following
[this official guide](https://www.teamspeak3.com/support/teamspeak-3-add-server-query-user.php).

The account on which you create the telnet login and password should have administrator privileges.

#### Install Dependencies

To install the dependencies, open a terminal and run the following command:

```bash
python3 -m venv .venv
source ./.venv/bin/activate
python3 -m pip install -r requirements.txt
```

#### Run the TS3Client

To run the TS3Client, open a terminal and run the following command:

```bash
python3 main.py
```

## Configuration

You can configure the TS3Client by editing the `config.py` file in the root directory of the TS3Client repository.
You can also check out the rest of the documentation in the `docs` directory.
