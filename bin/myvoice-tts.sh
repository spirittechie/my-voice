#!/bin/bash
# My Voice TTS hotkey wrapper (Super+R)

HOME_MYVOICE="$HOME/my-voice"
if [ -d "$HOME_MYVOICE" ]; then
  cd "$HOME_MYVOICE"
  text=$(wl-paste 2>/dev/null || xsel -p 2>/dev/null || xclip -selection primary -o 2>/dev/null)
  text=$(echo "$text" | head -c 500 | tr -d '\n\r')
  if [ -n "$text" ]; then
    dbus-send --session --dest=com.myvoice.Service /com/myvoice/service com.myvoice.Service.speak string:"$text"
  else
    notify-send "My Voice" "No selection"
  fi
else
  notify-send "My Voice" "Not in ~/my-voice"
fi