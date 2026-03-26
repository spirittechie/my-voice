#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

LOG_FILE="${MYVOICE_DIAG_LOG:-diagnose.log}"

log() {
    local msg="$1"
    echo "$msg" | tee -a "$LOG_FILE"
}

has_tool() {
    command -v "$1" >/dev/null 2>&1
}

section() {
    log ""
    log "=== $1 ==="
}

check_launcher() {
    section "launcher"
    if [[ -x "./bin/myvoice" ]]; then
        log "[PASS] launcher executable at ./bin/myvoice"
    else
        log "[FAIL] launcher missing or not executable: ./bin/myvoice"
        return 1
    fi

    if [[ -x "./bin/myvoice-stt.sh" ]]; then
        log "[PASS] one-shot STT helper executable at ./bin/myvoice-stt.sh"
    else
        log "[INFO] one-shot STT helper missing or not executable"
    fi

    if [[ -x "./bin/myvoice-tts.sh" ]]; then
        log "[PASS] one-shot TTS helper executable at ./bin/myvoice-tts.sh"
    else
        log "[INFO] one-shot TTS helper missing or not executable"
    fi
}

check_runtime_path() {
    section "runtime"
    if python3 - <<'PY'
from src.runtime.runtime import Runtime
rt = Runtime()
rt.state.transition("recording")
rt.state.transition("complete")
print("ok", rt.state.get(), len(rt.state.history))
PY
    then
        log "[PASS] runtime/state path imports and transitions"
    else
        log "[FAIL] runtime/state path import or transition failure"
        return 1
    fi
}

check_stt_path() {
    section "stt"
    local fail=0
    has_tool arecord || { log "[FAIL] missing arecord"; fail=1; }
    has_tool ffmpeg || { log "[FAIL] missing ffmpeg"; fail=1; }
    if [[ -d "assets/en-us-small" ]]; then
        log "[PASS] vosk model found at assets/en-us-small"
    else
        log "[FAIL] vosk model missing at assets/en-us-small"
        fail=1
    fi
    if python3 - <<'PY'
from src.runtime.runtime import Runtime
from src.agents.stt import create_stt
rt = Runtime()
engine = create_stt(rt)
print("ok", type(engine).__name__)
PY
    then
        log "[PASS] STT class loads with current model path"
    else
        log "[FAIL] STT class failed to initialize"
        fail=1
    fi
    return "$fail"
}

run_stt_live() {
    section "stt-live"
    if python3 - <<'PY'
from src.runtime.runtime import Runtime
from src.agents.stt import create_stt
rt = Runtime()
engine = create_stt(rt)
text = engine.transcribe()
print(text)
PY
    then
        log "[PASS] live STT invocation completed"
    else
        log "[FAIL] live STT invocation failed"
        return 1
    fi
}

attempt_paste_injector() {
    if has_tool wtype; then
        wtype -M ctrl -k v -m ctrl >/dev/null 2>&1 || true
        return 0
    fi
    if has_tool xdotool; then
        xdotool key --clearmodifiers ctrl+v >/dev/null 2>&1 || true
        return 0
    fi
    return 1
}

run_dictation_live() {
    section "dictation-live"
    local transcript
    transcript="$(python3 - <<'PY'
from src.runtime.runtime import Runtime
from src.agents.stt import create_stt
rt = Runtime()
engine = create_stt(rt)
text = engine.transcribe()
print(text)
PY
)"

    log "[INFO] transcript: ${transcript}"

    if [[ "$transcript" == capture\ failed:* ]]; then
        log "[FAIL] dictation capture/transcribe failed"
        return 1
    fi

    if has_tool wl-copy; then
        if printf "%s" "$transcript" | wl-copy; then
            log "[PASS] transcript copied to clipboard"
        else
            log "[FAIL] clipboard write failed"
            return 1
        fi
    else
        log "[FAIL] wl-copy unavailable; cannot restore clipboard step"
        return 1
    fi

    if [[ "${MYVOICE_AUTOPASTE:-1}" == "0" ]]; then
        log "[INFO] auto-paste skipped by MYVOICE_AUTOPASTE=0"
        return 0
    fi

    if attempt_paste_injector; then
        log "[PASS] paste key-injection attempted"
    else
        log "[INFO] no paste injector available (wtype/xdotool); clipboard step still complete"
    fi
}

