import requests
import argparse
import os

def download_easylist(url, save_path):
    try:
        
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        response = requests.get(url)
        response.raise_for_status()
        with open(save_path, 'w', encoding='utf-8') as file:
            file.write(response.text)
        print(f"File successfully downloaded and saved to {save_path}")
    except Exception as e:
        print(f"An error occurred: {e}")
    
def main():
    parser = argparse.ArgumentParser(description="Download easylist and easyprivacy")
    parser.add_argument("url", type=str, help="The URL to EasyList and EasyPrivacy")
    parser.add_argument("save_path", type=str, help="The local path to save the downloaded file")
    
    args = parser.parse_args()
    
    download_easylist(args.url, args.save_path)
    
if __name__ == "__main__":
    main()