#!/bin/bash

# Exit on any error
set -e

# Get inputs
GITHUB_TOKEN="$1"
GEMINI_API_KEY="$2"

# Export for Python script
export GITHUB_TOKEN="$GITHUB_TOKEN"
export GEMINI_API_KEY="$GEMINI_API_KEY"

# Execute the Python script
python /action/analyze_pr.py
