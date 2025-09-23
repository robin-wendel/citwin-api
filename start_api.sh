#!/bin/bash
# Activate Conda environment
source /opt/miniconda3/bin/activate citwin-api

# Change to app directory
cd /Users/robinwendel/Developer/mobility-lab/citwin-api || exit

# Start Uvicorn server
python -m uvicorn api:app --host localhost --port 8002 --workers 1
