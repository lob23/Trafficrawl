FRIDA_VERSION="16.5.9"
ARCH="arm64"

if [ ! -f "frida-server-${FRIDA_VERSION}-android-${ARCH}" ]; then
    echo "Downloading frida-server..."
    wget https://github.com/frida/frida/releases/${FRIDA_VERSION}/frida-server-${FRIDA_VERSION}-android-${ARCH}.xz

    echo "Extracting frida-server..."
    unxz frida-server-${FRIDA_VERSION}-android-${ARCH}.xz
    chmod +x frida-server-${FRIDA_VERSION}-android-${ARCH}
fi

echo "Pushing frida-server to emulator..."
adb push frida-server-${FRIDA_VERSION}-android-${ARCH} /data/local/tmp/frida-server

adb shell "chmod 755 /data/local/tmp/frida-server"

echo "Starting frida-server inside emulator..."
adb shell "/data/local/tmp/frida-server &"

echo "Frida-server setup completed."
