from src.runtime.runtime import Runtime
import subprocess
import json
import vosk
from pathlib import Path
import tempfile
import os


def _capture_audio(duration=None, output_path=None):
    if output_path is None:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            output_path = Path(f.name)
    cmd = ["arecord", "-f", "cd", "-t", "wav"]
    if duration is not None:
        cmd.extend(["-d", str(duration)])
    cmd.append(str(output_path))
    subprocess.run(cmd, check=True, timeout=(duration or 10) + 5)
    return output_path


class VoskSTT:
    def __init__(self, runtime: Runtime):
        self.runtime = runtime
        model_dir = os.getenv("MYVOICE_MODEL_DIR", "assets/en-us-small")
        self.record_seconds = int(os.getenv("MYVOICE_RECORD_SECONDS", "8"))
        self.model = vosk.Model(str(Path(model_dir)))

    def transcribe(self, audio_path=None):
        if audio_path is None:
            self.runtime.state.transition("transcribing")
        try:
            if audio_path is None:
                audio_file = _capture_audio(self.record_seconds)
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
                text = (
                    json.loads(rec.FinalResult()).get("text", "").strip() or "no input"
                )
                for p in (audio_file, pcm):
                    p.unlink(missing_ok=True)
            else:
                audio_file = Path(audio_path)
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
                text = (
                    json.loads(rec.FinalResult()).get("text", "").strip() or "no input"
                )
                pcm.unlink(missing_ok=True)
            return text
        except Exception as e:
            text = f"capture failed: {str(e)[:30]}"
            return text


class WhisperSTT:
    def __init__(self, runtime: Runtime):
        self.runtime = runtime
        self.record_seconds = int(os.getenv("MYVOICE_RECORD_SECONDS", "8"))
        import whisper

        self.model = whisper.load_model("tiny")

    def transcribe(self, audio_path=None):
        if audio_path is None:
            self.runtime.state.transition("transcribing")
        try:
            if audio_path is None:
                audio_file = _capture_audio(self.record_seconds)
                result = self.model.transcribe(str(audio_file))
                text = result.get("text", "").strip() or "no input"
                audio_file.unlink(missing_ok=True)
            else:
                result = self.model.transcribe(str(audio_path))
                text = result.get("text", "").strip() or "no input"
            return text
        except Exception as e:
            text = f"capture failed: {str(e)[:30]}"
            return text


def create_stt(runtime: Runtime):
    engine = os.getenv("MYVOICE_STT_ENGINE", "vosk").lower()
    if engine == "whisper":
        return WhisperSTT(runtime)
    return VoskSTT(runtime)
