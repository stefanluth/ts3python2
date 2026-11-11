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
TS3_SERVER_PORT=9987
TS3_QUERY_LOGIN="bot_login"
TS3_QUERY_PASSWORD="bot_password"
TS3_QUERY_PORT=10022
TS3_SSH_KNOWN_HOSTS="/path/to/known_hosts"
TS3_SSH_ACCEPT_ALL_KEYS=false
TS3_SSH_USE_SYSTEM_KEYS=true
```

Replace the values with your server's IP address, voice port, SSH query login and password, and SSH query port.
`TS3_SERVER_PORT` is the TeamSpeak 3 voice port (default `9987`), while `TS3_QUERY_PORT` is the SSH ServerQuery
port (default `10022`). The ServerQuery credentials authenticate during the SSH connection; there is no separate
login step.

You can create a ServerQuery login and password by following
[this official guide](https://www.teamspeak3.com/support/teamspeak-3-add-server-query-user.php).
The account on which you create the login and password should have administrator privileges.

The TS3Client only supports SSH ServerQuery. Enable it on the TeamSpeak 3 server by setting
`query_protocols=ssh` in the server's `ts3server.ini`, or by starting the server with the
`TS3SERVER_QUERY_PROTOCOLS=ssh` environment variable. The SSH query port can be configured with
`query_ssh_port=10022` in `ts3server.ini` or `TS3SERVER_QUERY_SSH_PORT=10022` in the environment. Make sure the
SSH query port is reachable and, when running in Docker, publish it with `-p 10022:10022`.

#### Pin the SSH Host Key

The client verifies the server's SSH host key. Collect it once with:

```bash
ssh-keyscan -p 10022 12.34.56.78 > known_hosts
```

Then set `TS3_SSH_KNOWN_HOSTS` to the path of that file. The client also loads the system known hosts file by
default; set `TS3_SSH_USE_SYSTEM_KEYS=false` to disable that. `TS3_SSH_ACCEPT_ALL_KEYS=true` disables host key
verification and is intended for first-run testing only, never for production deployments.

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
