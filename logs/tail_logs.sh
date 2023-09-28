#!/bin/bash


# Get the directory of the script
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Get the directory one level up
parent_dir="$(dirname "$script_dir")"

# Specify the file you want to parse
file_to_parse="${parent_dir}/IMCP_Banshee_NCSU.depl"
echo $file_to_parse

# Use grep to extract lines that are not commented out and contain IP addresses
ips=$(grep -E -o '^[[:space:]]*on \([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+\)' "$file_to_parse" | awk -F '[()]' '{print $2}')
echo $ips

# Build the xfce4-terminal command with tabs
xfce4_command="xfce4-terminal"

for ip in $ips; do
    xfce4_command+=" --tab --title=\"$ip\" --command=\"tail -f ${parent_path}/server_logs/${ip}_app.log\""
done

# Execute the xfce4-terminal command to open all tabs in a single terminal window
eval "$xfce4_command"
