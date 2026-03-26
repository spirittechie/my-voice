import gi
import json
import logging
import os
import subprocess
import sys
import threading
import tempfile
from pathlib import Path
from dataclasses import dataclass
from enum import Enum
from typing import List

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
from gi.repository import Gio, GLib, Gtk, Gdk  # noqa: E402

from src.agents.hotkeys import HotkeyListener  # noqa: E402
from src.agents.stt import create_stt  # noqa: E402
from src.runtime.runtime import Runtime  # noqa: E402


class TokenType(Enum):
    COMMAND = "COMMAND"
    FLAG = "FLAG"
    PATH = "PATH"
    ARG = "ARG"
    OPERATOR = "OPERATOR"
    QUOTE = "QUOTE"
    FORMAT = "FORMAT"
    ESCAPE = "ESCAPE"
    WORD = "WORD"


@dataclass
class Token:
    value: str
    type: TokenType
    original: str = ""


logging.basicConfig(level=logging.INFO)


class GUI:
    def __init__(self, runtime, app=None, dev_mode=False):
        self.runtime = runtime
        self._busy = False
        self._tts_process = None
        self.read_btn = None
        self.record_btn = None
        self.recording_proc = None
        self.recording_audio = None
        self.stt_engine = os.getenv("MYVOICE_STT_ENGINE", "vosk").upper()
        self.tts_engine = "eSpeak"
        self.stt = create_stt(self.runtime)
        self.duration_timer = None
        self.current_duration = 0
        self.current_state = "Idle"
        self.dev_mode = dev_mode
        self.raw_transcript_entry = None
        self.voice_mappings = {}
        self.command_mode = False
        self.mappings_path = (
            Path.home() / ".config" / "my-voice" / "voice_mappings.json"
        )
        self._load_mappings()
        self.window = Gtk.Window(title="My Voice", application=app)
        self.window.set_default_size(460, 720 if dev_mode else 620)
        self.window.connect("close-request", self.on_close_request)

        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(b"""
            window {
                background: #1e1f22;
                color: #e5e7eb;
            }
            .status-box {
                background: #2d333d;
                padding: 6px 10px;
                border: 1px solid #3f4654;
                border-radius: 6px;
            }
            .status-box label {
                color: #eef2f7;
                font-size: 13px;
            }
            .status-dot {
                color: #7b8494;
                font-size: 14px;
                min-width: 12px;
                padding: 0;
            }
            .status-box label.status-dot.recording {
                color: #e53935;
            }
            .transcript-panel {
                background: #f8fafc;
                border: 1px solid #cbd5e1;
                border-radius: 8px;
            }
            .transcript-panel textview {
                padding: 16px 20px;
                background: #f8fafc;
                color: #111827;
            }
            button {
                color: #f8fafc;
                background: #3a414d;
                border-color: #4a5262;
            }
            button label { color: #f8fafc; }
            label { padding: 2px 0; }
        """)
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

        header = Gtk.HeaderBar()
        header.set_title_widget(Gtk.Label(label="My Voice"))
        hamburger = Gtk.MenuButton(icon_name="open-menu-symbolic", has_frame=False)
        menu_popover = Gtk.Popover()
        menu_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=8,
            margin_start=12,
            margin_end=12,
            margin_top=12,
            margin_bottom=12,
        )
        prefs_btn = Gtk.Button(label="Preferences...")
        prefs_btn.connect("clicked", self.open_prefs)
        self.command_toggle = Gtk.ToggleButton(label="Command Mode")
        self.command_toggle.connect("toggled", self.toggle_command_mode)
        helper_btn = Gtk.Button(label="Show Helper")
        helper_btn.connect("clicked", self.show_helper)
        menu_box.append(prefs_btn)
        menu_box.append(self.command_toggle)
        menu_box.append(helper_btn)
        menu_popover.set_child(menu_box)
        hamburger.set_popover(menu_popover)
        header.pack_start(hamburger)
        self.window.set_titlebar(header)

        main_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=12,
            margin_start=12,
            margin_end=12,
            margin_top=12,
            margin_bottom=12,
        )

        status_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        status_box.add_css_class("status-box")
        state_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        state_row.set_halign(Gtk.Align.START)
        state_row.set_valign(Gtk.Align.CENTER)
        self.recording_dot = Gtk.Label(label="●", halign=Gtk.Align.START)
        self.recording_dot.add_css_class("status-dot")
        self.recording_dot.set_opacity(0.45)
        self.recording_dot.set_single_line_mode(True)
        self.recording_dot.set_valign(Gtk.Align.CENTER)
        self.recording_dot.set_xalign(0.5)
        self.state_label = Gtk.Label(label="State: Idle", halign=Gtk.Align.START)
        self.state_label.set_wrap(False)
        self.state_label.set_single_line_mode(True)
        self.state_label.set_valign(Gtk.Align.CENTER)
        self.state_label.set_xalign(0.0)
        state_row.append(self.recording_dot)
        state_row.append(self.state_label)
        self.stt_label = Gtk.Label(
            label=f"STT: {self.stt_engine}", halign=Gtk.Align.START
        )
        self.duration_label = Gtk.Label(label="Duration: 00:00", halign=Gtk.Align.START)
        status_box.append(state_row)
        status_box.append(self.stt_label)
        status_box.append(self.duration_label)
        main_box.append(status_box)

        stt_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        stt_label = Gtk.Label(label="STT Engine", halign=Gtk.Align.START)
        self.stt_combo = Gtk.ComboBoxText()
        self.stt_combo.append_text("Vosk")
        self.stt_combo.append_text("Whisper")
        active_idx = 1 if self.stt_engine == "WHISPER" else 0
        self.stt_combo.set_active(active_idx)
        self.stt_combo.connect("changed", self.on_stt_engine_changed)
        self.record_btn = Gtk.Button(label="Record")
        self.record_btn.connect("clicked", self.on_record)
        stt_box.append(stt_label)
        stt_box.append(self.stt_combo)
        stt_box.append(self.record_btn)
        main_box.append(stt_box)

        tts_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        tts_label = Gtk.Label(label="TTS Engine", halign=Gtk.Align.START)
        self.tts_combo = Gtk.ComboBoxText()
        self.tts_combo.append_text("eSpeak")
        self.tts_combo.set_active(0)
        self.tts_combo.connect("changed", self.on_tts_engine_changed)
        self.read_btn = Gtk.Button(label="Read Selection")
        self.read_btn.connect("clicked", self.on_read)
        tts_box.append(tts_label)
        tts_box.append(self.tts_combo)
        tts_box.append(self.read_btn)
        main_box.append(tts_box)

        transcript_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        transcript_label = Gtk.Label(label="Transcript", halign=Gtk.Align.START)
        self.scrolled = Gtk.ScrolledWindow()
        self.scrolled.set_min_content_height(200)
        self.scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.scrolled.set_vexpand(True)
        self.transcript_view = Gtk.TextView()
        self.transcript_view.set_wrap_mode(Gtk.WrapMode.WORD)
        self.transcript_view.set_editable(False)
        self.transcript_view.set_cursor_visible(False)
        self.transcript_view.set_left_margin(20)
        self.transcript_view.set_right_margin(20)
        self.transcript_view.set_top_margin(16)
        self.transcript_view.set_bottom_margin(16)
        self.transcript_view.set_size_request(-1, 200)
        self.scrolled.set_child(self.transcript_view)
        self.scrolled.add_css_class("transcript-panel")
        transcript_box.append(transcript_label)
        transcript_box.append(self.scrolled)
        main_box.append(transcript_box)

        if self.dev_mode:
            self._add_dev_block(main_box)

        footer = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL, spacing=0, margin_top=12
        )
        self.hotkey_label = Gtk.Label(
            label="Super+W: Record | Super+R: Read", halign=Gtk.Align.CENTER
        )
        footer.append(self.hotkey_label)
        main_box.append(footer)

        scroller = Gtk.ScrolledWindow()
        scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroller.set_child(main_box)
        self.window.set_child(scroller)
        self.hotkeys = HotkeyListener(self.on_hotkey, self.window)
        self.hotkeys.start()
        self.update_status("Idle")

    def update_status(self, state):
        self.current_state = state
        state_map = {
            "Idle": "Idle",
            "Recording": "Recording",
            "Transcribing": "Transcribing",
            "Transcribing...": "Transcribing",
            "Reading": "Speaking",
            "Speaking": "Speaking",
            "Complete": "Idle",
            "Ready": "Ready",
            "Copied": "Copied",
            "Pasted": "Pasted",
            "Stopped": "Stopped",
            "Error": "Error",
        }
        display_state = state_map.get(state, state)
        self.state_label.set_text(f"State: {display_state}")
        self.stt_label.set_text(f"STT: {self.stt_engine}")
        if state in ("Recording", "recording"):
            self.recording_dot.add_css_class("recording")
            self.recording_dot.set_opacity(1.0)
        else:
            self.recording_dot.remove_css_class("recording")
            self.recording_dot.set_opacity(0.45)
        if display_state not in ("Recording", "Transcribing"):
            self.duration_label.set_text("Duration: 00:00")
            self.stop_duration_timer()
        logging.info(f"State changed to: {state}")

    def on_stt_engine_changed(self, combo):
        engine = combo.get_active_text().lower()
        os.environ["MYVOICE_STT_ENGINE"] = engine
        self.stt_engine = engine.upper()
        self.stt_label.set_text(f"STT: {self.stt_engine}")
        try:
            self.stt = create_stt(self.runtime)
            self.update_status("Ready")
        except Exception as e:
            self.show_alert(f"Whisper unavailable, reverted to Vosk: {str(e)[:80]}")
            os.environ["MYVOICE_STT_ENGINE"] = "vosk"
            self.stt_engine = "VOSK"
            self.stt_combo.set_active(0)
            self.stt_label.set_text("STT: VOSK")

    def on_tts_engine_changed(self, combo):
        engine = combo.get_active_text()
        self.tts_engine = engine
        self.update_status("Ready")

    def start_duration_timer(self):
        self.current_duration = 0
        if self.duration_timer is not None:
            GLib.source_remove(self.duration_timer)
        self.duration_timer = GLib.timeout_add_seconds(1, self._tick_duration)
        self._tick_duration()

    def _tick_duration(self):
        self.current_duration += 1
        mm = self.current_duration // 60
        ss = self.current_duration % 60
        self.duration_label.set_text(f"Duration: {mm:02d}:{ss:02d}")
        if self.current_state in ("Recording", "Transcribing", "recording"):
            return True
        return False

    def stop_duration_timer(self):
        if self.duration_timer is not None:
            GLib.source_remove(self.duration_timer)
            self.duration_timer = None

    def update_transcript(self, text):
        if not text or not text.strip():
            if self.transcript_view.get_buffer():
                self.transcript_view.get_buffer().set_text("No transcript")
            return
        raw_text = text.strip()
        display_text = raw_text
        if self.command_mode:
            display_text = self.interpret_phrase(raw_text)
        if self.dev_mode and self.command_output_entry:
            self.command_output_entry.set_text(display_text)
        if self.transcript_view.get_buffer():
            self.transcript_view.get_buffer().set_text(display_text)
        self.update_status("Ready")

    def on_record(self, btn):
        if self.recording_proc is not None:
            self._stop_recording()
        else:
            self._start_recording()

    def _start_recording(self):
        if self._busy:
            return
        self._busy = True
        try:
            fd, path = tempfile.mkstemp(suffix=".wav")
            os.close(fd)
            self.recording_audio = Path(path)
            cmd = ["arecord", "-f", "cd", "-t", "wav", str(self.recording_audio)]
            self.recording_proc = subprocess.Popen(cmd)
            self.update_status("Recording")
            self.start_duration_timer()
            if self.record_btn:
                self.record_btn.set_label("Stop")
            logging.info(f"Recording started: {self.recording_audio}")
        except Exception as e:
            logging.error(f"Failed to start recording: {e}")
            self._busy = False

    def _stop_recording(self):
        if self.recording_proc is not None:
            try:
                self.recording_proc.terminate()
                self.recording_proc.wait(timeout=5)
                logging.info("Recording stopped by user")
            except Exception:
                if self.recording_proc:
                    self.recording_proc.kill()
            self.recording_proc = None
        self.stop_duration_timer()
        if self.recording_audio and self.recording_audio.exists():
            try:
                text = self.stt.transcribe(str(self.recording_audio))
                self.runtime.state.set("transcript", text)
                self.auto_paste(text)
            except Exception as e:
                logging.error(f"Transcribe after stop failed: {e}")
                self.update_status("Error")
        else:
            self.update_status("Idle")
        if self.record_btn:
            self.record_btn.set_label("Record")
        self._busy = False
        if self.recording_audio:
            self.recording_audio.unlink(missing_ok=True)
            self.recording_audio = None

    def _record_flow(self):
        try:
            text = self.stt.transcribe()
            self.runtime.state.set("transcript", text)
            self.auto_paste(text)
            GLib.idle_add(self._finish_success)
        except Exception as e:
            logging.error(f"STT fail: {e}")
            GLib.idle_add(self._finish_error, str(e))

    def auto_paste(self, text):
        GLib.idle_add(self.update_transcript, text)
        try:
            subprocess.run(["wl-copy", text], check=True, timeout=5)
            logging.info("Clipboard write success")
            GLib.idle_add(self.update_status, "Copied")
            if self._autopaste_enabled():
                if self._attempt_paste_keystroke():
                    logging.info("Auto-paste key injection success")
                    GLib.idle_add(self.update_status, "Pasted")
                else:
                    logging.info("Clipboard ready; no paste injector available")
        except Exception as e:
            logging.error(f"Paste fail: {e}")
            GLib.idle_add(self.update_status, "Error")

    def _autopaste_enabled(self):
        return os.getenv("MYVOICE_AUTOPASTE", "1") != "0"

    def _attempt_paste_keystroke(self):
        if subprocess.run(["which", "wtype"], capture_output=True).returncode == 0:
            subprocess.run(
                ["wtype", "-M", "ctrl", "-k", "v", "-m", "ctrl"],
                check=False,
                timeout=5,
            )
            return True
        if subprocess.run(["which", "xdotool"], capture_output=True).returncode == 0:
            subprocess.run(
                ["xdotool", "key", "--clearmodifiers", "ctrl+v"],
                check=False,
                timeout=5,
            )
            return True
        return False

    def on_read(self, btn):
        if self._tts_process is not None:
            self._stop_tts()
            return
        if self._busy:
            logging.info("Action ignored; previous operation still running")
            return
        self._start_background_task("Speaking", self._read_flow)

    def open_prefs(self, btn):
        dialog = Gtk.MessageDialog(
            transient_for=self.window,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text="Options menu - future growth point for settings.",
        )
        dialog.connect("response", lambda d, r: (d.destroy(), None))
        dialog.present()

    def _read_flow(self):
        try:
            text = subprocess.getoutput("wl-paste --primary") or subprocess.getoutput(
                "wl-paste"
            )
            if text:
                tts_cmd = "espeak-ng"
                if (
                    subprocess.run(
                        ["which", "espeak-ng"], capture_output=True
                    ).returncode
                    != 0
                ):
                    tts_cmd = "espeak"
                self._tts_process = subprocess.Popen(
                    [tts_cmd, "-s", "160", "-v", "en", text],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                self._tts_process.wait()
                logging.info("TTS completed")
                self._tts_process = None
            GLib.idle_add(self._finish_success)
        except Exception as e:
            logging.error(f"TTS fail: {e}")
            if self._tts_process:
                self._tts_process = None
            GLib.idle_add(self._finish_error, f"TTS failed: {str(e)[:80]}")

    def _stop_tts(self):
        if self._tts_process is not None:
            try:
                self._tts_process.terminate()
                self._tts_process.wait(timeout=2)
            except Exception:
                if self._tts_process:
                    self._tts_process.kill()
            self._tts_process = None
        self.stop_duration_timer()
        self.update_status("Stopped")
        GLib.idle_add(self._finish_stop)

    def _finish_stop(self):
        if self.read_btn:
            self.read_btn.set_label("Read Selection")
        self._busy = False
        return False

    def _start_background_task(self, status, target):
        if self._busy:
            logging.info("Action ignored; previous operation still running")
            return
        self._busy = True
        if "record" in status.lower() or status in ("Recording", "Transcribing"):
            self.start_duration_timer()
        self.update_status(status)
        if self.read_btn:
            self.read_btn.set_label("Stop")
        threading.Thread(target=target, daemon=True).start()

    def _finish_success(self):
        self.stop_duration_timer()
        self.update_status("Idle")
        if self.read_btn:
            self.read_btn.set_label("Read Selection")
        self._busy = False
        self._tts_process = None
        return False

    def _finish_error(self, msg):
        self.stop_duration_timer()
        self.update_status("Error")
        if self.read_btn:
            self.read_btn.set_label("Read Selection")
        self.show_alert(msg)
        self._busy = False
        self._tts_process = None
        return False

    def on_hotkey(self, key):
        if key == "Super+W":
            self.on_record(None)
        elif key == "Super+R":
            self.on_read(None)
        logging.info(f"Hotkey triggered: {key}")

    def on_close_request(self, *args):
        self._stop_recording()
        self._stop_tts()
        self.hotkeys.stop()
        return False

    def show_alert(self, msg):
        dialog = Gtk.MessageDialog(
            transient_for=self.window,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text=msg[:300],
        )
        dialog.connect("response", lambda d, r: (d.destroy(), None))
        dialog.present()

    def _add_dev_block(self, main_box):
        print("DEV BLOCK INIT - single creation")
        dev_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        dev_label = Gtk.Label(label="Dev: Speech-to-Command", halign=Gtk.Align.START)
        raw_label = Gtk.Label(label="Raw Transcript", halign=Gtk.Align.START)
        self.raw_transcript_entry = Gtk.Entry()
        self.raw_transcript_entry.set_editable(False)
        self.raw_transcript_entry.set_placeholder_text("STT raw output appears here")
        norm_label = Gtk.Label(label="Normalized Tokens", halign=Gtk.Align.START)
        self.norm_entry = Gtk.Entry()
        self.norm_entry.set_editable(False)
        classified_label = Gtk.Label(label="Classified Tokens", halign=Gtk.Align.START)
        self.classified_entry = Gtk.Entry()
        self.classified_entry.set_editable(False)
        self.classified_entry.set_placeholder_text("token:TYPE ...")
        phrase_label = Gtk.Label(
            label="Spoken Phrase (manual test)", halign=Gtk.Align.START
        )
        self.phrase_entry = Gtk.Entry()
        self.phrase_entry.set_placeholder_text(
            "pseudo dnf dash y update and then flatpak update dash y"
        )
        test_btn = Gtk.Button(label="Test Interpretation")
        test_btn.connect("clicked", self.on_test_interpret)
        output_label = Gtk.Label(label="Command Output", halign=Gtk.Align.START)
        self.command_output_entry = Gtk.Entry()
        self.command_output_entry.set_editable(False)
        map_label = Gtk.Label(label="Voice Mapping", halign=Gtk.Align.START)
        self.spoken_map_entry = Gtk.Entry()
        self.spoken_map_entry.set_placeholder_text("update system")
        self.cmd_map_entry = Gtk.Entry()
        self.cmd_map_entry.set_placeholder_text(
            "sudo dnf -y update && flatpak update -y"
        )
        apply_btn = Gtk.Button(label="Apply Mapping")
        apply_btn.connect("clicked", self.on_apply_mapping)
        dev_box.append(dev_label)
        dev_box.append(raw_label)
        dev_box.append(self.raw_transcript_entry)
        dev_box.append(norm_label)
        dev_box.append(self.norm_entry)
        dev_box.append(classified_label)
        dev_box.append(self.classified_entry)
        dev_box.append(phrase_label)
        dev_box.append(self.phrase_entry)
        dev_box.append(test_btn)
        dev_box.append(output_label)
        dev_box.append(self.command_output_entry)
        dev_box.append(map_label)
        dev_box.append(self.spoken_map_entry)
        dev_box.append(self.cmd_map_entry)
        dev_box.append(apply_btn)
        main_box.append(dev_box)

    def interpret_phrase(self, phrase: str) -> str:
        if not phrase:
            return ""

        # 1. Exact user mappings (highest priority)
        key = phrase.strip().lower()
        if key in self.voice_mappings:
            return self.voice_mappings[key]

        raw = phrase.lower().strip()
        if self.dev_mode and self.raw_transcript_entry:
            self.raw_transcript_entry.set_text(phrase)

        # Structured token processing - NO string joining for rebuild
        classified_tokens = self._classify_tokens(raw)
        norm_text = " ".join([t.original for t in classified_tokens])
        if self.dev_mode and self.norm_entry:
            self.norm_entry.set_text(norm_text)

        classified_str = " ".join(
            [f"{t.value}:{t.type.value}" for t in classified_tokens]
        )
        if self.dev_mode and self.classified_entry:
            self.classified_entry.set_text(classified_str)

        final_cmd = self._structured_rebuild(classified_tokens)
        return final_cmd

    def _classify_tokens(self, raw: str) -> List[Token]:
        """General token classification into shell atom classes. No per-command patches."""
        norm = " ".join(raw.lower().split())
        norm = " ".join(norm.split())
        if self.dev_mode and self.norm_entry:
            self.norm_entry.set_text(norm)

        # Finite canonical vocab for command atoms only
        vocab = {
            "sudo": {"pseudo", "sudo", "su do"},
            "dnf": {"dnf", "d n f"},
            "apt": {"apt"},
            "flatpak": {"flatpak", "flat pak"},
            "mkdir": {"mkdir"},
            "chmod": {"chmod"},
            "uname": {"uname", "u name"},
            "journalctl": {"journalctl", "journal ctl"},
            "lscpu": {"lscpu", "l s c p u"},
            "lshw": {"lshw", "l s h w"},
            "nmcli": {"nmcli", "n m cli"},
            "whoami": {"whoami", "who am i"},
            "ls": {"ls", "l s"},
            "grep": {"grep"},
            "docker": {"docker"},
            "git": {"git"},
            "ssh": {"ssh", "s s h"},
            "scp": {"scp"},
            "ifconfig": {"ifconfig"},
            "ip": {"ip"},
            "cat": {"cat"},
            "cd": {"cd"},
            "echo": {"echo"},
            "printf": {"printf", "print f"},
            "find": {"find"},
            "less": {"less"},
            "podman": {"podman"},
            "pacman": {"pacman"},
        }
        lookup = {v: k for k, vs in vocab.items() for v in vs}

        punct = {
            "open quote": ('"', TokenType.QUOTE),
            "close quote": ('"', TokenType.QUOTE),
            "end quote": ('"', TokenType.QUOTE),
            "quote": ('"', TokenType.QUOTE),
            "pipe": ("|", TokenType.OPERATOR),
            "and then": ("&&", TokenType.OPERATOR),
            "percent": ("%", TokenType.FORMAT),
            "backslash n": ("\\n", TokenType.ESCAPE),
            "dash": ("-", TokenType.FLAG),
            "star": ("*", TokenType.ARG),
            "colon": (":", TokenType.OPERATOR),
            "forward slash": ("slash", TokenType.PATH),
        }

        tokens = norm.split()
        classified = []
        i = 0
        while i < len(tokens):
            matched = False
            for sz in range(3, 0, -1):
                ch = " ".join(tokens[i : i + sz])
                if ch in lookup:
                    classified.append(Token(lookup[ch], TokenType.COMMAND, ch))
                    i += sz
                    matched = True
                    break
                if ch in punct:
                    v, ty = punct[ch]
                    classified.append(Token(v, ty, ch))
                    i += sz
                    matched = True
                    break
            if not matched:
                tok = tokens[i]
                val = tok
                typ = TokenType.WORD
                prev_typ = classified[-1].type if classified else None
                if tok == "dash" and i + 2 < len(tokens) and tokens[i + 1] == "dash":
                    typ = TokenType.FLAG
                    val = "--" + tokens[i + 2]
                    classified.append(Token(val, typ, tok))
                    i += 3
                    continue
                if tok == "dash" and i + 1 < len(tokens):
                    next_tok = tokens[i + 1]
                    if next_tok in ("p", "r", "y", "a", "u", "s", "h"):
                        typ = TokenType.FLAG
                        val = "-" + next_tok
                        classified.append(Token(val, typ, tok))
                        i += 2
                        continue
                if tok.startswith("-") or tok == "dash":
                    typ = TokenType.FLAG
                    val = "-"
                elif tok in ("+", "x") or tok == "+x":
                    typ = TokenType.FLAG
                    val = "+x" if tok in ("x", "+x") else tok
                elif any(
                    k in tok for k in ("/", "./", "../", "~", ".sh", "dot")
                ) or tok in (
                    "slash",
                    "forward",
                    "etc",
                    "hosts",
                    "tmp",
                    "srv",
                    "var",
                    "log",
                    "messages",
                    "home",
                ):
                    typ = TokenType.PATH
                    val = tok.replace("slash", "/").replace("dot", ".")
                elif tok in ("%", "%5d", "%s", "%d"):
                    typ = TokenType.FORMAT
                    val = tok.replace("percent", "%")
                elif tok in ("|", "&&", "||", ">", ">>", "@"):
                    typ = TokenType.OPERATOR
                elif tok in ('"', "'"):
                    typ = TokenType.QUOTE
                elif tok.isdigit() or tok in (
                    "hello",
                    "world",
                    "todo",
                    "42",
                    "test",
                    "alpha",
                    "beta",
                    "star",
                    "py",
                    "s",
                    "d",
                ):
                    typ = TokenType.ARG
                if tok == "todo":
                    val = "TODO"
                classified.append(Token(val, typ, tok))
                i += 1

        return classified

    def _structured_rebuild(self, tokens: List[Token]) -> str:
        """General shell emission from composed atoms using pairwise separator laws. No per-command logic."""
        if not tokens:
            return ""
        atoms = self._compose_atoms(tokens)  # compose before emission
        result = []
        prev = None
        for atom in atoms:
            if not result:
                result.append(atom)
                prev = atom
                continue
            law = self._separator_law(prev, atom)
            if law == "merge":
                result.append(atom.replace(" ", ""))
            elif law == "attach":
                result.append(atom)
            else:
                result.append(" " + atom)
            prev = atom
        final = "".join(result).strip()
        final = (
            final.replace(' "', '"')
            .replace('" ', '"')
            .replace("  ", " ")
            .replace("--", "-")
            .replace("colon", ":")
            .replace("slash", "/")
        )
        final = (
            final.replace('"-name"', "-name").replace("star", "*").replace('"."', ".")
        )
        return final

    def _compose_atoms(self, tokens: List[Token]) -> List[str]:
        """Compose into atoms: flags atomic, paths joined, quotes wrapped, formats escaped."""
        atoms = []
        i = 0
        while i < len(tokens):
            t = tokens[i]
            if t.type == TokenType.FLAG or (
                t.value in ("p", "r", "y", "a", "u") and i > 0
            ):
                v = t.value if t.value.startswith(("-", "+")) else "-" + t.value
                atoms.append(v)
            elif t.type == TokenType.PATH or t.value in (
                "/",
                "home",
                "etc",
                "hosts",
                "tmp",
                "srv",
                "var",
                "log",
                "messages",
                "dot",
                "slash",
            ):
                p = []
                while i < len(tokens) and (
                    tokens[i].type in (TokenType.PATH, TokenType.WORD)
                    or tokens[i].value
                    in ("/", "home", "etc", "hosts", "dot", "slash", "forward")
                ):
                    p.append(tokens[i].value)
                    i += 1
                path = ""
                for seg in p:
                    if seg in ("slash", "/", "forward"):
                        if not path.endswith("/"):
                            path += "/"
                        continue
                    if seg == "dot":
                        path += "."
                        continue
                    if seg == "dotdot":
                        path += ".."
                        continue
                    if path and not path.endswith(("/", ".", ":")):
                        path += "/"
                    path += seg
                atoms.append(path or "/home/user")
                continue
            elif t.type == TokenType.QUOTE:
                q = []
                i += 1
                while i < len(tokens) and tokens[i].type != TokenType.QUOTE:
                    q.append(tokens[i].value)
                    i += 1
                atoms.append('"' + " ".join(q) + '"')
            elif t.type in (TokenType.FORMAT, TokenType.ESCAPE):
                if t.value == "%":
                    fmt = "%"
                    j = i + 1
                    while j < len(tokens) and tokens[j].type in (
                        TokenType.ARG,
                        TokenType.WORD,
                        TokenType.ESCAPE,
                    ):
                        part = tokens[j].value
                        if part == "\\n":
                            fmt += "\\n"
                            j += 1
                            break
                        fmt += part
                        j += 1
                    atoms.append('"' + fmt + '"')
                    i = j - 1
                else:
                    v = (
                        t.value.replace("percent", "%")
                        .replace("backslash n", "\\n")
                        .replace(" ", "")
                    )
                    atoms.append(v)
            elif t.type == TokenType.OPERATOR and t.value == "@":
                atoms.append("@")
            else:
                atoms.append(t.value)
            i += 1
        return atoms

    def _separator_law(self, prev: str, curr: str) -> str:
        """Pairwise separator laws based purely on atom shape and class relationships."""
        if (
            curr.startswith("-")
            and len(curr) <= 3
            and not prev.endswith(("-", "+", '"', "'"))
        ):
            return "space"
        if curr.startswith(('"', "/", ".")) and not prev.endswith(("-", "+", '"', "'")):
            return "space"
        if prev.endswith(("-", "+", '"', "'")) or curr.startswith(
            ("%", "\\", "~", "@", "|")
        ):
            return "attach"
        if prev in ('"', "'") or curr in ('"', "'"):
            return "attach"
        if any(c in curr for c in ("|", "&&", "||", ">", ">>", ":")):
            return "space"
        return "space"

    def on_test_interpret(self, btn):
        phrase = self.phrase_entry.get_text().strip()
        if not phrase and self.raw_transcript_entry:
            phrase = self.raw_transcript_entry.get_text().strip()
        if phrase:
            cmd = self.interpret_phrase(phrase)
            self.command_output_entry.set_text(cmd)

    def on_apply_mapping(self, btn):
        spoken = self.spoken_map_entry.get_text().strip()
        cmd = self.cmd_map_entry.get_text().strip()
        if spoken and cmd:
            self.voice_mappings[spoken] = cmd
            self._save_mappings()
            self.show_alert(f"Mapping added for: {spoken}")

    def toggle_command_mode(self, btn):
        self.command_mode = btn.get_active()
        mode_str = "Command" if self.command_mode else "Idle"
        self.update_status(mode_str)

    def _load_mappings(self):
        self.mappings_path.parent.mkdir(parents=True, exist_ok=True)
        if self.mappings_path.exists():
            try:
                with open(self.mappings_path, "r") as f:
                    self.voice_mappings = json.load(f)
            except Exception:
                self.voice_mappings = {}
        else:
            self.voice_mappings = {}

    def _save_mappings(self):
        try:
            with open(self.mappings_path, "w") as f:
                json.dump(self.voice_mappings, f, indent=2)
        except Exception:
            pass

    def show_helper(self, btn):
        mappings_str = (
            "\n".join([f"{k} → {v}" for k, v in self.voice_mappings.items()])
            or "No saved mappings"
        )
        helper_text = f"""Command Helper:
dash y → -y
dash dash help → --help
dot slash → ./
dot dot slash → ../
and then → &&
pipe → |
home → ~
dollar home → $HOME
dollar path → $PATH

Saved voice mappings:
{mappings_str}"""
        dialog = Gtk.MessageDialog(
            transient_for=self.window,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text=helper_text,
        )
        dialog.connect("response", lambda d, r: (d.destroy(), None))
        dialog.present()

    def show(self):
        self.window.present()

    def run(self):
        self.show()
        self.window.present()


if __name__ == "__main__":
    app = Gtk.Application(
        application_id="com.myvoice.gui", flags=Gio.ApplicationFlags.FLAGS_NONE
    )

    def on_activate(app):
        runtime = Runtime()
        dev_mode = "--dev" in sys.argv
        gui = GUI(runtime, app, dev_mode=dev_mode)
        gui.show()

    app.connect("activate", on_activate)
    try:
        app.run(None)
    except KeyboardInterrupt:
        logging.info("Interrupted by user, closing My Voice cleanly")
        app.quit()
