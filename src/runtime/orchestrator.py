import asyncio
import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, GLib
from src.runtime.runtime import Runtime
from src.agents.stt import STTStub
from src.agents.clipboard_gateway import ClipboardGateway
from src.agents.gui import GUI
from src.agents.tts import TTS


class Orchestrator:
    def __init__(self):
        self.runtime = Runtime()
        self.stt = STTStub(self.runtime)
        self.tts = TTS(self.runtime)
        self.clipboard = ClipboardGateway(self.runtime)
        self.gui = GUI(self.runtime)
        self._wire_events()

    def _wire_events(self):
        self.runtime.events.subscribe("input_trigger", self._handle_input)
        self.runtime.events.subscribe("transcription_result", self._handle_transcript)
        self.runtime.events.subscribe("clipboard_write", self._handle_clipboard)

    def _handle_input(self, data):
        self.gui.update_status("Transcribing...")
        self.runtime.state.transition("transcribing")
        text = self.stt.transcribe()
        self.runtime.events.emit("transcription_result", {"text": text})

    def _handle_transcript(self, data):
        success = self.clipboard.transaction(data["text"])
        if success:
            self.gui.update_status("Ready")
            self.runtime.state.transition("idle")

    def _handle_clipboard(self, data):
        self.runtime.events.emit("success", data)

    def start(self):
        self.gui.run()
        GLib.timeout_add(100, self._tick)

    def _tick(self):
        return True

    async def run_flow(self):
        result = await self.runtime.trigger("input_trigger")
        return result
