import subprocess


class HotkeyListener:
    def __init__(self, callback):
        self.callback = callback

    def start(self):
        print("Hotkey listener started (stub for Super+W / Super+R)")

    def stop(self):
        pass
