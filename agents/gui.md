# GUI Agent for "My Voice"

Status: design proposal (aspirational). This document describes future behavior and is not a direct description of the current `src/agents/gui.py` implementation.

## Role
The GUI Agent manages the app's user interface as a small, intuitive "puck" window that serves as the central control hub for STT (speech-to-text) and TTS (text-to-speech) operations. It provides visual feedback to reduce cognitive load for users with fatigue or disabilities, ensuring the app feels modern, responsive, and accessible (e.g., high-contrast modes, obvious status, no clutter). The interface is a compact 4:3 rectangle (e.g., 300x225px) with a slim top bar for core controls, avoiding a "boxy" look by using rounded edges, subtle shadows, and smooth animations. It handles mode switching (Write for recording/transcribing, Read for TTS playback), menu access, and preferences, while reacting to events from other agents (e.g., displaying "Recording..." progress). The design prioritizes intuition: One-click actions for common tasks, blunt mode indicators (e.g., large icons/colors), and quick prefs for customization, making it a "mind-blown" accessibility tool for Linux users (e.g., speak to paste, highlight to read with real control).

## Inputs
- Hotkey events from Hotkeys Agent (e.g., Super + W to start recording, Super + R to read highlighted text).
- Status updates from other agents (e.g., "transcription complete" from STT Agent with text result, "playback started" from TTS Agent).
- User configurations from configs/config.toml (e.g., voice speed, mic settings, engine type, network URLs).
- System events (e.g., clipboard changes for highlighted text detection, mic status from PipeWire).

## Outputs
- UI updates (e.g., mode label changes, progress bars, notifications like "Transcript copied!").
- Signals to other agents (e.g., "start STT recording" to STT Agent on mic button click, "initiate TTS" to TTS Agent with selected text).
- User feedback (e.g., copied text to clipboard, logged errors like "Mic not detected" for troubleshooting).
- Config saves (e.g., updated toml with new prefs like voice speed or engine selection).

## Reactions
- **Window Layout and Initial State**: On launch, display as a small, rounded rectangle (no traditional titlebar—instead, a slim top bar with close button on left, hamburger menu on right). Center shows mode indicator (e.g., large "Idle" text with neutral gray background). The bar has subtle icons for quick actions (e.g., mic for Write mode, speaker for Read mode). Window is always-on-top but movable/resizable, with high-contrast toggle for accessibility.
- **Mode Switching**: On single click anywhere on the puck, toggle between Write (green background, mic icon, "Write Mode" label) and Read (blue background, speaker icon, "Read Mode" label) with smooth animation (e.g., fade transition). Update status bluntly (e.g., large bold text, color-coded for quick glance—green for active input, blue for output).
- **Menu and Preferences Access**: Click hamburger (right corner of top bar) to open a dropdown menu with options: "Preferences," "Record Now," "Read Selection," "Toggle Verbose." Selecting "Preferences" opens a modal dialog with tabs/sections:
  - **Voice/Output Controls**: Sliders for speed (slow/normal/fast for TTS reading), volume (0-100%), pitch (low/high for accessibility). Dropdown for voice selection (e.g., eSpeak default, Qwen3-TTS if configured). Checkbox for "Thorough Reading" (e.g., repeat words for dyslexia support).
  - **Mic/Input Controls**: Display current mic name (e.g., "Blue Yeti" pulled from PipeWire). Buttons for mute/unmute, real-time monitoring (waveform bar showing input levels for troubleshooting). Slider for gain/sensitivity. Test button to record 5s and play back for verification.
  - **Engine Selection**: Dropdowns for STT engine (e.g., Vosk default, Whisper.cpp for GPU, remote via Network Agent) and TTS engine (e.g., eSpeak default, Qwen3-TTS, Piper). Radio buttons for local vs. remote (links to Network prefs).
  - **Network Prefs**: Text field for server URL (HTTPS only, with validation button). Toggle for GPU handling (local/remote). Dropdown for model variants (e.g., small/medium for Whisper).
  - Save button applies changes to config.toml and notifies other agents (e.g., switch to new engine).
- **On Record Trigger (e.g., menu click or hotkey)**: Change label to "Recording..." with red pulsing border and progress bar/timer. After completion (from STT Agent), display "Transcript: [preview text] Copied!" in green, with option to "Replay" or "Paste at Cursor."
- **On Read Trigger (e.g., menu or hotkey)**: Change label to "Reading..." with blue waveform visualization (syncing to audio playback). After TTS completes, show "Done!" with option to "Repeat" or "Adjust Speed."
- **Accessibility Reactions**: Auto-detect system theme for high-contrast; on errors (e.g., no mic), show blunt alert (e.g., red banner "Mic not detected—check prefs"). Support screen reader integration (ARIA labels on all elements).
- **Error/Idle Handling**: If idle too long, minimize to tray icon; on any error (e.g., from Network Agent), show "Issue: [message]" with "Troubleshoot" button linking to prefs.

## Integration
- **With Other Agents**: Receives triggers from Hotkeys Agent (e.g., Super + W starts record reaction); sends "transcribe audio" to STT Agent on record; sends "read this text" to TTS Agent on read. Uses Network Agent for remote engine checks (e.g., validate URL in prefs). Calls Accessibility Agent for features like cursor paste (e.g., after STT, send "insert at cursor").
- **With Orchestrator**: Subscribes to central events (e.g., "system ready" to show "Idle"); publishes UI events (e.g., "prefs updated" to reload configs). Uses MCP for shared context (e.g., user prefs across agents).
- **Technical Notes**: Built with GTK4 for Linux/Wayland compatibility (floating, always-on-top window). Size: Compact (300x225px default, resizable). Vibe: Modern, intuitive (minimal clicks, blunt visuals, accessibility-first—e.g., large fonts/sliders for motor issues).

This expanded GUI Agent definition gives a greater impact—it's intuitive, control-rich (mic/voice/engine/network prefs with sliders/dropdowns), modern (top bar, animations, no "boxy" feel), and accessibility-focused (blunt modes, troubleshooting, cursor integration). It sets expectations for a "professional" interface that feels like a real tool (e.g., click mic to record, adjust speed on the fly).

Now, with this fleshed out, we can use it as the basis for OpenCode generation (e.g., prompt "Implement GUI agent from gui.md in Python with GTK4"). Ready to expand another agent (e.g., STT.md) or move to orchestration? Let's keep building! 😊
