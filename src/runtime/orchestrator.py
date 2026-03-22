import asyncio
from src.runtime.runtime import Runtime
from src.agents.stt import STTStub
from src.agents.clipboard_gateway import ClipboardGateway


class Orchestrator:
    def __init__(self):
        self.runtime = Runtime()
        self.stt = STTStub(self.runtime)
        self.clipboard = ClipboardGateway(self.runtime)
        self.runtime.events.subscribe("transcription_result", self._on_transcript)

    async def _on_transcript(self, data):
        await self.clipboard.transaction(data.get("text", ""))
        self.runtime.state.transition("idle")

    async def execute_flow(self, input_event="input_trigger"):
        self.runtime.state.transition("idle")
        await self.runtime.trigger(input_event)
        await self.stt.transcribe()
        await asyncio.sleep(0.01)
        return {
            "final_state": self.runtime.state.get(),
            "clipboard": self.runtime.state.get("clipboard"),
            "history": self.runtime.state.history,
        }
