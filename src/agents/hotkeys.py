import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
from gi.repository import GLib, Gtk, Gdk


class HotkeyListener:
    def __init__(self, callback, window=None):
        self.callback = callback
        self.running = False
        self.window = window
        self.controller = None

    def start(self):
        self.running = True
        if self.window is not None:
            self.controller = Gtk.EventControllerKey()
            self.controller.connect("key-pressed", self._on_key_pressed)
            self.window.add_controller(self.controller)
        else:
            GLib.timeout_add(100, self.poll)

    def _on_key_pressed(self, controller, keyval, keycode, state):
        if not self.running:
            return False
        is_super = (state & Gdk.ModifierType.SUPER_MASK) != 0
        if is_super and keyval in (Gdk.KEY_w, Gdk.KEY_W):
            self.callback("Super+W")
            return True
        if is_super and keyval in (Gdk.KEY_r, Gdk.KEY_R):
            self.callback("Super+R")
            return True
        return False

    def poll(self):
        if not self.running:
            return False
        return True

    def stop(self):
        self.running = False
        if self.controller is not None:
            self.controller = None

    def status(self):
        return {
            "implemented": True,
            "running": self.running,
            "mode": "gtk-key-controller" if self.window else "stub-poll",
            "note": "Focused-window hotkeys (Super+W/R). Global not implemented to avoid fragility.",
        }
