#/usr/bin/env bash

tmux has-session -t packagecontrol
if [[ $? != 0 ]]; then
    tmux new-session -s packagecontrol -d

    tmux split-window -h -t packagecontrol
    tmux split-window -v -t packagecontrol
    tmux split-window -h -t packagecontrol

    tmux set -g mouse on
    tmux select-layout -t packagecontrol tiled

    sleep 0.6
    tmux send-keys -t packagecontrol:0.0 'psql -U postgres package_control' C-m
    tmux send-keys -t packagecontrol:0.1 '. venv/bin/activate' C-m
    tmux send-keys -t packagecontrol:0.2 '. venv/bin/activate' C-m
    tmux send-keys -t packagecontrol:0.3 '. venv/bin/activate' C-m
    
    sleep 0.4
    tmux send-keys -t packagecontrol:0.1 './dev.py' C-m
    tmux send-keys -t packagecontrol:0.2 './compile.py' C-m
    tmux send-keys -t packagecontrol:0.3 'git status' C-m

fi
tmux attach -t packagecontrol
