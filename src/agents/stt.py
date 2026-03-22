from src.runtime.runtime import Runtime


class STTStub:
    def __init__(self, runtime: Runtime):
        self.runtime = runtime

    async def transcribe(self):
        self.runtime.state.transition("transcribing")
        text = "deterministic test voice input"
        await self.runtime.events.emit("transcription_result", {"text": text})
        return text
