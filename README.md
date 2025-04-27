# Trafficrawl

## I. Introduction:
This repository provides a lightweight tool to capture HTTP(S) requests from Android applications using mitmproxy. It is up-to-date and handles certificate pinning (using Frida) as well as the untrusted user certificate issue introduced in Android 7.0 (API level 24).

> ⚠️ **Warning:** The current version only supports macOS.  
> Support for other operating systems will be added later if requested.

## II. Prequisite:
### 1. Android Studio Emulator:

You should have at least one emulator available before running the tool. The emulator must be rooted. 
- If your emulator is created using a "Google APIs" system image, it is already rooted by default. 
- However, if it is created from a "Google Play" or other system images, you will need to manually root the emulator and manually install the mitmproxy certificate. For guidance on installing the mitmproxy certificate manually, you can refer to the mitmproxy's official documentation: https://docs.mitmproxy.org/stable/howto-install-system-trusted-ca-android/#3-insert-certificate-into-system-certificate-store.

### 2. Installed Tools
You should have these tools in your device
- adb (Android Debug Bridge) available in your PATH. Checking by `adb version`
- openssl (for certificate hash generation). Checking by `openssl version`
- wget or curl (for downloading frida-server). Checking by `wget --version` or `curl --version`.

### 3. Python Environment:
- python3 is required. Checking by `python --version`. Note that in some cases, your python is specified by different name, such as `python3`.

## III. Usage:
- Verify all the shell scripts in the repository has permissions to run. Specifically, using the command `ls -l` to see if all the scripts are have executed permission `-rwxr-xr-x`. If not, using `chmod +x` for each file.
- Starting the emulator (we assume you have created a rooted emulator already) by `./run_emulator.sh`. This script will not finish but keep showing the status of the emulator runtime, so that you can move to the next step when you see the emulator is shown the home screen. 
- Verify if the emulator is matched the criteria to continue by `./verify.sh`. This script will check if your emulator is rooted already.
- Installing the mitmproxy's certificate to the system directory of the emulator by `./install_certificate.sh`. **Important Note: If you use the "Google Play" or other system images that did not rooted by default, you have to do this step manually by following the tutorial at https://docs.mitmproxy.org/stable/howto-install-system-trusted-ca-android/#3-insert-certificate-into-system-certificate-store and skip running this script.**
- At this step, you can install APKPure from Google Chrome (or any other web browser available on the emulator). You can then use APKPure to install any applications you want to investigate for network traffic. Alternatively, if you already have an APK file, you can simply drag and drop it into the emulator to install.

    **Important: Please wait until all applications are fully installed before proceeding to the next steps. Once the proxy is set, the emulator will only be able to access the Internet if mitmproxy is running.**

- Set the proxy for the emulator by running `./proxy_setting.sh`. This script configures the emulator to route all network requests through mitmproxy before reaching the Internet.
