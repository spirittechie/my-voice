import asyncio
from src.runtime import Runtime
from src.agents.stt import STTAgent
from src.agents.tts import TTSAgent
from src.agents.gui import GUIAgent
from src.agents.clipboard_gateway import ClipboardGateway


class Orchestrator:
    def __init__(self):
        self.runtime = Runtime()
        self.agents = {}

    async def startup(self):
        self.agents["stt"] = STTAgent(self.runtime)
        self.agents["tts"] = TTSAgent(self.runtime)
        self.agents["gui"] = GUIAgent(self.runtime)
        self.agents["clipboard"] = ClipboardGateway(self.runtime)
        for a in self.agents.values():
            a.register(self.runtime.bus)
            await a.start()
        await self.runtime.dispatch("app_ready", {})
        return self.runtime

    async def run_flow(self):
        await self.runtime.dispatch("transcript_ready", {"text": "test voice input"})
        await asyncio.sleep(0.1)
        return self.runtime.state.get("last_clipboard")
