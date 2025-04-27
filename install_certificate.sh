#!/bin/bash

IP=$(ipconfig getifaddr en0 || hostname -I | awk '{print $1}')
PORT=8080

echo "Waiting for emulator to be ready..."
adb wait-for-device

# Ensure Android system is fully booted
BOOT_COMPLETED=""
until [[ "$BOOT_COMPLETED" == "1" ]]; do
    BOOT_COMPLETED=$(adb shell getprop sys.boot_completed 2>/dev/null | tr -d '\r')
    sleep 1
done
echo "Emulator fully booted."

adb root
sleep 1

echo "Starting mitmproxy..."
mitmdump &
MITMPROXY_PID=$!

echo "Waiting for mitmproxy certificate to be generated..."
while [ ! -f "$HOME/.mitmproxy/mitmproxy-ca-cert.pem" ]; do
    sleep 1
done

echo "Certificate generated!"

echo "Stopping mitmproxy..."
kill $MITMPROXY_PID

cp ~/.mitmproxy/mitmproxy-ca-cert.pem mitmproxy-ca-cert.cer

hashed_name=`openssl x509 -inform PEM -subject_hash_old -in mitmproxy-ca-cert.cer | head -1` && cp mitmproxy-ca-cert.cer $hashed_name.0

adb shell avbctl disable-verification
adb reboot

echo "Waiting for emulator after reboot..."
adb wait-for-device

BOOT_COMPLETED=""
until [[ "$BOOT_COMPLETED" == "1" ]]; do
    BOOT_COMPLETED=$(adb shell getprop sys.boot_completed 2>/dev/null | tr -d '\r')
    sleep 1
done
echo "Emulator rebooted and fully booted."

adb root
adb remount

# Check if /system is writable
MOUNT_MODE=$(adb shell mount | grep ' /system ')
if [[ "$MOUNT_MODE" != *"rw"* ]]; then
    echo "System partition is not writable!"
    exit 1
fi

echo "Pushing certificate to /system/etc/security/cacerts/"

adb push ${hashed_name}.0 /system/etc/security/cacerts
adb shell chmod 664 /system/etc/security/cacerts/${hashed_name}.0
adb reboot

echo "Certificate installed successfully. Emulator is ready!"
