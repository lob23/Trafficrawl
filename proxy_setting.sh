#!/bin/bash

# Get local IP (works for Linux/Mac)
IP=$(ipconfig getifaddr en0 || hostname -I | awk '{print $1}')
# Port where mitmproxy will listen
PORT=8080

echo "Setting proxy to $IP:$PORT"
adb shell settings put global http_proxy $(ipconfig getifaddr en0):8080
adb shell settings put global https_proxy $(ipconfig getifaddr en0):8889