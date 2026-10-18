#!/bin/zsh
set -eu
cd "${0:A:h}"
if [[ ! -x .venv/bin/python ]]; then
  echo '请先在 program 目录运行：bash install.sh'
  read '?按回车结束…'
  exit 1
fi
exec .venv/bin/python launch.py
