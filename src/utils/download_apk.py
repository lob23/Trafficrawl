import os
import requests
from bs4 import BeautifulSoup
import subprocess

def get_emulator_abi():
    try:
        result = subprocess.run(['adb', 'shell', 'getprop', 'ro.product.cpu.abi'])
        return result.decode().strip()
    except Exception as e:
        print("Error detecting emulator ABI:", e)
        return "arm64-v8a" 