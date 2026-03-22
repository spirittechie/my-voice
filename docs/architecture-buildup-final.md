# Architecture Build-Up Final for "My Voice": Bridging Spec to Production-Grade Execution

## Current Architecture Summary
The "My Voice" repository is at a critical "systems engineering" transition—strong on architectural specs (detailed MD files for agents and processes) but light on operational implementation, as the input highlights. This is a positive stage, where clarity exists before code complexity sets in, allowing for deliberate buildup. Key elements:
- **Repository State**: Spec-heavy with /agents MDs (gui.md, network.md, stt.md, tts.md, hotkeys.md, accessibility.md, clipboard-gateway.md), orchestrator.md for coordination, iteration-deployment.md for processes, and blueprint.md for overview. Implementation-light: No runtime in /src (e.g., no event loop code), no executable tests in /tests (plans only), configs has config.example.toml without validation. bin/launch.sh delegates to OpenCode, keeping it conceptual.
- **Agent Existence vs. Implementation Status** (Updated from Input):
  - GUI: Spec exists (puck with modes/prefs); no code (GTK4 reactions theoretical).
  - Network: Spec exists (HTTPS/remotes); no code (validation as plans).
  - STT: Spec exists (capture/transcription); no code (Vosk flows unbuilt).
  - TTS: Spec exists (synthesis/playback); no code (eSpeak controls absent).
  - Hotkeys: Spec exists (evdev/wake-words); no code (listener as stubs).
  - Accessibility: Spec exists (paste/modes/ARIA); no code (features conceptual).
  - Orchestrator: Spec exists (event routing); no code (message bus as text).
  - Clipboard Gateway: Spec exists (transaction safety); no code (snapshots planned).
- **Communication Flow (as Documented, Not Implemented)** (Synced with Input):
  - Core Write Path: hotkeys.start_stt → stt.recording_started → stt.transcript_ready → clipboard_gateway.snapshot_taken → accessibility.paste_completed → gui.
  - Core Read Path: hotkeys.start_tts → tts.playback_started → tts.playback_completed → gui/accessibility (with clipboard_gateway for selection semantics).
  - Remote Degradation Path: network failure → orchestrator reroute to local (with clipboard_gateway preserving state).
  - Shared State: MCP-like in orchestrator.md (user_prefs, etc.), but no registry code.
- **Overall Assessment**: Agentically coherent and "systems engineering"-ready, but the input's insight is spot-on: Spec-heavy leads to potential fragmentation without a runtime spine—focus now on execution to anchor the vision.

## Identified Weaknesses (Expanded with Agent Ties)
Expanding on the input's analysis, here's a deeper dive with specific agent connections and accessibility impact.
- **No Concrete Runtime/Execution Substrate**: Orchestrator overloads without a "voice runtime kernel" for loop/state. Tie-in: STT/TTS could crash without shared lifecycle; impact: Unreliable for chronic use (e.g., app hangs mid-read for fatigue users).
- **No Executable Tests/Harness**: Text plans only—no gating for accessibility (e.g., test clipboard races in Accessibility). Tie-in: Hotkeys/STT flows untested for evdev; impact: Frustrates users if wake-words fail inconsistently.
- **Config Contract Mismatch**: config.toml referenced but example-only, no validation. Tie-in: Network URLs could break, TTS params misconfigure; impact: Accessibility modes (e.g., slow TTS) don't apply, defeating usability.
- **No Formal Event Schema**: Names listed but no payloads/semantics/versioning. Tie-in: Orchestrator can't enforce (e.g., STT "transcript_ready" missing intent for Accessibility paste); impact: Silent breakages in write/read paths for cognitive users.
- **Clipboard Layer Not Fully Wired/Semantics Weak**: gateway.md exists, but no transaction model/ownership. Tie-in: STT outputs risk races (e.g., user copies mid-paste); impact: Motor users lose data, eroding trust.
- **Responsibility Overlap Risk**: E.g., STT owns transcription but Accessibility owns paste, Clipboard Gateway owns safety—fuzzy. Tie-in: Network fallbacks might not notify TTS; impact: Inconsistent experiences for fatigue users.
- **Concurrency/Race Risks**: No handling for simultaneous events (e.g., hotkey during STT). Tie-in: GUI updates lag; impact: Overwhelms attention-difficulty users.
- **Wayland/X11 Compatibility Risk**: Assumed but no probing. Tie-in: Accessibility cursor paste fails on Wayland; impact: Excludes modern desktops.
- **Fallback Behavior Under-Specified**: Conceptual, not mechanical. Tie-in: TTS doesn't adapt on STT fallback; impact: Offline users get stuck.
- **Error Handling/Recovery**: No supervisor. Tie-in: One agent crash (e.g., Network timeout) stops app; impact: Trust lost for daily needs.

