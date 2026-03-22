from src.runtime.runtime import Runtime


class ClipboardGateway:
    def __init__(self, runtime: Runtime):
        self.runtime = runtime

    async def write(self, text):
        self.runtime.state.set("clipboard", text)
        await self.runtime.events.emit("clipboard_updated", {"text": text})
