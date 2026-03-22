# Architecture Build-Up v2 for "My Voice": From Spec to Systems Engineering Excellence

## Current Architecture Summary
The "My Voice" repository is at a pivotal "ideation to engineering" stage—strong on architecture specs (MD files defining agents and flows) but light on implementation (no runtime code in /src, no executable tests in /tests, configs limited to examples). This is a natural transition point, where the vision is clear but the "execution substrate" is missing, as the input notes. Key elements:
- **Repository State**: Heavy on docs (/agents MDs for GUI/Network/STT/TTS/Hotkeys/Accessibility/Clipboard Gateway, orchestrator.md for coordination, iteration-deployment.md for process, blueprint.md for overview). Light on ops (e.g., bin/launch.sh delegates to OpenCode, configs/config.example.toml lacks validation, no event schemas).
- **Agent Existence vs. Implementation Status** (Updated from Input):
  - GUI: Spec exists (puck with modes/prefs); no code (GTK4 reactions unbuilt).
  - Network: Spec exists (HTTPS/remotes); no code (validation/fallbacks conceptual).
  - STT: Spec exists (capture/transcription); no code (Vosk/PipeWire not wired).
  - TTS: Spec exists (synthesis/playback); no code (eSpeak/Qwen3 not implemented).
  - Hotkeys: Spec exists (evdev/wake-words); no code (listener stubs only).
  - Accessibility: Spec exists (paste/modes/ARIA); no code (xdotool/portals theoretical).
  - Orchestrator: Spec exists (event routing); no code (message bus as plan, not executed).
  - Clipboard Gateway: Spec exists (transaction safety); no code (snapshots/conflicts not built).
- **Communication Flow (as Documented, Not Implemented)** (Synced with Input):
  - Core Write Path: hotkeys.start_stt → stt.recording_started → stt.transcript_ready → clipboard_gateway.snapshot_taken → accessibility.paste_completed → gui.
  - Core Read Path: hotkeys.start_tts → tts.playback_started → tts.playback_completed → gui/accessibility (with clipboard_gateway for selection handling).
  - Remote Degradation Path: network failure → orchestrator reroute to local (with clipboard_gateway preserving state).
  - Shared State: MCP-like in orchestrator.md (user_prefs, etc.), but no registry implementation.
- **Overall Assessment**: Agentically coherent but "operationally incomplete"—the input's key insight. It's spec-heavy, risking fragmentation without a runtime spine.

## Identified Weaknesses (Expanded with Agent Ties)
Expanding on the input's analysis, here's a deeper dive with specific agent connections and accessibility impact.
- **No Concrete Runtime/Execution Substrate**: Orchestrator overloads as coordinator/infrastructure, lacking a "voice runtime kernel" for event loop/state. Tie-in: STT/TTS could crash without shared lifecycle; impact: Unreliable for daily disability use (e.g., app hangs mid-transcription).
- **No Executable Tests/Harness**: Text plans only—no gating for accessibility (e.g., test clipboard races in Accessibility). Tie-in: Hotkeys/STT flows untested for evdev permissions; impact: Frustrates users if hotkeys fail inconsistently.
- **Config Contract Mismatch**: config.toml referenced but example-only, no validation/schema. Tie-in: Network URLs could break, TTS voices misconfigure; impact: Accessibility prefs (e.g., slow mode) don't apply, defeating the purpose.
- **No Formal Event Schema**: Names listed but no payloads/versioning/semantics. Tie-in: Orchestrator can't enforce (e.g., STT "transcript_ready" missing intent for Accessibility paste); impact: Silent breakages in read/write paths for cognitive-load users.
- **Clipboard Layer Not Fully Wired/Semantics Weak**: gateway.md exists, but no transaction model/ownership rules. Tie-in: STT outputs risk races (e.g., user copies something mid-paste); impact: Motor-impaired users lose data, eroding trust.
- **Responsibility Overlap Risk**: E.g., STT owns transcription but Accessibility owns paste, Clipboard Gateway owns safety—boundaries fuzzy. Tie-in: Network fallbacks might not notify TTS; impact: Inconsistent experiences for fatigue users.
- **Concurrency/Race Risks**: No handling for simultaneous events (e.g., hotkey during STT). Tie-in: GUI updates lag; impact: Overwhelms users with attention difficulties.
- **Wayland/X11 Compatibility Risk**: Assumed but no probing/abstraction. Tie-in: Accessibility cursor paste fails on Wayland; impact: Excludes modern desktops, limiting accessibility reach.
- **Fallback Behavior Under-Specified**: Conceptual, not state-machine driven. Tie-in: TTS doesn't adapt on STT fallback; impact: Offline users get stuck flows.
- **Error Handling/Recovery**: No supervisor/watchdog. Tie-in: One agent crash (e.g., Hotkeys evdev fail) halts all; impact: Unreliable for chronic use.

