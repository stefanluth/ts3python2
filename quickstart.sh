#!/bin/bash

# Ensure git is installed
if ! command -v git &> /dev/null
then
    echo "git could not be found"
    exit
fi

# Ensure python3 is installed
if ! command -v python3 &> /dev/null
then
    echo "python3 could not be found"
    exit
fi

# Clone repository
git clone https://github.com/stefanluth/ts3python2
cd ts3python2

# Read required variables from user input
echo "Enter the IP of the TeamSpeak 3 server: "
read TS3_SERVER_IP

echo "Enter the port of the TeamSpeak 3 server: "
read TS3_SERVER_PORT

echo "Enter the telnet login of the TeamSpeak 3 server: "
read TS3_TELNET_LOGIN

echo "Enter the telnet password of the TeamSpeak 3 server: "
read TS3_TELNET_PASSWORD

echo "Enter the telnet port of the TeamSpeak 3 server: "
read TS3_TELNET_PORT

# Create the .env file
echo "TS3_SERVER_IP=$TS3_SERVER_IP" > .env
echo "TS3_SERVER_PORT=$TS3_SERVER_PORT" >> .env
echo "TS3_TELNET_LOGIN=$TS3_TELNET_LOGIN" >> .env
echo "TS3_TELNET_PASSWORD=$TS3_TELNET_PASSWORD" >> .env
echo "TS3_TELNET_PORT=$TS3_TELNET_PORT" >> .env

# Install dependencies
python3 -m venv .venv
source ./.venv/bin/activate
python3 -m pip install -r requirements.txt

# Run the script
python3 main.py
