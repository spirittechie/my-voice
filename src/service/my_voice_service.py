import gi

gi.require_version("GLib", "2.0")
from gi.repository import GLib
import dbus.service
import os
import subprocess
import tempfile
import shutil
import json
from pathlib import Path
import vosk


class MyVoiceService(dbus.service.Object):
    def __init__(self, bus_name, object_path="/com/myvoice/service"):
        dbus.service.Object.__init__(self, bus_name, object_path)
        self.temp_dir = Path(tempfile.mkdtemp(prefix="myvoice_"))
        print(f"Service started. Temp dir: {self.temp_dir}")

        config_path = Path.home() / ".config" / "my-voice" / "config.toml"
        self.config = {}
        if config_path.exists():
            import tomli

            self.config = tomli.loads(config_path.read_text())
        self.model_dir = Path(
            self.config.get("stt", {}).get("model_dir", "assets/en-us-small")
        ).resolve()
        self.current_proc = None

    @dbus.service.method("com.myvoice.Service", in_signature="i", out_signature="s")
    def start_recording(self, duration):
        if self.current_proc and self.current_proc.poll() is None:
            self.current_proc.terminate()
            self.current_proc = None
        audio_file = self.temp_dir / "recording.wav"
        cmd = ["arecord", "-d", str(duration), "-f", "cd", "-t", "wav", str(audio_file)]
        proc = subprocess.Popen(cmd)
        proc.wait()
        self.recording_complete(str(audio_file))
        return str(audio_file)

    @dbus.service.method("com.myvoice.Service", in_signature="s", out_signature="s")
    def copy_to_clipboard(self, text):
        try:
            subprocess.run(
                ["wl-copy"], input=text.encode(), check=True, capture_output=True
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            try:
                subprocess.run(
                    ["xclip", "-selection", "clipboard"],
                    input=text.encode(),
                    check=True,
                )
            except:
                print(f"Transcript: {text}")

    @dbus.service.method("com.myvoice.Service", in_signature="s", out_signature="s")
    def transcribe(self, audio_file):
        audio_path = Path(audio_file)
        if not audio_path.exists():
            return ""

        pcm_file = audio_path.with_suffix(".pcm")
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(audio_path),
                "-ar",
                "16000",
                "-ac",
                "1",
                "-f",
                "s16le",
                str(pcm_file),
            ],
            check=True,
            capture_output=True,
        )

        model = vosk.Model(str(self.model_dir))
        rec = vosk.KaldiRecognizer(model, 16000.0)

        with open(pcm_file, "rb") as f:
            while True:
                data = f.read(4096)
                if len(data) == 0:
                    break
                rec.AcceptWaveform(data)

        result = json.loads(rec.FinalResult())
        text = result.get("text", "")
        pcm_file.unlink(missing_ok=True)

        self.copy_to_clipboard(text)
        self.transcription_ready(str(audio_path), text)
        return text

    @dbus.service.method("com.myvoice.Service", in_signature="", out_signature="s")
    def get_selection(self):
        try:
            return subprocess.check_output(["wl-paste"]).decode().strip()
        except FileNotFoundError:
            try:
                return subprocess.check_output(["xsel", "-p"]).decode().strip()
            except:
                return ""

    @dbus.service.method("com.myvoice.Service", in_signature="s", out_signature="")
    def speak(self, text):
        if (
            hasattr(self, "current_proc")
            and self.current_proc
            and self.current_proc.poll() is None
        ):
            self.current_proc.terminate()
        self.current_proc = subprocess.Popen(["espeak-ng", "-q", text])
        self.current_proc.wait()
        self.playback_completed(text)

    @dbus.service.signal("com.myvoice.Signal", signature="s")
    def recording_complete(self, path):
        pass

    @dbus.service.signal("com.myvoice.Signal", signature="ss")
    def transcription_ready(self, path, text):
        pass

    @dbus.service.signal("com.myvoice.Signal", signature="s")
    def playback_completed(self, text):
        pass

    @dbus.service.signal("com.myvoice.Signal", signature="s")
    def playback_failed(self, text):
        pass


if __name__ == "__main__":
    from dbus.mainloop.glib import DBusGMainLoop

    DBusGMainLoop(set_as_default=True)
    bus = dbus.SessionBus()
    name = dbus.service.BusName("com.myvoice.Service", bus)
    service = MyVoiceService(name)
    loop = GLib.MainLoop()
    print("My Voice service running. Ctrl+C to stop.")
    try:
        loop.run()
    except KeyboardInterrupt:
        shutil.rmtree(service.temp_dir)
