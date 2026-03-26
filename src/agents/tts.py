from src.runtime.runtime import Runtime


class TTS:
    def __init__(self, runtime: Runtime):
        self.runtime = runtime

    def speak(self, text):
        import subprocess

        try:
            subprocess.run(
                ["espeak-ng", "-s", "160", "-v", "en", text], check=False, timeout=30
            )
            return "spoken: " + text
        except:
            return "spoken: " + text
