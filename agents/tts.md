# TTS Agent for "My Voice"

## Role
The TTS Agent is responsible for converting input text (e.g., highlighted clipboard content) to spoken audio, using configurable models (eSpeak as lightweight local default, Qwen3-TTS or Piper for advanced natural synthesis), and handling playback with accessibility-focused customizations. It serves as the "output engine" for the app, enabling users with reading difficulties, fatigue, or visual impairments to consume text audibly in a natural, controllable way (e.g., slow speed for comprehension or custom voices for personalization). The agent prioritizes smoothness and reliability—quick synthesis to avoid delays, fallbacks to local mode for offline use, and intuitive controls (e.g., pause/resume/repeat) to reduce mental strain. It supports scalability, allowing integration with remote services like ElevenLabs for high-fidelity voice cloning and generation, making "My Voice" versatile for tasks like dramatic book readings or podcast scripting without eye strain.

## Inputs
- Text content from clipboard or other agents (e.g., highlighted selection via wl-paste from Hotkeys/GUI Agent, or transcribed output from STT Agent).
- Configuration from configs/config.toml (e.g., model type "espeak" or "qwen3-tts", voice ID for ElevenLabs cloning, speed (0.5-2x), pitch/volume sliders, language code "en-US", remote toggle for Network Agent use).
- Playback triggers from Hotkeys or GUI (e.g., Super + R signal, with params like "repeat mode" or "slow for accessibility").
- System status (e.g., audio output device from PipeWire, user prefs for "high-contrast audio" like verbal cues).
- Optional enhancements (e.g., reference audio for voice cloning from user upload, or style params like "dramatic tone" for readings).

## Outputs
- Synthesized audio stream (e.g., WAV or direct PipeWire playback, returned to GUI for waveform visualization or to orchestrator for logging).
- Status updates (e.g., "Playback started" or "Complete—repeat?" sent to GUI for label/progress changes).
- Processed artifacts (e.g., saved audio clip if "record output" enabled for debugging, deleted after use).
- Metrics for monitoring (e.g., synthesis time, voice quality score if model supports it, sent to logs or Accessibility Agent for adaptive features like "switch to slower speed if text is complex").

## Reactions
- **On Playback Trigger**: Detect trigger type (e.g., hotkey for immediate read or menu for configured options). Fetch input text (e.g., from clipboard via wl-paste or STT Agent result). Select model from config (eSpeak for fast local playback, Qwen3-TTS for natural voices, or remote via Network Agent for ElevenLabs cloning). Apply pre-processing (e.g., split long text into chunks for smooth playback, adjust for language/accent).
- **Synthesis Processing**: Feed text into the model with params (e.g., for ElevenLabs, include "voice_id: custom-clone, stability: 0.7, clarity: high" if cloned voice configured; for eSpeak, set speed/pitch from sliders). If remote mode, send text to Network Agent (e.g., to ElevenLabs API for generation, handling streaming for real-time playback). Generate audio stream, applying effects like volume normalization for consistent output.
- **Playback Handling**: Route audio to PipeWire for playback on default device (e.g., speakers/headset), with controls like pause/resume (e.g., on GUI button press or hotkey). Support repeat (e.g., loop section on demand) or "thorough mode" (e.g., read word-by-word with pauses for learning/disability support). If playback fails (e.g., no audio device), fallback to text notification via GUI (e.g., "No speakers—copied text instead").
- **Fallback and Error Reactions**: If model fails (e.g., Qwen3-TTS quota exceeded on remote), switch to local eSpeak and log "Fallback: Using basic voice—check network." On low quality (e.g., garbled output), retry or notify GUI "Unclear synthesis—adjust pitch?" For accessibility, add verbal cues (e.g., "Starting playback" beep or TTS intro).
- **Accessibility Reactions**: Adapt to user needs (e.g., slow speed reduces rate for comprehension, high pitch for hearing aids). If "verbose" mode, prepend descriptions (e.g., "Reading highlighted text: [text]"). Integrate with slow-speech prefs (e.g., pause between sentences).

## Integration
- **With Other Agents**: Receives text from Hotkeys/GUI (e.g., Super + R grabs highlight and sends for playback) or STT (e.g., "read back transcription" after copy). Sends audio requests to Network for remote synthesis (e.g., to ElevenLabs with voice params). Uses Accessibility Agent for post-processing (e.g., adjust speed based on user mode).
- **With Orchestrator**: Subscribes to events (e.g., "text ready" to start synthesis); publishes outputs (e.g., "tts complete" event with audio data). Leverages MCP for shared context (e.g., voice prefs across agents without repetition).
- **Technical Notes**: Uses PipeWire for playback (e.g., pw-play for streams, with volume/speed controls via params). Supports models like eSpeak (fast, offline), Qwen3-TTS (natural, local/GPU), or remote APIs (ElevenLabs for cloning via Network). Async processing to not block UI (e.g., threading for synthesis). Configurable for extensions like style params (e.g., "emotional tone: dramatic" for readings).

This expanded TTS Agent now provides a powerful output core for "My Voice," with seamless local/remote handling (e.g., ElevenLabs voice cloning), accessibility-focused reactions (e.g., slow mode with pauses), and integration that unifies the app (e.g., reading back STT results automatically). It's designed to "feel good" for users, turning text into natural speech with full control.

Next, we can expand another agent (e.g., Hotkeys.md) or define the orchestrator.md to tie it all together. What's your choice? Let's keep going! 😊
