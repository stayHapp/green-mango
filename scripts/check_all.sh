#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"

echo "知会项目检查"

if [ -x "$BACKEND_DIR/.venv/bin/python" ]; then
  PYTHON_BIN="$BACKEND_DIR/.venv/bin/python"
else
  PYTHON_BIN="python3"
fi

echo "运行后端测试..."
(
  cd "$BACKEND_DIR"
  "$PYTHON_BIN" -m pytest
)

echo "运行前端构建..."
(
  cd "$FRONTEND_DIR"
  npm run build
)

echo "检查完成"
