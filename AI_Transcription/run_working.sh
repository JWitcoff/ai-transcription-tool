#!/bin/bash
# Run the working CLI with the correct virtual environment

cd "$(dirname "$0")"

# Activate virtual environment
source venv/bin/activate

# Run the working CLI
python working_cli.py

# Deactivate when done
deactivate