# Architecture Improvements Build-Up for "My Voice": From Spec to Operational Excellence

## Current Architecture Summary
The "My Voice" repository is in a strong conceptual phase but remains implementation-light, with a focus on agent specs rather than runtime code. This is a common early-stage state for agentic projects, where MD files define the vision, but execution lags. Key elements:
- **Repository State**: Primarily Markdown contracts in /agents (gui.md, network.md, stt.md, tts.md, hotkeys.md, accessibility.md), orchestration in orchestrator.md, and process docs (blueprint.md, iteration-deployment.md, clipboard-gateway.md). No core runtime in /src (e.g., no event bus implementation), no executable tests in /tests (only plans), and configs has config.example.toml but lacks validation. Launch entrypoint (bin/launch.sh) exists but relies on external OpenCode orchestration, making it dependent rather than self-contained.
- **Agent Existence vs. Implementation Status**:
  - GUI: Spec exists (intuitive puck with modes/prefs); no code (e.g., GTK4 implementation missing).
  - Network: Spec exists (HTTPS validation/remotes); no code (e.g., requests handling absent).
  - STT: Spec exists (mic capture/transcription); no code (e.g., Vosk/PipeWire integration not built).
  - TTS: Spec exists (text synthesis/playback); no code (e.g., eSpeak/Qwen3 not wired).
  - Hotkeys: Spec exists (evdev/wake-words); no code (e.g., listener not operational).
  - Accessibility: Spec exists (paste/modes/ARIA); no code (e.g., xdotool/portals not implemented).
  - Orchestrator: Spec exists (event routing/unification); no code (e.g., message bus stub missing).
  - Clipboard Gateway: Spec exists (transaction safety); no code (e.g., snapshot logic not built).
- **Communication Flow (as Documented, Not Implemented)**:
  - Core Write Path: hotkeys.start_stt → stt.recording_started → stt.transcript_ready → accessibility.paste_completed → gui (with clipboard gateway for safe text handling).
  - Core Read Path: hotkeys.start_tts → tts.playback_started → tts.playback_completed → gui/accessibility (with TTS controls like pause/resume via events).
  - Remote Degradation Path: network failure event triggers local STT/TTS fallback (orchestrator reroutes).
  - Shared State: MCP-like context in orchestrator.md (user_prefs, binding_state, model_state, network_state, session_state, accessibility_state).
- **Overall Assessment**: The design is agentically correct (modular, event-driven) but operationally incomplete—strong on theory, weak on runtime, leading to fragility as agents scale.

