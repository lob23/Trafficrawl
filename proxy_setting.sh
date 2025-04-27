#!/bin/bash

IP=$(ipconfig getifaddr en0 || hostname -I | awk '{print $1}')
PORT=8080

echo "Waiting for emulator to be ready..."
adb wait-for-device

BOOT_COMPLETED=""
until [[ "$BOOT_COMPLETED" == "1" ]]; do
    BOOT_COMPLETED=$(adb shell getprop sys.boot_completed 2>/dev/null | tr -d '\r')
    sleep 1
done
echo "Emulator fully booted."

echo "Setting proxy to $IP:$PORT"
adb shell settings put global http_proxy $(ipconfig getifaddr en0):8080
adb shell settings put global https_proxy $(ipconfig getifaddr en0):8889
echo "Setting proxy to $IP:$PORT successfully"