# My Voice\n\n**Author:** Jesse Paul Riddle (spirittechie) &lt;drzin69@gmail.com&gt;

Lightweight fatigue-friendly desktop voice appliance for Linux (Fedora GNOME Wayland). STT/TTS with visual puck UI.

## Foundation Prompt
[paste full spec here for GitHub]

## Quick CPU Start
1. `sudo dnf install espeak-ng ffmpeg pipewire-alsa alsa-utils wl-clipboard xclip`
2. `pip install --user -r requirements.txt`
3. `./bin/setup.sh`
4. Launch puck from Applications menu or `python3 src/ui/my_voice_puck.py`
5. Launch puck: `python3 src/ui/my_voice_puck.py` or desktop file.

Hotkeys: Super+W STT, Super+R TTS (setup in Keyboard settings).

## Usage
- Puck: Toggle Write/Read, menu Record/TTS.
- Visual: Progress, modes, lock icon HTTPS.
- Clipboard auto-copy transcripts.

## Structure
- src/service: DBus daemon (Vosk STT, eSpeak TTS)
- src/ui: GTK4 puck
- assets/en-us-small: Vosk model
- configs/config.toml: prefs (TOML)
- bin/*.sh: hotkeys

## systemd
Enabled user unit.

## Extend
Remote HTTPS / GPU whisper.cpp / Piper TTS in config.toml.

MIT license. Contributions welcome!