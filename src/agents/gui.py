import gi
import logging
import os
import subprocess
import threading
import tempfile
from pathlib import Path

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
from gi.repository import Gio, GLib, Gtk, Gdk

from src.agents.hotkeys import HotkeyListener
from src.agents.stt import create_stt
from src.runtime.runtime import Runtime

logging.basicConfig(level=logging.INFO)


class GUI:
    def __init__(self, runtime, app=None):
        self.runtime = runtime
        self._busy = False
        self._tts_process = None
        self.read_btn = None
        self.record_btn = None
        self.recording_proc = None
        self.recording_audio = None
        self.stt_engine = os.getenv("MYVOICE_STT_ENGINE", "vosk").upper()
        self.tts_engine = "eSpeak"
        self.duration_timer = None
        self.current_duration = 0
        self.current_state = "Idle"
        self.window = Gtk.Window(title="My Voice", application=app)
        self.window.set_default_size(420, 480)
        self.window.connect("close-request", self.on_close_request)

        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(b"""
            .recording-dot { color: #d32f2f; font-size: 18px; }
            .status-box { background: #fafafa; padding: 6px; border-radius: 4px; }
            .transcript-panel { background: #fafafa; border: 1px solid #e0e0e0; border-radius: 6px; }
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
        menu_box.append(prefs_btn)
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

        status_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        status_box.add_css_class("status-box")
        self.recording_dot = Gtk.Label(label="●", halign=Gtk.Align.START)
        self.recording_dot.add_css_class("recording-dot")
        self.recording_dot.set_visible(False)
        self.state_label = Gtk.Label(label="State: Idle", halign=Gtk.Align.START)
        self.stt_label = Gtk.Label(
            label=f"STT: {self.stt_engine}", halign=Gtk.Align.START
        )
        self.duration_label = Gtk.Label(label="Duration: 00:00", halign=Gtk.Align.START)
        status_box.append(self.recording_dot)
        status_box.append(self.state_label)
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

        transcript_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        transcript_label = Gtk.Label(label="Transcript", halign=Gtk.Align.START)
        self.scrolled = Gtk.ScrolledWindow()
        self.scrolled.set_min_content_height(150)
        self.scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.transcript_view = Gtk.TextView()
        self.transcript_view.set_wrap_mode(Gtk.WrapMode.WORD)
        self.transcript_view.set_editable(False)
        self.transcript_view.set_cursor_visible(False)
        self.scrolled.set_child(self.transcript_view)
        self.scrolled.add_css_class("transcript-panel")
        transcript_box.append(transcript_label)
        transcript_box.append(self.scrolled)
        main_box.append(transcript_box)

        footer = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL, spacing=0, margin_top=12
        )
        self.hotkey_label = Gtk.Label(
            label="Super+W: Record | Super+R: Read", halign=Gtk.Align.CENTER
        )
        footer.append(self.hotkey_label)
        main_box.append(footer)

        self.window.set_child(main_box)
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
            self.recording_dot.set_visible(True)
        else:
            self.recording_dot.set_visible(False)
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
            create_stt(self.runtime)
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
        display_text = text.strip()
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
                stt = create_stt(self.runtime)
                text = stt.transcribe(str(self.recording_audio))
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
            stt = create_stt(self.runtime)
            text = stt.transcribe()
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
            text=msg[:300],  # truncate long error messages
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
        gui = GUI(runtime, app)
        gui.show()

    app.connect("activate", on_activate)
    try:
        app.run(None)
    except KeyboardInterrupt:
        logging.info("Interrupted by user, closing My Voice cleanly")
        app.quit()
