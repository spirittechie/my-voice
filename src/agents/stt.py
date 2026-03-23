from src.runtime.runtime import Runtime
import subprocess
import json
import vosk
from pathlib import Path
import tempfile
import os


class STTStub:
    def __init__(self, runtime: Runtime):
        self.runtime = runtime
        model_dir = os.getenv("MYVOICE_MODEL_DIR", "assets/en-us-small")
        self.record_seconds = int(os.getenv("MYVOICE_RECORD_SECONDS", "3"))
        self.model = vosk.Model(str(Path(model_dir)))

    def transcribe(self):
        self.runtime.state.transition("transcribing")
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                audio_file = Path(f.name)
            subprocess.run(
                [
                    "arecord",
                    "-d",
                    str(self.record_seconds),
                    "-f",
                    "cd",
                    "-t",
                    "wav",
                    str(audio_file),
                ],
                check=True,
                timeout=self.record_seconds + 2,
            )
            pcm = audio_file.with_suffix(".pcm")
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-i",
                    str(audio_file),
                    "-ar",
                    "16000",
                    "-ac",
                    "1",
                    "-f",
                    "s16le",
                    str(pcm),
                ],
                check=True,
                capture_output=True,
            )
            rec = vosk.KaldiRecognizer(self.model, 16000)
            with open(pcm, "rb") as f:
                while True:
                    d = f.read(4096)
                    if not d:
                        break
                    rec.AcceptWaveform(d)
            text = json.loads(rec.FinalResult()).get("text", "no input")
            for p in (audio_file, pcm):
                p.unlink(missing_ok=True)
            self.runtime.events.emit("transcription_result", {"text": text})
            return text
        except Exception as e:
            text = f"capture failed: {str(e)[:30]}"
            self.runtime.events.emit("transcription_result", {"text": text})
            return text
