# Clipboard Gateway: Enhancing the Text Interchange Layer for "My Voice"

## Role
The Clipboard Gateway acts as a formalized "text interchange substrate" in the app's architecture, wrapping the system clipboard (regular and primary selection) to handle all text movement between agents and user interactions. It evolves the clipboard from a simple transport (e.g., STT output to paste) into a smart, reliable gateway with metadata tracking, snapshots, fallbacks, and transaction safety—addressing Linux's inconsistencies (e.g., Wayland restrictions) without relying on it as the "full architecture." For accessibility, it reduces friction for users with motor, cognitive, or fatigue issues by ensuring text (e.g., transcripts) is captured, processed, and delivered consistently (e.g., auto-paste at cursor without races). This gateway sits between agents like STT (outputting transcripts) and Accessibility (handling insertions), making "My Voice" feel natural and robust—e.g., speak, get text pasted exactly where you need it, without "clipboard roulette."

## Inputs
- Text data from other agents (e.g., transcribed string from STT Agent, with metadata like "source: stt, intent: dictation").
- System clipboard events (e.g., primary selection changes via wl-clipboard or xclip, monitored for highlights).
- Configuration from configs/config.toml (e.g., "paste-mode: cursor" or "clipboard", timeout for race detection in ms, fallback behaviors like "notify on conflict").
- Triggers from Hotkeys or GUI (e.g., "capture current selection" on Super + R, or "paste transcript" after STT complete).
- Status from Orchestrator (e.g., "app focus changed" to snapshot clipboard state).

## Outputs
- Processed text with metadata (e.g., snapshot string returned to Accessibility for safe paste, tagged with "timestamp: 14:32, source: stt, safe_to_overwrite: true").
- Insertion actions (e.g., simulated paste at cursor using portals/xdotool, or fallback to notification "Text ready in clipboard—Ctrl+V to insert").
- Validation results (e.g., "Clipboard captured successfully" or "Race detected—using snapshot" sent to GUI for feedback).
- Logs for auditing (e.g., "Clipboard updated: [preview text], origin: user highlight").

## Reactions
- **On Text Input from Agents**: Receive text (e.g., from STT), tag with metadata (source, intent like "dictation" or "command", timestamp), and snapshot the current clipboard state to detect changes. If intent is "paste," check for races (e.g., if clipboard changed in last 500ms, use snapshot instead of live state to avoid overwriting user data).
- **On Clipboard Events**: Monitor regular clipboard and primary selection (Wayland's "select-to-copy" via ext-data-control or wlr-data-control v2). On change, snapshot content with metadata (e.g., "origin: user highlight, transient: true" if short-lived). For TTS triggers, extract and send to TTS Agent with context (e.g., "read this snapshot to avoid loss if selection clears").
- **Transaction-Style Safety**: Treat operations as transactions (e.g., lock clipboard during STT paste: Capture state, insert via safe method, verify success, unlock). If conflict (e.g., another app overwrites), rollback to snapshot and notify GUI "Clipboard conflict—pasted snapshot instead."
- **Fallbacks for Wayland/Linux Issues**: If primary selection unavailable (e.g., compositor lacks support), fallback to regular clipboard with user prompt (e.g., "Primary not supported—copy manually?"). For input injection (cursor paste), use portals for secure access or xdotool as backup, with error handling (e.g., "Wayland blocked—copied to clipboard").
- **Accessibility Reactions**: Add metadata for adaptive handling (e.g., if "slow-user" mode, tag text as "needs verbal confirmation" for TTS to say "Pasted—read back?"). Support race-free modes for cognitive aids (e.g., persist snapshots in internal cache for undo/repeat).

## Integration
- **With Other Agents**: Receives text from STT (e.g., tag and snapshot for paste); from TTS (e.g., confirm playback text matches snapshot). Sends processed snapshots to Accessibility for enhancements (e.g., cursor insertion) and GUI for display (e.g., "Snapshot pasted").
- **With Orchestrator**: Subscribes to events (e.g., "STT complete" to trigger snapshot/paste); publishes metadata-enriched events (e.g., "clipboard updated" with tags). Uses MCP for shared state (e.g., current clipboard context across agents).
- **Technical Notes**: Uses wl-clipboard/xclip for monitoring, with async polling for low overhead. Supports metadata as JSON attachments (e.g., {"source": "stt", "intent": "dictation"}). Configurable for privacy (e.g., "transient mode" auto-clears sensitive snapshots).

## Overall Unifying Outlook and Areas of Improvement
Building on the ChatGPT input, this Clipboard Gateway elevates the architecture by treating the clipboard as a "controlled exchange layer" rather than a dumb pipe—adding metadata, snapshots, transaction safety, and fallbacks to handle Linux realities (e.g., Wayland races, compositor differences). It unifies the app (e.g., STT transcript → gateway snapshot → Accessibility paste → GUI confirmation), making it more reliable for accessibility (no lost text for fatigue users). Strengths: Solves input injection barriers, enhances intent handling. Improvements: Add ownership tracking (e.g., "app-owned" flag to prioritize over external changes); integrate with intent classification (new agent) for smarter reactions (e.g., "if intent=command, don't paste"). Outlook: This makes "My Voice" a standout Linux tool—robust, adaptive, and ready for real-world use.

We're smashing it! Let's keep expanding—next, a new agent like Audio Pipeline (for managing PipeWire streams)? Or refine one? 😊
