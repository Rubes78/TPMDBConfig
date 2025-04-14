#!/bin/bash

args=()
while [[ $# -gt 0 ]]; do
  key="$1"
  if [[ "$key" == "-daterange" && "$2" =~ ^[0-9]{1,2}-[0-9]{1,2}-[0-9]{2,4}$ && ("$3" == "to" || "$3" == "--") && "$4" =~ ^[0-9]{1,2}-[0-9]{1,2}-[0-9]{2,4}$ ]]; then
    # Combine the 3 parts into one value
    args+=("-daterange" "$2 $3 $4")
    shift 4
  else
    args+=("$1")
    shift
  fi
done

# Run the import with corrected args
python3 import.py "${args[@]}"
