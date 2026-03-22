import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, GLib
from src.runtime.runtime import Runtime
import subprocess
import logging
import asyncio

logging.basicConfig(level=logging.INFO)


class GUI:
    def __init__(self, runtime):
        self.runtime = runtime
        self.window = Gtk.Window(title="My Voice")
        self.window.set_default_size(400, 300)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.status = Gtk.Label(label="Idle")
        record_btn = Gtk.Button(label="Record")
        record_btn.connect("clicked", self.on_record)
        read_btn = Gtk.Button(label="Read Selection")
        read_btn.connect("clicked", self.on_read)
        box.append(self.status)
        box.append(record_btn)
        box.append(read_btn)
        self.window.set_child(box)
        self.current_state = "Idle"

    def update_status(self, state):
        self.status.set_text(state)
        self.current_state = state
        logging.info(f"State changed to: {state}")

    def on_record(self, btn):
        self.update_status("Recording")
        asyncio.create_task(self._record_flow())

    async def _record_flow(self):
        try:
            self.update_status("Processing")
            text = "deterministic test voice input"
            self.runtime.state.set("transcript", text)
            await self.runtime.events.emit("transcription_result", {"text": text})
            self.update_status("Complete")
        except Exception as e:
            logging.error(f"STT fail: {e}")
            self.update_status("Error")

    def on_read(self, btn):
        self.update_status("Reading")
        try:
            text = subprocess.getoutput("wl-paste --primary") or subprocess.getoutput(
                "wl-paste"
            )
            if text:
                subprocess.run(["espeak", "-s", "150", text], check=False)
                self.update_status("Complete")
                logging.info("TTS completed")
        except Exception as e:
            logging.error(f"TTS fail: {e}")
            self.update_status("Error")

    def show(self):
        self.window.present()

    def run(self):
        self.show()
        Gtk.main()
