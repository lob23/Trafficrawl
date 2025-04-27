# Trafficrawl

## I. Introduction:
This repository provides a lightweight tool to capture HTTP(S) requests from Android applications using mitmproxy. The captured requests are filtered using EasyList and EasyPrivacy rules to identify advertisement and tracker requests, helping to reveal potential privacy threats within the APK. It is up-to-date and handles certificate pinning (using Frida) as well as the untrusted user certificate issue introduced in Android 7.0 (API level 24).

## ⚠️ Warning

> **The current version only supports macOS.**  
> Support for other operating systems (like Windows or Linux) will be added later based on user requests.


## II. Prequisite:
### 1. Android Studio Emulator:

You should have at least one emulator available before running the tool. The emulator must be rooted. 
- If your emulator is created using a "Google APIs" system image, it is already rooted by default. 
- However, if it is created from a "Google Play" or other system images, you will need to manually root the emulator and manually install the mitmproxy certificate. For guidance on installing the mitmproxy certificate manually, you can refer to the mitmproxy's official documentation: https://docs.mitmproxy.org/stable/howto-install-system-trusted-ca-android/#3-insert-certificate-into-system-certificate-store.

### 2. Installed Tools
You should have these tools in your device
- `adb` (Android Debug Bridge) available in your PATH. Checking by `adb version`
- `openssl` (for certificate hash generation). Checking by `openssl version`
- `wget` or `curl` (for downloading frida-server). Checking by `wget --version` or `curl --version`.
- `unxz` (for extracting frida server file). Checking by `unxz version`

### 3. Python Environment:
- python3 is required. Checking by `python --version`. Note that in some cases, your python is specified by different name, such as `python3`.

## III. Implementations:
- `./download_easylist.sh`: Preparing the EasyList block lists by running. This script downloads two lists are EasyList and EasyPrivacy.
- `./run_emulator.sh`: Starting the emulator (we assume you have created a rooted emulator already). 
- `./verify.sh`: This script will check if your emulator is rooted already.
- `./install_certificate.sh`: Installing the mitmproxy's certificate to the system directory of the emulator. 
- `./proxy_setting.sh`: Set the proxy for the emulator by running. This script configures the emulator to route all network requests through mitmproxy before reaching the Internet.

## IV. Usage
### Step 0: Check Script Permissions
- Make sure all `.sh` scripts in the repository have permission to run.
- Run `ls -l` to check. Each script should show `-rwxr-xr-x`.
- If not, add execute permission by running the following command for all files in the repo:
```
chmod +x <filename>.sh
```

### Step 1: Start the Emulator
- Run:
```
./run_emulator.sh
```
- This script will keep running and display the emulator status.
- As soon as you see the emulator homescreen, you can move to the next step without waiting for this script.

### Step 2: Set Up the Environment
- Run:
```
./setup.sh
```
- This will verify the emulator and install the required certificate.

>**Important:** If you use the "Google Play" or other system images that did not rooted by default, you have to do this step manually by following the tutorial at https://docs.mitmproxy.org/stable/howto-install-system-trusted-ca-android/#3-insert-certificate-into-system-certificate-store and skip running this script.

### Step 3: Install the APK
- Install the APK via a browser inside the emulator (like Chrome) or drag-and-drop your .apk file directly into the emulator window.

### Step 4: Start Capturing Traffic
- Run
```
./execution <PACKAGE_NAME>
```
Replace <PACKAGE_NAME> with the actual app's package name (example: vn.frt.longchau.app).

### Step 5: Interact with the app
- When you see: `"The capturing is ready for capture network traffic"`, you can now manually use the app.
- All network traffic will be automatically recorded.

### Step 6: Finish and Save Results
- When you are done:

    1. Close the app inside the emulator (swipe up the emulator to kill the app process).
    2. The traffic log will be saved in the results/ folder.
    File format: request_log_<PACKAGE_NAME>.jsonl
    Example: request_log_vn.frt.longchau.app.jsonl
    > **Note:**
    The new traffic will be added to the existing file.
    If you want a fresh capture, delete the old log file first.

### Step 7: Test More Apps
- If you want to capture traffic for another app, install the new APK and repeat from **Step 4**.

### Step 8: Stop the Emulator
- After you are finished with all testing, stop the emulator and clean up by running:
```
./stop_emulator.sh
```

## V. Results Analysis:
- The result is stored in jsonl file capture all fields of HTTP requests with the following key structure:
    - `timestamp`: The time the request was captured, including microseconds. For example, `"timestamp": "2025-04-27T20:08:56.775210"`.
    - `url`: The destination URL where the request is sent.
    - `decode_method`: The method used to decode the request body. Possible values include: gzip, utf-8, latin1, or as a fallback, base64-encoded binary.
    - `method`: The HTTP method used, such as POST, GET, etc.
    - `headers`: The HTTP request headers.
    - `request_body`: The content/body of the HTTP request.
    - `option`: The matching rule or modifier applied from EasyList or EasyPrivacy.
    - `action`: The result of the rule matching — typically BLOCKED or ALLOWED.

- You can use the visualization.py script to generate a visualization showing the percentage of BLOCKED requests in your captured dataset.

## VI. Conclusion:
In this work, we developed a lightweight tool that acts as a proxy to capture network traffic from Android applications. By leveraging EasyList and EasyPrivacy, the captured traffic is analyzed to detect advertisements and trackers, providing practical insights into the privacy behaviors of applications. We hope that our tool will support the research community, particularly in the areas of Android application security and privacy.

## VII. References:
[1] Epitron, "mitm-adblock," GitHub, [Online]. Available: https://github.com/epitron/mitm-adblock.
[2] Akabe1, "frida-multiple-unpinning," Codeshare by Frida, [Online]. Available: https://codeshare.frida.re/@akabe1/frida-multiple-unpinning/.
[3] EasyList, "EasyList" [Online]. Available:https://easylist.to/easylist/easylist.txt. 
[4] EasyList, "EasyPrivacy" [Online]. Available: https://easylist.to/easylist/easyprivacy.txt.