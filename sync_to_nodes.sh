#!/bin/bash

REMOTE_DIR="/home/riaps/projects/RIAPS"
APP_SUBDIR="app.IMCP"
REMOTE="$REMOTE_DIR/$APP_SUBDIR"
REMOTE_NODES=("riaps@192.168.10.111" "riaps@192.168.10.112" "riaps@192.168.10.113" "riaps@192.168.10.114" "riaps@192.168.10.115" "riaps@192.168.10.116")

for item in "${REMOTE_NODES[@]}"
do
  echo "Syncing to $item"
  rsync -avz --rsync-path="mkdir -p $REMOTE && rsync" "cfg_ncsu" "$item:$REMOTE"
  rsync -avz --rsync-path="mkdir -p $REMOTE/tests && rsync" "tests/test_ncsu_setup.py" "$item:$REMOTE/tests"
done


# while read -r REMOTE_NODE; do
#     rsync -avz --rsync-path="mkdir -p $REMOTE && rsync" "cfg_ncsu" "$REMOTE_NODE:$REMOTE"
#     rsync -avz --rsync-path="mkdir -p $REMOTE/tests && rsync" "tests/test_ncsu_setup.py" "$REMOTE_NODE:$REMOTE"

# done < "$REMOTE_NODES_FILE"

