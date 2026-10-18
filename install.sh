#!/bin/sh
set -eu
cd "$(dirname "$0")"
PYTHON_BIN="${SONAR_PYTHON:-python3.13}"
"$PYTHON_BIN" -m venv .venv
.venv/bin/python -m pip install -r scientific_reference/environment/requirements.lock.txt
.venv/bin/python -m pip install --no-deps --no-build-isolation .
.venv/bin/python -m sonar_app verify
echo '安装完成。运行 ./start.command，或 .venv/bin/sonar serve --open'
