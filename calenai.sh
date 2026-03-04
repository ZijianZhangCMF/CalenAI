#!/bin/bash
# CalenAI - Apple Shortcuts wrapper
# Shortcuts 操作配置：Shell=bash，传入输入内容=作为参数

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON="$(command -v python3 || echo /usr/bin/python3)"
export SHORTCUT_MODE=1

"$PYTHON" "$SCRIPT_DIR/calenai.py" "$@"