## Identified Weaknesses (Expanded with Agent Ties)
Building on the input, here's a deeper dive into weaknesses, with specific ties to our agents and accessibility impact.
- **No Concrete Runtime**: Orchestrator is overloaded as both coordinator and infrastructure, risking crashes (e.g., if STT floods the event bus). Tie-in: Affects all agents (e.g., Hotkeys dispatches could hang without proper queuing).
- **No Executable Tests**: Only text plans— no gating for accessibility (e.g., test "slow mode" in TTS doesn't delay for fatigue users). Tie-in: STT/Accessibility flows (e.g., cursor paste) untested for Wayland races.
- **Config Contract Mismatch**: config.toml referenced but example-only, no validation—could break Network (invalid URLs) or TTS (wrong voice params). Tie-in: Accessibility prefs (e.g., high-contrast) might not apply consistently.
- **No Formal Event Schema**: Event names listed but no payloads/versioning—risks drift (e.g., STT "transcript_ready" missing metadata for Accessibility paste). Tie-in: Orchestrator can't enforce consistency across agents.
- **Clipboard Layer Not Fully Wired**: gateway.md exists, but Orchestrator event map lacks integration (e.g., no "clipboard_conflict" event for fallbacks). Tie-in: STT outputs to clipboard could race with user actions, frustrating motor-impaired users.
- **Responsibility Overlap Risk**: E.g., STT owns transcription but Accessibility owns paste—boundaries blur, risking conflicts. Tie-in: Network fallbacks might not notify TTS properly for voice switches.
- **Concurrency/Race Risks**: No defined handling for simultaneous events (e.g., hotkey during ongoing STT). Tie-in: GUI updates could lag, annoying fatigue users.
- **Wayland/X11 Compatibility Risk**: Assumed in Accessibility (cursor paste), but no probing—fails on some compositors. Tie-in: Affects STT output usability for all users.
- **Fallback Behavior Under-Specified**: Policies conceptual, not mechanical (e.g., no state machine for Network to local switch). Tie-in: TTS might not adapt if STT falls back mid-flow.
- **Error Handling/Recovery**: Medium-high risk without supervisor (e.g., agent crash halts app). Tie-in: Hotkeys could fail silently, breaking accessibility.

## Reliability Risk Assessment (Expanded with Agent Ties)
- **Audio Capture Pipeline**: High risk—STT assumes PipeWire works, but no manager for device loss/noise. Assessment: Could cause "no transcript" failures; impact on accessibility: Frustrates users relying on speech input.
- **Clipboard Handling**: High risk without transactions—races overwrite data. Assessment: Breaks STT paste; impact: Motor-impaired users lose work.
- **Wayland/X11 Compatibility**: High risk—no detection for injection. Assessment: Cursor paste fails on Wayland; impact: Limits app to X11, excluding modern desktops.
- **Async Task Handling**: Medium-high risk—no timeouts/cancellation. Assessment: Long STT could hang GUI; impact: Fatigue users abandon the app.
- **Engine Fallback Behavior**: Medium risk—strategy exists but not enforced. Assessment: Network failure leaves TTS stuck; impact: Offline users get no feedback.
- **Error Handling/Recovery**: Medium-high risk—no watchdog. Assessment: One agent crash kills the app; impact: Unreliable for daily disability use.

## Proposed Architectural Improvements (Built-Up with Actionable Suggestions)
These improvements unify the system, addressing weaknesses while enhancing accessibility—each ties to agents and suggests implementation paths (e.g., new MD files or Orchestrator updates).

- **Introduce a Core Runtime Layer Beneath the Orchestrator**: Add a runtime.md defining a "voice operating kernel" with event bus (priority queues for urgent tasks like hotkey dispatches), device abstraction (unified PipeWire/evdev for STT/Hotkeys), state management (central store for MCP-shared data like prefs), and plugin loading (dynamic agent import). Tie-in: Orchestrator becomes a coordinator on top, reducing fragility (e.g., STT audio issues handled by runtime). Suggestion: Create agents/runtime.md and update orchestrator.md to depend on it—implement as a base Python module in src/runtime.py for low-overhead unification.
- **Formalize Boundaries and Ownership**: Define clear rules (e.g., Gateway owns clipboard snapshots, Accessibility owns policy like "paste if safe," STT/TTS own pipelines only). Tie-in: Prevents overlap (e.g., STT sends text to Gateway, which checks with Accessibility before paste). Suggestion: Add a boundaries.md file with a diagram (text-based) of ownership, and enforce in Orchestrator with validation checks.
- **Add Deterministic State Machines**: Create state-machines.md for key flows (e.g., recording: idle → capturing → transcribing → complete/fail, with transitions for fallbacks). Tie-in: Applies to STT (record lifecycle) and TTS (playback with pause). Suggestion: Integrate into Orchestrator reactions as finite state logic, tested in iteration step.
- **Add Capability Services**: Introduce services.md for detectors (e.g., display backend probe for Wayland/X11, permission checker for mic/clipboard). Tie-in: Accessibility uses this for reliable paste (e.g., fallback to clipboard if Wayland blocks). Suggestion: Build as a sub-agent in agents/capability.md, called by Orchestrator on startup.
- **Add Reliability Primitives**: Expand orchestrator.md with retry service (e.g., exponential backoff for Network failures), task cancellation (e.g., stop recording on hotkey), timeouts (e.g., 20s max for STT), and idempotency (e.g., dedupe duplicate events). Tie-in: Benefits all (e.g., Hotkeys queues during busy STT). Suggestion: Implement as Orchestrator methods, with metrics logging for monitoring.
- **Other Expansions**: For audio, add agents/audio-pipeline.md (manages buffering/noise for STT/TTS). For intent, add agents/intent-classifier.md (parses STT text for commands vs. dictation). Tie-in: Unifies flows (e.g., "dictate email" → STT → intent → paste).

## Overall Unifying Outlook
This build-up unifies "My Voice" into a resilient, adaptive platform—a true "voice operating kernel" for Linux accessibility that goes beyond wrappers to create an event-driven environment. Strengths like modularity are amplified by improvements (runtime layer for stability, state machines for reliability), addressing risks (e.g., Wayland paste via capability services) and enhancing impact (adaptive behaviors for disabilities). Outlook: Iterated to perfection, it's a game-changer—empowering users to speak/type/read effortlessly, with community potential (plugins for niches like medical dictation). This is the "professional" evolution you wanted. Ready for the next iteration (e.g., add a new MD like audio-pipeline.md)? 😊