## Reliability Risk Assessment (Expanded with Agent Ties)
- **Audio Capture Pipeline**: High risk—no dedicated manager for buffering/noise. Assessment: STT failures in noise; impact: Speech-impaired users get poor transcripts.
- **Clipboard Handling**: High risk—weak semantics lead to races/loss. Assessment: STT paste overwrites; impact: Cognitive users confused by lost data.
- **Wayland/X11 Compatibility**: High risk—no unified bridge. Assessment: Accessibility injection fails; impact: Mobility users can't rely on paste.
- **Async Task Handling**: Medium-high risk—no deadlines/dedupe. Assessment: Long TTS hangs GUI; impact: Fatigue users abandon.
- **Engine Fallback Behavior**: Medium risk—not enforced. Assessment: Network to local leaves TTS inconsistent; impact: Offline accessibility degraded.
- **Error Handling/Recovery**: Medium-high risk—no primitives. Assessment: Crash in one agent stops all; impact: Trust lost for chronic users.

## Proposed Architectural Improvements (Built-Up with Actionable Suggestions)
These build on the input, unifying the system with new elements (e.g., runtime spine as layer), tied to agents for coherence. Each is actionable (e.g., new MD files, updates).

- **Implement a Minimal Runtime Skeleton (Runtime Spine)**: Add runtime.md defining a "voice operating kernel" with event loop (async), message bus (pub/sub with priorities), shared state registry (MCP for prefs), and plugin loading. Tie-in: Orchestrator runs on top; STT/TTS plug in for lifecycle. Suggestion: Create agents/runtime.md and implement as src/runtime.py (asyncio base)—start with stubs logging "Event received."
- **Formalize Clipboard as Controlled Gateway**: Expand gateway.md with transaction model (snapshot, resolve conflicts, tag with semantics like "intent: dictation"). Tie-in: STT emits to Gateway, which checks with Accessibility before paste. Suggestion: Add clipboard-gateway-spec.md with schema (JSON payloads) and integrate as Orchestrator service—test with mocks for races.
- **Introduce Dedicated Audio Pipeline Manager**: Add audio-pipeline.md for managing streams (buffering, noise suppression with RNNoise, device switching). Tie-in: STT inputs route through here; TTS outputs for normalization. Suggestion: Build as agents/audio-pipeline.md, implement in src/audio_manager.py—integrate with PipeWire APIs for real-time handling.
- **Add Intent Routing for Smarter Flows**: Create intent-routing.md for classifying STT text (e.g., command vs. dictation using lightweight Vosk/LLM). Tie-in: Sits between STT and Orchestrator, routing to TTS or Accessibility. Suggestion: Define in agents/intent-classifier.md with patterns (e.g., "dictate: [text]" → paste); test for accuracy in iteration.
- **Develop Latency Strategy with Tiered Processing**: Update stt.md/tts.md for two tiers (fast streaming for immediate results, accurate refinement in background). Tie-in: Orchestrator queues refinements; GUI shows "Initial result..." instantly. Suggestion: Add to iteration-deployment.md as a test gate (e.g., "Latency < 2s for 80% cases").
- **Create Plugin SDK for Extensibility**: Add plugin-interface.md with hooks (e.g., register new voices/commands via JSON). Tie-in: TTS loads plugin voices; Orchestrator plugins for new agents. Suggestion: Define in docs/plugin-api.md—implement as Orchestrator loader for community extensions.
- **Deepen Adaptive Accessibility with Monitoring**: Expand accessibility.md with pattern detection (e.g., repeated corrections → slow TTS). Tie-in: Uses Orchestrator metrics for app-wide adaptations. Suggestion: Add to accessibility.md as reactions, with tests for scenarios like "low battery → lite mode."
- **Other Expansions**: For config, add config-schema.md (validation for toml). For events, add event-bus-spec.md (names/payloads/versioning). Tie-in: Prevents mismatches (e.g., STT events with intent for Accessibility).

## Implementation Sequence (To Drive Execution)
Follow this order to anchor specs in code (as per input):
1. Build runtime skeleton (event loop/messaging/state in src/runtime.py).
2. Implement clipboard gateway and audio manager (as services on runtime).
3. Add agents one by one (start with Hotkeys/STT for write path).
4. Wire tests around golden flows (write/read) and failure modes.
5. Iterate UX/accessibility (e.g., test adaptive behaviors).

## Overall Unifying Outlook
This build-up evolves "My Voice" from spec-heavy to a mature, production-grade platform—a "voice interaction layer for Linux" that unifies agents into a reliable, adaptive tool. Strengths like modularity are amplified by improvements (runtime spine for stability, clipboard gateway for safe flows), addressing risks (e.g., Wayland via capability detection) and enhancing impact (adaptive behaviors for disabilities, intent routing for natural use). Outlook: Iterated to excellence, it's positioned to compete with macOS—empowering users with seamless speak/type/read, open for community growth (plugins for niches like medical dictation). This is the "professional" evolution you wanted. Ready for the next iteration (e.g., add a new MD like audio-pipeline.md)? 😊
