#!/bin/bash

# Usage: start.sh [CONDA_ENV] [API_PORT] [API_ROOT_PATH]

CONDA_ENV="${1:-"citwin-api"}"
API_PORT="${2:-"8000"}"
API_ROOT_PATH="${3:-"/"}"

# Activate Conda environment
source /opt/miniconda3/bin/activate "$CONDA_ENV"

# Change to app directory
cd "$(dirname "$0")" || exit

# Start Uvicorn server
python -m uvicorn api:app --host localhost --port "$API_PORT" --root-path "$API_ROOT_PATH" --workers 1
