#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

usage() {
    cat <<'EOF'
Usage: ./bin/build.sh [deps|check|run|smoke]

deps   Install/update Python dependencies from requirements.txt
check  Verify developer runtime dependencies and app entrypoints
run    Launch the real app via ./bin/myvoice
smoke  Run operational diagnostics via ./bin/diagnose.sh full

Notes:
- This is a developer build/run helper, not a binary packager.
- It reports the current toolchain state for STT/TTS/launcher work.
EOF
}

install_deps() {
    echo "[build] installing python dependencies"
    python3 -m pip install --user -r requirements.txt
}

check_tool() {
    local name="$1"
    if command -v "$name" >/dev/null 2>&1; then
        echo "[ok] tool found: $name"
    else
        echo "[missing] tool not found: $name"
    fi
}

check_runtime() {
    echo "[build] checking operational dependencies"
    check_tool python3
    check_tool arecord
    check_tool ffmpeg
    check_tool wl-copy
    check_tool wl-paste
    check_tool espeak-ng
    if ! command -v espeak >/dev/null 2>&1 && ! command -v espeak-ng >/dev/null 2>&1; then
        echo "[missing] no espeak/espeak-ng found"
    fi

    if [[ -x "./bin/myvoice" ]]; then
        echo "[ok] launcher ready: ./bin/myvoice"
    else
        echo "[missing] launcher not executable: ./bin/myvoice"
    fi

    if [[ -d "assets/en-us-small" ]]; then
        echo "[ok] vosk model directory present: assets/en-us-small"
    else
        echo "[missing] vosk model directory missing: assets/en-us-small"
    fi
}

cmd="${1:-check}"

case "$cmd" in
deps)
    install_deps
    ;;
check)
    check_runtime
    ;;
run)
    exec ./bin/myvoice
    ;;
smoke)
    exec ./bin/diagnose.sh full
    ;;
*)
    usage
    exit 1
    ;;
esac