## Reliability Risk Assessment (Expanded with Agent Ties)
- **Audio Capture Pipeline**: High risk—no dedicated manager for buffering/noise. Assessment: STT failures in noisy settings; impact: Frustrates speech-impaired users needing consistent input.
- **Clipboard Handling**: High risk—weak semantics lead to races/loss. Assessment: STT paste overwrites; impact: Cognitive users confused by lost data.
- **Wayland/X11 Compatibility**: High risk—no unified bridge. Assessment: Accessibility injection fails; impact: Mobility users can't rely on cursor paste.
- **Async Task Handling**: Medium-high risk—no deadlines/ dedupe. Assessment: Long TTS hangs GUI; impact: Fatigue users abandon mid-task.
- **Engine Fallback Behavior**: Medium risk—not mechanical. Assessment: Network to local leaves TTS inconsistent; impact: Offline accessibility degraded.
- **Error Handling/Recovery**: Medium-high risk—no primitives. Assessment: Crash in one agent (e.g., Network timeout) stops app; impact: Daily users lose trust.

## Proposed Architectural Improvements (Built-Up with Actionable Suggestions)
These build on the input, unifying the system with new elements (e.g., runtime spine as a layer), tied to agents for coherence. Each is actionable (e.g., new MD files, updates).

- **Implement a Minimal Runtime Skeleton (Runtime Spine)**: Add runtime.md defining a "voice operating kernel" with event loop (async for handling), message bus (pub/sub with priorities), shared state registry (MCP for prefs), and plugin loading. Tie-in: Orchestrator runs on top (coordination only); STT/TTS plug in for lifecycle. Suggestion: Create agents/runtime.md and implement as src/runtime.py (asyncio base)—start with stubs logging "Event received."
- **Formalize Clipboard as Controlled Gateway**: Expand gateway.md with transaction model (snapshot, resolve conflicts, tag with semantics like "intent: dictation"). Tie-in: STT emits to Gateway, which checks with Accessibility before paste. Suggestion: Add clipboard-gateway-spec.md with schema (JSON payloads) and integrate as Orchestrator service—test with mocks for races.
- **Introduce Dedicated Audio Pipeline Manager**: Add audio-pipeline.md for managing streams (buffering, noise suppression with RNNoise, device switching). Tie-in: STT inputs route through here; TTS outputs for normalization. Suggestion: Build as agents/audio-pipeline.md, implement in src/audio_manager.py—integrate with PipeWire APIs for real-time handling.
- **Add Intent Routing for Smarter Flows**: Create intent-routing.md for classifying STT text (e.g., command vs. dictation using lightweight Vosk/LLM). Tie-in: Sits between STT and Orchestrator, routing to TTS or Accessibility. Suggestion: Define in agents/intent-classifier.md with patterns (e.g., "dictate: [text]" → paste); test for accuracy in iteration.
- **Develop Latency Strategy with Tiered Processing**: Update stt.md/tts.md for two tiers (fast streaming for immediate results, accurate refinement in background). Tie-in: Orchestrator queues refinements; GUI shows "Initial result..." instantly. Suggestion: Add to iteration-deployment.md as a test gate (e.g., "Latency < 2s for 80% cases").
- **Create Plugin SDK for Extensibility**: Add plugin-interface.md with hooks (e.g., register new voices/commands via JSON). Tie-in: TTS loads plugin voices; Orchestrator plugins for new agents. Suggestion: Define in docs/plugin-api.md—implement as Orchestrator loader for community extensions.
- **Deepen Adaptive Accessibility with Monitoring**: Expand accessibility.md with pattern detection (e.g., repeated corrections → slow TTS). Tie-in: Uses Orchestrator metrics for app-wide adaptations. Suggestion: Add to accessibility.md as reactions, with tests for scenarios like "low battery → lite mode."

## Overall Unifying Outlook
This build-up evolves "My Voice" from spec-heavy to a mature, systems-engineered platform—a "voice interface layer for Linux" that unifies agents into a reliable, adaptive tool. Strengths like modularity are amplified by improvements (runtime spine for stability, clipboard gateway for safe text flows), addressing risks (e.g., Wayland via capability detection) and enhancing impact (adaptive behaviors for disabilities, intent routing for natural use). Outlook: Iterated to excellence, it's positioned to compete with macOS accessibility—empowering users with seamless speak/type/read, open for community growth (plugins for niches like medical dictation). This is the "professional" foundation; next, implement the runtime skeleton to bridge spec to execution. Ready for that, or one more expansion? 😊
