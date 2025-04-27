#!/bin/bash

echo "Checking the existed emulator"
AVD_LIST=$($ANDROID_HOME/emulator/emulator -list-avds)

if [ -z "$AVD_LIST" ]; then
    echo "No emulator found"
    echo "Please create one manually using Android Studio or avdmanager."
    exit 1
fi  # <<< You forgot this 'fi'

echo "Available emulators:"
echo "$AVD_LIST"
echo ""

IFS=$'\n' read -rd '' -a AVD_ARRAY <<<"$AVD_LIST"
if [ "${#AVD_ARRAY[@]}" -eq 1 ]; then
    EMULATOR_NAME="${AVD_ARRAY[0]}"
    echo "Only one emulator found: $EMULATOR_NAME. Starting it automatically..."
else
    read -p "Enter the emulator name you want to start (must be a rooted emulator created with 'Google APIs' system image): " EMULATOR_NAME

    if [[ ! " ${AVD_ARRAY[@]} " =~ " ${EMULATOR_NAME} " ]]; then
        echo "Emulator '$EMULATOR_NAME' not found in the available list."
        exit 1
    fi
fi

echo "Starting emulator: $EMULATOR_NAME"
$ANDROID_HOME/emulator/emulator @$EMULATOR_NAME -writable-system -no-snapshot-load -no-boot-anim -accel on &

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
