#!/usr/bin/env python3
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
from gi.repository import Gtk, Gdk, GLib, Gio
import subprocess
import requests
import threading


class PrefsDialog(Gtk.Dialog):
    def __init__(self, parent):
        super().__init__(title="Preferences", transient_for=parent, modal=True)
        self.set_default_size(300, 200)

        box = self.get_content_area()
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.append(vbox)

        self.url_entry = Gtk.Entry()
        self.url_entry.set_placeholder_text("https://example.com")
        vbox.append(Gtk.Label(label="Remote URL (HTTPS only):"))
        vbox.append(self.url_entry)

        self.voice_combo = Gtk.ComboBoxText()
        self.voice_combo.append_text("Default CPU (eSpeak)")
        self.voice_combo.append_text("Qwen3-TTS (GPU)")
        self.voice_combo.append_text("Remote")
        self.voice_combo.set_active(0)
        vbox.append(Gtk.Label(label="Voice:"))
        vbox.append(self.voice_combo)

        test_btn = Gtk.Button(label="Test Endpoint")
        test_btn.connect("clicked", self.test_endpoint)
        vbox.append(test_btn)

        self.add_buttons("Close", Gtk.ResponseType.CLOSE)
        self.connect("response", lambda d, r: d.close())

    def test_endpoint(self, btn):
        url = self.url_entry.get_text().strip()
        if not url.startswith("https://"):
            self.url_entry.get_style_context().add_class("error")
            return

        def check():
            try:
                r = requests.get(url, timeout=5)
                GLib.idle_add(self.on_success)
            except:
                GLib.idle_add(self.on_fail)

        threading.Thread(target=check, daemon=True).start()

    def on_success(self, *args):
        dialog = Gtk.MessageDialog(
            self,
            0,
            Gtk.MessageType.INFO,
            Gtk.ButtonsType.OK,
            "HTTPS endpoint responsive!",
        )
        dialog.run()
        dialog.destroy()

    def on_fail(self, *args):
        dialog = Gtk.MessageDialog(
            self,
            0,
            Gtk.MessageType.ERROR,
            Gtk.ButtonsType.OK,
            "Failed: Non-HTTPS or unresponsive.",
        )
        dialog.run()
        dialog.destroy()


