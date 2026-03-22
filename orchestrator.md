# Orchestrator for "My Voice"

## Role
The Orchestrator serves as the central "brain" and unification layer of the app, coordinating all agents (e.g., GUI, Network, STT, TTS, Hotkeys, Accessibility) to ensure they work as one seamless system. It manages startup/shutdown, event routing, message passing, and shared state, turning the modular agents into a cohesive tool that launches with a single command and operates intuitively. For accessibility, it prioritizes reliability and low cognitive load—handling failovers (e.g., if STT fails, route to a simple fallback and notify gently), monitoring performance to avoid crashes, and optimizing flows for users with fatigue or disabilities (e.g., queuing events to prevent overload). The Orchestrator supports scalability, allowing easy addition of new agents (e.g., for future features like Braille output) and integration with OpenCode for agentic tasking, making "My Voice" a robust, "mind-blown" accessibility app on Linux where everything "just works" (e.g., hotkey press flows to transcription, paste, and feedback without manual steps).

## Inputs
- Agent definitions from /agents MD files (e.g., loaded roles/inputs/outputs for GUI, STT, etc.).
- Configuration from configs/config.toml (e.g., agent priorities, event queue size, MCP settings for shared context like user prefs or voice models).
- System events from startup (e.g., "app launch" signal to init agents) or external (e.g., OS notifications for low battery, triggering low-power mode).
- Messages from agents (e.g., "hotkey detected" from Hotkeys Agent, "transcription ready" from STT Agent with text data).
- User inputs via GUI or Hotkeys (e.g., "toggle mode" request routed through here for distribution).

## Outputs
- Initialized agents (e.g., started instances of STT/TTS with loaded configs).
- Routed events/messages (e.g., "start TTS" dispatched to TTS Agent with text from Hotkeys).
- Unified status updates (e.g., "All agents ready" or "Fallback activated" sent to GUI for display, or to logs for review).
- Error resolutions (e.g., "Retry failed—switching to local mode" with rerouted tasks).
- Metrics and logs (e.g., event latency, agent health, exported to a central log file or Accessibility Agent for adaptive features).

## Reactions
- **On App Startup**: Load all agent MD files from /agents, initialize each (e.g., start STT with Vosk model, GUI with puck window), and verify integrations (e.g., test DBus connections or event bus). Set up shared MCP context (e.g., load user prefs like "high-contrast on" and distribute to all agents). If an agent fails to start (e.g., missing dep), fallback gracefully (e.g., disable remote features and notify "Running in basic mode").
- **On Event/Message Reception**: Use an event bus (e.g., simple pub/sub system) to route inputs (e.g., Hotkeys sends "Super + W pressed" → dispatch to STT for recording, then to GUI for progress update, and to Accessibility for cursor paste). Queue events if busy (e.g., max 5 in queue to prevent overload, with priority for critical like "emergency stop").
- **On Error or Failure**: Detect issues (e.g., STT timeout) and orchestrate recovery (e.g., retry via Network Agent or fallback to local; log "Error: STT failed—using cached result" and notify GUI audibly/visually for accessibility). Monitor agent health (e.g., if TTS is slow, adjust priorities to favor faster local options).
- **On Shutdown or Idle**: Gracefully stop agents (e.g., save state like last used voice), clean up resources (e.g., close PipeWire streams), and log session summary (e.g., "Processed 5 transcriptions, 3 playbacks").
- **Accessibility Reactions**: Adapt orchestration for user needs (e.g., if "slow mode" enabled, add delays between agent steps for paced feedback; ensure all outputs include ARIA/verbal cues). On low resources (e.g., battery < 20%), throttle non-essential agents (e.g., disable wake-word listening).

## Integration
- **With Other Agents**: Acts as the hub—loads and starts all agents on init, routes messages between them (e.g., Hotkeys trigger to STT, STT output to Accessibility for paste, then to GUI for display). Uses MCP for efficient shared state (e.g., user prefs distributed without repetition).
- **With External Systems**: Interfaces with OpenCode for generation/iteration (e.g., "opencode orchestrate" runs this as the main loop). Connects to OS for global events (e.g., PipeWire status for audio readiness).
- **Technical Notes**: Implemented as a main script (e.g., Python with asyncio for async event handling) or OpenCode's built-in orchestrator. Uses a simple message queue (e.g., in-memory list or Redis for advanced) for routing. Configurable for extensions like agent monitoring (e.g., health checks every 30s). Keeps overhead low (e.g., lightweight pub/sub) for smooth performance on low-spec hardware.

We're absolutely smashing it— this Orchestrator expansion unifies the whole app, making it a single, reliable system that "just works" for accessibility (e.g., seamless hotkey-to-paste flows). With this, the architecture is complete and ready for OpenCode generation!

Let's keep the success rolling: Expand another (e.g., a new one like Config Agent for toml handling), or start generating from one (e.g., prompt OpenCode for GUI)? Your call! 😊
