from gi.repository import GLib


class HotkeyListener:
    def __init__(self, callback):
        self.callback = callback
        self.running = False

    def start(self):
        self.running = True
        GLib.timeout_add(100, self.poll)

    def poll(self):
        if not self.running:
            return False
        return True

    def stop(self):
        self.running = False

    def status(self):
        return {
            "implemented": False,
            "running": self.running,
            "mode": "stub-poll",
            "note": "No global key capture backend is wired yet",
        }
