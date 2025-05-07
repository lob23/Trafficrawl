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
    
def download_apk(package_name, abi, output_file='downloaded.apk'):
    dpi = 'nodpi'
    lang = 'en'
    url = f"https://apkcombo.com/downloader-api/?device=&arch={abi}&dpi={dpi}&package={package_name}&lang={lang}"