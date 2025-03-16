#!/bin/sh

# OPTIONS
REMOTE_HOST="pi5one" # tailscale hostname
REMOTE_USER="pi5one"
REMOTE_PORT=22

echo "Copying files from local machine to $REMOTE_HOST .........."

# Local path to upload the files from
LOCAL_PATH="."

# Remote path to copy the files to
REMOTE_PATH="/home/pi5one/apps/orbitos-demo/"

# rsync command with -e option for specifying port
rsync -rlD -v --delete-after -e "ssh -p $REMOTE_PORT" $LOCAL_PATH $REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH

# Restart the Docker container
ssh -p $REMOTE_PORT $REMOTE_USER@$REMOTE_HOST "cd $REMOTE_PATH && docker compose down && docker compose up --build"

echo "Done"
