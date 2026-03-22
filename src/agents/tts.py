from src.runtime.runtime import Runtime


class TTS:
    def __init__(self, runtime: Runtime):
        self.runtime = runtime

    async def speak(self, text):
        self.runtime.state.transition("speaking")
        self.runtime.events.emit("tts_complete", {"text": text})
        self.runtime.state.transition("idle")
        return "spoken: " + text
