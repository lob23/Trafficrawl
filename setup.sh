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

echo "Install mitmproxy's certificate succeeded. Continuing..."


bash src/proxy_setting.sh

if [ $? -ne 0 ]; then
    echo "Setting proxy failed. Exiting..."
    exit 1
fi

echo "Setting proxy succeeded."
echo "Setup is complete. Your emulator is now ready to capture network traffic."

