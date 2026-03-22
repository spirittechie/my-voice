import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, GLib, Gdk
from src.runtime.runtime import Runtime


class GUI:
    def __init__(self, runtime: Runtime):
        self.runtime = runtime
        self.window = Gtk.Window(title="My Voice")
        self.window.set_default_size(300, 200)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.record_btn = Gtk.Button(label="Record (STT)")
        self.record_btn.connect("clicked", self.on_record)
        self.read_btn = Gtk.Button(label="Read (TTS)")
        self.read_btn.connect("clicked", self.on_read)
        self.status = Gtk.Label(label="Idle")
        box.append(self.record_btn)
        box.append(self.read_btn)
        box.append(self.status)
        self.window.set_child(box)
        self.runtime.state.transition("idle")

    def on_record(self, btn):
        self.status.set_text("Listening...")
        self.runtime.state.transition("listening")
        GLib.idle_add(self._run_stt)

    def _run_stt(self):
        self.runtime.events.emit("input_trigger")
        return False

    def on_read(self, btn):
        self.status.set_text("Reading...")
        self.runtime.state.transition("reading")

    def update_status(self, state):
        self.status.set_text(state)

    def show(self):
        self.window.present()

    def run(self):
        self.show()
        Gtk.main()
