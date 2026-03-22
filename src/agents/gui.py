import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, GLib, Gio
from src.runtime.runtime import Runtime
from src.agents.stt import STTStub
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
            self.update_status("Recording")
            stt = STTStub(self.runtime)
            text = await stt.transcribe()
            self.runtime.state.set("transcript", text)
            self.auto_paste(text)
            self.update_status("Complete")
        except Exception as e:
            logging.error(f"STT fail: {e}")
            self.update_status("Error")
            self.show_alert(str(e))

    def auto_paste(self, text):
        try:
            subprocess.run(["wl-copy", text], timeout=5)
            subprocess.run(["xdotool", "key", "--clearmodifiers", "ctrl+v"], timeout=5)
            logging.info("Auto-paste success")
        except Exception as e:
            logging.error(f"Paste fail: {e}")

    def on_read(self, btn):
        self.update_status("Reading")
        try:
            text = subprocess.getoutput("wl-paste --primary") or subprocess.getoutput(
                "wl-paste"
            )
            if text:
                subprocess.run(
                    ["espeak-ng", "-s", "160", "-v", "en", text],
                    check=False,
                    timeout=15,
                )
                self.update_status("Complete")
                logging.info("TTS completed")
        except Exception as e:
            logging.error(f"TTS fail: {e}")
            self.update_status("Error")
            self.show_alert(str(e))

    def show_alert(self, msg):
        dialog = Gtk.MessageDialog(
            transient_for=self.window,
            flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text=msg,
        )
        dialog.run()
        dialog.destroy()

    def show(self):
        self.window.present()

    def run(self):
        self.show()
        self.window.present()


if __name__ == "__main__":
    runtime = Runtime()
    gui = GUI(runtime)
    app = Gtk.Application(
        application_id="com.myvoice.gui", flags=Gio.ApplicationFlags.FLAGS_NONE
    )
    app.connect("activate", lambda a: gui.show())
    app.run(None)
