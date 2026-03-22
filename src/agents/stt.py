from src.runtime.runtime import Runtime


class STTStub:
    def __init__(self, runtime: Runtime):
        self.runtime = runtime

    async def transcribe(self):
        text = "stub transcription"
        await self.runtime.events.emit("transcript_ready", {"text": text})
        return text
