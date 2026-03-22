from src.runtime.runtime import Runtime


class ClipboardGateway:
    def __init__(self, runtime: Runtime):
        self.runtime = runtime

    async def write(self, text):
        self.runtime.state.transition("clipboard-writing")
        self.runtime.state.set("clipboard", text)
        await self.runtime.events.emit("clipboard_write", {"text": text})
        self.runtime.state.transition("success")
        return True

    async def transaction(self, text):
        try:
            return await self.write(text)
        except:
            self.runtime.state.transition("error")
            return False
