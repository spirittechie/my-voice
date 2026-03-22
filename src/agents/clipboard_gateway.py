from src.runtime import Agent


class ClipboardGateway(Agent):
    async def start(self):
        pass

    def register(self, bus):
        bus.subscribe("transcript_ready", self.on_transcript)

    async def on_transcript(self, data):
        self.runtime.update_state("last_clipboard", data.get("text", ""))
        await self.runtime.dispatch("clipboard_updated", data)
