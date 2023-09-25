#!/bin/bash

# Specify the file you want to parse
file_to_parse="/home/riaps/my_riaps_apps/app.MgManage_refactor/appMgManage_banshee_ncsu.depl"

# Use grep to extract lines that are not commented out and contain IP addresses
ips=$(grep -E -o '^[[:space:]]*on \([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+\)' "$file_to_parse" | awk -F '[()]' '{print $2}')

# Build the xfce4-terminal command with tabs
xfce4_command="xfce4-terminal"

for ip in $ips; do
    xfce4_command+=" --tab --title=\"$ip\" --command=\"tail -f /home/riaps/my_riaps_apps/app.MgManage_refactor/server_logs/${ip}_app.log\""
done

# Execute the xfce4-terminal command to open all tabs in a single terminal window
eval "$xfce4_command"
