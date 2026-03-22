# Accessibility Agent for "My Voice"

## Role
The Accessibility Agent acts as the app's dedicated "enhancement layer," adapting core functionalities (STT/TTS, UI, inputs) for users with disabilities, including fatigue, visual/motor impairments, hearing issues, dyslexia, or cognitive challenges. It ensures the app is inclusive and low-effort by wrapping outputs (e.g., auto-pasting transcribed text at the cursor to eliminate manual copying) and inputs (e.g., adding verbal feedback for screen reader compatibility). Prioritizing WCAG/ARIA standards, it provides features like high-contrast modes, slow playback, and adaptive behaviors to make "My Voice" a seamless tool (e.g., speak to type directly in any field, hear highlights with pauses for comprehension). The agent supports customization for personal needs, with fallbacks to maintain usability (e.g., if high-contrast fails, notify audibly), turning the app into a "mind-blown" accessibility win for Linux—empowering users to interact without barriers, from quick dictation for mobility-limited folks to thorough reading for learning disabilities.

## Inputs
- Outputs from other agents (e.g., transcribed text from STT Agent, synthesized audio from TTS Agent, status events like "mode changed" from GUI Agent).
- User configurations from configs/config.toml (e.g., "high-contrast: on", "slow-mode: true", "cursor-paste: enabled", ARIA verbosity level, preferred feedback type like "verbal cues").
- System status (e.g., active window/cursor position from orchestrator, accessibility settings from GNOME like screen reader active).
- Hotkey or voice triggers (e.g., from Hotkeys Agent for "toggle accessibility mode").
- Optional user data (e.g., custom profiles for specific disabilities, like "dyslexia: word-by-word reading").

## Outputs
- Adjusted actions (e.g., pasted text at cursor, modified TTS audio with slowed speed, UI theme changes like high-contrast).
- Enhanced feedback (e.g., ARIA labels added to GUI elements, verbal notifications like "Text pasted" via TTS Agent).
- Status reports (e.g., "Accessibility mode activated" sent to GUI for visual confirmation, or logs for review).
- Metrics for monitoring (e.g., adaptation success rate, like "Cursor paste completed in 0.5s", sent to orchestrator or logs).

## Reactions
- **On STT/TTS Output Reception**: When receiving transcribed text from STT (e.g., after recording), check config for "cursor-paste" and auto-insert at active cursor position (using xdotool for X11 or Wayland portals for secure, compatible pasting in any app like browsers or editors). For TTS outputs, apply slow mode (e.g., insert pauses between words/sentences for dyslexia support) or repeat sections on demand (e.g., if config sets "thorough-reading: true").
- **Theme and Mode Adjustments**: On toggle request (e.g., from GUI prefs or hotkey), switch to high-contrast mode (e.g., invert colors, enlarge fonts, add borders for visual impairments) and notify "High-contrast enabled." If screen reader is detected (e.g., Orca active), add ARIA labels dynamically to puck elements (e.g., "aria-label: Current mode Write" for voice announcement).
- **Adaptive Enhancements**: For fatigue users, shorten interactions (e.g., auto-confirm pastes with a quick beep instead of pop-ups). For hearing issues, boost volume or add visual subtitles in GUI during TTS playback. On errors from other agents (e.g., "low quality transcript" from STT), react with alternatives (e.g., "Repeat input?" prompt via TTS or GUI alert).
- **Fallback and Error Reactions**: If a feature fails (e.g., cursor paste blocked by Wayland security), fallback to clipboard copy and notify "Pasted to clipboard—manual paste needed" audibly/visually. Log accessibility events (e.g., "High-contrast toggled at 14:32") for user review, with verbose mode for detailed audits.
- **Accessibility-Specific Reactions**: Support "voice feedback" mode (e.g., on app start, TTS says "My Voice ready"); for cognitive aids, break long transcripts into chunks before pasting. Integrate with system tools (e.g., notify Orca of changes for seamless reading).

## Integration
- **With Other Agents**: Wraps STT outputs for post-processing (e.g., receive transcript, perform cursor paste, then notify GUI "Pasted!"); enhances TTS by adjusting speed/pitch before playback (e.g., slow mode applied to audio stream). Subscribes to GUI for prefs changes (e.g., "update high-contrast" triggers theme switch) and to Hotkeys for input adaptations (e.g., "voice-only mode" disables key listening).
- **With Orchestrator**: Subscribes to global events (e.g., "STT complete" to trigger paste); publishes enhancements (e.g., "accessibility adjusted" event with details). Uses MCP for shared context (e.g., user disability profile across agents without repetition).
- **Technical Notes**: Uses xdotool/portals for cursor interactions (secure on Wayland), ARIA via GTK attributes for screen readers. Configurable for extensions like Braille output or integration with Linux accessibility daemons (e.g., AT-SPI for advanced feedback). Runs lightweight/async to not impact performance.

This expanded Accessibility Agent now provides a transformative layer for "My Voice," with features like cursor paste and slow modes that make it a true accessibility powerhouse (e.g., speak and have text appear at your cursor instantly). It's designed to "feel good" for users, reducing barriers and enhancing the app's impact.

Man, we're on fire—killing it with these expansions! Let's keep the streak going: Next up, expand the Orchestrator (to unify everything), or another agent like Hotkeys? Your call! 😊
