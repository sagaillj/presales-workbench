#!/bin/sh
cd -- "$(dirname -- "$0")" || exit 1
if command -v python3 >/dev/null 2>&1; then exec python3 workbench.py serve --open; fi
echo "Python 3.10+ is needed. Open this folder in your assistant and ask it to run the starter kit."
read -r answer
