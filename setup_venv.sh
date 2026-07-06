#!/usr/bin/env bash
set -euo pipefail

# Create a local virtual environment and install pinned dependencies.
python3 -m venv .venv

# shellcheck disable=SC1091
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -r requirements-dev.lock
python -m pip install -e .

echo "Virtual environment ready. Activate with: source .venv/bin/activate"
