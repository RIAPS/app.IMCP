#!/bin/bash

input_file="/etc/riaps/riaps-hosts.conf"

# Initialize a variable to store the xfce4-terminal command
terminal_command="xfce4-terminal --hold "
terminal_command+="--tab --title \"host\" "
terminal_command+="--tab --title \"ctrl\" "

# Process each line in the input file
while IFS= read -r line; do
  # Check if the line starts with '#' (a comment)
  if [[ $line == \#* ]]; then
    continue  # Skip comments
  fi

  # Extract the 'nodes' values
  if [[ $line == *"nodes ="* ]]; then
    # Extract the nodes portion of the line
    nodes_line="${line#*=}"
    # Remove leading and trailing spaces, and remove double quotes
    nodes_line="${nodes_line//\"/}"
    nodes_line="${nodes_line// /}" # Remove spaces
    # Split the nodes values into an array
    IFS=',' read -r -a nodes_array <<< "$nodes_line"
    # Process each node and add a tab to the terminal command
    first_node=true
    for node in "${nodes_array[@]}"; do
      # Remove "riaps", "-", "[" and "]" from the node name for the tab title
      tab_title="${node/riaps/}"
      tab_title="${tab_title/.local/}"
      tab_title="${tab_title//-/}"
      tab_title="${tab_title/\[}"
      tab_title="${tab_title/\]/}"
      # Add a tab with the modified tab title and SSH command to the terminal command
      if $first_node; then
        # Remove the first '[' from the first node
        node="${node/\[}"
        first_node=false
      fi
      # Remove "]" from the end of the node
      node="${node%\]}"
      echo "$node"
      terminal_command+=" --tab --title \"$tab_title\" --command \"ssh $node\""
    done
  fi
done < "$input_file"

# Execute the terminal command in the background
eval "$terminal_command" &

# Return control to the terminal immediately
exit 0