check_tts_path() {
    section "tts"
    if has_tool espeak-ng; then
        log "[PASS] espeak-ng available"
    elif has_tool espeak; then
        log "[PASS] espeak available"
    else
        log "[FAIL] no TTS CLI found (espeak-ng/espeak)"
        return 1
    fi

    if python3 - <<'PY'
from src.runtime.runtime import Runtime
from src.agents.tts import TTS
rt = Runtime()
tts = TTS(rt)
print(tts.speak("diag tts path"))
PY
    then
        log "[PASS] TTS runtime path callable"
    else
        log "[FAIL] TTS runtime path failed"
        return 1
    fi
}

run_tts_live() {
    section "tts-live"
    if has_tool espeak-ng; then
        espeak-ng -s 160 -v en "my voice diagnostic" >/dev/null 2>&1
    elif has_tool espeak; then
        espeak -s 160 -v en "my voice diagnostic" >/dev/null 2>&1
    else
        log "[FAIL] no TTS CLI available for live test"
        return 1
    fi
    log "[PASS] live TTS command executed"
}

check_hotkeys() {
    section "hotkeys"
    if python3 - <<'PY'
from src.agents.hotkeys import HotkeyListener
listener = HotkeyListener(lambda key: None)
status = listener.status()
print(status)
PY
    then
        log "[INFO] hotkey listener status printed above"
        log "[INFO] hotkeys are stubbed boundary only (no global capture backend yet)"
    else
        log "[FAIL] hotkey module import/status failed"
        return 1
    fi
}

run_launcher() {
    section "launch"
    local duration="${1:-12}"
    if timeout "${duration}s" ./bin/myvoice >/tmp/myvoice_launch.log 2>&1; then
        log "[PASS] launcher exited cleanly within ${duration}s"
    else
        local code=$?
        if [[ "$code" -eq 124 ]]; then
            log "[PASS] launcher stayed running for ${duration}s (timeout ended test window)"
        else
            log "[FAIL] launcher exited with code ${code}"
            log "[INFO] see /tmp/myvoice_launch.log"
            return 1
        fi
    fi
}

full_diag() {
    : > "$LOG_FILE"
    log "my-voice diagnostic start $(date)"
    check_launcher
    check_runtime_path
    check_stt_path
    check_tts_path
    check_hotkeys
    log ""
    log "Run live checks when ready:"
    log "  ./bin/diagnose.sh launch"
    log "  ./bin/diagnose.sh stt-live"
    log "  ./bin/diagnose.sh dictate-live"
    log "  ./bin/diagnose.sh tts-live"
    log "my-voice diagnostic end $(date)"
}

usage() {
    cat <<'EOF'
Usage: ./bin/diagnose.sh <command>

Commands:
  full            Run non-destructive operational checks (default)
  launch          Launch app for a timed diagnosis window
  stt             Verify STT dependencies and runtime initialization
  stt-live        Execute live STT capture/transcribe path
  dictate-live    Execute trigger->capture->transcribe->clipboard/paste path
  tts             Verify TTS dependency and runtime path
  tts-live        Execute live TTS speech command
  hotkeys         Report hotkey implementation status
  runtime         Verify runtime/state integration path

Examples:
  ./bin/diagnose.sh full
  ./bin/diagnose.sh launch
  ./bin/diagnose.sh dictate-live
  ./bin/diagnose.sh stt-live
EOF
}

cmd="${1:-full}"
case "$cmd" in
full)
    full_diag
    ;;
launch)
    run_launcher "${2:-12}"
    ;;
stt)
    : > "$LOG_FILE"
    check_stt_path
    ;;
stt-live)
    : > "$LOG_FILE"
    run_stt_live
    ;;
dictate-live)
    : > "$LOG_FILE"
    run_dictation_live
    ;;
tts)
    : > "$LOG_FILE"
    check_tts_path
    ;;
tts-live)
    : > "$LOG_FILE"
    run_tts_live
    ;;
hotkeys)
    : > "$LOG_FILE"
    check_hotkeys
    ;;
runtime)
    : > "$LOG_FILE"
    check_runtime_path
    ;;
*)
    usage
    exit 1
    ;;
esac
