# STT Agent for "My Voice"

Status: design proposal (aspirational). This document describes intended future behavior and is not a direct description of the current `src/agents/stt.py` implementation.

## Role
The STT Agent is responsible for capturing user speech from the microphone, transcribing it using configurable models (Vosk as lightweight local default, whisper.cpp for advanced GPU/accuracy), and handling output delivery (e.g., auto-copy to clipboard or paste at cursor). It serves as the "input engine" for the app, enabling seamless dictation for accessibility users (e.g., those with fatigue, motor impairments, or dyslexia) by turning spoken words into editable text that can be inserted directly into any text field or document. The agent prioritizes reliability and intuition—short recording sessions to avoid overwhelm, noise suppression for clear results in real-world settings, and quick fallbacks (e.g., to local mode if remote fails) with minimal user intervention. It supports scalability, allowing switches to remote services via the Network Agent for higher accuracy (e.g., cloud STT), making "My Voice" a versatile tool for creative tasks like podcast scripting or dramatic readings without typing strain.

## Inputs
- Record triggers from Hotkeys Agent or GUI Agent (e.g., Super + W hold/release signal, or "start record" menu click, with params like duration in seconds or "continuous mode" flag).
- Audio stream from PipeWire (e.g., raw PCM from default mic like Blue Yeti, with metadata like sample rate 16000Hz for Vosk compatibility).
- Configuration from configs/config.toml (e.g., model type "vosk" or "whisper.cpp", language code "en-US", max duration 15s default, noise threshold for VAD—voice activity detection, remote toggle for Network Agent use).
- System status (e.g., mic availability from orchestrator, accessibility prefs like "auto-paste at cursor").
- Optional reference data (e.g., custom vocabulary list for improved accuracy in specialized contexts like medical terms).

## Outputs
- Transcribed text string (e.g., "This is a test sentence" sent to clipboard via wl-clipboard or xclip, and to GUI Agent for display/preview).
- Status updates (e.g., "Transcription complete" or "Error: Low audio quality—retry?" sent to GUI for visual feedback).
- Processed audio artifacts (e.g., temporary WAV file for debugging, deleted after use; or enhanced audio with noise reduction if configured).
- Metrics for monitoring (e.g., transcription confidence score from Vosk, duration processed, sent to logs or Accessibility Agent for adaptive features like "re-record if confidence < 80%").

## Reactions
- **On Record Trigger**: Detect trigger type (e.g., hold for push-to-talk or timed 15s default from config). Start capturing audio from PipeWire (e.g., using ffmpeg or sounddevice for raw PCM, with VAD to ignore silence and auto-stop after pause). Apply pre-processing (e.g., noise suppression threshold from config to filter background noise for clearer input in noisy environments). If config specifies remote mode, send audio stream to Network Agent for cloud transcription (e.g., to Google STT API); otherwise, use local model (Vosk default for fast CPU processing, whisper.cpp if GPU available).
- **Transcription Processing**: Feed captured audio into the selected model (e.g., Vosk KaldiRecognizer for offline, real-time results; whisper.cpp for higher accuracy with GPU acceleration). Handle edge cases like low volume (boost gain if under threshold) or accents (use language code from config for better recognition). If transcription fails (e.g., empty result), retry once or fallback to a "retry prompt" via GUI (e.g., "Speak louder?").
- **Output Handling**: On successful transcription, auto-copy text to clipboard (using wl-paste for Wayland or xclip for compatibility). If accessibility mode is enabled (from config), perform cursor paste (e.g., simulate Ctrl+V at active cursor position using xdotool or Wayland portals to insert directly into text fields like browsers or editors). Send preview to GUI (e.g., first 50 chars for status label) and full text to Accessibility Agent for further enhancements (e.g., formatting for dyslexia).
- **Fallback and Error Reactions**: If mic input fails (e.g., no device detected), log "Mic error—check PipeWire" and notify GUI with a blunt alert (e.g., red banner "No mic; using default?"). On network/remote failure (from Network Agent), fallback to local Vosk and log "Remote failed—using CPU mode". For poor quality (e.g., confidence < 70%), suggest "Re-record?" via GUI notification.
- **Accessibility Reactions**: Support features like extended recording (e.g., no time limit for users with speech impediments) or voice activity extension (continue recording during pauses). Integrate with slow-speech prefs (e.g., if config sets "slow-speech," lower sample rate for better recognition).

## Integration
- **With Other Agents**: Triggered by Hotkeys Agent (e.g., Super + W sends "start record" with duration) or GUI Agent (e.g., menu click). Sends raw audio to Network Agent for remote processing if configured (e.g., to cloud STT service). Outputs transcribed text to Accessibility Agent for enhancements (e.g., cursor paste) and to GUI Agent for display/status updates (e.g., "Copied: [preview]").
- **With Orchestrator**: Subscribes to global events (e.g., "app start" to check mic availability and warm up model); publishes outputs (e.g., "stt complete" event with text data). Uses MCP for shared context (e.g., user language prefs across agents without repetition).
- **Technical Notes**: Uses PipeWire for audio capture (e.g., pw-record for WAV, with configurable sample rate/bit depth). Supports models like Vosk (lightweight, offline) or whisper.cpp (GPU-accelerated, via Network for remote). Keeps processing async to not block the app (e.g., threading for transcription). Configurable for extensions like custom vocab (load from toml for domain-specific accuracy, e.g., medical terms).
