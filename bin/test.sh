#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

cmd="${1:-full}"

case "$cmd" in
full)
    exec ./bin/diagnose.sh full
    ;;
dictate)
    exec ./bin/diagnose.sh dictate-live
    ;;
stt)
    exec ./bin/diagnose.sh stt-live
    ;;
tts)
    exec ./bin/diagnose.sh tts-live
    ;;
launch)
    exec ./bin/diagnose.sh launch "${2:-12}"
    ;;
*)
    echo "Usage: ./bin/test.sh [full|dictate|stt|tts|launch <seconds>]"
    exit 1
    ;;
esac
