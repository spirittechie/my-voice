# Hotkeys Agent for "My Voice"

Status: design proposal (aspirational). This document describes intended future behavior and is not a direct description of the current `src/agents/hotkeys.py` implementation.

## Role
The Hotkeys Agent serves as the central input listener and dispatcher for the app, capturing global hotkeys, keyboard events, and wake-words to trigger actions like starting STT recording or TTS playback. It acts as the "command hub," enabling hands-free and low-effort interaction for accessibility users (e.g., those with motor impairments, fatigue, or speech preferences) by supporting both physical keys (e.g., Super + W) and voice commands (e.g., "My Voice, read this"). The agent prioritizes reliability and intuition—short-hold detection to minimize physical strain, customizable bindings for personal needs, and graceful error handling (e.g., if permissions fail, fallback to GUI prompts). It supports scalability, allowing extension to advanced inputs like gesture detection or custom wake-phrases, making "My Voice" a versatile tool for tasks like quick dictation or reading without constant mouse/keyboard use.

## Inputs
- System events from evdev (e.g., key presses like Super + W hold/release, with configurable bindings from config.toml).
- Audio stream from PipeWire for wake-word detection (e.g., using Vosk to listen for phrases like "My Voice, start recording" in the background).
- Configuration from configs/config.toml (e.g., hotkey mappings like "stt: Super + W", wake-phrase list, hold duration threshold in ms for push-to-talk, sensitivity for voice detection).
- Status from orchestrator or other agents (e.g., "app busy" to queue events, user prefs for "voice-only mode").
- Optional extensions (e.g., gesture inputs from external devices if configured for advanced accessibility).

## Outputs
- Dispatched triggers to other agents (e.g., "start STT record" signal to STT Agent with duration param, "initiate TTS" to TTS Agent with highlighted text).
- Status notifications (e.g., "Hotkey detected—recording started" sent to GUI for visual confirmation, or "Wake-word heard" log).
- Error reports (e.g., "Permission denied for evdev—fallback to manual mode" sent to GUI or logs).
- Metrics for monitoring (e.g., event latency, false positive rate for wake-words, sent to orchestrator for adaptive tuning like "increase sensitivity if missed commands").

## Reactions
- **On Hotkey Detection**: Monitor for global keys (e.g., Super + W hold starts a timer; on hold > threshold like 200ms, send "start recording" to STT Agent with "push-to-talk" mode; on release, send "end recording" for transcription). For instant keys (e.g., Super + R tap), immediately grab highlighted text (via clipboard or system selection) and dispatch to TTS Agent. Customize per config (e.g., remap to Alt + V for users with limited mobility).
- **On Wake-Word Detection**: Continuously listen in background (low-CPU Vosk mode) for phrases like "My Voice, read this" or "My Voice, dictate"—parse the command (e.g., "read this" triggers TTS on current highlight; "dictate" starts STT recording). Use VAD (voice activity detection) to activate only on sound, reducing false positives and power use. If ambiguous (e.g., partial match), prompt via GUI ("Did you say 'read'?").
- **Event Dispatching and Queuing**: On detection, route to appropriate agent (e.g., hotkey to STT/TTS, wake-word to parser then dispatch). If app is busy (e.g., ongoing record), queue the event (e.g., buffer up to 3 pending) and notify GUI ("Queued: Read after current task"). Support combos (e.g., Super + Shift + W for extended record).
- **Fallback and Error Reactions**: If evdev permission fails (e.g., no access to /dev/input), fallback to polling or notify GUI "Grant input permissions in settings—using manual mode." On wake-word false positive (e.g., background noise), ignore with threshold filtering. Log all events (e.g., "Hotkey Super + W at 14:32:15, dispatched to STT") for debugging, with verbose mode for details.
- **Accessibility Reactions**: Support voice-only mode (disable key listening, rely on wake-words for hands-free use). Add tolerance for slow presses (e.g., extended hold detection for users with tremors). If no input detected (e.g., silent mic), send gentle GUI alert ("No voice heard—try again?").

## Integration
- **With Other Agents**: Dispatches to STT for recording triggers (e.g., Super + W sends audio capture request); to TTS for read commands (e.g., Super + R sends highlighted text). Receives status from agents (e.g., "STT complete" from STT to confirm dispatch success) and notifies GUI for visual cues (e.g., "Hotkey activated" icon flash).
- **With Orchestrator**: Subscribes to startup/shutdown events (e.g., "app ready" to start listening); publishes all inputs as events (e.g., "hotkey event: Super + W" with timestamp). Uses MCP for shared context (e.g., current user bindings across agents).
- **Technical Notes**: Uses evdev for key listening (with permission handling via udev rules if needed) and Vosk for wake-word detection (low-resource, offline). Configurable for custom phrases/bindings. Runs async in background to not block the app, with low CPU usage (e.g., sample audio at 8kHz for efficiency). Supports extensions like gesture inputs (e.g., via webcam for no-touch accessibility).

This expanded Hotkeys Agent now provides a reliable, intuitive input core for "My Voice," with hands-free wake-words, customizable reactions, and tight integration that unifies the app (e.g., dispatching to STT/TTS without manual steps). It's designed to "feel good" for accessibility, reducing physical effort (e.g., voice commands for mobility issues).

Next, we can expand another agent (e.g., Accessibility.md to tie in cursor paste) or move to the orchestrator.md for full unification. What's your preference? Let's keep the momentum! 😊
