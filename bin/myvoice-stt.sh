#!/bin/bash
# My Voice STT hotkey wrapper (Super+W)

HOME_MYVOICE="$HOME/my-voice"
if [ -d "$HOME_MYVOICE" ]; then
  cd "$HOME_MYVOICE"
  dbus-send --session --dest=com.myvoice.Service /com/myvoice/service com.myvoice.Service.start_recording int32:15
else
  notify-send "My Voice" "Not in ~/my-voice"
fi