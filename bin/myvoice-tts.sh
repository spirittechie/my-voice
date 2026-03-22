#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if command -v wl-paste >/dev/null 2>&1; then
    TEXT="$(wl-paste --primary 2>/dev/null || true)"
    if [[ -z "$TEXT" ]]; then
        TEXT="$(wl-paste 2>/dev/null || true)"
    fi
else
    TEXT=""
fi

if [[ -z "$TEXT" ]]; then
    echo "[myvoice-tts] no clipboard/selection text found"
    exit 1
fi

if command -v espeak-ng >/dev/null 2>&1; then
    exec espeak-ng -s 160 -v en "$TEXT"
elif command -v espeak >/dev/null 2>&1; then
    exec espeak -s 160 -v en "$TEXT"
else
    echo "[myvoice-tts] missing TTS engine: espeak-ng/espeak"
    exit 1
fi
