#!/bin/bash
# HTML GIF renderer: self-healing launcher for capture.py.
#
# The GIF toolchain (playwright, pillow, imageio, numpy) lives in the shared
# ~/.venvs/hydr8-tools venv, NOT in Homebrew's system python (which has no deps
# and blocks pip installs under PEP 668). This wrapper repairs the common
# breakage automatically: missing venv or missing packages get reinstalled from
# requirements.txt before rendering.
#
# The one case it will NOT auto-fix: a dangling venv interpreter (Homebrew
# removed the python the venv was built on). The venv is shared with other
# tooling (openpyxl, pypdf), so deleting it here would break those too.
# That case prints the exact fix and exits.
#
# Usage: scripts/render.sh <template.html> <output.gif> [capture.py flags]
set -euo pipefail

VENV="$HOME/.venvs/hydr8-tools"
PY="$VENV/bin/python3"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REQS="$SCRIPT_DIR/../requirements.txt"

if [ ! -d "$VENV" ]; then
    echo "[render.sh] $VENV missing, creating it..." >&2
    "$(command -v python3)" -m venv "$VENV"
fi

if ! "$PY" --version >/dev/null 2>&1; then
    TARGET="$(readlink -f "$PY" 2>/dev/null || echo "unknown")"
    FORMULA="$(echo "$TARGET" | sed -n 's|.*/opt/\(python@[0-9.]*\)/.*|\1|p')"
    echo "[render.sh] The venv interpreter at $PY is dead (target: $TARGET)." >&2
    echo "[render.sh] Homebrew likely removed the python this venv was built on." >&2
    echo "[render.sh] Fix option 1 (restores every venv built on that python):" >&2
    echo "    brew install ${FORMULA:-python@3.14}" >&2
    echo "[render.sh] Fix option 2 (rebuild this venv on the current python3; also" >&2
    echo "  reinstall the other hydr8-tools packages so xlsx/pdf tooling survives):" >&2
    echo "    python3 -m venv --clear $VENV" >&2
    echo "    $VENV/bin/pip install -r $REQS openpyxl pypdf cryptography" >&2
    echo "    $PY -m playwright install chromium" >&2
    exit 1
fi

if ! "$PY" -c "import playwright, PIL, imageio, numpy" >/dev/null 2>&1; then
    echo "[render.sh] GIF deps missing in $VENV, installing from requirements.txt..." >&2
    "$VENV/bin/pip" install --quiet -r "$REQS"
    "$PY" -m playwright install chromium
fi

exec "$PY" "$SCRIPT_DIR/capture.py" "$@"
