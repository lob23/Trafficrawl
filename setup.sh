#!/bin/bash

if [ ! -d "easylist" ]; then
    echo "Folder 'easylist' not found"
    bash src/download_easylist.sh
fi

bash src/verify.sh

if [ $? -ne 0 ]; then
    echo "Verification failed. Exiting..."
    exit 1
fi

echo "Verification succeeded. Continuing..."

bash src/install_certificate.sh

if [ $? -ne 0 ]; then
    echo "Install mitmproxy's certificate failed. Exiting..."
    exit 1
fi

echo "Waiting for emulator to be ready..."
adb wait-for-device

BOOT_COMPLETED=""
until [[ "$BOOT_COMPLETED" == "1" ]]; do
    BOOT_COMPLETED=$(adb shell getprop sys.boot_completed 2>/dev/null | tr -d '\r')
    sleep 1
done
echo "Emulator fully booted."

echo "Install mitmproxy's certificate succeeded."
echo "Setup is complete. Your emulator is now ready to capture network traffic."

