#!/bin/bash

tmux new-session -d

"authbind python2 server/server.py 80"

# tmux send-keys -t server.0 "echo 'Hello World'" ENTER
# tmux send-keys -t server.0 C-c