class VoicePuck(Gtk.Window):
    def __init__(self):
        super().__init__(title="My Voice", default_width=200, default_height=100)
        self.set_decorated(False)
        self.set_can_focus(True)

        # CSS
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(b"""
            window { background: #f0f0f0; border-radius: 50px; padding: 10px; }
            window.high-contrast { background: #000; color: #fff; }
            label { font-weight: bold; font-size: 14px; }
            progress { margin: 5px; }
            .error { border-color: red; background: #ffe6e6; }
            .write { color: #228B22; }
            .read { color: #4169E1; }
        """)
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

        self.mode = "Idle"
        self.is_write = False
        self.high_contrast = False
        self.progress = Gtk.ProgressBar(visible=False, margin_top=5, margin_bottom=5)

        self.label = Gtk.Label(
            label=self.mode, halign=Gtk.Align.CENTER, margin_top=10, margin_bottom=5
        )

        hamburger = Gtk.MenuButton(icon_name="open-menu-symbolic", has_frame=False)
        menu_popover = Gtk.Popover()
        hamburger.set_popover(menu_popover)
        menu_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        menu_box.set_margin_start(6)
        menu_box.set_margin_end(6)
        menu_box.set_margin_top(6)
        menu_box.set_margin_bottom(6)
        menu_popover.set_child(menu_box)

        record_btn = Gtk.Button(label="Record (15s STT)")
        record_btn.connect("clicked", self.on_record)
        read_btn = Gtk.Button(label="Read Selection (TTS)")
        read_btn.connect("clicked", self.on_read)
        verbose_btn = Gtk.ToggleButton(label="Verbose")
        test_audio_btn = Gtk.Button(label="Test TTS")
        test_audio_btn.connect("clicked", self.test_tts)
        toggle_contrast_btn = Gtk.Button(label="High Contrast")
        toggle_contrast_btn.connect("clicked", self.toggle_contrast)
        prefs_btn = Gtk.Button(label="Preferences")
        prefs_btn.connect("clicked", self.open_prefs)

        menu_box.append(record_btn)
        menu_box.append(read_btn)
        menu_box.append(verbose_btn)
        menu_box.append(test_audio_btn)
        menu_box.append(toggle_contrast_btn)
        menu_box.append(prefs_btn)

        main_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=5,
            halign=Gtk.Align.FILL,
            valign=Gtk.Align.CENTER,
        )
        main_box.append(self.label)
        main_box.append(self.progress)

        overlay = Gtk.Overlay()
        overlay.set_child(main_box)
        overlay.add_overlay(hamburger)
        self.set_child(overlay)

        self.connect("realize", self.on_realize)
        self.connect("button-press-event", self.on_button_press)

    def on_realize(self, widget):
        self.present()
        display = self.get_display()
        if display.get_name() == "wayland":
            print("Running on Wayland")

    def on_button_press(self, widget, event):
        if (
            event.type == Gdk.EventType._2BUTTON_PRESS
            and event.button == Gdk.BUTTON_PRIMARY
        ):
            # Double-click popover already in hamburger, stub
            self.show_progress()
        elif event.button == Gdk.BUTTON_PRIMARY:
            self.toggle_mode()
        return Gdk.EVENT_STOP

    def toggle_mode(self):
        self.is_write = not self.is_write
        self.mode = "Write" if self.is_write else "Read"
        self.label.set_label(self.mode)
        ctx = self.label.get_style_context()
        ctx.remove_class("read")
        ctx.remove_class("write")
        ctx.add_class("write" if self.is_write else "read")

    def test_tts(self, btn):
        if self.proxy:
            self.proxy.call_sync(
                "speak",
                GLib.Variant("s", "Test TTS via service."),
                Gio.DBusCallFlags.NONE,
                -1,
                None,
            )
        else:
            self.test_local_tts("Test TTS local.")

    def test_local_tts(self, text):
        try:
            subprocess.Popen(
                ["espeak-ng", text],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            self.show_progress(2)
        except FileNotFoundError:
            print("Install espeak-ng")

    def toggle_contrast(self, btn):
        self.high_contrast = not self.high_contrast
        ctx = self.get_style_context()
        if self.high_contrast:
            ctx.add_class("high-contrast")
        else:
            ctx.remove_class("high-contrast")

    def on_record(self, btn):
        if self.proxy:
            self.show_progress(20)  # ~15s record + process
            self.proxy.call_sync(
                "start_recording",
                GLib.Variant("i", 15),
                Gio.DBusCallFlags.NONE,
                -1,
                None,
            )
        else:
            print("Service not running")

    def on_read(self, btn):
        if self.proxy:
            try:
                sel_var = self.proxy.call_sync(
                    "get_selection",
                    None,
                    Gio.DBusCallFlags.NONE,
                    -1,
                    None,
                )
                sel = sel_var.get_child_value(0).get_string()
                if sel:
                    self.proxy.call_sync(
                        "speak",
                        GLib.Variant("s", sel),
                        Gio.DBusCallFlags.NONE,
                        -1,
                        None,
                    )
                    self.show_progress(10)
            except Exception as e:
                print(f"Read error: {e}")
        else:
            print("Service not running")

    def open_prefs(self, btn):
        dialog = PrefsDialog(self)
        dialog.present()

    def show_progress(self, duration=3):
        self.progress.set_visible(True)
        self.progress.pulse()
        GLib.timeout_add(duration * 1000, self.hide_progress)

    def hide_progress(self):
        self.progress.set_visible(False)
        return False


def main():
    app = Gtk.Application(
        application_id="com.myvoice.puck", flags=Gio.ApplicationFlags.FLAGS_NONE
    )
    app.connect("activate", lambda app: VoicePuck().present())
    return app.run(None)


if __name__ == "__main__":
    exit(main())
