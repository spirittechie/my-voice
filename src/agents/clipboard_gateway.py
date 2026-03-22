from src.runtime.runtime import Runtime


class ClipboardGateway:
    def __init__(self, runtime: Runtime):
        self.runtime = runtime

    def write(self, text):
        self.runtime.state.transition("clipboard-writing")
        self.runtime.state.set("clipboard", text)
        self.runtime.events.emit("clipboard_write", {"text": text})
        self.runtime.state.transition("success")
        return True

    def transaction(self, text):
        try:
            return self.write(text)
        except:
            self.runtime.state.transition("error")
            return False
