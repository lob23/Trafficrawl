import shutil
import subprocess
import sys
import importlib

REQUIRE_COMMANDS = ['wget', 'adb', 'python3', 'unxz', 'openssl', 'emulator']
REQUIRE_PACKAGES = ['re2', 'iso3166', 'publicsuffix2', 'tldextract', 'mitmproxy', 'adblockparser']
MIN_PYTHON_VERSION = (3, 8)

def check_python_version():
    if sys.version_info < MIN_PYTHON_VERSION:
        print(f"python version {sys.version_info.major}.{sys.version_info.minor} is not supported. Please use Python {MIN_PYTHON_VERSION[0]}.{MIN_PYTHON_VERSION[1]} or higher.")
        return False
    return True

def check_command(command):
    return shutil.which(command) is not None 

def check_emulator_installed():
    try:
        result = subprocess.run(['emulator', '-list-avds'], capture_output=True, text=True)
        return result.returncode == 0 and result.stdout.strip() != ""
    except Exception:
        return False
    
def check_packages(package):
    try:
        importlib.import_module(package)
    except ImportError:
        return False
    return True
    
def main():
    print("Checking system requirements...")
    
    for cmd in REQUIRE_COMMANDS:
        print(f"{cmd} if {"OK" if check_command(cmd) else "MISSING"}")
    
    print(f"Python version >= {MIN_PYTHON_VERSION[0]}.{MIN_PYTHON_VERSION[1]}: {'OK' if check_python_version() else 'Too old'}")
    print(f"Android emulator available: {'OK' if check_emulator_installed() else 'Missing or error'}")
    
    for package in REQUIRE_PACKAGES:
        print(f"{package} is {"OK" if check_packages(package) else "MISSING"}")
    
if __name__ == "__main__":
    main()


    
    