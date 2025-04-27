#!/bin/bash

echo "Waiting for emulator to boot..."
adb wait-for-device

BOOT_COMPLETED=""
until [[ "$BOOT_COMPLETED" == "1" ]]; do
    BOOT_COMPLETED=$(adb shell getprop sys.boot_completed 2>/dev/null | tr -d '\r')
    sleep 1
done

echo "Emulator booted!"

echo "Checking if emulator is rooted..."
adb root >/dev/null 2>&1

if [ $? -ne 0 ]; then
    echo "Emulator is NOT rooted. Please use an emulator created with a 'Google APIs' system image."
    exit 1
fi

echo "The emulator is good to continue."
