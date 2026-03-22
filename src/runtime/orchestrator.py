import asyncio
from src.runtime.runtime import Runtime
from src.agents.stt import STTStub
from src.agents.clipboard_gateway import ClipboardGateway


class Orchestrator:
    def __init__(self):
        self.runtime = Runtime()
        self.stt = STTStub(self.runtime)
        self.clipboard = ClipboardGateway(self.runtime)
        self.runtime.events.subscribe("transcript_ready", self._on_transcript)

    async def _on_transcript(self, data):
        await self.clipboard.write(data.get("text", ""))

    async def run(self):
        await self.stt.transcribe()
        await asyncio.sleep(0.01)
        return self.runtime.state.get("clipboard")
